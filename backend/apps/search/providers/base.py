"""
Base search provider interface.

This module defines the abstract interface that all search providers must implement.
The interface is provider-agnostic and does not depend on any specific search engine.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class IndexResult:
    """Result of a single document indexing operation."""
    success: bool
    document_id: str
    error: Optional[str] = None
    took_ms: Optional[int] = None


@dataclass
class BulkIndexResult:
    """Result of a bulk document indexing operation."""
    success: bool
    indexed_count: int
    failed_count: int
    errors: List[Dict[str, Any]]
    took_ms: Optional[int] = None


@dataclass
class DeleteResult:
    """Result of a document deletion operation."""
    success: bool
    document_id: str
    error: Optional[str] = None
    took_ms: Optional[int] = None


@dataclass
class BulkDeleteResult:
    """Result of a bulk document deletion operation."""
    success: bool
    deleted_count: int
    failed_count: int
    errors: List[Dict[str, Any]]
    took_ms: Optional[int] = None


@dataclass
class HealthResult:
    """Result of a health check operation."""
    healthy: bool
    provider_name: str
    details: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class StatisticsResult:
    """Result of a statistics query operation."""
    document_count: int
    index_size_bytes: Optional[int] = None
    details: Dict[str, Any] = None


class SearchProvider(ABC):
    """
    Abstract base class for search providers.

    All search providers (PostgreSQL, Elasticsearch, OpenSearch, Vector, Hybrid)
    must implement this interface to ensure compatibility with the search service layer.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the search provider with configuration.

        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        self._initialize()

    @abstractmethod
    def _initialize(self) -> None:
        """
        Initialize the provider connection and resources.

        This method is called during __init__ and should establish
        connections to the search engine, create indexes if needed, etc.
        """
        pass

    @abstractmethod
    def search(
        self,
        entity_type: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
        pagination: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a search query.

        Args:
            entity_type: Type of entity to search (e.g., 'job', 'candidate', 'resume')
            query: Search query string
            filters: Dictionary of field filters
            sort: List of sort specifications (field, direction)
            pagination: Pagination parameters (page, page_size or offset, limit)
            fields: List of fields to return (None for all fields)

        Returns:
            Dictionary containing:
                - results: List of matching documents
                - total: Total number of matching documents
                - took_ms: Query execution time in milliseconds
                - metadata: Additional provider-specific metadata
        """
        pass

    @abstractmethod
    def autocomplete(
        self,
        entity_type: str,
        field: str,
        prefix: str,
        context: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get autocomplete suggestions for a field prefix.

        Args:
            entity_type: Type of entity to search
            field: Field to autocomplete on
            prefix: Prefix string to match
            context: Additional context for suggestions
            limit: Maximum number of suggestions to return

        Returns:
            List of suggestion dictionaries with 'value' and optional 'metadata'
        """
        pass

    @abstractmethod
    def index(
        self,
        entity_type: str,
        document_id: str,
        document: Dict[str, Any],
    ) -> IndexResult:
        """
        Index a single document.

        Args:
            entity_type: Type of entity being indexed
            document_id: Unique identifier for the document
            document: Document data to index

        Returns:
            IndexResult with success status and metadata
        """
        pass

    @abstractmethod
    def bulk_index(
        self,
        entity_type: str,
        documents: List[Dict[str, Any]],
    ) -> BulkIndexResult:
        """
        Index multiple documents in bulk.

        Args:
            entity_type: Type of entities being indexed
            documents: List of documents to index, each with 'id' field

        Returns:
            BulkIndexResult with success status and counts
        """
        pass

    @abstractmethod
    def delete(
        self,
        entity_type: str,
        document_id: str,
    ) -> DeleteResult:
        """
        Delete a single document from the index.

        Args:
            entity_type: Type of entity being deleted
            document_id: Unique identifier for the document

        Returns:
            DeleteResult with success status and metadata
        """
        pass

    @abstractmethod
    def bulk_delete(
        self,
        entity_type: str,
        document_ids: List[str],
    ) -> BulkDeleteResult:
        """
        Delete multiple documents from the index in bulk.

        Args:
            entity_type: Type of entities being deleted
            document_ids: List of document identifiers to delete

        Returns:
            BulkDeleteResult with success status and counts
        """
        pass

    @abstractmethod
    def health(self) -> HealthResult:
        """
        Check the health of the search provider.

        Returns:
            HealthResult with health status and details
        """
        pass

    @abstractmethod
    def statistics(
        self,
        entity_type: Optional[str] = None,
    ) -> StatisticsResult:
        """
        Get statistics about indexed documents.

        Args:
            entity_type: Optional entity type to filter statistics

        Returns:
            StatisticsResult with document counts and metadata
        """
        pass

    def close(self) -> None:
        """
        Close provider connections and cleanup resources.

        This method is called when the provider is being shut down.
        Default implementation does nothing; override if cleanup is needed.
        """
        pass
