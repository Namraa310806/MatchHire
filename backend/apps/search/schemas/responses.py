"""
Search response models.

This module defines standardized response models for search operations.
All models are provider-agnostic and provide a consistent format across providers.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class Highlight:
    """Highlight information for matched text."""
    field: str
    fragments: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {"field": self.field, "fragments": self.fragments}


@dataclass
class PaginationMetadata:
    """Pagination metadata for search results."""
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

    @classmethod
    def from_total(cls, total: int, page: int, page_size: int) -> "PaginationMetadata":
        """Create pagination metadata from total count."""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        return cls(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_previous": self.has_previous,
        }


@dataclass
class FacetResponse:
    """Facet/aggregation response."""
    field: str
    values: List[Dict[str, Any]]
    total: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "field": self.field,
            "values": self.values,
            "total": self.total,
        }


@dataclass
class SuggestionResponse:
    """Autocomplete suggestion response."""
    value: str
    score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "value": self.value,
            "score": self.score,
            "metadata": self.metadata,
        }


@dataclass
class SearchResultItem:
    """Individual search result item."""
    id: str
    entity_type: str
    data: Dict[str, Any]
    score: Optional[float] = None
    highlights: List[Highlight] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "data": self.data,
            "score": self.score,
            "highlights": [h.to_dict() for h in self.highlights],
        }


@dataclass
class SearchResponse:
    """
    Standardized search response model.

    This model encapsulates all data returned from a search operation
    in a provider-agnostic way.
    """
    results: List[SearchResultItem]
    total: int
    took_ms: int
    pagination: Optional[PaginationMetadata] = None
    facets: List[FacetResponse] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "results": [r.to_dict() for r in self.results],
            "total": self.total,
            "took_ms": self.took_ms,
            "pagination": self.pagination.to_dict() if self.pagination else None,
            "facets": [f.to_dict() for f in self.facets],
            "metadata": self.metadata,
        }

    @classmethod
    def from_provider_response(
        cls,
        provider_response: Dict[str, Any],
        pagination: Optional[PaginationRequest] = None,
    ) -> "SearchResponse":
        """
        Create SearchResponse from provider-specific response.

        Args:
            provider_response: Raw response from search provider
            pagination: Original pagination request (for metadata)

        Returns:
            Standardized SearchResponse
        """
        results = []
        for item in provider_response.get("results", []):
            # Extract ID from the item
            item_id = item.get("id") or item.get("pk") or str(item)
            entity_type = provider_response.get("metadata", {}).get("entity_type", "unknown")

            results.append(
                SearchResultItem(
                    id=item_id,
                    entity_type=entity_type,
                    data=item,
                    score=item.get("score") or item.get("rank"),
                )
            )

        # Build pagination metadata
        pagination_metadata = None
        if pagination:
            total = provider_response.get("total", 0)
            pagination_metadata = PaginationMetadata.from_total(
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
            )

        return cls(
            results=results,
            total=provider_response.get("total", 0),
            took_ms=provider_response.get("took_ms", 0),
            pagination=pagination_metadata,
            metadata=provider_response.get("metadata", {}),
        )


@dataclass
class AutocompleteResponse:
    """Autocomplete response model."""
    suggestions: List[SuggestionResponse]
    took_ms: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "suggestions": [s.to_dict() for s in self.suggestions],
            "took_ms": self.took_ms,
            "metadata": self.metadata,
        }

    @classmethod
    def from_provider_response(
        cls,
        provider_response: List[Dict[str, Any]],
        entity_type: str,
        field: str,
    ) -> "AutocompleteResponse":
        """
        Create AutocompleteResponse from provider-specific response.

        Args:
            provider_response: Raw response from search provider
            entity_type: Entity type being searched
            field: Field being autocompleted

        Returns:
            Standardized AutocompleteResponse
        """
        suggestions = []
        for item in provider_response:
            value = item.get("value") or item.get(field) or str(item)
            suggestions.append(
                SuggestionResponse(
                    value=value,
                    score=item.get("score"),
                    metadata=item.get("metadata", {}),
                )
            )

        return cls(
            suggestions=suggestions,
            took_ms=0,  # Provider should track this
            metadata={"entity_type": entity_type, "field": field},
        )


@dataclass
class ErrorResponse:
    """Error response model."""
    error: str
    error_type: str
    details: Optional[Dict[str, Any]] = None
    took_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "error": self.error,
            "error_type": self.error_type,
            "details": self.details,
            "took_ms": self.took_ms,
        }
