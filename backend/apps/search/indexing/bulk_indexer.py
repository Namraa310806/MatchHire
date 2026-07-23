"""
Bulk Indexing Framework.

This module implements a memory-efficient bulk indexing framework with
chunked batches, progress reporting, transaction safety, resume capability,
and retry strategies.
"""

from typing import Any, Dict, List, Optional, Callable, Iterator
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
from enum import Enum
import json
import os

from django.db import transaction
from django.db.models import QuerySet

from apps.search.indexing.documents import BaseDocument, EntityType
from apps.search.indexing.sync_service import SyncService, SyncProgress, SyncResult, SyncStatus
from apps.search.indexing.metrics import get_metrics
from apps.search.exceptions import SearchError

logger = logging.getLogger(__name__)


class BulkIndexStatus(str, Enum):
    """Enumeration of bulk indexing statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BulkIndexJob:
    """Represents a bulk indexing job."""
    job_id: str
    entity_type: EntityType
    status: BulkIndexStatus = BulkIndexStatus.PENDING
    total_count: int = 0
    processed_count: int = 0
    failed_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    checkpoint: Optional[str] = None  # For resume capability
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_count == 0:
            return 100.0
        return (self.processed_count / self.total_count) * 100
    
    @property
    def duration(self) -> float:
        """Calculate duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            return (datetime.utcnow() - self.start_time).total_seconds()
        return 0.0
    
    @property
    def documents_per_second(self) -> float:
        """Calculate documents processed per second."""
        duration = self.duration
        if duration > 0:
            return self.processed_count / duration
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for serialization."""
        return {
            "job_id": self.job_id,
            "entity_type": self.entity_type.value,
            "status": self.status.value,
            "total_count": self.total_count,
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error_message": self.error_message,
            "checkpoint": self.checkpoint,
            "metadata": self.metadata,
            "progress_percentage": self.progress_percentage,
            "duration": self.duration,
            "documents_per_second": self.documents_per_second,
        }


class BulkIndexer:
    """
    Memory-efficient bulk indexing framework.
    
    This class provides chunked batch processing, progress reporting,
    transaction safety, resume capability, and retry strategies.
    """
    
    def __init__(self, sync_service: SyncService, chunk_size: int = 100):
        """
        Initialize the bulk indexer.
        
        Args:
            sync_service: SyncService instance for document synchronization
            chunk_size: Number of documents to process per chunk
        """
        self.sync_service = sync_service
        self.chunk_size = chunk_size
        self.metrics = get_metrics()
        
        # Job storage (in production, use database or Redis)
        self._jobs: Dict[str, BulkIndexJob] = {}
        
        # Checkpoint directory
        self.checkpoint_dir = "search_indexing_checkpoints"
        os.makedirs(self.checkpoint_dir, exist_ok=True)
    
    def create_job(
        self,
        entity_type: EntityType,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BulkIndexJob:
        """
        Create a new bulk indexing job.
        
        Args:
            entity_type: Type of entity to index
            metadata: Optional metadata for the job
            
        Returns:
            BulkIndexJob instance
        """
        import uuid
        job_id = str(uuid.uuid4())
        
        job = BulkIndexJob(
            job_id=job_id,
            entity_type=entity_type,
            metadata=metadata or {},
        )
        
        self._jobs[job_id] = job
        self._save_checkpoint(job)
        
        return job
    
    def execute_job(
        self,
        job: BulkIndexJob,
        progress_callback: Optional[Callable[[BulkIndexJob], None]] = None,
        use_transaction: bool = True,
    ) -> BulkIndexJob:
        """
        Execute a bulk indexing job.
        
        Args:
            job: BulkIndexJob to execute
            progress_callback: Optional callback for progress updates
            use_transaction: Whether to use database transactions
            
        Returns:
            Updated BulkIndexJob
        """
        job.status = BulkIndexStatus.IN_PROGRESS
        job.start_time = datetime.utcnow()
        self._save_checkpoint(job)
        
        try:
            # Get total count
            documents = self._get_document_iterator(job.entity_type)
            job.total_count = self._count_documents(job.entity_type)
            
            # Process in chunks
            chunk = []
            for document in documents:
                chunk.append(document)
                
                if len(chunk) >= self.chunk_size:
                    self._process_chunk(
                        chunk,
                        job,
                        use_transaction,
                    )
                    chunk.clear()
                    
                    # Save checkpoint
                    self._save_checkpoint(job)
                    
                    # Call progress callback
                    if progress_callback:
                        progress_callback(job)
            
            # Process remaining documents
            if chunk:
                self._process_chunk(chunk, job, use_transaction)
            
            job.status = BulkIndexStatus.COMPLETED
            job.end_time = datetime.utcnow()
            
        except Exception as e:
            job.status = BulkIndexStatus.FAILED
            job.error_message = str(e)
            job.end_time = datetime.utcnow()
            logger.error(f"Bulk indexing job {job.job_id} failed: {e}")
        
        self._save_checkpoint(job)
        return job
    
    def _process_chunk(
        self,
        documents: List[BaseDocument],
        job: BulkIndexJob,
        use_transaction: bool,
    ) -> None:
        """
        Process a chunk of documents.
        
        Args:
            documents: List of documents to process
            job: BulkIndexJob being executed
            use_transaction: Whether to use database transactions
        """
        if use_transaction:
            with transaction.atomic():
                self._sync_documents(documents, job)
        else:
            self._sync_documents(documents, job)
    
    def _sync_documents(
        self,
        documents: List[BaseDocument],
        job: BulkIndexJob,
    ) -> None:
        """
        Synchronize documents to search provider.
        
        Args:
            documents: List of documents to sync
            job: BulkIndexJob being executed
        """
        results = self.sync_service.sync_bulk_documents(documents)
        
        for result in results:
            job.processed_count += 1
            if result.status == SyncStatus.FAILED:
                job.failed_count += 1
        
        # Update checkpoint
        job.checkpoint = str(job.processed_count)
    
    def resume_job(
        self,
        job_id: str,
        progress_callback: Optional[Callable[[BulkIndexJob], None]] = None,
    ) -> BulkIndexJob:
        """
        Resume a paused or failed bulk indexing job.
        
        Args:
            job_id: ID of the job to resume
            progress_callback: Optional callback for progress updates
            
        Returns:
            Updated BulkIndexJob
        """
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        if job.status not in [BulkIndexStatus.PAUSED, BulkIndexStatus.FAILED]:
            raise ValueError(f"Job {job_id} cannot be resumed (status: {job.status})")
        
        # Load checkpoint
        self._load_checkpoint(job)
        
        # Resume from checkpoint
        job.status = BulkIndexStatus.IN_PROGRESS
        
        # Get documents starting from checkpoint
        documents = self._get_document_iterator(job.entity_type)
        skip_count = int(job.checkpoint) if job.checkpoint else 0
        
        for i, document in enumerate(documents):
            if i < skip_count:
                continue
            
            result = self.sync_service.sync_single_document(document)
            job.processed_count += 1
            if result.status == SyncStatus.FAILED:
                job.failed_count += 1
            
            # Save checkpoint periodically
            if job.processed_count % self.chunk_size == 0:
                self._save_checkpoint(job)
                if progress_callback:
                    progress_callback(job)
        
        job.status = BulkIndexStatus.COMPLETED
        job.end_time = datetime.utcnow()
        self._save_checkpoint(job)
        
        return job
    
    def pause_job(self, job_id: str) -> BulkIndexJob:
        """
        Pause a running bulk indexing job.
        
        Args:
            job_id: ID of the job to pause
            
        Returns:
            Updated BulkIndexJob
        """
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        if job.status != BulkIndexStatus.IN_PROGRESS:
            raise ValueError(f"Job {job_id} is not running (status: {job.status})")
        
        job.status = BulkIndexStatus.PAUSED
        self._save_checkpoint(job)
        
        return job
    
    def cancel_job(self, job_id: str) -> BulkIndexJob:
        """
        Cancel a bulk indexing job.
        
        Args:
            job_id: ID of the job to cancel
            
        Returns:
            Updated BulkIndexJob
        """
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        job.status = BulkIndexStatus.CANCELLED
        job.end_time = datetime.utcnow()
        self._save_checkpoint(job)
        
        return job
    
    def get_job(self, job_id: str) -> Optional[BulkIndexJob]:
        """
        Get a bulk indexing job by ID.
        
        Args:
            job_id: ID of the job
            
        Returns:
            BulkIndexJob if found, None otherwise
        """
        return self._jobs.get(job_id)
    
    def list_jobs(
        self,
        entity_type: Optional[EntityType] = None,
        status: Optional[BulkIndexStatus] = None,
    ) -> List[BulkIndexJob]:
        """
        List bulk indexing jobs with optional filters.
        
        Args:
            entity_type: Optional entity type filter
            status: Optional status filter
            
        Returns:
            List of BulkIndexJob instances
        """
        jobs = list(self._jobs.values())
        
        if entity_type:
            jobs = [j for j in jobs if j.entity_type == entity_type]
        
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        return jobs
    
    def _get_document_iterator(
        self,
        entity_type: EntityType,
    ) -> Iterator[BaseDocument]:
        """
        Get a memory-efficient iterator for documents.
        
        Args:
            entity_type: Type of entity
            
        Returns:
            Iterator of BaseDocument instances
        """
        from apps.search.indexing.serializers import (
            CandidateSerializer,
            RecruiterSerializer,
            JobSerializer,
            ResumeSerializer,
            ApplicationSerializer,
        )
        from apps.users.models import User
        from apps.jobs.models import Job
        from apps.resumes.models import ResumeVersion
        from apps.applications.models import Application
        
        # Use Django's iterator() for memory efficiency
        if entity_type == EntityType.CANDIDATE:
            users = User.objects.filter(
                role=User.Roles.CANDIDATE,
            ).select_related("candidate_profile").iterator()
            for user in users:
                yield CandidateSerializer.serialize_from_user(user)
        
        elif entity_type == EntityType.RECRUITER:
            users = User.objects.filter(
                role=User.Roles.RECRUITER,
            ).select_related("recruiter_profile").iterator()
            for user in users:
                yield RecruiterSerializer.serialize_from_user(user)
        
        elif entity_type == EntityType.JOB:
            jobs = Job.objects.all().iterator()
            for job in jobs:
                yield JobSerializer.serialize(job)
        
        elif entity_type == EntityType.RESUME:
            versions = ResumeVersion.objects.filter(
                is_current=True,
            ).select_related("resume__user").iterator()
            for version in versions:
                yield ResumeSerializer.serialize(version)
        
        elif entity_type == EntityType.APPLICATION:
            applications = Application.objects.all().iterator()
            for application in applications:
                yield ApplicationSerializer.serialize(application)
    
    def _count_documents(self, entity_type: EntityType) -> int:
        """
        Count total documents for an entity type.
        
        Args:
            entity_type: Type of entity
            
        Returns:
            Total count
        """
        from apps.users.models import User
        from apps.jobs.models import Job
        from apps.resumes.models import ResumeVersion
        from apps.applications.models import Application
        
        if entity_type == EntityType.CANDIDATE:
            return User.objects.filter(role=User.Roles.CANDIDATE).count()
        elif entity_type == EntityType.RECRUITER:
            return User.objects.filter(role=User.Roles.RECRUITER).count()
        elif entity_type == EntityType.JOB:
            return Job.objects.count()
        elif entity_type == EntityType.RESUME:
            return ResumeVersion.objects.filter(is_current=True).count()
        elif entity_type == EntityType.APPLICATION:
            return Application.objects.count()
        
        return 0
    
    def _save_checkpoint(self, job: BulkIndexJob) -> None:
        """
        Save job checkpoint to disk.
        
        Args:
            job: BulkIndexJob to save
        """
        checkpoint_path = os.path.join(
            self.checkpoint_dir,
            f"{job.job_id}.json",
        )
        
        with open(checkpoint_path, "w") as f:
            json.dump(job.to_dict(), f, indent=2)
    
    def _load_checkpoint(self, job: BulkIndexJob) -> None:
        """
        Load job checkpoint from disk.
        
        Args:
            job: BulkIndexJob to load checkpoint into
        """
        checkpoint_path = os.path.join(
            self.checkpoint_dir,
            f"{job.job_id}.json",
        )
        
        if os.path.exists(checkpoint_path):
            with open(checkpoint_path, "r") as f:
                data = json.load(f)
                job.checkpoint = data.get("checkpoint")
                job.processed_count = data.get("processed_count", 0)
                job.failed_count = data.get("failed_count", 0)
    
    def cleanup_checkpoints(self, older_than_days: int = 7) -> int:
        """
        Clean up old checkpoint files.
        
        Args:
            older_than_days: Delete checkpoints older than this many days
            
        Returns:
            Number of files deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        deleted_count = 0
        
        for filename in os.listdir(self.checkpoint_dir):
            if not filename.endswith(".json"):
                continue
            
            filepath = os.path.join(self.checkpoint_dir, filename)
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            
            if file_time < cutoff:
                os.remove(filepath)
                deleted_count += 1
        
        return deleted_count
