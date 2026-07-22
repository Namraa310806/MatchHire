# High Memory Usage Runbook

## Alert Condition
Container memory usage > 80% for 10 minutes

## Impact
Potential OOM kills, service instability, and possible service unavailability.

## Initial Assessment (5 minutes)

### 1. Verify Memory Usage
```bash
# Check container memory usage
docker stats

# Check system memory usage
free -m

# Check memory limits
docker inspect matchhire-web-1 | grep Memory
```

### 2. Identify Affected Service
```bash
# Check which container is using high memory
docker stats --no-stream

# Check process-level memory usage
docker compose exec web ps aux --sort=-%mem
```

### 3. Check for Memory Leaks
```bash
# Check for memory growth over time
# Review Grafana memory usage graph

# Check for long-running processes
docker compose exec web ps aux | grep -v defunct
```

## Troubleshooting Steps

### Step 1: Check Process List
```bash
# Check processes in container
docker compose exec web ps aux --sort=-%mem

# Check for memory-intensive processes
docker compose exec web top -b -n 1 -o %MEM
```

### Step 2: Check Application Logs
```bash
# Check for memory warnings
docker compose logs web | grep -i "memory\|oom"

# Check for large object creation
docker compose logs web | grep -i "allocation\|buffer"
```

### Step 3: Check Database Connections
```bash
# Check connection count
docker compose exec db psql -U matchhire -d matchhire -c "SELECT count(*) FROM pg_stat_activity;"

# Check for connection leaks
docker compose exec db psql -U matchhire -d matchhire -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC;"
```

### Step 4: Check Cache Usage
```bash
# Check Redis memory usage
docker compose exec redis redis-cli INFO memory

# Check cache size
docker compose exec redis redis-cli DBSIZE
```

## Resolution Strategies

### Strategy 1: Restart Service
```bash
# Restart web service
docker compose restart web

# Restart worker service
docker compose restart worker

# Monitor memory usage after restart
docker stats
```

### Strategy 2: Scale Service Horizontally
```bash
# Scale web service
docker compose up -d --scale web=3

# Scale worker service
docker compose up -d --scale worker=2
```

### Strategy 3: Optimize Database Connections
```bash
# Reduce connection pool size
# Update Django settings: CONN_MAX_AGE

# Kill idle connections
docker compose exec db psql -U matchhire -d matchhire -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND now() - pg_stat_activity.query_start > interval '10 minutes';"
```

### Strategy 4: Clear Cache
```bash
# Flush Redis cache
docker compose exec redis redis-cli FLUSHALL

# Or flush specific database
docker compose exec redis redis-cli FLUSHDB
```

### Strategy 5: Increase Memory Limits
```bash
# Update docker-compose.yml with increased memory limits
# Then restart
docker compose up -d
```

## Memory Optimization Checklist

### Database
- [ ] Reduce connection pool size
- [ ] Optimize query memory usage
- [ ] Use connection pooling
- [ ] Close idle connections

### Application
- [ ] Fix memory leaks
- [ ] Optimize data structures
- [ ] Use generators instead of lists
- [ ] Implement pagination

### Cache
- [ ] Set appropriate cache size limits
- [ ] Implement cache eviction policies
- [ ] Monitor cache memory usage
- [ ] Use memory-efficient serialization

### Infrastructure
- [ ] Set appropriate memory limits
- [ ] Implement memory monitoring
- [ ] Use memory profiling
- [ ] Implement OOM prevention

## Escalation Criteria

Escalate to Engineering Lead if:
- Memory usage persists despite scaling
- Memory leaks are suspected
- Code optimization is required

Escalate to CTO if:
- Memory usage persists for more than 1 hour
- Service is unstable
- Architecture changes are needed

## Prevention Measures

### Monitoring
- Monitor memory usage
- Monitor memory growth rate
- Monitor OOM kills
- Monitor connection count

### Capacity Planning
- Set appropriate memory limits
- Implement memory-based auto-scaling
- Use load testing
- Plan for peak memory usage

### Optimization
- Regular memory profiling
- Code review for memory efficiency
- Database connection optimization
- Cache optimization

## Post-Incident Actions

1. **Memory Analysis**
   - Identify memory-intensive operations
   - Document memory leaks
   - Profile application memory usage

2. **Optimization**
   - Implement fixes
   - Add monitoring
   - Create memory tests

3. **Prevention**
   - Add memory regression tests
   - Implement continuous memory monitoring
   - Document memory guidelines

## Related Runbooks
- [High CPU Usage](./high-cpu-usage.md)
- [Database Outage](./database-outage.md)
- [Redis Outage](./redis-outage.md)

## Related Metrics
- `container_memory_usage_bytes`
- `container_spec_memory_limit_bytes`
- `db_connections_active`
- `cache_hits_total`
