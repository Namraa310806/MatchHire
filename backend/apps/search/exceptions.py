"""
Search-specific exceptions for the MatchHire search infrastructure.
"""


class SearchError(Exception):
    """Base exception for all search-related errors."""
    pass


class ProviderUnavailable(SearchError):
    """Raised when the search provider is not available."""
    pass


class InvalidQuery(SearchError):
    """Raised when the search query is invalid."""
    pass


class InvalidFilter(SearchError):
    """Raised when a filter is invalid."""
    pass


class SearchTimeout(SearchError):
    """Raised when a search operation times out."""
    pass


class ConfigurationError(SearchError):
    """Raised when there's a configuration error."""
    pass


class ProviderNotRegistered(SearchError):
    """Raised when attempting to use a provider that is not registered."""
    pass


class IndexingError(SearchError):
    """Raised when document indexing fails."""
    pass


class BulkIndexingError(SearchError):
    """Raised when bulk document indexing fails."""
    pass
