"""
Tests for Elasticsearch provider.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from elasticsearch import Elasticsearch

from apps.search.providers.elasticsearch import ElasticsearchProvider
from apps.search.providers.base import IndexResult, BulkIndexResult, DeleteResult, BulkDeleteResult
from apps.search.exceptions import ProviderUnavailable


@pytest.fixture
def mock_es_client():
    """Mock Elasticsearch client."""
    client = MagicMock(spec=Elasticsearch)
    client.ping.return_value = True
    client.info.return_value = {
        "name": "test-cluster",
        "cluster_uuid": "test-uuid",
        "version": {"number": "8.15.0", "build_date": "2024-01-01", "build_hash": "abc123", "lucene_version": "9.10.0"},
        "tagline": "You Know, for Search",
    }
    client.cluster.health.return_value = {
        "status": "green",
        "number_of_nodes": 1,
        "number_of_data_nodes": 1,
        "active_primary_shards": 5,
        "active_shards": 5,
        "relocating_shards": 0,
        "initializing_shards": 0,
        "unassigned_shards": 0,
        "delayed_unassigned_shards": 0,
        "number_of_pending_tasks": 0,
        "task_max_waiting_in_queue_millis": 0,
        "active_shards_percent_as_number": 100.0,
    }
    client.indices.exists.return_value = False
    client.indices.create.return_value = {}
    return client


@pytest.fixture
def provider_config():
    """Elasticsearch provider configuration."""
    return {
        "hosts": ["http://localhost:9200"],
        "index_prefix": "matchhire_test",
        "use_aliases": False,
    }


@pytest.fixture
def elasticsearch_provider(mock_es_client, provider_config):
    """Elasticsearch provider fixture."""
    with patch("apps.search.providers.elasticsearch.Elasticsearch", return_value=mock_es_client):
        provider = ElasticsearchProvider(provider_config)
        provider.client = mock_es_client
        return provider


class TestElasticsearchProvider:
    """Test ElasticsearchProvider implementation."""

    def test_initialization(self, provider_config):
        """Test provider initialization."""
        with patch("apps.search.providers.elasticsearch.Elasticsearch") as mock_es_class:
            mock_client = MagicMock()
            mock_es_class.return_value = mock_client
            mock_client.ping.return_value = True
            mock_client.info.return_value = {
                "name": "test-cluster",
                "cluster_uuid": "test-uuid",
                "version": {"number": "8.15.0"},
            }
            mock_client.cluster.health.return_value = {"status": "green"}
            mock_client.indices.exists.return_value = False
            mock_client.indices.create.return_value = {}

            provider = ElasticsearchProvider(provider_config)

            assert provider.client is not None
            assert provider.cluster_manager is not None
            assert provider.index_lifecycle is not None

    def test_initialization_connection_failure(self, provider_config):
        """Test provider initialization with connection failure."""
        with patch("apps.search.providers.elasticsearch.Elasticsearch") as mock_es_class:
            mock_client = MagicMock()
            mock_es_class.return_value = mock_client
            mock_client.ping.return_value = False

            with pytest.raises(ProviderUnavailable):
                ElasticsearchProvider(provider_config)

    def test_search(self, elasticsearch_provider, mock_es_client):
        """Test search functionality."""
        mock_es_client.search.return_value = {
            "hits": {
                "total": {"value": 2},
                "hits": [
                    {"_source": {"id": "1", "title": "Software Engineer"}},
                    {"_source": {"id": "2", "title": "Data Scientist"}},
                ],
            }
        }

        result = elasticsearch_provider.search(
            entity_type="job",
            query="software engineer",
            filters={"location": "San Francisco"},
            sort=[{"field": "created_at", "direction": "desc"}],
            pagination={"page": 1, "page_size": 10},
        )

        assert result["total"] == 2
        assert len(result["results"]) == 2
        assert result["metadata"]["provider"] == "elasticsearch"
        assert result["metadata"]["entity_type"] == "job"

    def test_search_no_query(self, elasticsearch_provider, mock_es_client):
        """Test search with no query (match all)."""
        mock_es_client.search.return_value = {
            "hits": {
                "total": {"value": 5},
                "hits": [
                    {"_source": {"id": str(i), "title": f"Job {i}"}}
                    for i in range(5)
                ],
            }
        }

        result = elasticsearch_provider.search(entity_type="job", query="")

        assert result["total"] == 5
        assert len(result["results"]) == 5

    def test_autocomplete(self, elasticsearch_provider, mock_es_client):
        """Test autocomplete functionality."""
        mock_es_client.search.return_value = {
            "aggregations": {
                "suggestions": {
                    "buckets": [
                        {"key": "Software Engineer", "doc_count": 100},
                        {"key": "Software Developer", "doc_count": 50},
                    ]
                }
            }
        }

        suggestions = elasticsearch_provider.autocomplete(
            entity_type="job",
            field="title",
            prefix="soft",
            limit=10,
        )

        assert len(suggestions) == 2
        assert suggestions[0]["value"] == "Software Engineer"
        assert suggestions[0]["metadata"]["count"] == 100

    def test_index(self, elasticsearch_provider, mock_es_client):
        """Test single document indexing."""
        mock_es_client.index.return_value = {"result": "created"}

        result = elasticsearch_provider.index(
            entity_type="job",
            document_id="123",
            document={"id": "123", "title": "Software Engineer"},
        )

        assert result.success is True
        assert result.document_id == "123"
        assert result.error is None

    def test_index_failure(self, elasticsearch_provider, mock_es_client):
        """Test single document indexing failure."""
        mock_es_client.index.side_effect = Exception("Indexing failed")

        result = elasticsearch_provider.index(
            entity_type="job",
            document_id="123",
            document={"id": "123", "title": "Software Engineer"},
        )

        assert result.success is False
        assert result.document_id == "123"
        assert result.error is not None

    def test_bulk_index(self, elasticsearch_provider, mock_es_client):
        """Test bulk document indexing."""
        with patch("elasticsearch.helpers.bulk", return_value=(3, [])):
            documents = [
                {"id": "1", "title": "Job 1"},
                {"id": "2", "title": "Job 2"},
                {"id": "3", "title": "Job 3"},
            ]

            result = elasticsearch_provider.bulk_index(entity_type="job", documents=documents)

            assert result.success is True
            assert result.indexed_count == 3
            assert result.failed_count == 0

    def test_bulk_index_with_failures(self, elasticsearch_provider, mock_es_client):
        """Test bulk document indexing with partial failures."""
        failed_items = [{"index": {"_id": "2", "error": "Document not found"}}]
        with patch("elasticsearch.helpers.bulk", return_value=(2, failed_items)):
            documents = [
                {"id": "1", "title": "Job 1"},
                {"id": "2", "title": "Job 2"},
                {"id": "3", "title": "Job 3"},
            ]

            result = elasticsearch_provider.bulk_index(entity_type="job", documents=documents)

            assert result.success is False
            assert result.indexed_count == 2
            assert result.failed_count == 1
            assert len(result.errors) == 1

    def test_delete(self, elasticsearch_provider, mock_es_client):
        """Test single document deletion."""
        mock_es_client.delete.return_value = {"result": "deleted"}

        result = elasticsearch_provider.delete(
            entity_type="job",
            document_id="123",
        )

        assert result.success is True
        assert result.document_id == "123"

    def test_bulk_delete(self, elasticsearch_provider, mock_es_client):
        """Test bulk document deletion."""
        with patch("elasticsearch.helpers.bulk", return_value=(3, [])):
            document_ids = ["1", "2", "3"]

            result = elasticsearch_provider.bulk_delete(
                entity_type="job",
                document_ids=document_ids,
            )

            assert result.success is True
            assert result.deleted_count == 3
            assert result.failed_count == 0

    def test_health(self, elasticsearch_provider, mock_es_client):
        """Test health check."""
        mock_es_client.cluster.health.return_value = {
            "status": "green",
            "number_of_nodes": 3,
            "number_of_data_nodes": 3,
            "active_primary_shards": 10,
            "active_shards": 20,
            "relocating_shards": 0,
            "initializing_shards": 0,
            "unassigned_shards": 0,
            "delayed_unassigned_shards": 0,
            "number_of_pending_tasks": 0,
            "task_max_waiting_in_queue_millis": 0,
            "active_shards_percent_as_number": 100.0,
        }

        result = elasticsearch_provider.health()

        assert result.healthy is True
        assert result.provider_name == "elasticsearch"
        assert result.details["status"] == "green"
        assert result.details["number_of_nodes"] == 3

    def test_health_unhealthy(self, elasticsearch_provider, mock_es_client):
        """Test health check with unhealthy cluster."""
        mock_es_client.cluster.health.return_value = {
            "status": "red",
            "number_of_nodes": 1,
            "number_of_data_nodes": 1,
            "active_primary_shards": 5,
            "active_shards": 5,
            "relocating_shards": 0,
            "initializing_shards": 0,
            "unassigned_shards": 10,
            "delayed_unassigned_shards": 5,
            "number_of_pending_tasks": 0,
            "task_max_waiting_in_queue_millis": 0,
            "active_shards_percent_as_number": 50.0,
        }

        result = elasticsearch_provider.health()

        assert result.healthy is False
        assert result.details["status"] == "red"

    def test_statistics(self, elasticsearch_provider, mock_es_client):
        """Test statistics query."""
        mock_es_client.indices.stats.return_value = {
            "indices": {
                "matchhire_test_job_alias": {
                    "primaries": {
                        "docs": {"count": 100},
                        "store": {"size_in_bytes": 1024000},
                    }
                }
            }
        }

        result = elasticsearch_provider.statistics(entity_type="job")

        assert result.document_count == 100
        assert result.index_size_bytes == 1024000

    def test_statistics_all_indices(self, elasticsearch_provider, mock_es_client):
        """Test statistics query for all indices."""
        mock_es_client.indices.stats.return_value = {
            "indices": {
                "matchhire_test_job_alias": {
                    "primaries": {
                        "docs": {"count": 100},
                        "store": {"size_in_bytes": 1024000},
                    }
                },
                "matchhire_test_candidate_alias": {
                    "primaries": {
                        "docs": {"count": 50},
                        "store": {"size_in_bytes": 512000},
                    }
                },
            }
        }

        result = elasticsearch_provider.statistics()

        assert result.document_count == 150
        assert result.index_size_bytes == 1536000

    def test_refresh(self, elasticsearch_provider, mock_es_client):
        """Test index refresh."""
        mock_es_client.indices.refresh.return_value = {}

        elasticsearch_provider.refresh(entity_type="job")

        mock_es_client.indices.refresh.assert_called_once()

    def test_refresh_all(self, elasticsearch_provider, mock_es_client):
        """Test refresh all indices."""
        mock_es_client.indices.refresh.return_value = {}

        elasticsearch_provider.refresh()

        # Should be called for each entity type
        assert mock_es_client.indices.refresh.call_count == len(elasticsearch_provider.ENTITY_INDICES)

    def test_close(self, elasticsearch_provider, mock_es_client):
        """Test provider close."""
        elasticsearch_provider.close()

        mock_es_client.close.assert_called_once()

    def test_get_cluster_health(self, elasticsearch_provider):
        """Test getting cluster health."""
        result = elasticsearch_provider.get_cluster_health()

        assert "status" in result
        assert "number_of_nodes" in result

    def test_get_supported_features(self, elasticsearch_provider):
        """Test getting supported features."""
        result = elasticsearch_provider.get_supported_features()

        assert isinstance(result, dict)
        assert "vector_search" in result
        assert "knn_search" in result

    def test_create_versioned_index(self, elasticsearch_provider, mock_es_client):
        """Test creating versioned index."""
        mock_es_client.indices.exists.return_value = False
        mock_es_client.indices.create.return_value = {}
        mock_es_client.indices.get_alias.side_effect = Exception("No alias")

        result = elasticsearch_provider.create_versioned_index(entity_type="job", switch_alias=True)

        assert isinstance(result, str)
        assert "job_v" in result

    def test_cleanup_old_indices(self, elasticsearch_provider, mock_es_client):
        """Test cleaning up old indices."""
        mock_es_client.indices.get.return_value = {
            "matchhire_test_job_v1": {"aliases": {}},
            "matchhire_test_job_v2": {"aliases": {}},
            "matchhire_test_job_v3": {"aliases": {}},
        }
        mock_es_client.indices.get_alias.return_value = {
            "matchhire_test_job_v3": {"aliases": {"matchhire_test_job_alias": {}}}
        }
        mock_es_client.indices.delete.return_value = {}

        result = elasticsearch_provider.cleanup_old_indices(entity_type="job", keep_versions=2)

        assert result >= 0
