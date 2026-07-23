"""
Elasticsearch search provider package.

This package provides a complete Elasticsearch implementation of the
SearchProvider interface for the MatchHire search infrastructure.
"""

from .elasticsearch import ElasticsearchProvider

__all__ = ["ElasticsearchProvider"]
