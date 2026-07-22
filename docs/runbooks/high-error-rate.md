# High Error Rate Runbook

## Alert Condition
Error rate > 5% for 5 minutes

## Impact
Users are experiencing errors when using the application. This may indicate:
- Application bugs
- Database issues
- External service failures
- Configuration errors
- Resource exhaustion

## Initial Assessment (5 minutes)

### 1. Verify Alert
- Check Grafana dashboard for error rate spike
- Confirm error rate is sustained, not a transient blip
- Check if errors are concentrated in specific endpoints

### 2. Check Recent Changes
- Review recent deployments
- Check for configuration changes
- Review recent code commits
- Check for database schema changes

### 3. Identify Error Pattern
```bash
# Check error logs
docker compose logs web | grep ERROR | tail -100

# Check specific error types
docker compose logs web | grep "500\|502\|503" | tail -50
```

### 4. Check Dependencies
- Database connectivity: `curl http://localhost:8000/api/v1/health/ready`
- Redis connectivity: Check Redis health
- External services: Check third-party API status

## Troubleshooting Steps

### Step 1: Check Application Logs
```bash
# View recent error logs
docker compose logs --tail=500 web | grep -i error

# Check for specific error patterns
docker compose logs web | grep -i "exception\|traceback"
```

### Step 2: Check Database Health
```bash
# Check database connectivity
docker compose exec web python manage.py dbshell

# Check database connections
docker compose exec db psql -U matchhire -d matchhire -c "SELECT count(*) FROM pg_stat_activity;"
```

### Step 3: Check Resource Usage
```bash
# Check container resources
docker stats

# Check disk space
df -h

# Check memory usage
free -m
```

### Step 4: Check Recent Deployments
```bash
# Check deployment history
git log --oneline -10

# Rollback if needed
git revert <commit-hash>
docker compose up -d --build
```

### Step 5: Check External Services
- Verify third-party API status
- Check rate limits
- Verify API keys and credentials

## Resolution Strategies

### Strategy 1: Rollback Recent Deployment
If errors started after a recent deployment:
```bash
# Identify the last working commit
git log --oneline

# Rollback to previous commit
git checkout <previous-commit>
docker compose up -d --build
```

### Strategy 2: Scale Resources
If resource exhaustion is the cause:
```bash
# Scale web service
docker compose up -d --scale web=3

# Check if scaling resolves the issue
```

### Strategy 3: Restart Services
```bash
# Restart web service
docker compose restart web

# Restart database
docker compose restart db

# Restart Redis
docker compose restart redis
```

### Strategy 4: Database Maintenance
If database is the issue:
```bash
# Check for long-running queries
docker compose exec db psql -U matchhire -d matchhire -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC;"

# Kill long-running queries if necessary
docker compose exec db psql -U matchhire -d matchhire -c "SELECT pg_terminate_backend(pid);"
```

### Strategy 5: Cache Flush
If cache corruption is suspected:
```bash
# Flush Redis cache
docker compose exec redis redis-cli FLUSHALL

# Restart application
docker compose restart web
```

## Escalation Criteria

Escalate to Engineering Lead if:
- Issue persists for more than 30 minutes
- Multiple services are affected
- Root cause cannot be identified
- Database corruption is suspected

Escalate to CTO if:
- Issue persists for more than 1 hour
- Critical business functions are impacted
- Data loss is suspected

## Post-Incident Actions

1. **Document the incident**
   - Root cause analysis
   - Timeline of events
   - Actions taken

2. **Update monitoring**
   - Add alerts for early detection
   - Adjust thresholds if needed
   - Create dashboards for visibility

3. **Prevent recurrence**
   - Add automated tests
   - Improve code review process
   - Add circuit breakers for external services

4. **Communicate**
   - Notify stakeholders
   - Post-mortem meeting
   - Update runbook with lessons learned

## Related Runbooks
- [Database Outage](./database-outage.md)
- [High Latency](./high-latency.md)
- [Redis Outage](./redis-outage.md)

## Related Metrics
- `http_requests_total{status=~"5.."}`
- `http_request_duration_seconds`
- `db_errors_total`
