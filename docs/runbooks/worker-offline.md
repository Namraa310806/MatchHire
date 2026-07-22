# Worker Offline Runbook

## Alert Condition
No active Celery workers for 5 minutes

## Impact
Background tasks are not being processed, which affects:
- Email notifications
- Job matching calculations
- Resume parsing
- Analytics aggregation
- All async operations

## Initial Assessment (5 minutes)

### 1. Verify Worker Status
```bash
# Check worker containers
docker compose ps worker

# Check worker logs
docker compose logs worker --tail=100

# Check if workers are registered
docker compose exec web python manage.py celery -A matchhire_backend inspect active
```

### 2. Check Worker Resources
```bash
# Check container resources
docker stats worker

# Check CPU usage
top

# Check memory usage
free -m
```

### 3. Check Celery Configuration
```bash
# Check Celery broker connectivity
docker compose exec redis redis-cli ping

# Check Celery configuration
docker compose exec web env | grep CELERY_
```

## Troubleshooting Steps

### Step 1: Check Worker Logs
```bash
# View recent logs
docker compose logs worker --tail=200

# Check for startup errors
docker compose logs worker | grep -i "error\|exception\|traceback"

# Check for connection errors
docker compose logs worker | grep -i "connection\|broker"
```

### Step 2: Check Broker Connectivity
```bash
# Check Redis connectivity
docker compose exec redis redis-cli ping

# Check Redis logs
docker compose logs redis --tail=50

# Check if Redis is accepting connections
docker compose exec redis redis-cli INFO clients
```

### Step 3: Restart Workers
```bash
# Restart worker service
docker compose restart worker

# Wait for workers to start
sleep 10

# Check status
docker compose ps worker
```

### Step 4: Check Worker Configuration
```bash
# Check worker command in docker-compose.yml
# Verify configuration is correct

# Test worker manually
docker compose run --rm worker celery -A matchhire_backend inspect active
```

## Resolution Strategies

### Strategy 1: Restart Worker Service
```bash
# Stop workers
docker compose stop worker

# Start workers
docker compose start worker

# Verify workers are active
docker compose exec web python manage.py celery -A matchhire_backend inspect active
```

### Strategy 2: Recreate Worker Containers
```bash
# Stop and remove containers
docker compose rm -f worker

# Recreate containers
docker compose up -d worker

# Wait for initialization
sleep 15

# Verify
docker compose exec web python manage.py celery -A matchhire_backend inspect active
```

### Strategy 3: Scale Workers
```bash
# Scale worker service
docker compose up -d --scale worker=2

# Verify workers are active
docker compose exec web python manage.py celery -A matchhire_backend inspect active
```

### Strategy 4: Fix Configuration Issues
If configuration is the issue:
```bash
# Update docker-compose.yml with correct configuration
# Then restart
docker compose up -d worker
```

### Strategy 5: Check for Resource Exhaustion
```bash
# Check if workers are OOM killed
docker compose logs worker | grep -i "oom"

# Check memory limits
docker inspect matchhire-worker-1 | grep Memory

# Increase memory limits if needed
```

## Worker Health Checks

### Manual Health Check
```bash
# Check if workers are processing tasks
docker compose exec web python manage.py celery -A matchhire_backend inspect active

# Check worker stats
docker compose exec web python manage.py celery -A matchhire_backend inspect stats

# Check registered tasks
docker compose exec web python manage.py celery -A matchhire_backend inspect registered
```

### Automated Health Check
```bash
# Add to monitoring
# Check celery_worker_active_tasks metric
# Alert if metric is 0 for > 5 minutes
```

## Escalation Criteria

Escalate to Engineering Lead if:
- Workers cannot be restarted
- Configuration issues cannot be resolved
- Issue persists for more than 15 minutes

Escalate to CTO if:
- Issue persists for more than 30 minutes
- Multiple worker types are affected
- Broker issues are suspected

## Prevention Measures

### Monitoring
- Monitor worker health
- Monitor worker resource usage
- Monitor task processing rate
- Monitor queue length

### Configuration
- Set appropriate worker concurrency
- Configure worker timeouts
- Configure worker health checks
- Set up worker monitoring

### Resilience
- Use supervisor for worker management
- Implement worker auto-restart
- Use multiple worker processes
- Implement worker health checks

## Post-Incident Actions

1. **Root Cause Analysis**
   - Why did workers go offline?
   - Was it a configuration issue?
   - Was it resource exhaustion?
   - Was it a broker issue?

2. **Update Monitoring**
   - Add worker health alerts
   - Add resource usage alerts
   - Add broker connectivity alerts

3. **Improve Resilience**
   - Implement auto-restart
   - Implement health checks
   - Add worker monitoring
   - Implement circuit breakers

## Related Runbooks
- [Queue Backlog](./queue-backlog.md)
- [Redis Outage](./redis-outage.md)
- [High Memory Usage](./high-memory-usage.md)

## Related Metrics
- `celery_worker_active_tasks`
- `celery_tasks_total`
- `celery_task_duration_seconds`
- `celery_queue_length`
