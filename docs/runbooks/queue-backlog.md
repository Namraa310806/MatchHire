# Queue Backlog Runbook

## Alert Condition
Celery queue length > 1000 tasks for 10 minutes

## Impact
Background tasks are delayed, which may affect:
- Email notifications
- Job matching calculations
- Resume parsing
- Analytics aggregation
- Data synchronization

## Initial Assessment (5 minutes)

### 1. Verify Queue Status
```bash
# Check queue length
docker compose exec redis redis-cli LLEN celery

# Check other queues
docker compose exec redis redis-cli LLEN matching
docker compose exec redis redis-cli LLEN notifications
```

### 2. Check Worker Status
```bash
# Check worker processes
docker compose ps worker

# Check worker logs
docker compose logs worker --tail=100
```

### 3. Check Task Types
```bash
# Check what tasks are in the queue
docker compose exec redis redis-cli LRANGE celery 0 10

# Check for stuck tasks
docker compose exec redis redis-cli LRANGE celery -10 -1
```

## Troubleshooting Steps

### Step 1: Check Worker Health
```bash
# Check if workers are running
docker compose ps worker

# Check worker logs for errors
docker compose logs worker | grep -i "error\|exception"

# Check worker stats
docker compose exec web python manage.py celery -A matchhire_backend inspect active
```

### Step 2: Check Worker Resources
```bash
# Check container resources
docker stats worker

# Check CPU usage
top

# Check memory usage
free -m
```

### Step 3: Check Task Failure Rate
```bash
# Check for failed tasks
docker compose logs worker | grep -i "failed"

# Check Celery metrics
# Review Grafana Celery metrics
```

### Step 4: Check Task Types
```bash
# Identify which tasks are backing up
docker compose exec web python manage.py celery -A matchhire_backend inspect registered

# Check task execution time
docker compose logs worker | grep "duration"
```

## Resolution Strategies

### Strategy 1: Scale Workers
```bash
# Scale worker service horizontally
docker compose up -d --scale worker=3

# Monitor queue length reduction
docker compose exec redis redis-cli LLEN celery
```

### Strategy 2: Restart Workers
```bash
# Restart worker service
docker compose restart worker

# Wait for workers to start
sleep 10

# Check status
docker compose ps worker
```

### Strategy 3: Clear Stuck Tasks
```bash
# WARNING: This will delete queued tasks
# Use only if tasks can be safely discarded

# Clear specific queue
docker compose exec redis redis-cli DEL celery

# Or move tasks to a backup queue
docker compose exec redis redis-cli RENAME celery celery_backup
```

### Strategy 4: Prioritize Critical Tasks
```bash
# Create a high-priority queue
# Route critical tasks to this queue
# Scale workers for high-priority queue
```

### Strategy 5: Optimize Task Performance
```bash
# Review task code for inefficiencies
# Add task timeouts
# Implement task retries with exponential backoff
# Break large tasks into smaller chunks
```

## Task Prioritization

### Critical Tasks (Process Immediately)
- User-facing notifications
- Time-sensitive operations
- Data consistency tasks

### Important Tasks (Process Within 1 Hour)
- Analytics aggregation
- Background calculations
- Data synchronization

### Non-Critical Tasks (Process Within 24 Hours)
- Cleanup tasks
- Reporting
- Data archiving

## Escalation Criteria

Escalate to Engineering Lead if:
- Queue continues to grow despite scaling
- Workers are failing consistently
- Critical tasks are delayed

Escalate to CTO if:
- Queue backlog affects business operations
- Data loss is possible
- Issue persists for more than 1 hour

## Prevention Measures

### Monitoring
- Monitor queue length
- Monitor worker health
- Monitor task execution time
- Monitor task failure rate

### Configuration
- Set appropriate worker concurrency
- Configure task timeouts
- Configure retry policies
- Set up queue monitoring

### Capacity Planning
- Scale workers based on load
- Implement auto-scaling
- Use multiple queues for task prioritization
- Implement backpressure mechanisms

## Post-Incident Actions

1. **Root Cause Analysis**
   - Why did the queue back up?
   - Was it a task spike?
   - Was it worker failure?
   - Was it task performance issues?

2. **Optimization**
   - Optimize slow tasks
   - Add more workers
   - Implement task prioritization
   - Add monitoring

3. **Prevention**
   - Implement auto-scaling
   - Add queue length alerts
   - Implement circuit breakers
   - Add task performance monitoring

## Related Runbooks
- [Worker Offline](./worker-offline.md)
- [High CPU Usage](./high-cpu-usage.md)
- [High Memory Usage](./high-memory-usage.md)

## Related Metrics
- `celery_queue_length`
- `celery_tasks_total`
- `celery_task_duration_seconds`
- `celery_worker_active_tasks`
