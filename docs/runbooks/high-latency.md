# High Latency Runbook

## Alert Condition
P95 request duration > 2 seconds for 5 minutes

## Impact
Users are experiencing slow response times, which may lead to:
- Poor user experience
- Abandoned applications
- Reduced platform engagement
- Potential timeout errors

## Initial Assessment (5 minutes)

### 1. Verify Latency Spike
- Check Grafana dashboard for latency spike
- Confirm if latency is sustained or transient
- Check if specific endpoints are affected

### 2. Check Traffic Patterns
```bash
# Check request rate
docker compose logs web | grep "GET\|POST" | tail -100

# Check for traffic spikes
# Review Grafana request rate graph
```

### 3. Check Resource Usage
```bash
# Check container resources
docker stats

# Check CPU usage
top

# Check memory usage
free -m

# Check disk I/O
iostat
```

## Troubleshooting Steps

### Step 1: Check Database Performance
```bash
# Check slow queries
docker compose exec db psql -U matchhire -d matchhire -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state != 'idle' AND now() - pg_stat_activity.query_start > interval '5 seconds' ORDER BY duration DESC;"

# Check database connections
docker compose exec db psql -U matchhire -d matchhire -c "SELECT count(*) FROM pg_stat_activity;"

# Check database size
docker compose exec db psql -U matchhire -d matchhire -c "SELECT pg_size_pretty(pg_database_size('matchhire'));"
```

### Step 2: Check Cache Performance
```bash
# Check Redis stats
docker compose exec redis redis-cli INFO stats

# Check cache hit rate
# Review Grafana cache metrics
```

### Step 3: Check Application Logs
```bash
# Check for slow request logs
docker compose logs web | grep "duration" | tail -50

# Check for N+1 query warnings
docker compose logs web | grep "N+1"
```

### Step 4: Check External Services
- Verify third-party API response times
- Check for rate limiting
- Verify network latency

## Resolution Strategies

### Strategy 1: Scale Web Service
```bash
# Scale web service horizontally
docker compose up -d --scale web=3

# Monitor if latency improves
```

### Strategy 2: Optimize Database Queries
```bash
# Add missing indexes
docker compose exec db psql -U matchhire -d matchhire -c "CREATE INDEX CONCURRENTLY idx_name ON table(column);"

# Update query statistics
docker compose exec db psql -U matchhire -d matchhire -c "ANALYZE;"

# Vacuum database
docker compose exec db psql -U matchhire -d matchhire -c "VACUUM ANALYZE;"
```

### Strategy 3: Increase Cache
```bash
# Check Redis memory usage
docker compose exec redis redis-cli INFO memory

# If cache hit rate is low, consider:
# - Increasing cache TTL
# - Caching more data
# - Using a larger Redis instance
```

### Strategy 4: Optimize Application Code
```bash
# Review recent code changes
git log --oneline -10

# Check for inefficient queries
# Review Django Debug Toolbar output (in development)
```

### Strategy 5: Rate Limiting
```bash
# If traffic spike is the cause, implement rate limiting
# Already configured in Django settings
# Adjust throttle rates if needed
```

## Performance Optimization Checklist

### Database
- [ ] Add missing indexes
- [ ] Optimize slow queries
- [ ] Update statistics
- [ ] Vacuum and analyze
- [ ] Consider read replicas

### Cache
- [ ] Increase cache hit rate
- [ ] Cache frequently accessed data
- [ ] Use cache for expensive operations
- [ ] Implement cache warming

### Application
- [ ] Optimize N+1 queries
- [ ] Use select_related/prefetch_related
- [ ] Implement pagination
- [ ] Optimize serialization
- [ ] Use async operations where appropriate

### Infrastructure
- [ ] Scale web service
- [ ] Scale database
- [ ] Use CDN for static assets
- [ ] Optimize network configuration

## Escalation Criteria

Escalate to Engineering Lead if:
- Latency persists for more than 30 minutes
- Database optimization doesn't help
- Code changes are required

Escalate to CTO if:
- Latency persists for more than 1 hour
- Infrastructure scaling is required
- Architecture changes are needed

## Post-Incident Actions

1. **Performance Analysis**
   - Identify root cause
   - Document slow queries
   - Document bottlenecks

2. **Optimization**
   - Implement fixes
   - Add monitoring
   - Create performance tests

3. **Prevention**
   - Add performance regression tests
   - Implement continuous performance monitoring
   - Document performance guidelines

## Related Runbooks
- [High Error Rate](./high-error-rate.md)
- [Database Outage](./database-outage.md)
- [High CPU Usage](./high-cpu-usage.md)

## Related Metrics
- `http_request_duration_seconds`
- `db_query_duration_seconds`
- `cache_hit_rate`
- `db_connections_active`
