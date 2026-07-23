"""
Base search service.

This module defines the base search service that provides
common functionality for all entity-specific search services.
"""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

from apps.search.providers.base import SearchProvider
from apps.search.schemas.requests import SearchRequest, AutocompleteRequest
from apps.search.schemas.responses import SearchResponse, AutocompleteResponse
from apps.search.exceptions import SearchError, ProviderUnavailable


class BaseSearchService(ABC):
    """
    Base class for entity-specific search services.

    This class provides common functionality for searching specific
    entity types (jobs, candidates, resumes, etc.).
    """

    def __init__(self, provider: SearchProvider):
        """
        Initialize the search service.

        Args:
            provider: Search provider instance to use
        """
        self.provider = provider

    @abstractmethod
    def get_entity_type(self) -> str:
        """
        Get the entity type for this service.

        Returns:
            Entity type string (e.g., 'job', 'candidate')
        """
        pass

    def search(
        self,
        request: SearchRequest,
    ) -> SearchResponse:
        """
        Execute a search using the provider.

        Args:
            request: Search request with query, filters, sort, pagination

        Returns:
            SearchResponse with results and metadata

        Raises:
            SearchError: If search operation fails
        """
        try:
            # Ensure entity type matches
            request.entity_type = self.get_entity_type()

            # Convert request to provider format
            provider_request = request.to_dict()

            # Execute search through provider
            provider_response = self.provider.search(
                entity_type=provider_request["entity_type"],
                query=provider_request.get("query", ""),
                filters=provider_request.get("filters"),
                sort=provider_request.get("sort"),
                pagination=provider_request.get("pagination"),
                fields=provider_request.get("fields"),
            )

            # Convert to standardized response
            return SearchResponse.from_provider_response(
                provider_response=provider_response,
                pagination=request.pagination,
            )

        except ProviderUnavailable as e:
            raise SearchError(f"Search provider unavailable: {e}")
        except Exception as e:
            raise SearchError(f"Search failed: {e}")

    def autocomplete(
        self,
        request: AutocompleteRequest,
    ) -> AutocompleteResponse:
        """
        Get autocomplete suggestions.

        Args:
            request: Autocomplete request with field and prefix

        Returns:
            AutocompleteResponse with suggestions

        Raises:
            SearchError: If autocomplete operation fails
        """
        try:
            # Ensure entity type matches
            request.entity_type = self.get_entity_type()

            # Execute autocomplete through provider
            provider_response = self.provider.autocomplete(
                entity_type=request.entity_type,
                field=request.field,
                prefix=request.prefix,
                context=request.context,
                limit=request.limit,
            )

            # Convert to standardized response
            return AutocompleteResponse.from_provider_response(
                provider_response=provider_response,
                entity_type=request.entity_type,
                field=request.field,
            )

        except ProviderUnavailable as e:
            raise SearchError(f"Search provider unavailable: {e}")
        except Exception as e:
            raise SearchError(f"Autocomplete failed: {e}")

    def index_document(
        self,
        document_id: str,
        document: Dict[str, Any],
    ) -> bool:
        """
        Index a single document.

        Args:
            document_id: Unique identifier for the document
            document: Document data to index

        Returns:
            True if successful, False otherwise

        Raises:
            SearchError: If indexing operation fails
        """
        try:
            result = self.provider.index(
                entity_type=self.get_entity_type(),
                document_id=document_id,
                document=document,
            )
            return result.success

        except ProviderUnavailable as e:
            raise SearchError(f"Search provider unavailable: {e}")
        except Exception as e:
            raise SearchError(f"Indexing failed: {e}")

    def bulk_index_documents(
        self,
        documents: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """
        Index multiple documents in bulk.

        Args:
            documents: List of documents to index

        Returns:
            Dictionary with 'indexed' and 'failed' counts

        Raises:
            SearchError: If bulk indexing operation fails
        """
        try:
            result = self.provider.bulk_index(
                entity_type=self.get_entity_type(),
                documents=documents,
            )
            return {
                "indexed": result.indexed_count,
                "failed": result.failed_count,
            }

        except ProviderUnavailable as e:
            raise SearchError(f"Search provider unavailable: {e}")
        except Exception as e:
            raise SearchError(f"Bulk indexing failed: {e}")

    def delete_document(
        self,
        document_id: str,
    ) -> bool:
        """
        Delete a document from the index.

        Args:
            document_id: Unique identifier for the document

        Returns:
            True if successful, False otherwise

        Raises:
            SearchError: If deletion operation fails
        """
        try:
            result = self.provider.delete(
                entity_type=self.get_entity_type(),
                document_id=document_id,
            )
            return result.success

        except ProviderUnavailable as e:
            raise SearchError(f"Search provider unavailable: {e}")
        except Exception as e:
            raise SearchError(f"Deletion failed: {e}")

    def bulk_delete_documents(
        self,
        document_ids: List[str],
    ) -> Dict[str, int]:
        """
        Delete multiple documents from the index.

        Args:
            document_ids: List of document identifiers to delete

        Returns:
            Dictionary with 'deleted' and 'failed' counts

        Raises:
            SearchError: If bulk deletion operation fails
        """
        try:
            result = self.provider.bulk_delete(
                entity_type=self.get_entity_type(),
                document_ids=document_ids,
            )
            return {
                "deleted": result.deleted_count,
                "failed": result.failed_count,
            }

        except ProviderUnavailable as e:
            raise SearchError(f"Search provider unavailable: {e}")
        except Exception as e:
            raise SearchError(f"Bulk deletion failed: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about indexed documents.

        Returns:
            Dictionary with statistics

        Raises:
            SearchError: If statistics query fails
        """
        try:
            result = self.provider.statistics(entity_type=self.get_entity_type())
            return {
                "document_count": result.document_count,
                "details": result.details,
            }

        except ProviderUnavailable as e:
            raise SearchError(f"Search provider unavailable: {e}")
        except Exception as e:
            raise SearchError(f"Statistics query failed: {e}")
