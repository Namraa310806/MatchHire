"""
Integrity verification tools.

This module provides tools for verifying search index integrity including
missing documents, extra documents, version mismatches, orphaned documents,
relationship consistency, and synchronization status.
"""

from typing import Any, Dict, List, Set, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

from apps.search.indexing.documents import BaseDocument, EntityType
from apps.search.indexing.index_manager import IndexManager
from apps.search.indexing.serializers import (
    CandidateSerializer,
    RecruiterSerializer,
    JobSerializer,
    ResumeSerializer,
    ApplicationSerializer,
)
from apps.search.exceptions import SearchError

logger = logging.getLogger(__name__)


@dataclass
class VerificationIssue:
    """Represents a verification issue."""
    issue_type: str
    entity_type: str
    document_id: str
    description: str
    severity: str  # "critical", "warning", "info"
    metadata: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class VerificationReport:
    """Report from index verification."""
    entity_type: str
    total_db_documents: int
    total_index_documents: int
    issues: List[VerificationIssue]
    verified_at: datetime
    
    @property
    def is_healthy(self) -> bool:
        """Check if the index is healthy (no critical issues)."""
        critical_issues = [i for i in self.issues if i.severity == "critical"]
        return len(critical_issues) == 0
    
    @property
    def issue_count(self) -> int:
        """Total number of issues."""
        return len(self.issues)
    
    @property
    def critical_count(self) -> int:
        """Number of critical issues."""
        return sum(1 for i in self.issues if i.severity == "critical")
    
    @property
    def warning_count(self) -> int:
        """Number of warning issues."""
        return sum(1 for i in self.issues if i.severity == "warning")
    
    @property
    def info_count(self) -> int:
        """Number of info issues."""
        return sum(1 for i in self.issues if i.severity == "info")


class IndexVerifier:
    """
    Index integrity verifier.
    
    This class provides comprehensive verification of search index integrity
    including missing documents, extra documents, version mismatches, and
    relationship consistency.
    """
    
    def __init__(self, index_manager: IndexManager):
        """
        Initialize the verifier.
        
        Args:
            index_manager: IndexManager instance
        """
        self.index_manager = index_manager
    
    def verify_entity_type(
        self,
        entity_type: EntityType,
        detailed: bool = False,
    ) -> VerificationReport:
        """
        Verify a specific entity type.
        
        Args:
            entity_type: Entity type to verify
            detailed: Whether to perform detailed verification
            
        Returns:
            VerificationReport
        """
        issues = []
        
        # Get documents from database
        db_documents = self._get_db_documents(entity_type)
        db_ids = {doc.id for doc in db_documents}
        
        # Get documents from index
        index_documents = self._get_index_documents(entity_type)
        index_ids = {doc["id"] for doc in index_documents}
        
        # Check for missing documents
        missing_ids = db_ids - index_ids
        for doc_id in missing_ids:
            issues.append(VerificationIssue(
                issue_type="missing_document",
                entity_type=entity_type.value,
                document_id=doc_id,
                description="Document exists in database but not in search index",
                severity="critical",
                metadata={"location": "database_only"},
            ))
        
        # Check for extra documents
        extra_ids = index_ids - db_ids
        for doc_id in extra_ids:
            issues.append(VerificationIssue(
                issue_type="extra_document",
                entity_type=entity_type.value,
                document_id=doc_id,
                description="Document exists in search index but not in database",
                severity="warning",
                metadata={"location": "index_only"},
            ))
        
        # Check version mismatches
        if detailed:
            db_doc_map = {doc.id: doc for doc in db_documents}
            index_doc_map = {doc["id"]: doc for doc in index_documents}
            
            for doc_id in db_ids & index_ids:
                db_doc = db_doc_map[doc_id]
                index_doc = index_doc_map[doc_id]
                
                if db_doc.version != index_doc.get("version", 1):
                    issues.append(VerificationIssue(
                        issue_type="version_mismatch",
                        entity_type=entity_type.value,
                        document_id=doc_id,
                        description=f"Document version mismatch (DB: {db_doc.version}, Index: {index_doc.get('version', 1)})",
                        severity="warning",
                        metadata={
                            "db_version": db_doc.version,
                            "index_version": index_doc.get("version", 1),
                        },
                    ))
        
        # Check for orphaned documents
        orphaned = self._check_orphaned_documents(entity_type, db_documents)
        for doc_id in orphaned:
            issues.append(VerificationIssue(
                issue_type="orphaned_document",
                entity_type=entity_type.value,
                document_id=doc_id,
                description="Document has broken or missing relationships",
                severity="warning",
                metadata={"issue": "broken_relationships"},
            ))
        
        # Check relationship consistency
        relationship_issues = self._check_relationships(entity_type, db_documents)
        for issue in relationship_issues:
            issues.append(VerificationIssue(
                issue_type="relationship_issue",
                entity_type=entity_type.value,
                document_id=issue["document_id"],
                description=issue["description"],
                severity="warning",
                metadata=issue["metadata"],
            ))
        
        return VerificationReport(
            entity_type=entity_type.value,
            total_db_documents=len(db_documents),
            total_index_documents=len(index_documents),
            issues=issues,
            verified_at=datetime.utcnow(),
        )
    
    def verify_all_entity_types(
        self,
        detailed: bool = False,
    ) -> List[VerificationReport]:
        """
        Verify all entity types.
        
        Args:
            detailed: Whether to perform detailed verification
            
        Returns:
            List of VerificationReports
        """
        reports = []
        
        for entity_type in EntityType:
            try:
                report = self.verify_entity_type(entity_type, detailed)
                reports.append(report)
            except Exception as e:
                logger.error(f"Failed to verify {entity_type.value}: {e}")
                reports.append(VerificationReport(
                    entity_type=entity_type.value,
                    total_db_documents=0,
                    total_index_documents=0,
                    issues=[VerificationIssue(
                        issue_type="verification_error",
                        entity_type=entity_type.value,
                        document_id="",
                        description=f"Verification failed: {str(e)}",
                        severity="critical",
                        metadata={"error": str(e)},
                    )],
                    verified_at=datetime.utcnow(),
                ))
        
        return reports
    
    def _get_db_documents(self, entity_type: EntityType) -> List[BaseDocument]:
        """
        Get documents from database.
        
        Args:
            entity_type: Entity type
            
        Returns:
            List of BaseDocument instances
        """
        from apps.users.models import User
        from apps.jobs.models import Job
        from apps.resumes.models import ResumeVersion
        from apps.applications.models import Application
        
        documents = []
        
        if entity_type == EntityType.CANDIDATE:
            users = User.objects.filter(role=User.Roles.CANDIDATE).select_related("candidate_profile")
            for user in users:
                documents.append(CandidateSerializer.serialize_from_user(user))
        
        elif entity_type == EntityType.RECRUITER:
            users = User.objects.filter(role=User.Roles.RECRUITER).select_related("recruiter_profile")
            for user in users:
                documents.append(RecruiterSerializer.serialize_from_user(user))
        
        elif entity_type == EntityType.JOB:
            jobs = Job.objects.all()
            for job in jobs:
                documents.append(JobSerializer.serialize(job))
        
        elif entity_type == EntityType.RESUME:
            versions = ResumeVersion.objects.filter(is_current=True).select_related("resume__user")
            for version in versions:
                documents.append(ResumeSerializer.serialize(version))
        
        elif entity_type == EntityType.APPLICATION:
            applications = Application.objects.all()
            for application in applications:
                documents.append(ApplicationSerializer.serialize(application))
        
        return documents
    
    def _get_index_documents(self, entity_type: EntityType) -> List[Dict[str, Any]]:
        """
        Get documents from search index.
        
        Args:
            entity_type: Entity type
            
        Returns:
            List of document dictionaries
        """
        # This would call the provider to get indexed documents
        # For now, return empty list as placeholder
        # In production, this would call provider.get_all_documents()
        if hasattr(self.index_manager.provider, "get_all_documents"):
            return self.index_manager.provider.get_all_documents(entity_type.value)
        return []
    
    def _check_orphaned_documents(
        self,
        entity_type: EntityType,
        db_documents: List[BaseDocument],
    ) -> Set[str]:
        """
        Check for orphaned documents.
        
        Args:
            entity_type: Entity type
            db_documents: List of documents from database
            
        Returns:
            Set of orphaned document IDs
        """
        orphaned = set()
        
        # Check for documents with broken relationships
        for document in db_documents:
            # Placeholder: Add specific orphaned document checks
            # For example, check if referenced entities still exist
            pass
        
        return orphaned
    
    def _check_relationships(
        self,
        entity_type: EntityType,
        db_documents: List[BaseDocument],
    ) -> List[Dict[str, Any]]:
        """
        Check relationship consistency.
        
        Args:
            entity_type: Entity type
            db_documents: List of documents from database
            
        Returns:
            List of relationship issue dictionaries
        """
        issues = []
        
        # Check for relationship consistency issues
        for document in db_documents:
            # Placeholder: Add specific relationship checks
            # For example, check if foreign keys point to valid entities
            pass
        
        return issues
    
    def get_summary(self, reports: List[VerificationReport]) -> Dict[str, Any]:
        """
        Get a summary of verification reports.
        
        Args:
            reports: List of VerificationReports
            
        Returns:
            Summary dictionary
        """
        total_db_docs = sum(r.total_db_documents for r in reports)
        total_index_docs = sum(r.total_index_documents for r in reports)
        total_issues = sum(r.issue_count for r in reports)
        critical_issues = sum(r.critical_count for r in reports)
        warning_issues = sum(r.warning_count for r in reports)
        info_issues = sum(r.info_count for r in reports)
        healthy_count = sum(1 for r in reports if r.is_healthy)
        
        return {
            "total_entity_types": len(reports),
            "total_db_documents": total_db_docs,
            "total_index_documents": total_index_docs,
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "warning_issues": warning_issues,
            "info_issues": info_issues,
            "healthy_entity_types": healthy_count,
            "unhealthy_entity_types": len(reports) - healthy_count,
            "overall_healthy": critical_issues == 0,
        }
