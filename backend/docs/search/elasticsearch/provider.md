# Elasticsearch Provider Design

## Provider Overview

The `ElasticsearchProvider` class implements the `SearchProvider` interface, providing a complete Elasticsearch-based search solution for MatchHire.

## Class Structure

```python
class ElasticsearchProvider(SearchProvider):
    """Elasticsearch-based search provider."""
```

## Initialization

### Configuration Parameters

The provider accepts configuration through Django settings:

```python
SEARCH_CONFIG = {
    "elasticsearch": {
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
}
```

### Initialization Process

1. Load configuration from `SearchConfig.get_elasticsearch_config()`
2. Build Elasticsearch client with authentication and SSL settings
3. Initialize `ClusterManager` for health monitoring
4. Initialize `IndexLifecycleManager` for index operations
5. Verify cluster connection
6. Create indices if they don't exist

## Core Methods

### search()

Executes a search query with full-text search, filters, sorting, and pagination.

**Parameters:**
- `entity_type`: Type of entity to search (job, candidate, resume, etc.)
- `query`: Search query string
- `filters`: Dictionary of field filters
- `sort`: List of sort specifications
- `pagination`: Pagination parameters
- `fields`: List of fields to return

**Returns:**
```python
{
    "results": [...],
    "total": 100,
    "offset": 0,
    "took_ms": 25,
    "metadata": {
        "provider": "elasticsearch",
        "entity_type": "job",
        "query": "software engineer",
        "index": "matchhire_job_alias"
    }
}
```

**Query Building:**
- Uses `multi_match` for full-text search across multiple fields
- Supports fuzzy matching with `AUTO` fuzziness
- Applies filters using `bool` query
- Supports range filters (gte, lte, gt, lt)
- Supports term filters and `terms` filters for lists
- Includes highlighting for matched terms

### autocomplete()

Provides autocomplete suggestions for field prefixes.

**Parameters:**
- `entity_type`: Type of entity
- `field`: Field to autocomplete on
- `prefix`: Prefix string to match
- `context`: Additional context filters
- `limit`: Maximum number of suggestions

**Returns:**
```python
[
    {"value": "Software Engineer", "metadata": {"count": 100}},
    {"value": "Software Developer", "metadata": {"count": 50}}
]
```

**Implementation:**
- Uses edge n-gram tokenizer for prefix matching
- Uses keyword field for exact matching
- Aggregates suggestions for deduplication
- Supports context filters for scoped suggestions

### index()

Indexes a single document.

**Parameters:**
- `entity_type`: Type of entity
- `document_id`: Unique document identifier
- `document`: Document data

**Returns:**
```python
IndexResult(
    success=True,
    document_id="123",
    took_ms=15
)
```

### bulk_index()

Indexes multiple documents in bulk.

**Parameters:**
- `entity_type`: Type of entity
- `documents`: List of documents to index

**Returns:**
```python
BulkIndexResult(
    success=True,
    indexed_count=500,
    failed_count=0,
    errors=[],
    took_ms=1250
)
```

**Implementation:**
- Uses `elasticsearch.helpers.bulk` for efficiency
- Chunks documents into batches of 500
- Handles partial failures gracefully
- Returns detailed error information

### delete()

Deletes a single document.

**Parameters:**
- `entity_type`: Type of entity
- `document_id`: Document identifier

**Returns:**
```python
DeleteResult(
    success=True,
    document_id="123",
    took_ms=10
)
```

### bulk_delete()

Deletes multiple documents in bulk.

**Parameters:**
- `entity_type`: Type of entity
- `document_ids`: List of document identifiers

**Returns:**
```python
BulkDeleteResult(
    success=True,
    deleted_count=100,
    failed_count=0,
    errors=[],
    took_ms=500
)
```

### health()

Checks the health of the Elasticsearch cluster.

**Returns:**
```python
HealthResult(
    healthy=True,
    provider_name="elasticsearch",
    details={
        "cluster_name": "matchhire-cluster",
        "cluster_version": "8.15.0",
        "status": "green",
        "number_of_nodes": 3,
        "number_of_data_nodes": 3,
        "active_shards": 20,
        "active_primary_shards": 10,
        "relocating_shards": 0,
        "initializing_shards": 0,
        "unassigned_shards": 0,
        "active_shards_percent": 100.0
    }
)
```

### statistics()

Gets statistics about indexed documents.

**Parameters:**
- `entity_type`: Optional entity type filter

**Returns:**
```python
StatisticsResult(
    document_count=1000,
    index_size_bytes=10240000,
    details={"entity_type": "job"}
)
```

## Provider-Specific Methods

### refresh()

Refreshes index(es) to make changes visible to search.

```python
provider.refresh(entity_type="job")  # Refresh specific index
provider.refresh()  # Refresh all indices
```

### get_cluster_health()

Gets detailed cluster health information.

```python
health = provider.get_cluster_health()
```

### get_nodes_info()

Gets information about cluster nodes.

```python
nodes = provider.get_nodes_info()
```

### get_index_health()

Gets health status for a specific index.

```python
health = provider.get_index_health(entity_type="job")
```

### create_versioned_index()

Creates a new versioned index and optionally switches the alias.

```python
new_index = provider.create_versioned_index(
    entity_type="job",
    switch_alias=True
)
```

### cleanup_old_indices()

Cleans up old versioned indices.

```python
deleted_count = provider.cleanup_old_indices(
    entity_type="job",
    keep_versions=2
)
```

### get_supported_features()

Gets supported features based on cluster version.

```python
features = provider.get_supported_features()
# Returns: {"vector_search": True, "knn_search": True, "sql": True, ...}
```

## Error Handling

### Exceptions

- `ProviderUnavailable`: Raised when cluster connection fails
- `InvalidQuery`: Raised when query is invalid
- `SearchTimeout`: Raised when query times out

### Retry Logic

- Automatic retry on timeout
- Configurable retry count
- Retry on specific HTTP status codes (502, 503, 504)

## Performance Optimization

### Bulk Operations
- Default chunk size: 500 documents
- Configurable via `DEFAULT_CHUNK_SIZE`
- Parallel processing for large bulk operations

### Query Optimization
- Uses `_source` filtering to limit returned fields
- Implements query caching in cluster manager
- Uses efficient query DSL

### Connection Pooling
- Reuses connections
- Configurable pool size
- HTTP compression support

## Usage Examples

### Basic Search

```python
from apps.search.registry import get_registry

registry = get_registry()
provider = registry.get_provider()

results = provider.search(
    entity_type="job",
    query="software engineer",
    filters={"location": "San Francisco"},
    sort=[{"field": "created_at", "direction": "desc"}],
    pagination={"page": 1, "page_size": 20}
)
```

### Autocomplete

```python
suggestions = provider.autocomplete(
    entity_type="job",
    field="title",
    prefix="soft",
    limit=10
)
```

### Bulk Indexing

```python
documents = [
    {"id": "1", "title": "Software Engineer", ...},
    {"id": "2", "title": "Data Scientist", ...},
]

result = provider.bulk_index(entity_type="job", documents=documents)
```

### Health Check

```python
health = provider.health()
if health.healthy:
    print("Cluster is healthy")
else:
    print(f"Cluster status: {health.details['status']}")
```

## Best Practices

1. **Use bulk operations** for indexing multiple documents
2. **Refresh indices** after bulk operations if immediate visibility is needed
3. **Monitor cluster health** regularly
4. **Use versioned indices** for schema changes
5. **Configure appropriate shard counts** based on data volume
6. **Use aliases** for zero-downtime deployments
7. **Set appropriate timeouts** for your workload
8. **Enable compression** for large payloads
