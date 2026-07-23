"""
Search request models.

This module defines standardized request models for search operations.
All models include validation and are provider-agnostic.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class SortDirection(Enum):
    """Sort direction options."""
    ASC = "asc"
    DESC = "desc"


@dataclass
class SearchSort:
    """Sort specification for search results."""
    field: str
    direction: SortDirection = SortDirection.ASC

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        return {"field": self.field, "direction": self.direction.value}


@dataclass
class SearchFilter:
    """Filter specification for search results."""
    field: str
    value: Any
    operator: str = "exact"  # exact, gte, lte, gt, lt, in, contains

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        if self.operator == "exact":
            return {self.field: self.value}
        elif self.operator in ["gte", "lte", "gt", lt"]:
            return {self.field: {self.operator: self.value}}
        elif self.operator == "in":
            return {self.field: self.value if isinstance(self.value, list) else [self.value]}
        elif self.operator == "contains":
            return {f"{self.field}__icontains": self.value}
        else:
            return {self.field: self.value}


@dataclass
class PaginationRequest:
    """Pagination parameters for search requests."""
    page: int = 1
    page_size: int = 20

    def __post_init__(self):
        """Validate pagination parameters."""
        if self.page < 1:
            raise ValueError("page must be >= 1")
        if self.page_size < 1:
            raise ValueError("page_size must be >= 1")
        if self.page_size > 100:
            raise ValueError("page_size must be <= 100")

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary format."""
        return {"page": self.page, "page_size": self.page_size}

    def to_offset_limit(self) -> Dict[str, int]:
        """Convert to offset/limit format."""
        offset = (self.page - 1) * self.page_size
        return {"offset": offset, "limit": self.page_size}


@dataclass
class AutocompleteRequest:
    """Request model for autocomplete operations."""
    entity_type: str
    field: str
    prefix: str
    context: Optional[Dict[str, Any]] = None
    limit: int = 10

    def __post_init__(self):
        """Validate autocomplete parameters."""
        if not self.entity_type:
            raise ValueError("entity_type is required")
        if not self.field:
            raise ValueError("field is required")
        if not self.prefix:
            raise ValueError("prefix is required")
        if self.limit < 1:
            raise ValueError("limit must be >= 1")
        if self.limit > 50:
            raise ValueError("limit must be <= 50")


@dataclass
class SearchRequest:
    """
    Standardized search request model.

    This model encapsulates all parameters for a search operation
    in a provider-agnostic way.
    """
    entity_type: str
    query: str = ""
    filters: List[SearchFilter] = field(default_factory=list)
    sort: List[SearchSort] = field(default_factory=list)
    pagination: Optional[PaginationRequest] = None
    fields: Optional[List[str]] = None

    def __post_init__(self):
        """Validate search request parameters."""
        if not self.entity_type:
            raise ValueError("entity_type is required")

        # Set default pagination if not provided
        if self.pagination is None:
            self.pagination = PaginationRequest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for provider consumption."""
        filters_dict = {}
        for f in self.filters:
            filter_dict = f.to_dict()
            filters_dict.update(filter_dict)

        sort_dict = [s.to_dict() for s in self.sort]
        pagination_dict = self.pagination.to_dict() if self.pagination else {}

        return {
            "entity_type": self.entity_type,
            "query": self.query,
            "filters": filters_dict if filters_dict else None,
            "sort": sort_dict if sort_dict else None,
            "pagination": pagination_dict if pagination_dict else None,
            "fields": self.fields,
        }

    def add_filter(self, field: str, value: Any, operator: str = "exact") -> "SearchRequest":
        """Add a filter to the request."""
        self.filters.append(SearchFilter(field=field, value=value, operator=operator))
        return self

    def add_sort(self, field: str, direction: SortDirection = SortDirection.ASC) -> "SearchRequest":
        """Add a sort to the request."""
        self.sort.append(SearchSort(field=field, direction=direction))
        return self

    def with_pagination(self, page: int, page_size: int) -> "SearchRequest":
        """Set pagination parameters."""
        self.pagination = PaginationRequest(page=page, page_size=page_size)
        return self

    def with_fields(self, fields: List[str]) -> "SearchRequest":
        """Set field selection."""
        self.fields = fields
        return self
