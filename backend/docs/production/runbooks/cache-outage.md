# Cache Outage Runbook

## Severity
High

## Symptoms
- Slow API responses
- Increased database load
- Cache connection errors
- High cache memory usage

## Immediate Actions

### 1. Verify Cache Status
```bash
# Check Redis status
docker exec matchhire-redis redis-cli ping

# Check Redis memory usage
docker exec matchhire-redis redis-cli INFO memory

# Check Redis connections
docker exec matchhire-redis redis-cli INFO clients
```

### 2. Check Application Cache Configuration
```bash
# Check cache settings in environment
docker exec matchhire-backend env | grep -i cache

# Check cache hit rate (if metrics enabled)
docker exec matchhire-redis redis-cli INFO stats
```

### 3. Restart Cache (if needed)
```bash
# Restart Redis container
docker-compose restart redis

# Clear cache (use with caution)
docker exec matchhire-redis redis-cli FLUSHALL
```

### 4. Verify Application Connectivity
```bash
# Test cache from application
docker exec matchhire-backend python -c "from django.core.cache import cache; cache.set('test', 'value', 10); print(cache.get('test'))"
```

## Root Cause Analysis

### Check Cache Metrics
- Memory usage approaching maxmemory
- High eviction rate
- Connection count near limit
- Slow operations

### Common Causes
1. **Memory exhaustion** - Cache evicting too frequently
2. **Connection pool exhaustion** - Too many connections
3. **Cache stampede** - Many requests for same uncached key
4. **Network issues** - Connectivity problems

## Resolution Steps

### For Memory Exhaustion
```bash
# Check current memory policy
docker exec matchhire-redis redis-cli CONFIG GET maxmemory-policy

# Increase maxmemory in docker-compose.production.yml
# command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
```

### For Connection Pool Exhaustion
```bash
# Increase maxclients in Redis configuration
# Or scale application to reduce connection count
docker-compose up -d --scale backend=2
```

### For Cache Stampede
```bash
# Enable cache warming
# Implement distributed locks (already in distributed_cache.py)
# Use adaptive TTL (already in caching.py)
```

## Prevention
- Monitor cache memory usage
- Set up alerts for eviction rate
- Implement cache warming
- Use tiered caching (L1/L2)
- Set appropriate TTL values
- Monitor cache hit/miss ratio

## Escalation
- If unresolved in 10 minutes: Escalate to platform team
- If data loss suspected: Check cache persistence settings
- If persistent issues: Review caching strategy
