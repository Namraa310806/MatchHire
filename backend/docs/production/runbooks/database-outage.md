# Database Outage Runbook

## Severity
Critical

## Symptoms
- Database connection errors
- Slow database queries
- High database CPU/memory usage
- Connection pool exhaustion

## Immediate Actions

### 1. Verify Database Status
```bash
# Check PostgreSQL status
docker exec matchhire-postgres pg_isready

# Check connection count
docker exec matchhire-postgres psql -U matchhire -d matchhire -c "SELECT count(*) FROM pg_stat_activity;"

# Check long-running queries
docker exec matchhire-postgres psql -U matchhire -d matchhire -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"
```

### 2. Check Application Logs
```bash
# Check backend logs
docker logs matchhire-backend --tail 100

# Check for database errors
docker logs matchhire-backend | grep -i "database\|connection\|timeout"
```

### 3. Restart Database (if needed)
```bash
# Restart PostgreSQL container
docker-compose restart postgres

# Or restart entire stack
docker-compose restart
```

### 4. Scale Application (if connection pool exhausted)
```bash
# Scale backend services
docker-compose up -d --scale backend=3
```

## Root Cause Analysis

### Check Database Metrics
- CPU usage > 80%
- Memory usage > 90%
- Disk I/O saturation
- Connection count near max_connections
- Lock contention

### Common Causes
1. **Long-running queries** - Identify and kill or optimize
2. **Connection leaks** - Restart application to release connections
3. **Insufficient resources** - Scale database or optimize queries
4. **Disk full** - Clean up old data or expand storage

## Resolution Steps

### For Long-Running Queries
```sql
-- Kill specific query
SELECT pg_cancel_backend(<pid>);

-- Terminate backend connection
SELECT pg_terminate_backend(<pid>);
```

### For Connection Leaks
```bash
# Restart application to release connections
docker-compose restart backend celery-worker celery-beat
```

### For Resource Exhaustion
```bash
# Scale PostgreSQL resources in docker-compose.production.yml
# Increase:
# - max_connections
# - shared_buffers
# - effective_cache_size
# - maintenance_work_mem
```

## Prevention
- Enable query logging
- Set up connection pool monitoring
- Implement query timeouts
- Regular database maintenance (VACUUM, ANALYZE)
- Set up alerts for database metrics

## Escalation
- If unresolved in 15 minutes: Escalate to DBA
- If data corruption suspected: Restore from backup
- If persistent issues: Engage platform engineering team
