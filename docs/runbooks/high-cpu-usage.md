# High CPU Usage Runbook

## Alert Condition
Container CPU usage > 80% for 10 minutes

## Impact
Performance degradation, potential service instability, and possible service unavailability.

## Initial Assessment (5 minutes)

### 1. Verify CPU Usage
```bash
# Check container CPU usage
docker stats

# Check system CPU usage
top

# Check CPU cores
nproc
```

### 2. Identify Affected Service
```bash
# Check which container is using high CPU
docker stats --no-stream

# Check process-level CPU usage
docker compose exec web top
```

### 3. Check Traffic Patterns
```bash
# Check request rate
# Review Grafana request rate graph

# Check for traffic spikes
docker compose logs web | grep "GET\|POST" | tail -100
```

## Troubleshooting Steps

### Step 1: Check Process List
```bash
# Check processes in container
docker compose exec web ps aux

# Check for runaway processes
docker compose exec web top -b -n 1
```

### Step 2: Check Application Logs
```bash
# Check for CPU-intensive operations
docker compose logs web | grep -i "matching\|parsing\|calculation"

# Check for loops or infinite processes
docker compose logs web | grep -i "loop\|while\|for"
```

### Step 3: Check Database Queries
```bash
# Check for expensive queries
docker compose exec db psql -U matchhire -d matchhire -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC LIMIT 10;"
```

### Step 4: Check Background Tasks
```bash
# Check Celery worker status
docker compose exec web python manage.py celery -A matchhire_backend inspect active

# Check for CPU-intensive tasks
docker compose logs worker | grep -i "matching\|parsing"
```

## Resolution Strategies

### Strategy 1: Scale Service Horizontally
```bash
# Scale web service
docker compose up -d --scale web=3

# Scale worker service
docker compose up -d --scale worker=2
```

### Strategy 2: Optimize Database Queries
```bash
# Add missing indexes
docker compose exec db psql -U matchhire -d matchhire -c "CREATE INDEX CONCURRENTLY idx_name ON table(column);"

# Update statistics
docker compose exec db psql -U matchhire -d matchhire -c "ANALYZE;"

# Vacuum database
docker compose exec db psql -U matchhire -d matchhire -c "VACUUM ANALYZE;"
```

### Strategy 3: Optimize Application Code
```bash
# Review recent code changes
git log --oneline -10

# Check for inefficient algorithms
# Review Django Debug Toolbar output (in development)
```

### Strategy 4: Rate Limiting
```bash
# If traffic spike is the cause, implement stricter rate limiting
# Adjust throttle rates in Django settings
```

### Strategy 5: Resource Limits
```bash
# Update docker-compose.yml with increased CPU limits
# Then restart
docker compose up -d
```

## CPU Optimization Checklist

### Database
- [ ] Add missing indexes
- [ ] Optimize slow queries
- [ ] Use connection pooling
- [ ] Consider read replicas

### Application
- [ ] Optimize algorithms
- [ ] Use caching
- [ ] Implement pagination
- [ ] Use async operations

### Infrastructure
- [ ] Scale horizontally
- [ ] Use load balancing
- [ ] Optimize container resources
- [ ] Use CPU profiling

## Escalation Criteria

Escalate to Engineering Lead if:
- CPU usage persists despite scaling
- Code optimization is required
- Infrastructure changes are needed

Escalate to CTO if:
- CPU usage persists for more than 1 hour
- Service is unstable
- Architecture changes are needed

## Prevention Measures

### Monitoring
- Monitor CPU usage
- Monitor request rate
- Monitor query performance
- Monitor task execution time

### Capacity Planning
- Scale based on load
- Implement auto-scaling
- Use load testing
- Plan for peak traffic

### Optimization
- Regular performance audits
- Code review for efficiency
- Database optimization
- Caching strategy

## Post-Incident Actions

1. **Performance Analysis**
   - Identify CPU-intensive operations
   - Document bottlenecks
   - Profile application code

2. **Optimization**
   - Implement fixes
   - Add monitoring
   - Create performance tests

3. **Prevention**
   - Add performance regression tests
   - Implement continuous performance monitoring
   - Document performance guidelines

## Related Runbooks
- [High Latency](./high-latency.md)
- [High Memory Usage](./high-memory-usage.md)
- [Database Outage](./database-outage.md)

## Related Metrics
- `container_cpu_usage_seconds_total`
- `http_request_duration_seconds`
- `db_query_duration_seconds`
- `celery_task_duration_seconds`
