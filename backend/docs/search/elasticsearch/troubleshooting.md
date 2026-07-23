# Elasticsearch Troubleshooting Guide

## Overview

This guide covers common issues and solutions when using the Elasticsearch provider with MatchHire.

## Connection Issues

### Connection Refused

**Problem:**
```
ConnectionRefusedError: [Errno 61] Connection refused
```

**Solutions:**

1. Check if Elasticsearch is running:
```bash
curl http://localhost:9200
```

2. Start Elasticsearch:
```bash
# Docker
docker start elasticsearch

# Systemd
sudo systemctl start elasticsearch

# Service
sudo serviceelasticsearch start
```

3. Verify host and port configuration:
```python
SEARCH_CONFIG = {
    "elasticsearch": {
        "hosts": ["http://localhost:9200"],  # Verify this is correct
    }
}
```

4. Check firewall rules:
```bash
# Allow port 9200
sudo ufw allow 9200
```

### Timeout Errors

**Problem:**
```
ConnectionTimeout: Connection timed out
```

**Solutions:**

1. Increase timeout:
```python
SEARCH_CONFIG = {
    "elasticsearch": {
        "request_timeout": 60,  # Increase from default 30
    }
}
```

2. Check cluster health:
```python
from apps.search.registry import get_registry

registry = get_registry()
provider = registry.get_provider("elasticsearch")
health = provider.health()
print(f"Cluster status: {health.details['status']}")
```

3. Verify network connectivity:
```bash
ping elasticsearch-host
telnet elasticsearch-host 9200
```

4. Check cluster load:
```bash
curl http://localhost:9200/_cluster/health?pretty
```

### Authentication Failed

**Problem:**
```
AuthenticationException: Authentication failed
```

**Solutions:**

1. Verify credentials:
```python
SEARCH_CONFIG = {
    "elasticsearch": {
        "username": "elastic",
        "password": "changeme",  # Verify this is correct
    }
}
```

2. Check user permissions:
```bash
curl -u elastic:changeme http://localhost:9200/_cluster/health
```

3. Use API key instead:
```python
SEARCH_CONFIG = {
    "elasticsearch": {
        "api_key": "base64_encoded_api_key",
    }
}
```

4. Reset password:
```bash
/usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic
```

## SSL/TLS Issues

### SSL Certificate Verification Failed

**Problem:**
```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**Solutions:**

1. For development only, disable verification:
```python
SEARCH_CONFIG = {
    "elasticsearch": {
        "verify_certs": False,  # Only for development
    }
}
```

2. Provide correct CA certificate:
```python
SEARCH_CONFIG = {
    "elasticsearch": {
        "verify_certs": True,
        "ca_certs": "/path/to/ca.crt",
    }
}
```

3. Update system certificates:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ca-certificates

# CentOS/RHEL
sudo yum update ca-certificates
```

### Self-Signed Certificate

**Problem:**
```
SSLError: unable to get local issuer certificate
```

**Solutions:**

1. Add certificate to trusted store:
```bash
sudo cp self-signed.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

2. Disable verification for development:
```python
SEARCH_CONFIG = {
    "elasticsearch": {
        "verify_certs": False,
        "ssl_show_warn": False,
    }
}
```

## Index Issues

### Index Not Found

**Problem:**
```
NotFoundError: IndexNotFoundException[no such index [matchhire_job]]
```

**Solutions:**

1. Check if index exists:
```python
from apps.search.registry import get_registry

registry = get_registry()
provider = registry.get_provider("elasticsearch")

if not provider.index_lifecycle.index_exists("job"):
    print("Index does not exist")
```

2. Create index manually:
```python
from apps.search.providers.elasticsearch.mappings import Mappings
from apps.search.providers.elasticsearch.analyzers import Analyzers

mapping = Mappings.get_mapping("job")
settings = Analyzers.get_index_settings()
provider.index_lifecycle.create_index("job", mapping, settings)
```

3. List all indices:
```python
indices = provider.index_lifecycle.list_indices()
print(f"Available indices: {indices}")
```

### Mapping Error

**Problem:**
```
MapperParsingException: mapping [field] not found
```

**Solutions:**

1. Check current mapping:
```python
mapping = provider.index_lifecycle.get_index_mapping("job")
print(mapping)
```

2. Recreate index with correct mapping:
```python
provider.index_lifecycle.recreate_index("job", mapping, settings)
```

3. Use versioned index for mapping changes:
```python
new_index = provider.create_versioned_index("job", switch_alias=True)
```

### Index Red

**Problem:**
```
Cluster status is red
```

**Solutions:**

1. Check cluster health:
```python
health = provider.health()
print(f"Status: {health.details['status']}")
print(f"Unassigned shards: {health.details['unassigned_shards']}")
```

2. Check shard allocation:
```bash
curl http://localhost:9200/_cat/shards?v&h=index,shard,prirep,state,node
```

3. Retry allocation:
```bash
curl -X POST http://localhost:9200/_cluster/reroute?retry_failed=true
```

4. Check disk space:
```bash
curl http://localhost:9200/_cat/allocation?v
```

## Search Issues

### No Results Returned

**Problem:**
Search returns no results when expected

**Solutions:**

1. Check if documents are indexed:
```python
stats = provider.statistics(entity_type="job")
print(f"Document count: {stats.document_count}")
```

2. Refresh index:
```python
provider.refresh(entity_type="job")
```

3. Check query syntax:
```python
# Try a simple match_all query
results = provider.search(entity_type="job", query="")
print(f"Total documents: {results['total']}")
```

4. Check field mapping:
```python
mapping = provider.index_lifecycle.get_index_mapping("job")
print(mapping)
```

### Slow Queries

**Problem:**
Search queries are slow

**Solutions:**

1. Check query profile:
```python
# Add profile to query
es_query = {
    "query": {...},
    "profile": True
}
response = provider.client.search(index=index_name, body=es_query)
print(response.get("profile"))
```

2. Check cluster health:
```python
health = provider.health()
print(f"Cluster status: {health.details['status']}")
```

3. Optimize query:
- Use filters instead of query clauses
- Limit returned fields
- Use appropriate pagination
- Add missing indexes

4. Check index settings:
```python
settings = provider.index_lifecycle.get_index_settings("job")
print(settings)
```

### Autocomplete Not Working

**Problem:**
Autocomplete returns no suggestions

**Solutions:**

1. Check edge n-gram field exists:
```python
mapping = provider.index_lifecycle.get_index_mapping("job")
print(mapping["properties"]["title"]["fields"])
```

2. Check analyzer configuration:
```python
from apps.search.providers.elasticsearch.analyzers import Analyzers
settings = Analyzers.get_analysis_settings()
print(settings["analysis"]["analyzer"]["edge_ngram_analyzer"])
```

3. Reindex data with correct mapping:
```python
new_index = provider.create_versioned_index("job", switch_alias=True)
# Reindex data here
```

## Bulk Operations Issues

### Bulk Indexing Failed

**Problem:**
Bulk indexing returns errors

**Solutions:**

1. Check error details:
```python
result = provider.bulk_index(entity_type="job", documents=documents)
for error in result.errors:
    print(f"Error: {error}")
```

2. Validate document structure:
```python
for doc in documents:
    if "id" not in doc:
        print(f"Missing id in document: {doc}")
```

3. Reduce chunk size:
```python
provider.DEFAULT_CHUNK_SIZE = 100  # Reduce from 500
```

4. Check index mapping:
```python
mapping = provider.index_lifecycle.get_index_mapping("job")
print(mapping)
```

### Partial Bulk Failures

**Problem:**
Some documents fail to index

**Solutions:**

1. Retry failed documents:
```python
failed_ids = [error.get("document_id") for error in result.errors]
failed_docs = [doc for doc in documents if doc["id"] in failed_ids]
retry_result = provider.bulk_index(entity_type="job", documents=failed_docs)
```

2. Check document size:
```python
for doc in documents:
    size = len(str(doc))
    if size > 10485760:  # 10MB
        print(f"Document too large: {doc['id']}")
```

3. Check cluster health:
```python
health = provider.health()
if not health.healthy:
    print("Cluster is unhealthy, retry later")
```

## Memory Issues

### Out of Memory

**Problem:**
```
OutOfMemoryError: Java heap space
```

**Solutions:**

1. Increase heap size:
```bash
# Docker
ES_JAVA_OPTS=-Xms4g -Xmx4g

# Config file
# elasticsearch.yml
# Set in environment
```

2. Reduce bulk operation size:
```python
provider.DEFAULT_CHUNK_SIZE = 100
```

3. Check JVM heap usage:
```bash
curl http://localhost:9200/_nodes/stats/jvm?pretty
```

4. Close unused indices:
```python
provider.index_lifecycle.close_index("job")
```

### High Memory Usage

**Problem:**
Elasticsearch using too much memory

**Solutions:**

1. Check field data cache:
```bash
curl http://localhost:9200/_nodes/stats/indices/fielddata?pretty
```

2. Clear field data cache:
```python
provider.client.indices.clear_cache(index="matchhire_*", body={"fielddata": True})
```

3. Reduce number of shards:
```python
SEARCH_CONFIG = {
    "elasticsearch": {
        "number_of_shards": 3,  # Reduce from 5
    }
}
```

4. Monitor heap usage:
```bash
curl http://localhost:9200/_cat/nodes?v&h=name,heap.current,heap.percent
```

## Disk Space Issues

### Disk Full

**Problem:**
```
DiskQuotaExceededException: disk quota exceeded
```

**Solutions:**

1. Check disk usage:
```bash
curl http://localhost:9200/_cat/allocation?v
```

2. Cleanup old indices:
```python
provider.cleanup_old_indices(entity_type="job", keep_versions=2)
```

3. Delete old snapshots:
```python
snapshots = provider.client.snapshot.get(repository="backup")
for snapshot in snapshots["snapshots"]:
    provider.client.snapshot.delete(repository="backup", snapshot=snapshot["snapshot"])
```

4. Increase disk space or add nodes

### High Disk Usage

**Problem:**
Disk usage growing rapidly

**Solutions:**

1. Check index sizes:
```python
for entity_type in ["job", "candidate", "resume"]:
    stats = provider.statistics(entity_type=entity_type)
    size_mb = stats.index_size_bytes / (1024 * 1024)
    print(f"{entity_type}: {size_mb:.2f} MB")
```

2. Force merge indices:
```python
provider.client.indices.forcemerge(index="matchhire_*", max_num_segments=1)
```

3. Adjust refresh interval:
```python
SEARCH_CONFIG = {
    "elasticsearch": {
        "refresh_interval": "30s",  # Slower refresh
    }
}
```

4. Implement index lifecycle management (ILM)

## Cluster Issues

### Cluster Yellow

**Problem:**
Cluster status is yellow

**Solutions:**

1. Check unassigned shards:
```bash
curl http://localhost:9200/_cat/shards?v&h=index,shard,prirep,state,node
```

2. Check replica settings:
```python
settings = provider.index_lifecycle.get_index_settings("job")
print(settings)
```

3. Reduce replica count:
```python
provider.client.indices.put_settings(
    index="matchhire_*",
    body={"index": {"number_of_replicas": 0}}
)
```

4. Add more nodes to cluster

### Split Brain

**Problem:**
Multiple master nodes elected

**Solutions:**

1. Check master nodes:
```bash
curl http://localhost:9200/_cat/master?v
```

2. Configure minimum master nodes:
```yaml
# elasticsearch.yml
discovery.zen.minimum_master_nodes: 2
```

3. Check network connectivity between nodes

4. Restart cluster nodes

## Performance Issues

### Slow Indexing

**Problem:**
Indexing is slow

**Solutions:**

1. Disable refresh during bulk indexing:
```python
provider.client.indices.put_settings(
    index="matchhire_job",
    body={"index": {"refresh_interval": "-1"}}
)

# Perform bulk indexing

# Re-enable refresh
provider.client.indices.put_settings(
    index="matchhire_job",
    body={"index": {"refresh_interval": "1s"}}
)
```

2. Increase bulk size:
```python
provider.DEFAULT_CHUNK_SIZE = 1000
```

3. Use async indexing with Celery

4. Check cluster resources

### High CPU Usage

**Problem:**
Elasticsearch using high CPU

**Solutions:**

1. Check hot threads:
```bash
curl http://localhost:9200/_nodes/hot_threads
```

2. Check query performance:
```python
# Profile slow queries
es_query = {"query": {...}, "profile": True}
response = provider.client.search(index=index_name, body=es_query)
```

3. Optimize complex queries
4. Add more nodes to cluster

## Debugging Tools

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
es_logger = logging.getLogger('elasticsearch')
es_logger.setLevel(logging.DEBUG)
```

### Query Validation

```python
# Validate query
from elasticsearch import RequestError

try:
    response = provider.client.search(
        index="matchhire_job",
        body={"query": {...}},
        validate_only=True
    )
except RequestError as e:
    print(f"Invalid query: {e}")
```

### Index Analysis

```python
# Analyze text
response = provider.client.indices.analyze(
    index="matchhire_job",
    body={
        "analyzer": "standard",
        "text": "software engineer"
    }
)
print(response)
```

### Cluster State

```python
# Get cluster state
state = provider.client.cluster.state()
print(state)
```

## Getting Help

### Check Logs

```bash
# Docker logs
docker logs elasticsearch

# System logs
sudo journalctl -u elasticsearch -f

# Application logs
tail -f /var/log/matchhire/app.log
```

### Enable Slow Logs

```python
# Enable slow query logging
provider.client.indices.put_settings(
    index="matchhire_job",
    body={
        "index.search.slowlog.threshold.query.warn": "10s",
        "index.search.slowlog.threshold.query.info": "5s"
    }
)
```

### Export Diagnostic Information

```python
# Export cluster info
info = provider.cluster_manager.get_cluster_info()
health = provider.cluster_manager.get_cluster_health()
nodes = provider.cluster_manager.get_nodes_info()

print(f"Cluster: {info.name}")
print(f"Version: {info.version}")
print(f"Status: {health.status}")
print(f"Nodes: {len(nodes)}")
```

## Common Mistakes

1. **Not refreshing index after bulk operations**
   - Solution: Call `provider.refresh()` after bulk operations

2. **Using wrong field names in queries**
   - Solution: Check mapping with `provider.index_lifecycle.get_index_mapping()`

3. **Not handling partial bulk failures**
   - Solution: Check `result.errors` and retry failed documents

4. **Using too many shards**
   - Solution: Use appropriate shard count based on data size

5. **Not monitoring cluster health**
   - Solution: Set up health checks and alerts

6. **Forgetting to configure SSL in production**
   - Solution: Always enable SSL/TLS in production

7. **Using default heap size**
   - Solution: Set heap to 50% of available RAM

8. **Not implementing backup strategy**
   - Solution: Set up snapshot repository and regular backups
