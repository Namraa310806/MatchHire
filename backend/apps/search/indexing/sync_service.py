"""
Synchronization Service.

This module implements the synchronization engine that keeps search providers
in sync with application data. It supports single document sync, bulk sync,
incremental sync, full rebuild, retry logic, and progress tracking.
"""

from typing import Any, Dict, List, Optional, Iterator
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from enum import Enum

from apps.search.indexing.documents import BaseDocument, EntityType
from apps.search.indexing.serializers import (
    CandidateSerializer,
    ResumeSerializer,
    JobSerializer,
    CompanySerializer,
    RecruiterSerializer,
    SkillSerializer,
    ApplicationSerializer,
    InterviewSerializer,
)
from apps.search.indexing.metrics import get_metrics
from apps.search.exceptions import SearchError

logger = logging.getLogger(__name__)


class SyncStatus(str, Enum):
    """Enumeration of synchronization statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class SyncResult:
    """Result of a synchronization operation."""
    document_id: str
    entity_type: str
    status: SyncStatus
    error: Optional[str] = None
    duration_seconds: float = 0.0
    retry_count: int = 0


@dataclass
class SyncProgress:
    """Progress tracking for synchronization operations."""
    total: int
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total == 0:
            return 100.0
        return (self.completed / self.total) * 100
    
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
            return self.completed / duration
        return 0.0


class SyncService:
    """
    Synchronization service for keeping search providers in sync.
    
    This service handles all synchronization operations including single
    document sync, bulk sync, incremental sync, and full rebuilds.
    """
    
    def __init__(self, provider: Any):
        """
        Initialize the synchronization service.
        
        Args:
            provider: Search provider instance
        """
        self.provider = provider
        self.metrics = get_metrics()
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = timedelta(seconds=1)
        
        # Dead letter queue placeholder
        self._dead_letter_queue: List[SyncResult] = []
    
    def sync_single_document(
        self,
        document: BaseDocument,
        retry_count: int = 0,
    ) -> SyncResult:
        """
        Synchronize a single document to the search provider.
        
        Args:
            document: Search document to sync
            retry_count: Current retry attempt
            
        Returns:
            SyncResult with operation details
        """
        start_time = datetime.utcnow()
        
        try:
            # Delegate to provider
            if hasattr(self.provider, "index_document"):
                self.provider.index_document(document.to_dict())
            else:
                # For PostgreSQL provider, sync is implicit
                logger.debug(f"Document sync for {document.entity_type} is implicit for PostgreSQL provider")
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Record metrics
            self.metrics.record_document_synced(
                entity_type=document.entity_type.value,
                success=True,
            )
            
            return SyncResult(
                document_id=document.id,
                entity_type=document.entity_type.value,
                status=SyncStatus.COMPLETED,
                duration_seconds=duration,
                retry_count=retry_count,
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            error_message = str(e)
            
            # Record metrics
            self.metrics.record_document_synced(
                entity_type=document.entity_type.value,
                success=False,
            )
            
            # Retry logic
            if retry_count < self.max_retries:
                logger.warning(
                    f"Sync failed for {document.entity_type.value}:{document.id}, "
                    f"retrying ({retry_count + 1}/{self.max_retries}): {error_message}"
                )
                return self._retry_sync(document, retry_count)
            
            # Add to dead letter queue
            logger.error(
                f"Sync failed for {document.entity_type.value}:{document.id} "
                f"after {retry_count} retries: {error_message}"
            )
            self._dead_letter_queue.append(
                SyncResult(
                    document_id=document.id,
                    entity_type=document.entity_type.value,
                    status=SyncStatus.FAILED,
                    error=error_message,
                    duration_seconds=duration,
                    retry_count=retry_count,
                )
            )
            
            return SyncResult(
                document_id=document.id,
                entity_type=document.entity_type.value,
                status=SyncStatus.FAILED,
                error=error_message,
                duration_seconds=duration,
                retry_count=retry_count,
            )
    
    def _retry_sync(
        self,
        document: BaseDocument,
        retry_count: int,
    ) -> SyncResult:
        """
        Retry a failed synchronization.
        
        Args:
            document: Search document to retry
            retry_count: Current retry attempt
            
        Returns:
            SyncResult with operation details
        """
        import time
        time.sleep(self.retry_delay.total_seconds())
        return self.sync_single_document(document, retry_count + 1)
    
    def sync_bulk_documents(
        self,
        documents: List[BaseDocument],
        progress_callback: Optional[callable] = None,
    ) -> List[SyncResult]:
        """
        Synchronize multiple documents in bulk.
        
        Args:
            documents: List of search documents to sync
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of SyncResults
        """
        progress = SyncProgress(total=len(documents), start_time=datetime.utcnow())
        results = []
        
        for document in documents:
            result = self.sync_single_document(document)
            results.append(result)
            
            # Update progress
            if result.status == SyncStatus.COMPLETED:
                progress.completed += 1
            elif result.status == SyncStatus.FAILED:
                progress.failed += 1
            else:
                progress.skipped += 1
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(progress)
        
        progress.end_time = datetime.utcnow()
        
        # Record metrics
        self.metrics.record_document_indexed(
            entity_type="bulk",
            count=progress.completed,
        )
        
        return results
    
    def sync_incremental(
        self,
        entity_type: EntityType,
        since: datetime,
        progress_callback: Optional[callable] = None,
    ) -> SyncProgress:
        """
        Synchronize documents changed since a given timestamp.
        
        Args:
            entity_type: Type of entity to sync
            since: Only sync documents updated after this timestamp
            progress_callback: Optional callback for progress updates
            
        Returns:
            SyncProgress with operation details
        """
        start_time = datetime.utcnow()

        # Get documents changed since timestamp
        documents = self._get_documents_since(entity_type, since)
        
        # Sync documents
        results = self.sync_bulk_documents(documents, progress_callback)
        
        # Calculate progress
        progress = SyncProgress(
            total=len(documents),
            completed=sum(1 for r in results if r.status == SyncStatus.COMPLETED),
            failed=sum(1 for r in results if r.status == SyncStatus.FAILED),
            start_time=start_time,
            end_time=datetime.utcnow(),
        )
        
        return progress
    
    def sync_full_rebuild(
        self,
        entity_type: EntityType,
        progress_callback: Optional[callable] = None,
    ) -> SyncProgress:
        """
        Perform a full rebuild of the index for an entity type.
        
        Args:
            entity_type: Type of entity to rebuild
            progress_callback: Optional callback for progress updates
            
        Returns:
            SyncProgress with operation details
        """
        start_time = datetime.utcnow()

        # Get all documents for entity type
        documents = self._get_all_documents(entity_type)
        
        # Sync documents
        results = self.sync_bulk_documents(documents, progress_callback)
        
        # Calculate progress
        progress = SyncProgress(
            total=len(documents),
            completed=sum(1 for r in results if r.status == SyncStatus.COMPLETED),
            failed=sum(1 for r in results if r.status == SyncStatus.FAILED),
            start_time=start_time,
            end_time=datetime.utcnow(),
        )
        
        return progress
    
    def delete_document(
        self,
        document_id: str,
        entity_type: EntityType,
    ) -> SyncResult:
        """
        Delete a document from the search provider.
        
        Args:
            document_id: ID of document to delete
            entity_type: Type of entity
            
        Returns:
            SyncResult with operation details
        """
        start_time = datetime.utcnow()
        
        try:
            # Delegate to provider
            if hasattr(self.provider, "delete_document"):
                self.provider.delete_document(
                    document_id=document_id,
                    entity_type=entity_type.value,
                )
            else:
                # For PostgreSQL provider, deletion is implicit
                logger.debug(f"Document deletion for {entity_type.value} is implicit for PostgreSQL provider")
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return SyncResult(
                document_id=document_id,
                entity_type=entity_type.value,
                status=SyncStatus.COMPLETED,
                duration_seconds=duration,
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            error_message = str(e)
            
            logger.error(f"Failed to delete {entity_type.value}:{document_id}: {error_message}")
            
            return SyncResult(
                document_id=document_id,
                entity_type=entity_type.value,
                status=SyncStatus.FAILED,
                error=error_message,
                duration_seconds=duration,
            )
    
    def get_dead_letter_queue(self) -> List[SyncResult]:
        """
        Get all failed sync operations in the dead letter queue.
        
        Returns:
            List of failed SyncResults
        """
        return self._dead_letter_queue.copy()
    
    def retry_dead_letter_queue(self) -> List[SyncResult]:
        """
        Retry all failed sync operations in the dead letter queue.
        
        Returns:
            List of SyncResults from retry attempts
        """
        results = []
        
        # Clear the queue and retry each item
        failed_items = self._dead_letter_queue.copy()
        self._dead_letter_queue.clear()
        
        for item in failed_items:
            # Reconstruct document from metadata (placeholder)
            # In production, you would store the full document or re-fetch it
            logger.info(f"Retrying dead letter item: {item.entity_type}:{item.document_id}")
            # Placeholder: would need to reconstruct document here
            results.append(item)
        
        return results
    
    def clear_dead_letter_queue(self) -> None:
        """Clear the dead letter queue."""
        self._dead_letter_queue.clear()
    
    def _get_documents_since(
        self,
        entity_type: EntityType,
        since: datetime,
    ) -> List[BaseDocument]:
        """
        Get documents updated since a given timestamp.
        
        Args:
            entity_type: Type of entity
            since: Timestamp to filter by
            
        Returns:
            List of search documents
        """
        # Import models to avoid circular imports
        from apps.users.models import User, CandidateProfile, RecruiterProfile
        from apps.jobs.models import Job
        from apps.resumes.models import ResumeVersion
        from apps.applications.models import Application
        
        documents = []
        
        if entity_type == EntityType.CANDIDATE:
            users = User.objects.filter(
                role=User.Roles.CANDIDATE,
                updated_at__gte=since,
            ).select_related("candidate_profile")
            for user in users:
                documents.append(CandidateSerializer.serialize_from_user(user))
        
        elif entity_type == EntityType.RECRUITER:
            users = User.objects.filter(
                role=User.Roles.RECRUITER,
                updated_at__gte=since,
            ).select_related("recruiter_profile")
            for user in users:
                documents.append(RecruiterSerializer.serialize_from_user(user))
        
        elif entity_type == EntityType.JOB:
            jobs = Job.objects.filter(updated_at__gte=since)
            for job in jobs:
                documents.append(JobSerializer.serialize(job))
        
        elif entity_type == EntityType.RESUME:
            versions = ResumeVersion.objects.filter(
                created_at__gte=since,
            ).select_related("resume__user")
            for version in versions:
                documents.append(ResumeSerializer.serialize(version))
        
        elif entity_type == EntityType.APPLICATION:
            applications = Application.objects.filter(updated_at__gte=since)
            for application in applications:
                documents.append(ApplicationSerializer.serialize(application))
        
        return documents
    
    def _get_all_documents(
        self,
        entity_type: EntityType,
    ) -> List[BaseDocument]:
        """
        Get all documents for an entity type.
        
        Args:
            entity_type: Type of entity
            
        Returns:
            List of search documents
        """
        # Import models to avoid circular imports
        from apps.users.models import User, CandidateProfile, RecruiterProfile
        from apps.jobs.models import Job
        from apps.resumes.models import ResumeVersion
        from apps.applications.models import Application
        
        documents = []
        
        if entity_type == EntityType.CANDIDATE:
            users = User.objects.filter(
                role=User.Roles.CANDIDATE,
            ).select_related("candidate_profile")
            for user in users:
                documents.append(CandidateSerializer.serialize_from_user(user))
        
        elif entity_type == EntityType.RECRUITER:
            users = User.objects.filter(
                role=User.Roles.RECRUITER,
            ).select_related("recruiter_profile")
            for user in users:
                documents.append(RecruiterSerializer.serialize_from_user(user))
        
        elif entity_type == EntityType.JOB:
            jobs = Job.objects.all()
            for job in jobs:
                documents.append(JobSerializer.serialize(job))
        
        elif entity_type == EntityType.RESUME:
            versions = ResumeVersion.objects.filter(
                is_current=True,
            ).select_related("resume__user")
            for version in versions:
                documents.append(ResumeSerializer.serialize(version))
        
        elif entity_type == EntityType.APPLICATION:
            applications = Application.objects.all()
            for application in applications:
                documents.append(ApplicationSerializer.serialize(application))
        
        return documents
