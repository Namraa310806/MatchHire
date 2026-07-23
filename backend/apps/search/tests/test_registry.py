"""
Tests for search registry.
"""

import pytest

from apps.search.registry import SearchRegistry, get_registry
from apps.search.providers.base import SearchProvider
from apps.search.providers.postgresql import PostgreSQLProvider
from apps.search.exceptions import ProviderNotRegistered, ConfigurationError


class MockProvider(SearchProvider):
    """Mock provider for testing."""

    def _initialize(self):
        pass

    def search(self, entity_type, query, filters=None, sort=None, pagination=None, fields=None):
        return {"results": [], "total": 0, "took_ms": 0}

    def autocomplete(self, entity_type, field, prefix, context=None, limit=10):
        return []

    def index(self, entity_type, document_id, document):
        from apps.search.providers.base import IndexResult
        return IndexResult(success=True, document_id=document_id)

    def bulk_index(self, entity_type, documents):
        from apps.search.providers.base import BulkIndexResult
        return BulkIndexResult(success=True, indexed_count=len(documents), failed_count=0, errors=[])

    def delete(self, entity_type, document_id):
        from apps.search.providers.base import DeleteResult
        return DeleteResult(success=True, document_id=document_id)

    def bulk_delete(self, entity_type, document_ids):
        from apps.search.providers.base import BulkDeleteResult
        return BulkDeleteResult(success=True, deleted_count=len(document_ids), failed_count=0, errors=[])

    def health(self):
        from apps.search.providers.base import HealthResult
        return HealthResult(healthy=True, provider_name="mock", details={})

    def statistics(self, entity_type=None):
        from apps.search.providers.base import StatisticsResult
        return StatisticsResult(document_count=0)


class TestSearchRegistry:
    """Test search registry functionality."""

    def test_singleton_pattern(self):
        """Test that registry is a singleton."""
        registry1 = SearchRegistry()
        registry2 = SearchRegistry()
        assert registry1 is registry2

    def test_get_registry_function(self):
        """Test get_registry function returns singleton."""
        registry = get_registry()
        assert isinstance(registry, SearchRegistry)

    def test_register_provider(self):
        """Test registering a provider."""
        registry = SearchRegistry()
        registry.register_provider("mock", MockProvider)
        assert registry.is_registered("mock")

    def test_register_invalid_provider(self):
        """Test registering an invalid provider raises error."""
        registry = SearchRegistry()
        with pytest.raises(ValueError):
            registry.register_provider("invalid", str)  # Not a SearchProvider subclass

    def test_unregister_provider(self):
        """Test unregistering a provider."""
        registry = SearchRegistry()
        registry.register_provider("mock", MockProvider)
        registry.unregister_provider("mock")
        assert not registry.is_registered("mock")

    def test_list_providers(self):
        """Test listing registered providers."""
        registry = SearchRegistry()
        providers = registry.list_providers()
        assert "postgresql" in providers

    def test_is_registered(self):
        """Test checking if provider is registered."""
        registry = SearchRegistry()
        assert registry.is_registered("postgresql")
        assert not registry.is_registered("nonexistent")

    def test_set_current_provider(self):
        """Test setting current provider."""
        registry = SearchRegistry()
        registry.set_current_provider("postgresql")
        assert registry.get_current_provider() == "postgresql"

    def test_set_current_provider_not_registered(self):
        """Test setting current provider that is not registered."""
        registry = SearchRegistry()
        with pytest.raises(ProviderNotRegistered):
            registry.set_current_provider("nonexistent")

    def test_get_provider_with_config(self):
        """Test getting a provider instance with config."""
        registry = SearchRegistry()
        config = {"connection": "default"}
        provider = registry.get_provider("postgresql", config=config)
        assert isinstance(provider, PostgreSQLProvider)

    def test_get_provider_without_config(self):
        """Test getting a provider without config raises error."""
        registry = SearchRegistry()
        with pytest.raises(ConfigurationError):
            registry.get_provider("postgresql")

    def test_get_provider_not_registered(self):
        """Test getting a provider that is not registered."""
        registry = SearchRegistry()
        with pytest.raises(ProviderNotRegistered):
            registry.get_provider("nonexistent", config={})

    def test_get_provider_uses_current(self):
        """Test that get_provider uses current provider if name not specified."""
        registry = SearchRegistry()
        registry.set_current_provider("postgresql")
        config = {"connection": "default"}
        provider = registry.get_provider(config=config)
        assert isinstance(provider, PostgreSQLProvider)

    def test_get_provider_no_current_and_no_name(self):
        """Test that get_provider raises error when no current provider set."""
        registry = SearchRegistry()
        registry._current_provider = None
        with pytest.raises(ConfigurationError):
            registry.get_provider(config={})

    def test_close_all(self):
        """Test closing all provider instances."""
        registry = SearchRegistry()
        config = {"connection": "default"}
        registry.get_provider("postgresql", config=config)
        registry.close_all()
        assert registry._instances == {}
        assert registry._current_provider is None

    def test_postgresql_registered_by_default(self):
        """Test that PostgreSQL provider is registered by default."""
        registry = SearchRegistry()
        assert registry.is_registered("postgresql")
