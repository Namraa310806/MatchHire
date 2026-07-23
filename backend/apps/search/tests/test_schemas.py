"""
Tests for search request and response schemas.
"""

import pytest

from apps.search.schemas.requests import (
    SearchRequest,
    SearchFilter,
    SearchSort,
    PaginationRequest,
    AutocompleteRequest,
    SortDirection,
)
from apps.search.schemas.responses import (
    SearchResponse,
    SearchResultItem,
    PaginationMetadata,
    AutocompleteResponse,
    SuggestionResponse,
)


class TestSearchFilter:
    """Test SearchFilter model."""

    def test_exact_filter(self):
        """Test exact filter operator."""
        filter_obj = SearchFilter(field="status", value="active", operator="exact")
        result = filter_obj.to_dict()
        assert result == {"status": "active"}

    def test_gte_filter(self):
        """Test gte filter operator."""
        filter_obj = SearchFilter(field="salary", value=50000, operator="gte")
        result = filter_obj.to_dict()
        assert result == {"salary": {"gte": 50000}}

    def test_in_filter(self):
        """Test in filter operator."""
        filter_obj = SearchFilter(field="status", value=["active", "draft"], operator="in")
        result = filter_obj.to_dict()
        assert result == {"status": ["active", "draft"]}

    def test_contains_filter(self):
        """Test contains filter operator."""
        filter_obj = SearchFilter(field="title", value="engineer", operator="contains")
        result = filter_obj.to_dict()
        assert result == {"title__icontains": "engineer"}


class TestSearchSort:
    """Test SearchSort model."""

    def test_asc_sort(self):
        """Test ascending sort."""
        sort = SearchSort(field="created_at", direction=SortDirection.ASC)
        result = sort.to_dict()
        assert result == {"field": "created_at", "direction": "asc"}

    def test_desc_sort(self):
        """Test descending sort."""
        sort = SearchSort(field="created_at", direction=SortDirection.DESC)
        result = sort.to_dict()
        assert result == {"field": "created_at", "direction": "desc"}


class TestPaginationRequest:
    """Test PaginationRequest model."""

    def test_valid_pagination(self):
        """Test valid pagination parameters."""
        pagination = PaginationRequest(page=1, page_size=20)
        assert pagination.page == 1
        assert pagination.page_size == 20

    def test_invalid_page(self):
        """Test invalid page number raises error."""
        with pytest.raises(ValueError):
            PaginationRequest(page=0, page_size=20)

    def test_invalid_page_size(self):
        """Test invalid page size raises error."""
        with pytest.raises(ValueError):
            PaginationRequest(page=1, page_size=0)

    def test_page_size_too_large(self):
        """Test page size exceeding maximum raises error."""
        with pytest.raises(ValueError):
            PaginationRequest(page=1, page_size=101)

    def test_to_dict(self):
        """Test converting to dictionary."""
        pagination = PaginationRequest(page=2, page_size=10)
        result = pagination.to_dict()
        assert result == {"page": 2, "page_size": 10}

    def test_to_offset_limit(self):
        """Test converting to offset/limit format."""
        pagination = PaginationRequest(page=2, page_size=10)
        result = pagination.to_offset_limit()
        assert result == {"offset": 10, "limit": 10}


class TestAutocompleteRequest:
    """Test AutocompleteRequest model."""

    def test_valid_request(self):
        """Test valid autocomplete request."""
        request = AutocompleteRequest(
            entity_type="job",
            field="title",
            prefix="eng",
            limit=10,
        )
        assert request.entity_type == "job"
        assert request.field == "title"
        assert request.prefix == "eng"
        assert request.limit == 10

    def test_missing_entity_type(self):
        """Test missing entity type raises error."""
        with pytest.raises(ValueError):
            AutocompleteRequest(entity_type="", field="title", prefix="eng")

    def test_missing_field(self):
        """Test missing field raises error."""
        with pytest.raises(ValueError):
            AutocompleteRequest(entity_type="job", field="", prefix="eng")

    def test_missing_prefix(self):
        """Test missing prefix raises error."""
        with pytest.raises(ValueError):
            AutocompleteRequest(entity_type="job", field="title", prefix="")

    def test_limit_too_large(self):
        """Test limit exceeding maximum raises error."""
        with pytest.raises(ValueError):
            AutocompleteRequest(entity_type="job", field="title", prefix="eng", limit=51)


class TestSearchRequest:
    """Test SearchRequest model."""

    def test_basic_request(self):
        """Test basic search request."""
        request = SearchRequest(entity_type="job", query="engineer")
        assert request.entity_type == "job"
        assert request.query == "engineer"
        assert request.pagination is not None  # Default pagination

    def test_request_with_filters(self):
        """Test search request with filters."""
        request = SearchRequest(
            entity_type="job",
            query="engineer",
            filters=[SearchFilter(field="status", value="active")],
        )
        assert len(request.filters) == 1

    def test_request_with_sort(self):
        """Test search request with sort."""
        request = SearchRequest(
            entity_type="job",
            query="engineer",
            sort=[SearchSort(field="created_at", direction=SortDirection.DESC)],
        )
        assert len(request.sort) == 1

    def test_missing_entity_type(self):
        """Test missing entity type raises error."""
        with pytest.raises(ValueError):
            SearchRequest(entity_type="", query="engineer")

    def test_to_dict(self):
        """Test converting to dictionary."""
        request = SearchRequest(entity_type="job", query="engineer")
        result = request.to_dict()
        assert result["entity_type"] == "job"
        assert result["query"] == "engineer"

    def test_add_filter(self):
        """Test adding a filter."""
        request = SearchRequest(entity_type="job", query="engineer")
        request.add_filter("status", "active")
        assert len(request.filters) == 1

    def test_add_sort(self):
        """Test adding a sort."""
        request = SearchRequest(entity_type="job", query="engineer")
        request.add_sort("created_at", SortDirection.DESC)
        assert len(request.sort) == 1

    def test_with_pagination(self):
        """Test setting pagination."""
        request = SearchRequest(entity_type="job", query="engineer")
        request.with_pagination(page=2, page_size=10)
        assert request.pagination.page == 2
        assert request.pagination.page_size == 10

    def test_with_fields(self):
        """Test setting field selection."""
        request = SearchRequest(entity_type="job", query="engineer")
        request.with_fields(["title", "company"])
        assert request.fields == ["title", "company"]


class TestPaginationMetadata:
    """Test PaginationMetadata model."""

    def test_from_total(self):
        """Test creating metadata from total count."""
        metadata = PaginationMetadata.from_total(total=100, page=1, page_size=20)
        assert metadata.total == 100
        assert metadata.page == 1
        assert metadata.page_size == 20
        assert metadata.total_pages == 5
        assert metadata.has_next is True
        assert metadata.has_previous is False

    def test_last_page(self):
        """Test metadata for last page."""
        metadata = PaginationMetadata.from_total(total=100, page=5, page_size=20)
        assert metadata.has_next is False
        assert metadata.has_previous is True

    def test_to_dict(self):
        """Test converting to dictionary."""
        metadata = PaginationMetadata.from_total(total=100, page=1, page_size=20)
        result = metadata.to_dict()
        assert result["total"] == 100
        assert result["page"] == 1
        assert result["page_size"] == 20


class TestSearchResponse:
    """Test SearchResponse model."""

    def test_basic_response(self):
        """Test basic search response."""
        response = SearchResponse(
            results=[],
            total=0,
            took_ms=10,
        )
        assert response.total == 0
        assert response.took_ms == 10

    def test_response_with_pagination(self):
        """Test search response with pagination metadata."""
        pagination = PaginationMetadata.from_total(total=100, page=1, page_size=20)
        response = SearchResponse(
            results=[],
            total=100,
            took_ms=10,
            pagination=pagination,
        )
        assert response.pagination is not None

    def test_from_provider_response(self):
        """Test creating response from provider response."""
        provider_response = {
            "results": [{"id": "1", "title": "Job 1"}],
            "total": 1,
            "took_ms": 5,
            "metadata": {"entity_type": "job"},
        }
        pagination = PaginationRequest(page=1, page_size=20)
        response = SearchResponse.from_provider_response(provider_response, pagination)
        assert len(response.results) == 1
        assert response.total == 1

    def test_to_dict(self):
        """Test converting to dictionary."""
        response = SearchResponse(results=[], total=0, took_ms=10)
        result = response.to_dict()
        assert result["total"] == 0
        assert result["took_ms"] == 10


class TestAutocompleteResponse:
    """Test AutocompleteResponse model."""

    def test_basic_response(self):
        """Test basic autocomplete response."""
        suggestions = [SuggestionResponse(value="engineer")]
        response = AutocompleteResponse(suggestions=suggestions, took_ms=5)
        assert len(response.suggestions) == 1

    def test_from_provider_response(self):
        """Test creating response from provider response."""
        provider_response = [{"value": "engineer"}, {"value": "developer"}]
        response = AutocompleteResponse.from_provider_response(
            provider_response, entity_type="job", field="title"
        )
        assert len(response.suggestions) == 2
