# Elasticsearch Operations

## Overview

This guide covers operational tasks for the Elasticsearch provider including index management, cluster operations, backup and recovery, and performance tuning.

## Index Operations

### Creating Indices

Indices are automatically created during provider initialization. To manually create an index:

```python
from apps.search.registry import get_registry

registry = get_registry()
provider = registry.get_provider("elasticsearch")

# Create a specific index
provider.index_lifecycle.create_index(
    entity_type="job",
    mapping=provider.index_lifecycle.mappings.get_job_mapping(),
    settings=provider.index_lifecycle.analyzers.get_index_settings()
)
```

### Deleting Indices

```python
# Delete a specific index
provider.index_lifecycle.delete_index(entity_type="job")

# Delete a versioned index
provider.index_lifecycle.delete_index(entity_type="job", version=1)
```

**Warning:** Deleting an index is irreversible. Always backup before deletion.

### Recreating Indices

```python
# Recreate an index (delete and create)
provider.index_lifecycle.recreate_index(
    entity_type="job",
    mapping=mapping,
    settings=settings
)
```

### Refreshing Indices

Make changes visible to search:

```python
# Refresh a specific index
provider.refresh(entity_type="job")

# Refresh all indices
provider.refresh()
```

### Closing and Opening Indices

Close an index to free up resources:

```python
# Close an index
provider.index_lifecycle.close_index(entity_type="job")

# Open an index
provider.index_lifecycle.open_index(entity_type="job")
```

**Use Cases:**
- Temporarily disable search for an entity type
- Free up memory during maintenance
- Archive old data

## Alias Operations

### Creating Aliases

```python
# Create an alias
provider.index_lifecycle.create_alias(
    entity_type="job",
    index_name="matchhire_job_v1"
)
```

### Switching Aliases

Zero-downtime index switching:

```python
# Switch alias from old index to new index
provider.index_lifecycle.switch_alias(
    entity_type="job",
    old_index="matchhire_job_v1",
    new_index="matchhire_job_v2"
)
```

### Deleting Aliases

```python
# Delete an alias
provider.index_lifecycle.delete_alias(entity_type="job")
```

### Listing Aliases

```python
# Get aliases for an entity type
aliases = provider.index_lifecycle.get_aliases(entity_type="job")
```

## Versioned Index Operations

### Creating Versioned Indices

Create a new versioned index and switch the alias:

```python
# Create versioned index and switch alias
new_index = provider.create_versioned_index(
    entity_type="job",
    switch_alias=True
)

print(f"Created new index: {new_index}")
```

### Cleaning Up Old Versions

Remove old versioned indices:

```python
# Keep only the 2 most recent versions
deleted_count = provider.cleanup_old_indices(
    entity_type="job",
    keep_versions=2
)

print(f"Deleted {deleted_count} old indices")
```

### Listing Versioned Indices

```python
# List all indices for an entity type
indices = provider.index_lifecycle.list_indices(entity_type="job")

for index in indices:
    print(index)
```

## Cluster Operations

### Checking Cluster Health

```python
# Get cluster health
health = provider.health()

if health.healthy:
    print(f"Cluster is {health.details['status']}")
else:
    print(f"Cluster is unhealthy: {health.error}")
```

### Getting Detailed Cluster Health

```python
# Get detailed cluster health
cluster_health = provider.get_cluster_health()

print(f"Status: {cluster_health['status']}")
print(f"Nodes: {cluster_health['number_of_nodes']}")
print(f"Shards: {cluster_health['active_shards']}")
```

### Getting Node Information

```python
# Get node information
nodes = provider.get_nodes_info()

for node in nodes:
    print(f"Node: {node['name']}")
    print(f"Roles: {node['roles']}")
    print(f"Version: {node['version']}")
```

### Waiting for Cluster Health

Wait for cluster to reach desired health status:

```python
# Wait for green status (timeout 30 seconds)
from apps.search.providers.elasticsearch.cluster import ClusterManager

cluster_manager = provider.cluster_manager
success = cluster_manager.wait_for_cluster_health(
    status="green",
    timeout=30,
    interval=1
)

if success:
    print("Cluster is green")
else:
    print("Cluster did not reach green status")
```

### Getting Index Health

```python
# Get health for a specific index
index_health = provider.get_index_health(entity_type="job")

print(index_health)
```

### Getting Index Statistics

```python
# Get statistics for a specific index
stats = provider.statistics(entity_type="job")

print(f"Document count: {stats.document_count}")
print(f"Index size: {stats.index_size_bytes} bytes")

# Get statistics for all indices
all_stats = provider.statistics()
```

## Bulk Operations

### Bulk Indexing

```python
# Prepare documents
documents = [
    {"id": "1", "title": "Software Engineer", ...},
    {"id": "2", "title": "Data Scientist", ...},
    # ... more documents
]

# Bulk index
result = provider.bulk_index(entity_type="job", documents=documents)

print(f"Indexed: {result.indexed_count}")
print(f"Failed: {result.failed_count}")

if result.errors:
    print("Errors:")
    for error in result.errors:
        print(f"  - {error}")
```

### Bulk Deletion

```python
# Delete multiple documents
document_ids = ["1", "2", "3", "4", "5"]

result = provider.bulk_delete(entity_type="job", document_ids=document_ids)

print(f"Deleted: {result.deleted_count}")
print(f"Failed: {result.failed_count}")
```

### Bulk Indexing with Retry

```python
# Index with automatic retry on failure
result = provider.bulk_index(entity_type="job", documents=documents)

# Handle partial failures
if not result.success:
    # Retry failed documents
    failed_ids = [error.get("document_id") for error in result.errors]
    failed_docs = [doc for doc in documents if doc["id"] in failed_ids]

    retry_result = provider.bulk_index(entity_type="job", documents=failed_docs)
```

## Reindexing

### Reindexing to a New Index

```python
# Create new versioned index
new_index = provider.create_versioned_index(entity_type="job", switch_alias=False)

# Reindex data (using Elasticsearch reindex API)
from elasticsearch.helpers import reindex

reindex(
    client=provider.client,
    source_index="matchhire_job_alias",
    target_index=new_index,
    query={"match_all": {}}
)

# Switch alias
provider.index_lifecycle.switch_alias(
    entity_type="job",
    old_index="matchhire_job_alias",
    new_index=new_index
)

# Cleanup old indices
provider.cleanup_old_indices(entity_type="job", keep_versions=2)
```

## Backup and Recovery

### Snapshot Repository

Configure a snapshot repository:

```python
# Create snapshot repository
provider.client.snapshot.create_repository(
    repository="matchhire_backup",
    body={
        "type": "fs",
        "settings": {
            "location": "/backup/elasticsearch"
        }
    }
)
```

### Creating Snapshots

```python
# Create snapshot of all indices
provider.client.snapshot.create(
    repository="matchhire_backup",
    snapshot="snapshot_1",
    body={
        "indices": "matchhire_*",
        "include_global_state": False
    }
)
```

### Restoring from Snapshot

```python
# Restore from snapshot
provider.client.snapshot.restore(
    repository="matchhire_backup",
    snapshot="snapshot_1",
    body={
        "indices": "matchhire_job",
        "include_global_state": False
    }
)
```

### Listing Snapshots

```python
# List snapshots
snapshots = provider.client.snapshot.get(repository="matchhire_backup")

for snapshot in snapshots["snapshots"]:
    print(f"Snapshot: {snapshot['snapshot']}")
    print(f"State: {snapshot['state']}")
    print(f"Indices: {snapshot['indices']}")
```

## Performance Tuning

### Optimizing Index Settings

```python
# Update index settings for performance
provider.client.indices.put_settings(
    index="matchhire_job",
    body={
        "index": {
            "refresh_interval": "30s",  # Slower refresh for bulk indexing
            "translog.durability": "async"  # Async translog for speed
        }
    }
)
```

### Force Merge

Reduce segment count for better performance:

```python
# Force merge indices
provider.client.indices.forcemerge(
    index="matchhire_*",
    max_num_segments=1
)
```

**Warning:** Force merge is resource-intensive. Run during maintenance windows.

### Clear Cache

Clear field data cache:

```python
# Clear cache
provider.client.indices.clear_cache(
    index="matchhire_*",
    body={
        "fielddata": True,
        "fields": ["title", "company_name"]
    }
)
```

## Monitoring

### Monitoring Cluster Health

```python
# Continuous health monitoring
import time

while True:
    health = provider.health()
    print(f"Cluster status: {health.details['status']}")
    print(f"Active shards: {health.details['active_shards']}")
    print(f"Unassigned shards: {health.details['unassigned_shards']}")
    time.sleep(60)
```

### Monitoring Index Size

```python
# Monitor index sizes
for entity_type in ["job", "candidate", "resume"]:
    stats = provider.statistics(entity_type=entity_type)
    size_mb = stats.index_size_bytes / (1024 * 1024)
    print(f"{entity_type}: {size_mb:.2f} MB, {stats.document_count} documents")
```

### Monitoring Query Performance

```python
# Monitor query latency
import time

start = time.time()
results = provider.search(entity_type="job", query="software engineer")
latency = (time.time() - start) * 1000

print(f"Query latency: {latency:.2f} ms")
print(f"Results: {results['total']}")
```

## Maintenance Tasks

### Daily Tasks

- Check cluster health
- Monitor index sizes
- Review error logs
- Check disk space

### Weekly Tasks

- Review slow queries
- Check shard distribution
- Monitor JVM heap usage
- Review index statistics

### Monthly Tasks

- Cleanup old indices
- Review snapshot retention
- Analyze index patterns
- Update synonyms if needed

## Troubleshooting Operations

### Index Not Found

**Problem:** Index does not exist

**Solution:**
```python
# Check if index exists
if not provider.index_lifecycle.index_exists(entity_type="job"):
    # Create index
    provider.index_lifecycle.create_index(entity_type="job", mapping, settings)
```

### Alias Not Found

**Problem:** Alias does not exist

**Solution:**
```python
# Create alias
provider.index_lifecycle.create_alias(
    entity_type="job",
    index_name="matchhire_job_v1"
)
```

### Cluster Red

**Problem:** Cluster status is red

**Solution:**
1. Check unassigned shards
2. Check node health
3. Review cluster logs
4. Restart if necessary

### Slow Queries

**Problem:** Queries are slow

**Solution:**
1. Check cluster health
2. Review query complexity
3. Add missing indexes
4. Optimize index settings
5. Consider increasing resources

## Best Practices

1. **Use aliases** for zero-downtime deployments
2. **Version indices** for schema changes
3. **Monitor cluster health** regularly
4. **Backup regularly** using snapshots
5. **Optimize bulk operations** with appropriate chunk sizes
6. **Clean up old indices** to save disk space
7. **Use refresh intervals** appropriate for your workload
8. **Monitor disk space** to prevent out-of-space errors
9. **Test operations** in development first
10. **Document operational procedures** for your team
