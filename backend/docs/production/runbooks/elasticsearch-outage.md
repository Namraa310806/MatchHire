# Elasticsearch Outage Runbook

## Severity
High

## Symptoms
- Search functionality unavailable
- Slow search queries
- Elasticsearch connection errors
- Indexing failures

## Immediate Actions

### 1. Verify Elasticsearch Status
```bash
# Check Elasticsearch health
curl http://localhost:9200/_cluster/health

# Check node status
curl http://localhost:9200/_cat/nodes?v

# Check index status
curl http://localhost:9200/_cat/indices?v
```

### 2. Check Application Logs
```bash
# Check for Elasticsearch errors
docker logs matchhire-backend | grep -i "elasticsearch\|search"

# Check indexing logs
docker logs matchhire-celery-worker | grep -i "index"
```

### 3. Restart Elasticsearch (if needed)
```bash
# Restart Elasticsearch container
docker-compose restart elasticsearch

# Or restart entire stack
docker-compose restart
```

### 4. Enable Fallback (if configured)
```bash
# Elasticsearch has circuit breaker in resilience.py
# Check if fallback is active
docker logs matchhire-backend | grep -i "circuit breaker\|fallback"
```

## Root Cause Analysis

### Check Elasticsearch Metrics
- Cluster health (red/yellow/green)
- JVM heap usage
- Disk space
- Index size
- Query performance

### Common Causes
1. **JVM heap exhaustion** - Increase heap or optimize queries
2. **Disk full** - Clean up old indices or expand storage
3. **High query load** - Optimize queries or scale nodes
4. **Index corruption** - Rebuild index from backup

## Resolution Steps

### For JVM Heap Exhaustion
```bash
# Check heap usage
curl http://localhost:9200/_nodes/stats/jvm?pretty

# Increase heap in docker-compose.production.yml
# - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
```

### For Disk Full
```bash
# Check disk usage
docker exec matchhire-elasticsearch df -h

# Delete old indices
curl -X DELETE "localhost:9200/old-index-*"

# Or expand storage volume
```

### For High Query Load
```bash
# Optimize queries
# Add query caching
# Scale Elasticsearch nodes
# Use query DSL optimizations
```

### For Index Corruption
```bash
# Restore from snapshot
curl -X POST "localhost:9200/_snapshot/backups/snapshot_1/_restore"

# Or rebuild index from database
python manage.py rebuild_search_index
```

## Prevention
- Monitor cluster health
- Set up heap usage alerts
- Implement index lifecycle management
- Use query caching
- Regular index optimization
- Set up snapshots
- Monitor query performance

## Escalation
- If unresolved in 15 minutes: Escalate to platform team
- If data loss: Restore from snapshot
- If persistent issues: Review search architecture
