# Database Outage Runbook

## Alert Condition
Database health check fails for 2 consecutive checks

## Impact
Application cannot function without database connectivity. All database-dependent operations will fail:
- User authentication
- Job postings
- Resume uploads
- Applications
- All CRUD operations

## Initial Assessment (2 minutes)

### 1. Verify Database Status
```bash
# Check database container
docker compose ps db

# Check database logs
docker compose logs db --tail=100

# Check database connectivity
docker compose exec web python manage.py dbshell
```

### 2. Check Database Resources
```bash
# Check container resources
docker stats db

# Check disk space
df -h

# Check memory
free -m
```

### 3. Check Database Configuration
```bash
# Check database connection settings
docker compose exec web env | grep DB_

# Check database is accepting connections
docker compose exec db pg_isready
```

## Troubleshooting Steps

### Step 1: Restart Database Container
```bash
# Restart database
docker compose restart db

# Wait for database to start
sleep 10

# Check status
docker compose ps db
```

### Step 2: Check Database Logs
```bash
# View recent logs
docker compose logs db --tail=200

# Check for specific errors
docker compose logs db | grep -i "error\|fatal\|panic"
```

### Step 3: Check Database Connections
```bash
# Check connection count
docker compose exec db psql -U matchhire -d matchhire -c "SELECT count(*) FROM pg_stat_activity;"

# Check for blocking queries
docker compose exec db psql -U matchhire -d matchhire -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC;"
```

### Step 4: Check Disk Space
```bash
# Check disk usage
df -h

# Check PostgreSQL data directory
docker compose exec db du -sh /var/lib/postgresql/data
```

### Step 5: Check Database Configuration
```bash
# Check max_connections
docker compose exec db psql -U matchhire -d matchhire -c "SHOW max_connections;"

# Check shared_buffers
docker compose exec db psql -U matchhire -d matchhire -c "SHOW shared_buffers;"
```

## Resolution Strategies

### Strategy 1: Restart Database Service
```bash
# Stop database
docker compose stop db

# Start database
docker compose start db

# Verify connectivity
docker compose exec web python manage.py check --database default
```

### Strategy 2: Recreate Database Container
```bash
# Stop and remove container
docker compose rm -f db

# Recreate container
docker compose up -d db

# Wait for initialization
sleep 30

# Verify
docker compose exec web python manage.py check --database default
```

### Strategy 3: Scale Database Resources
If resource exhaustion is the cause:
```bash
# Update docker-compose.yml with increased resources
# Then restart
docker compose up -d db
```

### Strategy 4: Database Recovery from Backup
If database is corrupted:
```bash
# Stop application
docker compose stop web

# Restore from backup
docker compose exec -T db pg_restore -U matchhire -d matchhire < /path/to/backup.dump

# Restart application
docker compose start web
```

### Strategy 5: Clear Connection Pool
```bash
# Kill all connections except maintenance
docker compose exec db psql -U matchhire -d matchhire -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'matchhire' AND pid <> pg_backend_pid();"
```

## Escalation Criteria

Escalate to Engineering Lead if:
- Database cannot be restarted
- Data corruption is suspected
- Issue persists for more than 15 minutes

Escalate to CTO if:
- Data loss is confirmed
- Issue persists for more than 30 minutes
- Database requires full restore from backup

## Prevention Measures

### Regular Backups
```bash
# Daily backup
0 2 * * * docker compose exec -T db pg_dump -U matchhire matchhire > /backup/matchhire-$(date +\%Y\%m\%d).sql

# Weekly full backup
0 3 * * 0 docker compose exec -T db pg_dump -U matchhire -Fc matchhire > /backup/matchhire-weekly.dump
```

### Monitoring
- Monitor database connection count
- Monitor query performance
- Monitor disk space
- Monitor replication lag (if applicable)

### Maintenance
- Regular vacuum and analyze
- Index maintenance
- Log rotation
- Configuration tuning

## Post-Incident Actions

1. **Root Cause Analysis**
   - Why did the database go down?
   - Was it resource exhaustion?
   - Was it a configuration issue?
   - Was it a bug?

2. **Update Monitoring**
   - Add alerts for connection count
   - Add alerts for disk space
   - Add alerts for query performance

3. **Improve Resilience**
   - Consider read replicas
   - Consider connection pooling
   - Consider automatic failover

4. **Documentation**
   - Update runbook with lessons learned
   - Document any configuration changes
   - Share findings with team

## Related Runbooks
- [High Error Rate](./high-error-rate.md)
- [High CPU Usage](./high-cpu-usage.md)
- [High Memory Usage](./high-memory-usage.md)

## Related Metrics
- `db_connections_active`
- `db_query_duration_seconds`
- `db_errors_total`
- `health_check{check="database"}`
