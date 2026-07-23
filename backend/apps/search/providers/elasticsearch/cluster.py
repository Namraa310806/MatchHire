"""
Elasticsearch cluster management utilities.

This module provides cluster health monitoring, node information,
connection verification, and graceful reconnection logic.
"""

import time
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ClusterHealth:
    """Elasticsearch cluster health information."""
    status: str  # green, yellow, red
    number_of_nodes: int
    number_of_data_nodes: int
    active_primary_shards: int
    active_shards: int
    relocating_shards: int
    initializing_shards: int
    unassigned_shards: int
    delayed_unassigned_shards: int
    number_of_pending_tasks: int
    task_max_waiting_in_queue_millis: int
    active_shards_percent_as_number: float

    @property
    def is_healthy(self) -> bool:
        """Check if cluster is healthy (green or yellow)."""
        return self.status in ("green", "yellow")

    @property
    def is_fully_healthy(self) -> bool:
        """Check if cluster is fully healthy (green)."""
        return self.status == "green"


@dataclass
class NodeInfo:
    """Elasticsearch node information."""
    name: str
    host: str
    ip: str
    version: str
    roles: List[str]
    os_name: str
    os_version: str
    jvm_version: str
    cpu_percent: Optional[float] = None
    heap_percent: Optional[float] = None
    ram_percent: Optional[float] = None


@dataclass
class ClusterInfo:
    """Elasticsearch cluster information."""
    name: str
    cluster_uuid: str
    version: str
    build_date: str
    build_hash: str
    lucene_version: str
    tagline: str


class ClusterManager:
    """
    Elasticsearch cluster management utilities.

    Provides cluster health monitoring, node information,
    connection verification, and graceful reconnection.
    """

    def __init__(self, client):
        """
        Initialize cluster manager.

        Args:
            client: Elasticsearch client instance
        """
        self.client = client
        self._cluster_info: Optional[ClusterInfo] = None
        self._last_health_check: Optional[float] = None
        self._cached_health: Optional[ClusterHealth] = None
        self._health_cache_ttl = 5  # seconds

    def ping(self) -> bool:
        """
        Ping the Elasticsearch cluster.

        Returns:
            True if cluster is reachable, False otherwise
        """
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Elasticsearch ping failed: {e}")
            return False

    def get_cluster_health(self, use_cache: bool = True) -> ClusterHealth:
        """
        Get cluster health status.

        Args:
            use_cache: Whether to use cached health if available

        Returns:
            ClusterHealth instance
        """
        if use_cache and self._is_health_cache_valid():
            return self._cached_health

        try:
            response = self.client.cluster.health()
            health = ClusterHealth(
                status=response.get("status", "unknown"),
                number_of_nodes=response.get("number_of_nodes", 0),
                number_of_data_nodes=response.get("number_of_data_nodes", 0),
                active_primary_shards=response.get("active_primary_shards", 0),
                active_shards=response.get("active_shards", 0),
                relocating_shards=response.get("relocating_shards", 0),
                initializing_shards=response.get("initializing_shards", 0),
                unassigned_shards=response.get("unassigned_shards", 0),
                delayed_unassigned_shards=response.get("delayed_unassigned_shards", 0),
                number_of_pending_tasks=response.get("number_of_pending_tasks", 0),
                task_max_waiting_in_queue_millis=response.get(
                    "task_max_waiting_in_queue_millis", 0
                ),
                active_shards_percent_as_number=response.get(
                    "active_shards_percent_as_number", 0.0
                ),
            )

            self._cached_health = health
            self._last_health_check = time.time()
            return health

        except Exception as e:
            logger.error(f"Failed to get cluster health: {e}")
            raise

    def get_cluster_info(self, force_refresh: bool = False) -> ClusterInfo:
        """
        Get cluster information.

        Args:
            force_refresh: Force refresh of cluster info

        Returns:
            ClusterInfo instance
        """
        if self._cluster_info and not force_refresh:
            return self._cluster_info

        try:
            response = self.client.info()
            info = ClusterInfo(
                name=response.get("name", ""),
                cluster_uuid=response.get("cluster_uuid", ""),
                version=response.get("version", {}).get("number", ""),
                build_date=response.get("version", {}).get("build_date", ""),
                build_hash=response.get("version", {}).get("build_hash", ""),
                lucene_version=response.get("version", {}).get("lucene_version", ""),
                tagline=response.get("tagline", ""),
            )

            self._cluster_info = info
            return info

        except Exception as e:
            logger.error(f"Failed to get cluster info: {e}")
            raise

    def get_nodes_info(self) -> List[NodeInfo]:
        """
        Get information about all nodes in the cluster.

        Returns:
            List of NodeInfo instances
        """
        try:
            response = self.client.nodes.info()
            nodes = []

            for node_id, node_data in response.get("nodes", {}).items():
                node_info = NodeInfo(
                    name=node_data.get("name", ""),
                    host=node_data.get("host", ""),
                    ip=node_data.get("ip", ""),
                    version=node_data.get("version", ""),
                    roles=node_data.get("roles", []),
                    os_name=node_data.get("os", {}).get("name", ""),
                    os_version=node_data.get("os", {}).get("version", ""),
                    jvm_version=node_data.get("jvm", {}).get("version", ""),
                )
                nodes.append(node_info)

            return nodes

        except Exception as e:
            logger.error(f"Failed to get nodes info: {e}")
            raise

    def get_node_stats(self) -> Dict[str, Any]:
        """
        Get node statistics.

        Returns:
            Dictionary with node statistics
        """
        try:
            return self.client.nodes.stats()
        except Exception as e:
            logger.error(f"Failed to get node stats: {e}")
            raise

    def verify_connection(self) -> bool:
        """
        Verify connection to Elasticsearch cluster.

        Returns:
            True if connection is verified
        """
        try:
            # Ping the cluster
            if not self.ping():
                return False

            # Get cluster info
            self.get_cluster_info()

            # Get cluster health
            health = self.get_cluster_health(use_cache=False)

            return health.is_healthy

        except Exception as e:
            logger.error(f"Connection verification failed: {e}")
            return False

    def detect_features(self) -> Dict[str, bool]:
        """
        Detect supported features based on cluster version.

        Returns:
            Dictionary of feature flags
        """
        try:
            info = self.get_cluster_info()
            version = info.version

            # Parse version
            major_version = int(version.split(".")[0])

            features = {
                "vector_search": major_version >= 8,
                "knn_search": major_version >= 8,
                "sql": major_version >= 7,
                "eql": major_version >= 7,
                "async_search": major_version >= 7,
                "point_in_time": major_version >= 7,
                "transform": major_version >= 7,
                "rollup": major_version >= 7,
                "index_sorting": major_version >= 7,
                "runtime_fields": major_version >= 7,
            }

            return features

        except Exception as e:
            logger.error(f"Failed to detect features: {e}")
            return {}

    def wait_for_cluster_health(
        self,
        status: str = "yellow",
        timeout: int = 30,
        interval: int = 1,
    ) -> bool:
        """
        Wait for cluster to reach desired health status.

        Args:
            status: Desired health status (green, yellow, red)
            timeout: Maximum wait time in seconds
            interval: Check interval in seconds

        Returns:
            True if cluster reached desired status
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                health = self.get_cluster_health(use_cache=False)
                if health.status == status:
                    return True
                elif health.status == "green" and status == "yellow":
                    return True
            except Exception:
                pass

            time.sleep(interval)

        return False

    def _is_health_cache_valid(self) -> bool:
        """Check if health cache is still valid."""
        if not self._cached_health or not self._last_health_check:
            return False

        return time.time() - self._last_health_check < self._health_cache_ttl

    def get_index_health(self, index: str) -> Dict[str, Any]:
        """
        Get health status for a specific index.

        Args:
            index: Index name or pattern

        Returns:
            Dictionary with index health information
        """
        try:
            return self.client.indices.health(index=index)
        except Exception as e:
            logger.error(f"Failed to get index health for {index}: {e}")
            raise

    def get_index_stats(self, index: str) -> Dict[str, Any]:
        """
        Get statistics for a specific index.

        Args:
            index: Index name or pattern

        Returns:
            Dictionary with index statistics
        """
        try:
            return self.client.indices.stats(index=index)
        except Exception as e:
            logger.error(f"Failed to get index stats for {index}: {e}")
            raise
