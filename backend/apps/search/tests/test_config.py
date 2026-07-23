"""
Tests for search configuration.
"""

import pytest
from django.conf import settings

from apps.search.config import SearchConfig


class TestSearchConfig:
    """Test SearchConfig functionality."""

    def test_get_provider(self):
        """Test getting configured provider."""
        provider = SearchConfig.get_provider()
        assert provider in ["postgresql", "elasticsearch", "opensearch"]

    def test_get_provider_config(self):
        """Test getting provider configuration."""
        config = SearchConfig.get_provider_config("postgresql")
        assert isinstance(config, dict)

    def test_get_page_size(self):
        """Test getting default page size."""
        page_size = SearchConfig.get_page_size()
        assert isinstance(page_size, int)
        assert page_size > 0

    def test_get_max_page_size(self):
        """Test getting maximum page size."""
        max_page_size = SearchConfig.get_max_page_size()
        assert isinstance(max_page_size, int)
        assert max_page_size > 0

    def test_get_autocomplete_limit(self):
        """Test getting autocomplete limit."""
        limit = SearchConfig.get_autocomplete_limit()
        assert isinstance(limit, int)
        assert limit > 0

    def test_get_max_autocomplete_limit(self):
        """Test getting maximum autocomplete limit."""
        max_limit = SearchConfig.get_max_autocomplete_limit()
        assert isinstance(max_limit, int)
        assert max_limit > 0

    def test_get_timeout(self):
        """Test getting search timeout."""
        timeout = SearchConfig.get_timeout()
        assert isinstance(timeout, int)
        assert timeout > 0

    def test_is_cache_enabled(self):
        """Test checking if cache is enabled."""
        enabled = SearchConfig.is_cache_enabled()
        assert isinstance(enabled, bool)

    def test_get_cache_ttl(self):
        """Test getting cache TTL values."""
        ttl = SearchConfig.get_cache_ttl()
        assert isinstance(ttl, dict)

    def test_get_feature_flags(self):
        """Test getting feature flags."""
        flags = SearchConfig.get_feature_flags()
        assert isinstance(flags, dict)

    def test_is_feature_enabled(self):
        """Test checking if a feature is enabled."""
        enabled = SearchConfig.is_feature_enabled("full_text_search")
        assert isinstance(enabled, bool)

    def test_get_vector_config(self):
        """Test getting vector configuration."""
        config = SearchConfig.get_vector_config()
        assert isinstance(config, dict)

    def test_get_ranking_config(self):
        """Test getting ranking configuration."""
        config = SearchConfig.get_ranking_config()
        assert isinstance(config, dict)

    def test_get_default_ranking_strategy(self):
        """Test getting default ranking strategy."""
        strategy = SearchConfig.get_default_ranking_strategy()
        assert isinstance(strategy, str)
