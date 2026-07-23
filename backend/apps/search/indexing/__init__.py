"""
Search indexing module.

This module provides a provider-agnostic indexing engine that keeps search
providers synchronized with application data. It serves as the single source
of truth for document indexing across all search providers.
"""

from apps.search.indexing.documents import (
    CandidateDocument,
    ResumeDocument,
    JobDocument,
    CompanyDocument,
    RecruiterDocument,
    SkillDocument,
    ApplicationDocument,
    InterviewDocument,
)
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
from apps.search.indexing.index_manager import IndexManager
from apps.search.indexing.sync_service import SyncService
from apps.search.indexing.bulk_indexer import BulkIndexer
from apps.search.indexing.event_handlers import register_indexing_signals
from apps.search.indexing.metrics import IndexingMetrics

__all__ = [
    # Documents
    "CandidateDocument",
    "ResumeDocument",
    "JobDocument",
    "CompanyDocument",
    "RecruiterDocument",
    "SkillDocument",
    "ApplicationDocument",
    "InterviewDocument",
    # Serializers
    "CandidateSerializer",
    "ResumeSerializer",
    "JobSerializer",
    "CompanySerializer",
    "RecruiterSerializer",
    "SkillSerializer",
    "ApplicationSerializer",
    "InterviewSerializer",
    # Core services
    "IndexManager",
    "SyncService",
    "BulkIndexer",
    # Event handlers
    "register_indexing_signals",
    # Metrics
    "IndexingMetrics",
]
