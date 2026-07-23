# Elasticsearch Migration Guide

## Overview

This guide covers migrating from PostgreSQL to Elasticsearch as the search provider, or switching between providers in general.

## Provider Switching

### Switching from PostgreSQL to Elasticsearch

The MatchHire search infrastructure is designed to allow provider switching via configuration only, with no code changes required.

#### Step 1: Install Dependencies

```bash
pip install elasticsearch==8.15.0
```

#### Step 2: Configure Elasticsearch

Update Django settings:

```python
# settings.py
SEARCH_PROVIDER = "elasticsearch"

SEARCH_CONFIG = {
    "elasticsearch": {
        "hosts": ["http://localhost:9200"],
        "username": None,
        "password": None,
        "verify_certs": True,
        "request_timeout": 30,
        "max_retries": 3,
        "index_prefix": "matchhire",
        "use_aliases": True,
        "number_of_shards": 3,
        "number_of_replicas": 1,
    }
}
```

#### Step 3: Deploy Elasticsearch

Follow the deployment guide to set up Elasticsearch cluster.

#### Step 4: Verify Connection

```python
from apps.search.registry import get_registry

registry = get_registry()
provider = registry.get_provider("elasticsearch")
health = provider.health()

if health.healthy:
    print("Elasticsearch is ready")
else:
    print(f"Elasticsearch is not healthy: {health.error}")
```

#### Step 5: Index Data

The existing indexing engine will automatically use Elasticsearch. Trigger a full reindex:

```python
from apps.search.indexing.bulk_indexer import BulkIndexer
from apps.search.indexing.sync_service import SyncService
from apps.search.indexing.documents import EntityType

# Create sync service
registry = get_registry()
provider = registry.get_provider("elasticsearch")
sync_service = SyncService(provider)

# Create bulk indexer
bulk_indexer = BulkIndexer(sync_service, chunk_size=100)

# Create and execute job for each entity type
for entity_type in [EntityType.JOB, EntityType.CANDIDATE, EntityType.RESUME]:
    job = bulk_indexer.create_job(entity_type)
    result = bulk_indexer.execute_job(job)
    print(f"Indexed {entity_type}: {result.processed_count} documents")
```

#### Step 6: Verify Search

```python
# Test search
results = provider.search(
    entity_type="job",
    query="software engineer",
    filters={"location": "San Francisco"}
)

print(f"Found {results['total']} results")
```

### Switching from Elasticsearch to PostgreSQL

Simply change the configuration:

```python
# settings.py
SEARCH_PROVIDER = "postgresql"
```

No other changes required. The application will automatically use PostgreSQL for search.

## Data Migration

### Export from PostgreSQL

```python
from apps.search.providers.postgresql import PostgreSQLProvider
from apps.search.config import SearchConfig

# Get PostgreSQL provider
config = SearchConfig.get_provider_config("postgresql")
pg_provider = PostgreSQLProvider(config)

# Export data
for entity_type in ["job", "candidate", "resume"]:
    results = pg_provider.search(entity_type, "")
    documents = results["results"]
    
    # Save to file or transfer to Elasticsearch
    # ...
```

### Import to Elasticsearch

```python
from apps.search.registry import get_registry

# Get Elasticsearch provider
registry = get_registry()
es_provider = registry.get_provider("elasticsearch")

# Import data in bulk
for entity_type, documents in data.items():
    result = es_provider.bulk_index(entity_type, documents)
    print(f"Indexed {result.indexed_count} documents")
```

### Reindex from Database

For a clean migration, reindex directly from the database:

```python
from apps.search.indexing.bulk_indexer import BulkIndexer
from apps.search.indexing.sync_service import SyncService
from apps.search.indexing.documents import EntityType

# Create sync service with Elasticsearch provider
registry = get_registry()
provider = registry.get_provider("elasticsearch")
sync_service = SyncService(provider)

# Create bulk indexer
bulk_indexer = BulkIndexer(sync_service, chunk_size=100)

# Reindex all entity types
for entity_type in [EntityType.JOB, EntityType.CANDIDATE, EntityType.RESUME]:
    job = bulk_indexer.create_job(entity_type)
    result = bulk_indexer.execute_job(job)
    print(f"Reindexed {entity_type}: {result.processed_count} documents")
```

## Zero-Downtime Migration

### Strategy 1: Shadow Mode

Run both providers in parallel during migration:

```python
# Phase 1: Enable shadow mode
SEARCH_PROVIDER = "postgresql"
SHADOW_SEARCH_PROVIDER = "elasticsearch"

# Phase 2: Write to both providers
# Update indexing engine to write to both providers

# Phase 3: Verify data consistency
# Compare search results between providers

# Phase 4: Switch read traffic
SEARCH_PROVIDER = "elasticsearch"

# Phase 5: Deprecate old provider
# Remove PostgreSQL search
```

### Strategy 2: Canary Deployment

Gradually migrate traffic:

```python
# Phase 1: Migrate 10% of traffic
if random.random() < 0.1:
    provider = registry.get_provider("elasticsearch")
else:
    provider = registry.get_provider("postgresql")

# Phase 2: Migrate 50% of traffic
if random.random() < 0.5:
    provider = registry.get_provider("elasticsearch")
else:
    provider = registry.get_provider("postgresql")

# Phase 3: Migrate 100% of traffic
provider = registry.get_provider("elasticsearch")
```

## Schema Migration

### Mapping Changes

When Elasticsearch mappings need to change:

```python
# Create new versioned index
new_index = provider.create_versioned_index(
    entity_type="job",
    switch_alias=False
)

# Reindex data to new index
from elasticsearch.helpers import reindex

reindex(
    client=provider.client,
    source_index="matchhire_job_alias",
    target_index=new_index,
    query={"match_all": {}}
)

# Switch alias
old_index = provider.index_lifecycle.get_index_name("job")
provider.index_lifecycle.switch_alias(
    entity_type="job",
    old_index=old_index,
    new_index=new_index
)

# Cleanup old indices
provider.cleanup_old_indices(entity_type="job", keep_versions=2)
```

### Analyzer Changes

When analyzers need to change:

```python
# Update analyzer configuration
from apps.search.providers.elasticsearch.analyzers import Analyzers

# Modify analyzers
Analyzers.ANALYSIS_SETTINGS["analysis"]["analyzer"]["standard"]["stopwords"] = "_english_"

# Create new versioned index with new analyzers
new_index = provider.create_versioned_index(entity_type="job", switch_alias=False)

# Reindex data
# ... reindex logic ...

# Switch alias
# ... switch logic ...
```

## Rollback Procedure

### Rollback to PostgreSQL

If Elasticsearch migration fails:

```python
# Step 1: Switch configuration
SEARCH_PROVIDER = "postgresql"

# Step 2: Restart application
# No data loss - PostgreSQL still has source of truth

# Step 3: Verify functionality
# Test search operations
```

### Rollback Index Changes

If index changes cause issues:

```python
# Step 1: Switch alias back to old index
old_index = provider.index_lifecycle.get_index_name("job", version=1)
current_index = provider.index_lifecycle.get_index_name("job", version=2)

provider.index_lifecycle.switch_alias(
    entity_type="job",
    old_index=current_index,
    new_index=old_index
)

# Step 2: Delete problematic index
provider.index_lifecycle.delete_index(entity_type="job", version=2)
```

## Validation

### Data Consistency Check

```python
def validate_migration(pg_provider, es_provider, entity_type):
    """Validate data consistency between providers."""
    
    # Get counts
    pg_stats = pg_provider.statistics(entity_type)
    es_stats = es_provider.statistics(entity_type)
    
    print(f"PostgreSQL count: {pg_stats.document_count}")
    print(f"Elasticsearch count: {es_stats.document_count}")
    
    # Sample comparison
    pg_results = pg_provider.search(entity_type, "", pagination={"limit": 100})
    es_results = es_provider.search(entity_type, "", pagination={"limit": 100})
    
    # Compare sample results
    pg_ids = {doc["id"] for doc in pg_results["results"]}
    es_ids = {doc["id"] for doc in es_results["results"]}
    
    missing = pg_ids - es_ids
    extra = es_ids - pg_ids
    
    print(f"Missing in Elasticsearch: {len(missing)}")
    print(f"Extra in Elasticsearch: {len(extra)}")
    
    return len(missing) == 0 and len(extra) == 0
```

### Search Result Comparison

```python
def compare_search_results(pg_provider, es_provider, query, filters=None):
    """Compare search results between providers."""
    
    pg_results = pg_provider.search("job", query, filters=filters)
    es_results = es_provider.search("job", query, filters=filters)
    
    print(f"PostgreSQL results: {pg_results['total']}")
    print(f"Elasticsearch results: {es_results['total']}")
    
    # Compare top results
    pg_top = pg_results["results"][:10]
    es_top = es_results["results"][:10]
    
    pg_ids = [doc["id"] for doc in pg_top]
    es_ids = [doc["id"] for doc in es_top]
    
    overlap = len(set(pg_ids) & set(es_ids))
    print(f"Top 10 overlap: {overlap}/10")
```

## Performance Comparison

### Benchmark Search Performance

```python
import time

def benchmark_search(provider, entity_type, query, iterations=100):
    """Benchmark search performance."""
    
    times = []
    for _ in range(iterations):
        start = time.time()
        results = provider.search(entity_type, query)
        times.append((time.time() - start) * 1000)
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"Average: {avg_time:.2f} ms")
    print(f"Min: {min_time:.2f} ms")
    print(f"Max: {max_time:.2f} ms")
    
    return avg_time
```

### Benchmark Indexing Performance

```python
def benchmark_indexing(provider, entity_type, documents):
    """Benchmark indexing performance."""
    
    start = time.time()
    result = provider.bulk_index(entity_type, documents)
    duration = (time.time() - start) * 1000
    
    docs_per_second = len(documents) / (duration / 1000)
    
    print(f"Total time: {duration:.2f} ms")
    print(f"Documents per second: {docs_per_second:.2f}")
    
    return docs_per_second
```

## Migration Checklist

### Pre-Migration

- [ ] Install Elasticsearch dependencies
- [ ] Deploy Elasticsearch cluster
- [ ] Configure Elasticsearch settings
- [ ] Test Elasticsearch connection
- [ ] Backup PostgreSQL database
- [ ] Document current search functionality
- [ ] Set up monitoring for Elasticsearch
- [ ] Prepare rollback plan

### Migration

- [ ] Switch provider configuration to Elasticsearch
- [ ] Initialize Elasticsearch indices
- [ ] Reindex data from database
- [ ] Validate data consistency
- [ ] Compare search results
- [ ] Benchmark performance
- [ ] Test autocomplete functionality
- [ ] Verify health checks

### Post-Migration

- [ ] Monitor cluster health
- [ ] Monitor search performance
- [ ] Monitor error rates
- [ ] Set up alerts
- [ ] Clean up old indices
- [ ] Update documentation
- [ ] Train team on Elasticsearch
- [ ] Decommission PostgreSQL search (if applicable)

## Common Migration Issues

### Issue: Data Inconsistency

**Problem:** Elasticsearch has different document count than PostgreSQL

**Solutions:**
1. Reindex from database
2. Check for indexing errors
3. Verify mapping configuration
4. Check for duplicate documents

### Issue: Search Result Differences

**Problem:** Search results differ between providers

**Solutions:**
1. Check analyzer configuration
2. Verify field mappings
3. Compare query construction
4. Check filter implementation

### Issue: Performance Degradation

**Problem:** Elasticsearch is slower than PostgreSQL

**Solutions:**
1. Check cluster resources
2. Optimize index settings
3. Add more nodes
4. Tune query configuration
5. Check shard allocation

### Issue: Memory Issues

**Problem:** Elasticsearch using too much memory

**Solutions:**
1. Increase heap size
2. Reduce bulk operation size
3. Close unused indices
4. Clear field data cache
5. Reduce replica count

## Best Practices

1. **Test in staging** before production migration
2. **Backup data** before migration
3. **Monitor closely** during migration
4. **Have rollback plan** ready
5. **Validate thoroughly** after migration
6. **Gradual rollout** for large datasets
7. **Document process** for future migrations
8. **Train team** on new provider
9. **Monitor performance** post-migration
10. **Clean up** old resources after validation
