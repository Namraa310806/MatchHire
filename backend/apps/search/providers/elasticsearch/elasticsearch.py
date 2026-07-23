"""
Elasticsearch search provider implementation.

This provider implements the SearchProvider interface using Elasticsearch,
supporting full-text search, autocomplete, bulk operations, and
cluster management.
"""

import time
import logging
from typing import Any, Dict, List, Optional
from elasticsearch import Elasticsearch, TransportError
from elasticsearch.helpers import bulk

from apps.search.providers.base import (
    SearchProvider,
    IndexResult,
    BulkIndexResult,
    DeleteResult,
    BulkDeleteResult,
    HealthResult,
    StatisticsResult,
)
from apps.search.exceptions import ProviderUnavailable, InvalidQuery, SearchTimeout
from apps.search.config import SearchConfig

from .cluster import ClusterManager
from .index_lifecycle import IndexLifecycleManager
from .mappings import Mappings
from .analyzers import Analyzers

logger = logging.getLogger(__name__)


class ElasticsearchProvider(SearchProvider):
    """
    Elasticsearch-based search provider.

    This provider implements search using:
    - Elasticsearch for full-text search and indexing
    - Custom analyzers for text processing
    - Production-ready mappings for all entity types
    - Cluster management for health monitoring
    - Index lifecycle management for zero-downtime operations
    - Bulk operations with chunking and retry
    """

    # Entity type to index name mapping
    ENTITY_INDICES = {
        "job": "job",
        "candidate": "candidate",
        "resume": "resume",
        "company": "company",
        "recruiter": "recruiter",
        "skill": "skill",
        "application": "application",
        "interview": "interview",
    }

    # Default bulk operation settings
    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_MAX_RETRIES = 3

    def _initialize(self) -> None:
        """Initialize Elasticsearch provider."""
        try:
            # Get configuration
            config = SearchConfig.get_elasticsearch_config()

            # Build Elasticsearch client
            client_config = {
                "hosts": config.get("hosts", ["http://localhost:9200"]),
                "request_timeout": config.get("request_timeout", 30),
                "max_retries": config.get("max_retries", 3),
                "retry_on_timeout": config.get("retry_on_timeout", True),
                "retry_on_status": config.get("retry_on_status", [502, 503, 504]),
                "http_compress": config.get("http_compress", False),
                "max_connections": config.get("max_connections", 10),
                "max_connections_per_host": config.get("max_connections_per_host", 10),
            }

            # Add authentication if provided
            if config.get("username") and config.get("password"):
                client_config["basic_auth"] = (
                    config.get("username"),
                    config.get("password"),
                )
            elif config.get("api_key"):
                client_config["api_key"] = config.get("api_key")

            # Add SSL configuration
            if config.get("verify_certs") is not None:
                client_config["verify_certs"] = config.get("verify_certs")
            if config.get("ca_certs"):
                client_config["ca_certs"] = config.get("ca_certs")
            if config.get("client_cert"):
                client_config["client_cert"] = config.get("client_cert")
            if config.get("client_key"):
                client_config["client_key"] = config.get("client_key")

            # Add cloud ID if provided
            if config.get("cloud_id"):
                client_config["cloud_id"] = config.get("cloud_id")

            # Create client
            self.client = Elasticsearch(**client_config)

            # Initialize cluster manager
            self.cluster_manager = ClusterManager(self.client)

            # Initialize index lifecycle manager
            index_prefix = config.get("index_prefix", "matchhire")
            use_aliases = config.get("use_aliases", True)
            self.index_lifecycle = IndexLifecycleManager(self.client, index_prefix)
            self.use_aliases = use_aliases

            # Verify connection
            if not self.cluster_manager.verify_connection():
                raise ProviderUnavailable("Elasticsearch connection verification failed")

            # Initialize indices if they don't exist
            self._initialize_indices()

            logger.info("Elasticsearch provider initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch provider: {e}")
            raise ProviderUnavailable(f"Elasticsearch initialization failed: {e}")

    def _initialize_indices(self) -> None:
        """Initialize indices for all entity types if they don't exist."""
        try:
            settings = Analyzers.get_index_settings()

            for entity_type, index_name in self.ENTITY_INDICES.items():
                if not self.index_lifecycle.index_exists(entity_type):
                    mapping = Mappings.get_mapping(entity_type)
                    self.index_lifecycle.create_index(entity_type, mapping, settings)
                    logger.info(f"Created index for {entity_type}")

        except Exception as e:
            logger.error(f"Failed to initialize indices: {e}")
            # Don't fail initialization if index creation fails
            # Indices can be created manually later

    def _get_index_name(self, entity_type: str) -> str:
        """
        Get the index name for an entity type.

        Args:
            entity_type: Entity type

        Returns:
            Index name or alias name
        """
        if self.use_aliases:
            return self.index_lifecycle.get_alias_name(entity_type)
        return self.index_lifecycle.get_index_name(entity_type)

    def _build_query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
        pagination: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Build Elasticsearch query from parameters.

        Args:
            query: Search query string
            filters: Dictionary of field filters
            sort: List of sort specifications
            pagination: Pagination parameters
            fields: List of fields to return

        Returns:
            Elasticsearch query body
        """
        es_query = {"query": {"bool": {}}}

        # Add full-text search if query is provided
        if query:
            es_query["query"]["bool"]["must"] = [
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["searchable_text", "title^2", "full_name^2", "name^2", "company_name^2"],
                        "type": "best_fields",
                        "fuzziness": "AUTO",
                    }
                }
            ]
        else:
            es_query["query"]["bool"]["must"] = [{"match_all": {}}]

        # Add filters
        if filters:
            filter_clauses = []
            for field, value in filters.items():
                if isinstance(value, (list, tuple)):
                    filter_clauses.append({"terms": {field: value}})
                elif isinstance(value, dict):
                    # Handle range filters
                    range_filter = {"range": {field: {}}}
                    if "gte" in value:
                        range_filter["range"][field]["gte"] = value["gte"]
                    if "lte" in value:
                        range_filter["range"][field]["lte"] = value["lte"]
                    if "gt" in value:
                        range_filter["range"][field]["gt"] = value["gt"]
                    if "lt" in value:
                        range_filter["range"][field]["lt"] = value["lt"]
                    filter_clauses.append(range_filter)
                elif isinstance(value, bool):
                    filter_clauses.append({"term": {field: value}})
                else:
                    filter_clauses.append({"term": {field: value}})

            if filter_clauses:
                es_query["query"]["bool"]["filter"] = filter_clauses

        # Add sorting
        if sort:
            es_sort = []
            for sort_spec in sort:
                field = sort_spec.get("field")
                direction = sort_spec.get("direction", "asc")
                es_sort.append({field: {"order": direction}})
            es_query["sort"] = es_sort
        else:
            # Default sort by created_at descending
            es_query["sort"] = [{"created_at": {"order": "desc"}}]

        # Add pagination
        if pagination:
            if "offset" in pagination and "limit" in pagination:
                es_query["from"] = pagination["offset"]
                es_query["size"] = pagination["limit"]
            elif "page" in pagination and "page_size" in pagination:
                page = max(1, pagination["page"])
                page_size = max(1, min(100, pagination["page_size"]))
                es_query["from"] = (page - 1) * page_size
                es_query["size"] = page_size
            else:
                es_query["from"] = 0
                es_query["size"] = 20
        else:
            es_query["from"] = 0
            es_query["size"] = 20

        # Add field selection
        if fields:
            es_query["_source"] = fields

        # Add highlighting
        if query:
            es_query["highlight"] = {
                "fields": {
                    "searchable_text": {},
                    "title": {},
                    "description": {},
                    "full_name": {},
                },
                "pre_tags": ["<em>"],
                "post_tags": ["</em>"],
            }

        return es_query

    def search(
        self,
        entity_type: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
        pagination: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute a search query using Elasticsearch."""
        start_time = time.time()

        try:
            index_name = self._get_index_name(entity_type)
            es_query = self._build_query(query, filters, sort, pagination, fields)

            # Execute search
            response = self.client.search(index=index_name, body=es_query)

            # Extract results
            hits = response.get("hits", {})
            results = [hit.get("_source") for hit in hits.get("hits", [])]

            # Add highlights to results
            for i, hit in enumerate(hits.get("hits", [])):
                if "highlight" in hit:
                    results[i]["_highlight"] = hit["highlight"]

            took_ms = int((time.time() - start_time) * 1000)

            return {
                "results": results,
                "total": hits.get("total", {}).get("value", 0),
                "offset": es_query.get("from", 0),
                "took_ms": took_ms,
                "metadata": {
                    "provider": "elasticsearch",
                    "entity_type": entity_type,
                    "query": query,
                    "index": index_name,
                },
            }

        except TransportError as e:
            if e.status_code == 408:
                raise SearchTimeout(f"Elasticsearch search timeout: {e}")
            raise InvalidQuery(f"Elasticsearch search failed: {e}")
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise InvalidQuery(f"Search failed: {e}")

    def autocomplete(
        self,
        entity_type: str,
        field: str,
        prefix: str,
        context: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get autocomplete suggestions using Elasticsearch."""
        try:
            index_name = self._get_index_name(entity_type)

            # Build autocomplete query
            es_query = {
                "size": limit,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "prefix": {
                                    f"{field}.edge_ngram": {
                                        "value": prefix,
                                        "boost": 2.0,
                                    }
                                }
                            },
                            {
                                "prefix": {
                                    f"{field}.keyword": {
                                        "value": prefix,
                                    }
                                }
                            },
                        ]
                    }
                },
                "_source": [field],
                "aggs": {
                    "suggestions": {
                        "terms": {
                            "field": f"{field}.keyword",
                            "size": limit,
                        }
                    }
                },
            }

            # Add context filters if provided
            if context:
                filter_clauses = []
                for filter_field, filter_value in context.items():
                    if isinstance(filter_value, (list, tuple)):
                        filter_clauses.append({"terms": {filter_field: filter_value}})
                    else:
                        filter_clauses.append({"term": {filter_field: filter_value}})

                if filter_clauses:
                    es_query["query"]["bool"]["filter"] = filter_clauses

            # Execute search
            response = self.client.search(index=index_name, body=es_query)

            # Extract suggestions from aggregation
            buckets = (
                response.get("aggregations", {})
                .get("suggestions", {})
                .get("buckets", [])
            )

            suggestions = [
 {"value": bucket["key"], "metadata": {"count": bucket["doc_count"]}}
                for bucket in buckets
            ]

            return suggestions

        except Exception as e:
            logger.error(f"Autocomplete failed: {e}")
            raise InvalidQuery(f"Autocomplete failed: {e}")

    def index(
        self,
        entity_type: str,
        document_id: str,
        document: Dict[str, Any],
    ) -> IndexResult:
        """Index a single document."""
        start_time = time.time()

        try:
            index_name = self._get_index_name(entity_type)

            # Index document
            self.client.index(
                index=index_name,
                id=document_id,
                body=document,
                refresh=False,
            )

            took_ms = int((time.time() - start_time) * 1000)

            return IndexResult(
                success=True,
                document_id=document_id,
                took_ms=took_ms,
            )

        except Exception as e:
            logger.error(f"Indexing failed for document {document_id}: {e}")
            return IndexResult(
                success=False,
                document_id=document_id,
                error=str(e),
                took_ms=int((time.time() - start_time) * 1000),
            )

    def bulk_index(
        self,
        entity_type: str,
        documents: List[Dict[str, Any]],
    ) -> BulkIndexResult:
        """Index multiple documents in bulk."""
        start_time = time.time()
        indexed_count = 0
        failed_count = 0
        errors = []

        try:
            index_name = self._get_index_name(entity_type)

            # Prepare bulk actions
            actions = []
            for doc in documents:
                doc_id = doc.get("id")
                if not doc_id:
                    failed_count += 1
                    errors.append({"document": doc, "error": "Missing id field"})
                    continue

                actions.append(
                    {
                        "_index": index_name,
                        "_id": doc_id,
                        "_source": doc,
                    }
                )

            # Execute bulk operation with helpers.bulk for better error handling
            success_count, failed_items = bulk(
                self.client,
                actions,
                chunk_size=self.DEFAULT_CHUNK_SIZE,
                raise_on_error=False,
                stats_only=False,
            )

            indexed_count = success_count
            failed_count = len(failed_items)

            for item in failed_items:
                errors.append(
                    {
                        "document_id": item.get("index", {}).get("_id"),
                        "error": item.get("index", {}).get("error"),
                    }
                )

            took_ms = int((time.time() - start_time) * 1000)

            return BulkIndexResult(
                success=failed_count == 0,
                indexed_count=indexed_count,
                failed_count=failed_count,
                errors=errors,
                took_ms=took_ms,
            )

        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return BulkIndexResult(
                success=False,
                indexed_count=indexed_count,
                failed_count=len(documents) - indexed_count,
                errors=[{"error": str(e)}],
                took_ms=int((time.time() - start_time) * 1000),
            )

    def delete(
        self,
        entity_type: str,
        document_id: str,
    ) -> DeleteResult:
        """Delete a single document from the index."""
        start_time = time.time()

        try:
            index_name = self._get_index_name(entity_type)

            # Delete document
            response = self.client.delete(
                index=index_name,
                id=document_id,
                refresh=False,
            )

            took_ms = int((time.time() - start_time) * 1000)

            if response.get("result") in ["deleted", "not_found"]:
                return DeleteResult(
                    success=True,
                    document_id=document_id,
                    took_ms=took_ms,
                )
            else:
                return DeleteResult(
                    success=False,
                    document_id=document_id,
                    error=f"Unexpected result: {response.get('result')}",
                    took_ms=took_ms,
                )

        except Exception as e:
            logger.error(f"Delete failed for document {document_id}: {e}")
            return DeleteResult(
                success=False,
                document_id=document_id,
                error=str(e),
                took_ms=int((time.time() - start_time) * 1000),
            )

    def bulk_delete(
        self,
        entity_type: str,
        document_ids: List[str],
    ) -> BulkDeleteResult:
        """Delete multiple documents from the index in bulk."""
        start_time = time.time()
        deleted_count = 0
        failed_count = 0
        errors = []

        try:
            index_name = self._get_index_name(entity_type)

            # Prepare bulk delete actions
            actions = []
            for doc_id in document_ids:
                actions.append(
                    {
                        "_op_type": "delete",
                        "_index": index_name,
                        "_id": doc_id,
                    }
                )

            # Execute bulk operation
            success_count, failed_items = bulk(
                self.client,
                actions,
                chunk_size=self.DEFAULT_CHUNK_SIZE,
                raise_on_error=False,
                stats_only=False,
            )

            deleted_count = success_count
            failed_count = len(failed_items)

            for item in failed_items:
                errors.append(
                    {
                        "document_id": item.get("delete", {}).get("_id"),
                        "error": item.get("delete", {}).get("error"),
                    }
                )

            took_ms = int((time.time() - start_time) * 1000)

            return BulkDeleteResult(
                success=failed_count == 0,
                deleted_count=deleted_count,
                failed_count=failed_count,
                errors=errors,
                took_ms=took_ms,
            )

        except Exception as e:
            logger.error(f"Bulk delete failed: {e}")
            return BulkDeleteResult(
                success=False,
                deleted_count=deleted_count,
                failed_count=len(document_ids) - deleted_count,
                errors=[{"error": str(e)}],
                took_ms=int((time.time() - start_time) * 1000),
            )

    def health(self) -> HealthResult:
        """Check the health of the Elasticsearch cluster."""
        try:
            # Get cluster health
            cluster_health = self.cluster_manager.get_cluster_health(use_cache=False)

            # Get cluster info
            cluster_info = self.cluster_manager.get_cluster_info()

            details = {
                "cluster_name": cluster_info.name,
                "cluster_version": cluster_info.version,
                "status": cluster_health.status,
                "number_of_nodes": cluster_health.number_of_nodes,
                "number_of_data_nodes": cluster_health.number_of_data_nodes,
                "active_shards": cluster_health.active_shards,
                "active_primary_shards": cluster_health.active_primary_shards,
                "relocating_shards": cluster_health.relocating_shards,
                "initializing_shards": cluster_health.initializing_shards,
                "unassigned_shards": cluster_health.unassigned_shards,
                "active_shards_percent": cluster_health.active_shards_percent_as_number,
            }

            return HealthResult(
                healthy=cluster_health.is_healthy,
                provider_name="elasticsearch",
                details=details,
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthResult(
                healthy=False,
                provider_name="elasticsearch",
                details={},
                error=str(e),
            )

    def statistics(
        self,
        entity_type: Optional[str] = None,
    ) -> StatisticsResult:
        """Get statistics about indexed documents."""
        try:
            if entity_type:
                index_name = self._get_index_name(entity_type)
                stats = self.index_lifecycle.get_index_stats(entity_type)
                doc_count = (
                    stats.get("indices", {})
                    .get(index_name, {})
                    .get("primaries", {})
                    .get("docs", {})
                    .get("count", 0)
                )
                store_size = (
                    stats.get("indices", {})
                    .get(index_name, {})
                    .get("primaries", {})
                    .get("store", {})
                    .get("size_in_bytes", 0)
                )
            else:
                # Get stats for all indices
                doc_count = 0
                store_size = 0
                for et in self.ENTITY_INDICES.keys():
                    index_name = self._get_index_name(et)
                    try:
                        stats = self.index_lifecycle.get_index_stats(et)
                        doc_count += (
                            stats.get("indices", {})
                            .get(index_name, {})
                            .get("primaries", {})
                            .get("docs", {})
                            .get("count", 0)
                        )
                        store_size += (
                            stats.get("indices", {})
                            .get(index_name, {})
                            .get("primaries", {})
                            .get("store", {})
                            .get("size_in_bytes", 0)
                        )
                    except Exception:
                        pass

            return StatisticsResult(
                document_count=doc_count,
                index_size_bytes=store_size,
                details={"entity_type": entity_type} if entity_type else None,
            )

        except Exception as e:
            logger.error(f"Statistics query failed: {e}")
            raise InvalidQuery(f"Statistics query failed: {e}")

    def refresh(self, entity_type: Optional[str] = None) -> None:
        """
        Refresh index(es) to make changes visible to search.

        Args:
            entity_type: Optional entity type to refresh (refreshes all if None)
        """
        try:
            if entity_type:
                self.index_lifecycle.refresh_index(entity_type)
            else:
                # Refresh all indices
                for et in self.ENTITY_INDICES.keys():
                    try:
                        self.index_lifecycle.refresh_index(et)
                    except Exception as e:
                        logger.warning(f"Failed to refresh {et}: {e}")

        except Exception as e:
            logger.error(f"Refresh failed: {e}")
            raise

    def close(self) -> None:
        """Close Elasticsearch client connection."""
        try:
            if hasattr(self, "client"):
                self.client.close()
                logger.info("Elasticsearch client closed")
        except Exception as e:
            logger.error(f"Failed to close Elasticsearch client: {e}")

    # Additional provider-specific methods

    def get_cluster_health(self) -> Dict[str, Any]:
        """
        Get detailed cluster health information.

        Returns:
            Cluster health details
        """
        return self.cluster_manager.get_cluster_health().to_dict()

    def get_nodes_info(self) -> List[Dict[str, Any]]:
        """
        Get information about cluster nodes.

        Returns:
            List of node information dictionaries
        """
        nodes = self.cluster_manager.get_nodes_info()
        return [node.__dict__ for node in nodes]

    def get_index_health(self, entity_type: str) -> Dict[str, Any]:
        """
        Get health status for a specific index.

        Args:
            entity_type: Entity type

        Returns:
            Index health information
        """
        index_name = self._get_index_name(entity_type)
        return self.index_lifecycle.get_index_health(entity_type)

    def create_versioned_index(
        self,
        entity_type: str,
        switch_alias: bool = True,
    ) -> str:
        """
        Create a new versioned index and optionally switch the alias.

        Args:
            entity_type: Entity type
            switch_alias: Whether to switch the alias to the new index

        Returns:
            New index name
        """
        mapping = Mappings.get_mapping(entity_type)
        settings = Analyzers.get_index_settings()
        return self.index_lifecycle.create_versioned_index(
            entity_type, mapping, settings, switch_alias
        )

    def cleanup_old_indices(
        self,
        entity_type: str,
        keep_versions: int = 2,
    ) -> int:
        """
        Clean up old versioned indices.

        Args:
            entity_type: Entity type
            keep_versions: Number of recent versions to keep

        Returns:
            Number of indices deleted
        """
        return self.index_lifecycle.cleanup_old_indices(entity_type, keep_versions)

    def get_supported_features(self) -> Dict[str, bool]:
        """
        Get supported features based on cluster version.

        Returns:
            Dictionary of feature flags
        """
        return self.cluster_manager.detect_features()
