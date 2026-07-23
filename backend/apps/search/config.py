"""
Search configuration.

This module provides configuration settings for the search infrastructure.
Configuration is loaded from Django settings and provides defaults.
"""

from typing import Any, Dict
from django.conf import settings


class SearchConfig:
    """
    Search configuration manager.

    This class provides access to search-related configuration
    settings with sensible defaults.
    """

    # Default configuration values
    DEFAULT_PROVIDER = "postgresql"
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    DEFAULT_AUTOCOMPLETE_LIMIT = 10
    MAX_AUTOCOMPLETE_LIMIT = 50
    DEFAULT_TIMEOUT = 30

    @classmethod
    def get_provider(cls) -> str:
        """
        Get the configured search provider name.

        Returns:
            Provider name (e.g., 'postgresql', 'elasticsearch')
        """
        return getattr(settings, "SEARCH_PROVIDER", cls.DEFAULT_PROVIDER)

    @classmethod
    def get_provider_config(cls, provider: str) -> Dict[str, Any]:
        """
        Get configuration for a specific provider.

        Args:
            provider: Provider name

        Returns:
            Provider configuration dictionary
        """
        search_config = getattr(settings, "SEARCH_CONFIG", {})
        return search_config.get(provider, {})

    @classmethod
    def get_page_size(cls) -> int:
        """
        Get the default page size for search results.

        Returns:
            Default page size
        """
        return getattr(settings, "SEARCH_PAGE_SIZE", cls.DEFAULT_PAGE_SIZE)

    @classmethod
    def get_max_page_size(cls) -> int:
        """
        Get the maximum allowed page size.

        Returns:
            Maximum page size
        """
        return getattr(settings, "SEARCH_MAX_PAGE_SIZE", cls.MAX_PAGE_SIZE)

    @classmethod
    def get_autocomplete_limit(cls) -> int:
        """
        Get the default autocomplete suggestion limit.

        Returns:
            Default autocomplete limit
        """
        return getattr(settings, "SEARCH_AUTOCOMPLETE_LIMIT", cls.DEFAULT_AUTOCOMPLETE_LIMIT)

    @classmethod
    def get_max_autocomplete_limit(cls) -> int:
        """
        Get the maximum allowed autocomplete limit.

        Returns:
            Maximum autocomplete limit
        """
        return getattr(settings, "SEARCH_MAX_AUTOCOMPLETE_LIMIT", cls.MAX_AUTOCOMPLETE_LIMIT)

    @classmethod
    def get_timeout(cls) -> int:
        """
        Get the search timeout in seconds.

        Returns:
            Timeout in seconds
        """
        return getattr(settings, "SEARCH_TIMEOUT", cls.DEFAULT_TIMEOUT)

    @classmethod
    def is_cache_enabled(cls) -> bool:
        """
        Check if search result caching is enabled.

        Returns:
            True if caching is enabled
        """
        cache_config = getattr(settings, "SEARCH_CACHE_CONFIG", {})
        return cache_config.get("enabled", False)

    @classmethod
    def get_cache_ttl(cls) -> Dict[str, int]:
        """
        Get cache TTL values for different result types.

        Returns:
            Dictionary with TTL values in seconds
        """
        cache_config = getattr(settings, "SEARCH_CACHE_CONFIG", {})
        return cache_config.get("ttl", {})

    @classmethod
    def get_feature_flags(cls) -> Dict[str, bool]:
        """
        Get search feature flags.

        Returns:
            Dictionary of feature flags
        """
        return getattr(settings, "SEARCH_FEATURE_FLAGS", {})

    @classmethod
    def is_feature_enabled(cls, feature: str) -> bool:
        """
        Check if a specific feature is enabled.

        Args:
            feature: Feature name

        Returns:
            True if feature is enabled
        """
        flags = cls.get_feature_flags()
        return flags.get(feature, False)

    @classmethod
    def get_vector_config(cls) -> Dict[str, Any]:
        """
        Get vector search configuration.

        Returns:
            Vector search configuration dictionary
        """
        return getattr(settings, "SEARCH_VECTOR_CONFIG", {})

    @classmethod
    def get_ranking_config(cls) -> Dict[str, Any]:
        """
        Get ranking configuration.

        Returns:
            Ranking configuration dictionary
        """
        return getattr(settings, "SEARCH_RANKING_CONFIG", {})

    @classmethod
    def get_default_ranking_strategy(cls) -> str:
        """
        Get the default ranking strategy.

        Returns:
            Default ranking strategy name
        """
        ranking_config = cls.get_ranking_config()
        return ranking_config.get("default_strategy", "bm25")

    @classmethod
    def get_elasticsearch_config(cls) -> Dict[str, Any]:
        """
        Get Elasticsearch-specific configuration.

        Returns:
            Elasticsearch configuration dictionary with defaults
        """
        search_config = getattr(settings, "SEARCH_CONFIG", {})
        es_config = search_config.get("elasticsearch", {})

        # Default Elasticsearch configuration
        defaults = {
            "hosts": ["http://localhost:9200"],
            "username": None,
            "password": None,
            "api_key": None,
            "cloud_id": None,
            "verify_certs": True,
            "ca_certs": None,
            "client_cert": None,
            "client_key": None,
            "ssl_show_warn": True,
            "request_timeout": 30,
            "max_retries": 3,
            "retry_on_timeout": True,
            "retry_on_status": [502, 503, 504],
            "http_compress": False,
            "max_connections": 10,
            "max_connections_per_host": 10,
            "connection_class": None,
            "index_prefix": "matchhire",
            "use_aliases": True,
            "refresh_interval": "1s",
            "number_of_shards": 3,
            "number_of_replicas": 1,
        }

        # Merge with user configuration
        defaults.update(es_config)
        return defaults
