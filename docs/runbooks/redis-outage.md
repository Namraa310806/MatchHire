# Redis Outage Runbook

## Alert Condition
Redis health check fails for 2 consecutive checks

## Impact
Caching and task queue operations are degraded:
- Cache misses will increase database load
- Celery tasks will not be processed
- Session management may be affected
- Performance will degrade significantly

## Initial Assessment (2 minutes)

### 1. Verify Redis Status
```bash
# Check Redis container
docker compose ps redis

# Check Redis logs
docker compose logs redis --tail=100

# Check Redis connectivity
docker compose exec redis redis-cli ping
```

### 2. Check Redis Resources
```bash
# Check container resources
docker stats redis

# Check disk space
df -h

# Check memory
free -m
```

### 3. Check Redis Configuration
```bash
# Check Redis configuration
docker compose exec redis redis-cli CONFIG GET maxmemory

# Check Redis memory usage
docker compose exec redis redis-cli INFO memory
```

## Troubleshooting Steps

### Step 1: Restart Redis Container
```bash
# Restart Redis
docker compose restart redis

# Wait for Redis to start
sleep 5

# Check status
docker compose exec redis redis-cli ping
```

### Step 2: Check Redis Logs
```bash
# View recent logs
docker compose logs redis --tail=200

# Check for specific errors
docker compose logs redis | grep -i "error\|fatal\|oom"
```

### Step 3: Check Redis Memory
```bash
# Check memory usage
docker compose exec redis redis-cli INFO memory | grep used_memory

# Check maxmemory setting
docker compose exec redis redis-cli CONFIG GET maxmemory
```

### Step 4: Check Redis Persistence
```bash
# Check if persistence is enabled
docker compose exec redis redis-cli CONFIG GET save

# Check RDB file
docker compose exec redis ls -lh /data/dump.rdb
```

## Resolution Strategies

### Strategy 1: Restart Redis Service
```bash
# Stop Redis
docker compose stop redis

# Start Redis
docker compose start redis

# Verify connectivity
docker compose exec redis redis-cli ping
```

### Strategy 2: Recreate Redis Container
```bash
# Stop and remove container
docker compose rm -f redis

# Recreate container
docker compose up -d redis

# Wait for initialization
sleep 10

# Verify
docker compose exec redis redis-cli ping
```

### Strategy 3: Clear Redis Cache
```bash
# Flush all data (use with caution)
docker compose exec redis redis-cli FLUSHALL

# Or flush specific database
docker compose exec redis redis-cli FLUSHDB
```

### Strategy 4: Increase Redis Memory
If memory exhaustion is the cause:
```bash
# Update docker-compose.yml with increased memory limits
# Then restart
docker compose up -d redis
```

### Strategy 5: Restore from Persistence
```bash
# If using RDB persistence, ensure dump file exists
docker compose exec redis ls -lh /data/dump.rdb

# Redis will automatically load dump on startup
# If not, manually load:
docker compose exec redis redis-cli --rdb /data/dump.rdb
```

## Degraded Mode Operation

If Redis cannot be restored immediately, the application can operate in degraded mode:

### Impact of Degraded Mode
- No caching (increased database load)
- No background task processing
- Possible session issues

### Mitigation Steps
```bash
# Scale database to handle increased load
docker compose up -d --scale db=2

# Monitor database performance closely
# Consider temporarily disabling non-critical features
```

## Escalation Criteria

Escalate to Engineering Lead if:
- Redis cannot be restarted
- Data loss is suspected
- Issue persists for more than 15 minutes

Escalate to CTO if:
- Data loss is confirmed
- Issue persists for more than 30 minutes
- Cache data cannot be recovered

## Prevention Measures

### Monitoring
- Monitor Redis memory usage
- Monitor Redis connection count
- Monitor cache hit rate
- Monitor queue length

### Configuration
- Set appropriate maxmemory policy
- Enable persistence (RDB/AOF)
- Configure memory limits
- Set up Redis monitoring

### Maintenance
- Regular backup of Redis data
- Monitor key expiration
- Clean up unused keys
- Monitor fragmentation

## Post-Incident Actions

1. **Root Cause Analysis**
   - Why did Redis go down?
   - Was it memory exhaustion?
   - Was it a configuration issue?
   - Was it a bug?

2. **Update Monitoring**
   - Add alerts for memory usage
   - Add alerts for connection count
   - Add alerts for cache hit rate

3. **Improve Resilience**
   - Consider Redis Cluster
   - Consider Redis Sentinel
   - Consider backup Redis instance

4. **Documentation**
   - Update runbook with lessons learned
   - Document any configuration changes
   - Share findings with team

## Related Runbooks
- [High Error Rate](./high-error-rate.md)
- [Database Outage](./database-outage.md)
- [Queue Backlog](./queue-backlog.md)

## Related Metrics
- `cache_hits_total`
- `cache_misses_total`
- `celery_queue_length`
- `health_check{check="redis"}`
