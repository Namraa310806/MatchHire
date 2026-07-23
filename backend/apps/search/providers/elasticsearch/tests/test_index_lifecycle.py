"""
Tests for Elasticsearch index lifecycle manager.
"""

import pytest
from unittest.mock import MagicMock

from apps.search.providers.elasticsearch.index_lifecycle import IndexLifecycleManager


@pytest.fixture
def mock_client():
    """Mock Elasticsearch client."""
    client = MagicMock()
    client.indices.exists.return_value = False
    client.indices.create.return_value = {}
    client.indices.delete.return_value = {}
    client.indices.refresh.return_value = {}
    client.indices.close.return_value = {}
    client.indices.open.return_value = {}
    client.indices.put_alias.return_value = {}
    client.indices.delete_alias.return_value = {}
    client.indices.get_alias.return_value = {}
    client.indices.update_aliases.return_value = {}
    client.indices.get_settings.return_value = {}
    client.indices.get_mapping.return_value = {}
    client.indices.get.return_value = {}
    return client


@pytest.fixture
def index_lifecycle_manager(mock_client):
    """Index lifecycle manager fixture."""
    return IndexLifecycleManager(mock_client, "matchhire_test")


class TestIndexLifecycleManager:
    """Test IndexLifecycleManager implementation."""

    def test_initialization(self, mock_client):
        """Test index lifecycle manager initialization."""
        manager = IndexLifecycleManager(mock_client, "test_prefix")

        assert manager.client is mock_client
        assert manager.index_prefix == "test_prefix"

    def test_get_index_name(self, index_lifecycle_manager):
        """Test getting index name."""
        index_name = index_lifecycle_manager.get_index_name("job")

        assert index_name == "matchhire_test_job"

    def test_get_index_name_with_version(self, index_lifecycle_manager):
        """Test getting index name with version."""
        index_name = index_lifecycle_manager.get_index_name("job", version=2)

        assert index_name == "matchhire_test_job_v2"

    def test_get_alias_name(self, index_lifecycle_manager):
        """Test getting alias name."""
        alias_name = index_lifecycle_manager.get_alias_name("job")

        assert alias_name == "matchhire_test_job_alias"

    def test_create_index(self, index_lifecycle_manager, mock_client):
        """Test creating an index."""
        mapping = {"properties": {"title": {"type": "text"}}}
        settings = {"number_of_shards": 3}

        result = index_lifecycle_manager.create_index("job", mapping, settings)

        assert result is True
        mock_client.indices.create.assert_called_once()

    def test_create_index_already_exists(self, index_lifecycle_manager, mock_client):
        """Test creating an index that already exists."""
        mock_client.indices.exists.return_value = True
        mapping = {"properties": {"title": {"type": "text"}}}

        result = index_lifecycle_manager.create_index("job", mapping)

        assert result is False
        mock_client.indices.create.assert_not_called()

    def test_delete_index(self, index_lifecycle_manager, mock_client):
        """Test deleting an index."""
        mock_client.indices.exists.return_value = True

        result = index_lifecycle_manager.delete_index("job")

        assert result is True
        mock_client.indices.delete.assert_called_once()

    def test_delete_index_not_exists(self, index_lifecycle_manager, mock_client):
        """Test deleting an index that doesn't exist."""
        mock_client.indices.exists.return_value = False

        result = index_lifecycle_manager.delete_index("job")

        assert result is False
        mock_client.indices.delete.assert_not_called()

    def test_recreate_index(self, index_lifecycle_manager, mock_client):
        """Test recreating an index."""
        mock_client.indices.exists.return_value = True
        mapping = {"properties": {"title": {"type": "text"}}}

        result = index_lifecycle_manager.recreate_index("job", mapping)

        assert result is True
        mock_client.indices.delete.assert_called_once()
        mock_client.indices.create.assert_called_once()

    def test_refresh_index(self, index_lifecycle_manager, mock_client):
        """Test refreshing an index."""
        index_lifecycle_manager.refresh_index("job")

        mock_client.indices.refresh.assert_called_once()

    def test_close_index(self, index_lifecycle_manager, mock_client):
        """Test closing an index."""
        mock_client.indices.exists.return_value = True

        result = index_lifecycle_manager.close_index("job")

        assert result is True
        mock_client.indices.close.assert_called_once()

    def test_open_index(self, index_lifecycle_manager, mock_client):
        """Test opening an index."""
        mock_client.indices.exists.return_value = True

        result = index_lifecycle_manager.open_index("job")

        assert result is True
        mock_client.indices.open.assert_called_once()

    def test_create_alias(self, index_lifecycle_manager, mock_client):
        """Test creating an alias."""
        result = index_lifecycle_manager.create_alias("job", "matchhire_test_job")

        assert result is True
        mock_client.indices.put_alias.assert_called_once()

    def test_delete_alias(self, index_lifecycle_manager, mock_client):
        """Test deleting an alias."""
        result = index_lifecycle_manager.delete_alias("job")

        assert result is True
        mock_client.indices.delete_alias.assert_called_once()

    def test_get_aliases(self, index_lifecycle_manager, mock_client):
        """Test getting aliases."""
        mock_client.indices.get_alias.return_value = {
            "matchhire_test_job": {"aliases": {"matchhire_test_job_alias": {}}}
        }

        aliases = index_lifecycle_manager.get_aliases("job")

        assert "matchhire_test_job" in aliases

    def test_switch_alias(self, index_lifecycle_manager, mock_client):
        """Test switching an alias."""
        result = index_lifecycle_manager.switch_alias(
            "job", "matchhire_test_job_v1", "matchhire_test_job_v2"
        )

        assert result is True
        mock_client.indices.update_aliases.assert_called_once()

    def test_create_versioned_index(self, index_lifecycle_manager, mock_client):
        """Test creating a versioned index."""
        mock_client.indices.get.return_value = {}
        mock_client.indices.get_alias.side_effect = Exception("No alias")
        mapping = {"properties": {"title": {"type": "text"}}}

        result = index_lifecycle_manager.create_versioned_index("job", mapping, switch_alias=True)

        assert "job_v" in result
        mock_client.indices.create.assert_called_once()

    def test_index_exists(self, index_lifecycle_manager, mock_client):
        """Test checking if index exists."""
        mock_client.indices.exists.return_value = True

        result = index_lifecycle_manager.index_exists("job")

        assert result is True

    def test_index_not_exists(self, index_lifecycle_manager, mock_client):
        """Test checking if index doesn't exist."""
        mock_client.indices.exists.return_value = False

        result = index_lifecycle_manager.index_exists("job")

        assert result is False

    def test_list_indices(self, index_lifecycle_manager, mock_client):
        """Test listing indices."""
        mock_client.indices.get.return_value = {
            "matchhire_test_job": {},
            "matchhire_test_candidate": {},
            "matchhire_test_job_v1": {},
        }

        indices = index_lifecycle_manager.list_indices()

        assert "matchhire_test_job" in indices
        assert "matchhire_test_candidate" in indices

    def test_list_indices_filtered(self, index_lifecycle_manager, mock_client):
        """Test listing indices with entity type filter."""
        mock_client.indices.get.return_value = {
            "matchhire_test_job": {},
            "matchhire_test_job_v1": {},
        }

        indices = index_lifecycle_manager.list_indices(entity_type="job")

        assert "matchhire_test_job" in indices
        assert "matchhire_test_job_v1" in indices

    def test_get_index_settings(self, index_lifecycle_manager, mock_client):
        """Test getting index settings."""
        mock_client.indices.get_settings.return_value = {
            "matchhire_test_job": {"settings": {"index": {"number_of_shards": 3}}}
        }

        settings = index_lifecycle_manager.get_index_settings("job")

        assert "settings" in settings

    def test_get_index_mapping(self, index_lifecycle_manager, mock_client):
        """Test getting index mapping."""
        mock_client.indices.get_mapping.return_value = {
            "matchhire_test_job": {"mappings": {"properties": {}}}
        }

        mapping = index_lifecycle_manager.get_index_mapping("job")

        assert "mappings" in mapping

    def test_cleanup_old_indices(self, index_lifecycle_manager, mock_client):
        """Test cleaning up old indices."""
        mock_client.indices.get.return_value = {
            "matchhire_test_job_v1": {"aliases": {}},
            "matchhire_test_job_v2": {"aliases": {}},
            "matchhire_test_job_v3": {"aliases": {"matchhire_test_job_alias": {}}},
        }
        mock_client.indices.get_alias.return_value = {
            "matchhire_test_job_v3": {"aliases": {"matchhire_test_job_alias": {}}}
        }

        result = index_lifecycle_manager.cleanup_old_indices("job", keep_versions=2)

        assert result >= 0
