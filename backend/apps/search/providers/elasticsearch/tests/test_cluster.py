"""
Tests for Elasticsearch cluster manager.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from apps.search.providers.elasticsearch.cluster import (
    ClusterManager,
    ClusterHealth,
    NodeInfo,
    ClusterInfo,
)


@pytest.fixture
def mock_client():
    """Mock Elasticsearch client."""
    client = MagicMock()
    client.ping.return_value = True
    client.info.return_value = {
        "name": "test-cluster",
        "cluster_uuid": "test-uuid",
        "version": {"number": "8.15.0", "build_date": "2024-01-01", "build_hash": "abc123", "lucene_version": "9.10.0"},
        "tagline": "You Know, for Search",
    }
    client.cluster.health.return_value = {
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
    client.nodes.info.return_value = {
        "nodes": {
            "node1": {
                "name": "node1",
                "host": "localhost",
                "ip": "127.0.0.1",
                "version": "8.15.0",
                "roles": ["master", "data", "ingest"],
                "os": {"name": "Linux", "version": "5.4.0"},
                "jvm": {"version": "17.0.1"},
            }
        }
    }
    return client


@pytest.fixture
def cluster_manager(mock_client):
    """Cluster manager fixture."""
    return ClusterManager(mock_client)


class TestClusterManager:
    """Test ClusterManager implementation."""

    def test_initialization(self, mock_client):
        """Test cluster manager initialization."""
        manager = ClusterManager(mock_client)

        assert manager.client is mock_client
        assert manager._cluster_info is None
        assert manager._cached_health is None

    def test_ping(self, cluster_manager, mock_client):
        """Test cluster ping."""
        result = cluster_manager.ping()

        assert result is True
        mock_client.ping.assert_called_once()

    def test_ping_failure(self, cluster_manager, mock_client):
        """Test cluster ping failure."""
        mock_client.ping.side_effect = Exception("Connection failed")

        result = cluster_manager.ping()

        assert result is False

    def test_get_cluster_health(self, cluster_manager, mock_client):
        """Test getting cluster health."""
        health = cluster_manager.get_cluster_health(use_cache=False)

        assert health.status == "green"
        assert health.number_of_nodes == 3
        assert health.is_healthy is True
        assert health.is_fully_healthy is True

    def test_get_cluster_health_cache(self, cluster_manager, mock_client):
        """Test getting cluster health with caching."""
        # First call
        health1 = cluster_manager.get_cluster_health(use_cache=False)
        mock_client.cluster.health.assert_called_once()

        # Second call with cache
        health2 = cluster_manager.get_cluster_health(use_cache=True)
        # Should not call cluster.health again
        assert mock_client.cluster.health.call_count == 1

        assert health1.status == health2.status

    def test_get_cluster_health_yellow(self, cluster_manager, mock_client):
        """Test getting cluster health with yellow status."""
        mock_client.cluster.health.return_value = {
            "status": "yellow",
            "number_of_nodes": 3,
            "number_of_data_nodes": 3,
            "active_primary_shards": 10,
            "active_shards": 20,
            "relocating_shards": 0,
            "initializing_shards": 0,
            "unassigned_shards": 5,
            "delayed_unassigned_shards": 0,
            "number_of_pending_tasks": 0,
            "task_max_waiting_in_queue_millis": 0,
            "active_shards_percent_as_number": 80.0,
        }

        health = cluster_manager.get_cluster_health(use_cache=False)

        assert health.status == "yellow"
        assert health.is_healthy is True
        assert health.is_fully_healthy is False

    def test_get_cluster_health_red(self, cluster_manager, mock_client):
        """Test getting cluster health with red status."""
        mock_client.cluster.health.return_value = {
            "status": "red",
            "number_of_nodes": 3,
            "number_of_data_nodes": 3,
            "active_primary_shards": 10,
            "active_shards": 20,
            "relocating_shards": 0,
            "initializing_shards": 0,
            "unassigned_shards": 10,
            "delayed_unassigned_shards": 5,
            "number_of_pending_tasks": 0,
            "task_max_waiting_in_queue_millis": 0,
            "active_shards_percent_as_number": 50.0,
        }

        health = cluster_manager.get_cluster_health(use_cache=False)

        assert health.status == "red"
        assert health.is_healthy is False
        assert health.is_fully_healthy is False

    def test_get_cluster_info(self, cluster_manager, mock_client):
        """Test getting cluster information."""
        info = cluster_manager.get_cluster_info()

        assert info.name == "test-cluster"
        assert info.cluster_uuid == "test-uuid"
        assert info.version == "8.15.0"

    def test_get_cluster_info_cache(self, cluster_manager, mock_client):
        """Test getting cluster info with caching."""
        # First call
        info1 = cluster_manager.get_cluster_info()
        mock_client.info.assert_called_once()

        # Second call should use cache
        info2 = cluster_manager.get_cluster_info()
        assert mock_client.info.call_count == 1

        assert info1.name == info2.name

    def test_get_nodes_info(self, cluster_manager, mock_client):
        """Test getting nodes information."""
        nodes = cluster_manager.get_nodes_info()

        assert len(nodes) == 1
        assert nodes[0].name == "node1"
        assert nodes[0].ip == "127.0.0.1"
        assert "master" in nodes[0].roles

    def test_get_node_stats(self, cluster_manager, mock_client):
        """Test getting node statistics."""
        mock_client.nodes.stats.return_value = {"nodes": {"node1": {"stats": "data"}}}

        stats = cluster_manager.get_node_stats()

        assert "nodes" in stats

    def test_verify_connection(self, cluster_manager, mock_client):
        """Test connection verification."""
        result = cluster_manager.verify_connection()

        assert result is True

    def test_verify_connection_failure(self, cluster_manager, mock_client):
        """Test connection verification failure."""
        mock_client.ping.return_value = False

        result = cluster_manager.verify_connection()

        assert result is False

    def test_detect_features(self, cluster_manager, mock_client):
        """Test feature detection."""
        features = cluster_manager.detect_features()

        assert features["vector_search"] is True
        assert features["knn_search"] is True
        assert features["sql"] is True

    def test_detect_features_old_version(self, cluster_manager, mock_client):
        """Test feature detection with old version."""
        mock_client.info.return_value = {
            "name": "test-cluster",
            "cluster_uuid": "test-uuid",
            "version": {"number": "6.8.0"},
        }

        features = cluster_manager.detect_features()

        assert features["vector_search"] is False
        assert features["knn_search"] is False
        assert features["sql"] is False

    def test_wait_for_cluster_health(self, cluster_manager, mock_client):
        """Test waiting for cluster health."""
        result = cluster_manager.wait_for_cluster_health(status="green", timeout=5, interval=1)

        assert result is True

    def test_wait_for_cluster_health_timeout(self, cluster_manager, mock_client):
        """Test waiting for cluster health with timeout."""
        mock_client.cluster.health.return_value = {
            "status": "red",
            "number_of_nodes": 1,
            "number_of_data_nodes": 1,
            "active_primary_shards": 5,
            "active_shards": 5,
            "relocating_shards": 0,
            "initializing_shards": 0,
            "unassigned_shards": 10,
            "delayed_unassigned_shards": 0,
            "number_of_pending_tasks": 0,
            "task_max_waiting_in_queue_millis": 0,
            "active_shards_percent_as_number": 50.0,
        }

        result = cluster_manager.wait_for_cluster_health(status="green", timeout=1, interval=0.5)

        assert result is False

    def test_get_index_health(self, cluster_manager, mock_client):
        """Test getting index health."""
        mock_client.indices.health.return_value = {"indices": {"test_index": {"status": "green"}}}

        health = cluster_manager.get_index_health("test_index")

        assert "indices" in health

    def test_get_index_stats(self, cluster_manager, mock_client):
        """Test getting index statistics."""
        mock_client.indices.stats.return_value = {
            "indices": {"test_index": {"primaries": {"docs": {"count": 100}}}}
        }

        stats = cluster_manager.get_index_stats("test_index")

        assert "indices" in stats


class TestClusterHealth:
    """Test ClusterHealth dataclass."""

    def test_is_healthy_green(self):
        """Test is_healthy with green status."""
        health = ClusterHealth(
            status="green",
            number_of_nodes=3,
            number_of_data_nodes=3,
            active_primary_shards=10,
            active_shards=20,
            relocating_shards=0,
            initializing_shards=0,
            unassigned_shards=0,
            delayed_unassigned_shards=0,
            number_of_pending_tasks=0,
            task_max_waiting_in_queue_millis=0,
            active_shards_percent_as_number=100.0,
        )

        assert health.is_healthy is True

    def test_is_healthy_yellow(self):
        """Test is_healthy with yellow status."""
        health = ClusterHealth(
            status="yellow",
            number_of_nodes=3,
            number_of_data_nodes=3,
            active_primary_shards=10,
            active_shards=20,
            relocating_shards=0,
            initializing_shards=0,
            unassigned_shards=5,
            delayed_unassigned_shards=0,
            number_of_pending_tasks=0,
            task_max_waiting_in_queue_millis=0,
            active_shards_percent_as_number=80.0,
        )

        assert health.is_healthy is True

    def test_is_healthy_red(self):
        """Test is_healthy with red status."""
        health = ClusterHealth(
            status="red",
            number_of_nodes=3,
            number_of_data_nodes=3,
            active_primary_shards=10,
            active_shards=20,
            relocating_shards=0,
            initializing_shards=0,
            unassigned_shards=10,
            delayed_unassigned_shards=5,
            number_of_pending_tasks=0,
            task_max_waiting_in_queue_millis=0,
            active_shards_percent_as_number=50.0,
        )

        assert health.is_healthy is False


class TestClusterInfo:
    """Test ClusterInfo dataclass."""

    def test_cluster_info_creation(self):
        """Test ClusterInfo creation."""
        info = ClusterInfo(
            name="test-cluster",
            cluster_uuid="test-uuid",
            version="8.15.0",
            build_date="2024-01-01",
            build_hash="abc123",
            lucene_version="9.10.0",
            tagline="You Know, for Search",
        )

        assert info.name == "test-cluster"
        assert info.version == "8.15.0"


class TestNodeInfo:
    """Test NodeInfo dataclass."""

    def test_node_info_creation(self):
        """Test NodeInfo creation."""
        node = NodeInfo(
            name="node1",
            host="localhost",
            ip="127.0.0.1",
            version="8.15.0",
            roles=["master", "data"],
            os_name="Linux",
            os_version="5.4.0",
            jvm_version="17.0.1",
        )

        assert node.name == "node1"
        assert "master" in node.roles
