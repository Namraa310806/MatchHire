# Elasticsearch Provider Architecture

## Overview

The Elasticsearch provider implements the `SearchProvider` interface using Elasticsearch as the backend search engine. It provides full-text search, autocomplete, bulk operations, cluster management, and index lifecycle management.

## Design Principles

1. **Provider Abstraction**: The provider implements the standard `SearchProvider` interface, making it a drop-in replacement for PostgreSQL or other providers.
2. **Configuration-Driven**: All settings are configurable through Django settings, with sensible defaults.
3. **Production-Ready**: Includes cluster management, health monitoring, and zero-downtime index operations.
4. **Extensible**: Designed to support future features like vector search, semantic search, and advanced aggregations.

## Architecture Components

### Core Components

```
apps/search/providers/elasticsearch/
├── __init__.py              # Package initialization
├── elasticsearch.py         # Main provider implementation
├── cluster.py               # Cluster management utilities
├── index_lifecycle.py       # Index lifecycle management
├── mappings.py              # Index mappings for all entities
├── analyzers.py             # Custom text analyzers
└── tests/                   # Comprehensive test suite
```

### Component Responsibilities

#### ElasticsearchProvider (`elasticsearch.py`)
- Implements the `SearchProvider` interface
- Manages Elasticsearch client connection
- Handles search, autocomplete, indexing, and deletion operations
- Integrates with cluster and index lifecycle managers
- Provides provider-specific methods for advanced operations

#### ClusterManager (`cluster.py`)
- Monitors cluster health and status
- Provides node information and statistics
- Detects supported features based on cluster version
- Handles connection verification and graceful reconnection
- Caches health information for performance

#### IndexLifecycleManager (`index_lifecycle.py`)
- Manages index creation, deletion, and recreation
- Handles index refresh, close, and open operations
- Implements alias management for zero-downtime operations
- Supports versioned indices for safe schema changes
- Provides cleanup utilities for old indices

#### Mappings (`mappings.py`)
- Defines production-ready mappings for all entity types
- Includes keyword, text, date, numeric, and boolean fields
- Supports nested objects for complex data structures
- Provides placeholders for geo and vector search
- Implements edge n-gram fields for autocomplete

#### Analyzers (`analyzers.py`)
- Defines custom text analyzers for search
- Includes standard, lowercase, ASCII folding analyzers
- Implements edge n-gram analyzer for autocomplete
- Provides synonym support (placeholder for future)
- Defines custom normalizers for keyword fields

## Data Flow

### Search Flow

```
Service Layer
    ↓
Search Registry
    ↓
ElasticsearchProvider.search()
    ↓
Build Query (filters, sort, pagination)
    ↓
Elasticsearch Client
    ↓
Cluster
    ↓
Results
```

### Indexing Flow

```
Service Layer
    ↓
Search Registry
    ↓
ElasticsearchProvider.index() / bulk_index()
    ↓
IndexLifecycleManager (get index name)
    ↓
Elasticsearch Client
    ↓
Index
```

### Bulk Indexing Flow

```
BulkIndexer
    ↓
SyncService
    ↓
ElasticsearchProvider.bulk_index()
    ↓
Chunking (500 docs per chunk)
    ↓
elasticsearch.helpers.bulk()
    ↓
Index with retry on failure
```

## Configuration

### Environment Variables

```python
# Django settings
SEARCH_PROVIDER = "elasticsearch"

SEARCH_CONFIG = {
    "elasticsearch": {
        "hosts": ["http://localhost:9200"],
        "username": None,
        "password": None,
        "api_key": None,
        "cloud_id": None,
        "verify_certs": True,
        "request_timeout": 30,
        "max_retries": 3,
        "retry_on_timeout": True,
        "http_compress": False,
        "max_connections": 10,
        "index_prefix": "matchhire",
        "use_aliases": True,
        "refresh_interval": "1s",
        "number_of_shards": 3,
        "number_of_replicas": 1,
    }
}
```

### Index Naming Convention

- **Standard Index**: `{prefix}_{entity_type}` (e.g., `matchhire_job`)
- **Versioned Index**: `{prefix}_{entity_type}_v{version}` (e.g., `matchhire_job_v2`)
- **Alias**: `{prefix}_{entity_type}_alias` (e.g., `matchhire_job_alias`)

## Integration Points

### Registry Integration

The provider is automatically registered in the `SearchRegistry`:

```python
from apps.search.registry import get_registry

registry = get_registry()
provider = registry.get_provider("elasticsearch", config)
```

### Indexing Engine Integration

The provider integrates with the existing bulk indexing engine:

```python
from apps.search.indexing.sync_service import SyncService

sync_service = SyncService(provider)
sync_service.sync_bulk_documents(documents)
```

### Service Layer Integration

Services use the provider through the registry:

```python
from apps.search.registry import get_registry

registry = get_registry()
provider = registry.get_provider()
results = provider.search("job", "software engineer")
```

## Performance Considerations

### Bulk Operations
- Default chunk size: 500 documents
- Configurable via `DEFAULT_CHUNK_SIZE`
- Uses `elasticsearch.helpers.bulk` for efficiency
- Automatic retry on partial failures

### Caching
- Cluster health cached for 5 seconds
- Cluster info cached until force refresh
- Reduces unnecessary cluster calls

### Connection Pooling
- Configurable max connections
- Configurable max connections per host
- Reuses connections for efficiency

### Index Refresh
- Default refresh interval: 1 second
- Configurable per index
- Manual refresh available via `refresh()` method

## Fault Tolerance

### Connection Failures
- Automatic retry on timeout
- Configurable retry count
- Graceful degradation on connection loss

### Partial Bulk Failures
- Continues processing on individual document failures
- Returns detailed error information
- Supports retry of failed documents

### Cluster Health
- Monitors cluster health status
- Returns unhealthy status on red/yellow clusters
- Supports waiting for cluster health

## Security

### Authentication
- Basic auth (username/password)
- API key authentication
- Cloud ID authentication

### SSL/TLS
- Certificate verification
- Custom CA certificates
- Client certificate support

## Monitoring

### Health Checks
- Cluster health (green/yellow/red)
- Node information
- Index health
- Document counts
- Storage size

### Metrics
- Query latency
- Indexing throughput
- Error rates
- Connection metrics

## Future Enhancements

### Planned Features
- Vector search integration
- Semantic search
- Advanced aggregations
- SQL support
- Point-in-time queries
- Async search
- Transform jobs
- Rollup jobs

### Extension Points
- Custom analyzers
- Custom mappings
- Custom scoring functions
- Plugin system for custom behavior
