"""
Tests for search exceptions.
"""

import pytest

from apps.search.exceptions import (
    SearchError,
    ProviderUnavailable,
    InvalidQuery,
    InvalidFilter,
    SearchTimeout,
    ConfigurationError,
    ProviderNotRegistered,
    IndexingError,
    BulkIndexingError,
)


class TestSearchExceptions:
    """Test search exception hierarchy and behavior."""

    def test_search_error_base(self):
        """Test base SearchError exception."""
        with pytest.raises(SearchError):
            raise SearchError("Test error")

    def test_provider_unavailable(self):
        """Test ProviderUnavailable exception."""
        with pytest.raises(ProviderUnavailable):
            raise ProviderUnavailable("Provider not available")

        # Verify it's a SearchError
        with pytest.raises(SearchError):
            raise ProviderUnavailable("Test")

    def test_invalid_query(self):
        """Test InvalidQuery exception."""
        with pytest.raises(InvalidQuery):
            raise InvalidQuery("Invalid query")

        # Verify it's a SearchError
        with pytest.raises(SearchError):
            raise InvalidQuery("Test")

    def test_invalid_filter(self):
        """Test InvalidFilter exception."""
        with pytest.raises(InvalidFilter):
            raise InvalidFilter("Invalid filter")

        # Verify it's a SearchError
        with pytest.raises(SearchError):
            raise InvalidFilter("Test")

    def test_search_timeout(self):
        """Test SearchTimeout exception."""
        with pytest.raises(SearchTimeout):
            raise SearchTimeout("Search timed out")

        # Verify it's a SearchError
        with pytest.raises(SearchError):
            raise SearchTimeout("Test")

    def test_configuration_error(self):
        """Test ConfigurationError exception."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Configuration error")

        # Verify it's a SearchError
        with pytest.raises(SearchError):
            raise ConfigurationError("Test")

    def test_provider_not_registered(self):
        """Test ProviderNotRegistered exception."""
        with pytest.raises(ProviderNotRegistered):
            raise ProviderNotRegistered("Provider not registered")

        # Verify it's a SearchError
        with pytest.raises(SearchError):
            raise ProviderNotRegistered("Test")

    def test_indexing_error(self):
        """Test IndexingError exception."""
        with pytest.raises(IndexingError):
            raise IndexingError("Indexing failed")

        # Verify it's a SearchError
        with pytest.raises(SearchError):
            raise IndexingError("Test")

    def test_bulk_indexing_error(self):
        """Test BulkIndexingError exception."""
        with pytest.raises(BulkIndexingError):
            raise BulkIndexingError("Bulk indexing failed")

        # Verify it's a SearchError
        with pytest.raises(SearchError):
            raise BulkIndexingError("Test")

    def test_exception_messages(self):
        """Test that exception messages are preserved."""
        error_msg = "This is a test error message"
        with pytest.raises(SearchError) as exc_info:
            raise SearchError(error_msg)

        assert str(exc_info.value) == error_msg
