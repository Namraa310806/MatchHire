# Rollback Checklist

## Overview

This checklist provides step-by-step procedures for rolling back the MatchHire backend to a previous version.

## Pre-Rollback Checklist

- [ ] Identify rollback point (commit hash/tag)
- [ ] Verify backup availability
- [ ] Notify stakeholders
- [ ] Prepare rollback environment
- [ ] Document current state
- [ ] Estimate rollback time
- [ ] Prepare communication plan

## Rollback Procedure

### 1. Document Current State

```bash
# Record current deployment
git log -1 > /tmp/current-deployment.txt
docker-compose -f docker-compose.production.yml ps > /tmp/current-services.txt
docker stats --no-stream > /tmp/current-resources.txt
```

### 2. Stop Current Deployment

```bash
# Stop all services
docker-compose -f docker-compose.production.yml down

# Verify stopped
docker-compose -f docker-compose.production.yml ps
```

### 3. Restore Previous Code

```bash
# Checkout previous version
git checkout <commit-hash-or-tag>

# Verify version
git log -1
```

### 4. Restore Database (if needed)

```bash
# List available backups
docker-compose -f docker-compose.production.yml exec backend python manage.py list_backups

# Restore specific backup
docker-compose -f docker-compose.production.yml exec backend python manage.py restore_backup <backup-file>

# Verify database
docker-compose -f docker-compose.production.yml exec backend python manage.py dbshell
```

### 5. Restore Elasticsearch (if needed)

```bash
# List snapshots
curl -X GET "localhost:9200/_snapshot/backups/_all?pretty"

# Restore snapshot
curl -X POST "localhost:9200/_snapshot/backups/<snapshot-name>/_restore"

# Verify
curl http://localhost:9200/_cat/indices?v
```

### 6. Rebuild and Start Services

```bash
# Build previous version
docker-compose -f docker-compose.production.yml build

# Start services
docker-compose -f docker-compose.production.yml up -d

# Verify services
docker-compose -f docker-compose.production.yml ps
```

### 7. Verify Rollback

```bash
# Check health endpoint
curl http://localhost:8000/health/

# Check logs
docker-compose -f docker-compose.production.yml logs -f backend

# Run smoke tests
docker-compose -f docker-compose.production.yml exec backend python manage.py test
```

### 8. Warm Up Cache

```bash
# Clear cache
docker-compose -f docker-compose.production.yml exec redis redis-cli FLUSHALL

# Warm up cache
docker-compose -f docker-compose.production.yml exec backend python manage.py warmup_cache
```

## Rollback Scenarios

### Database Rollback Only

```bash
# Stop backend services
docker-compose -f docker-compose.production.yml stop backend celery-worker celery-beat

# Restore database
docker-compose -f docker-compose.production.yml exec backend python manage.py restore_backup <backup-file>

# Start services
docker-compose -f docker-compose.production.yml start backend celery-worker celery-beat
```

### Code Rollback Only

```bash
# Stop backend services
docker-compose -f docker-compose.production.yml stop backend

# Checkout previous code
git checkout <commit-hash>

# Rebuild and start
docker-compose -f docker-compose.production.yml build backend
docker-compose -f docker-compose.production.yml up -d backend
```

### Full System Rollback

```bash
# Complete rollback including database and code
# Follow full rollback procedure above
```

## Rollback Verification Checklist

- [ ] Services started successfully
- [ ] Health endpoint healthy
- [ ] Database connectivity verified
- [ ] Cache connectivity verified
- [ ] Search functionality working
- [ ] API endpoints responding
- [ ] No errors in logs
- [ ] Performance acceptable
- [ ] Smoke tests passing
- [ ] User functionality verified

## Post-Rollback Actions

### Communication

- Update status page
- Notify stakeholders of rollback
- Communicate with users if needed
- Document rollback incident

### Analysis

- Document root cause of failure
- Identify lessons learned
- Update deployment procedures
- Schedule post-mortem meeting

### Monitoring

- Increase monitoring frequency
- Set up additional alerts
- Monitor for recurrence
- Review metrics regularly

## Rollback Time Estimates

| Scenario | Estimated Time |
|----------|----------------|
| Code rollback only | 10-15 minutes |
| Database rollback only | 15-30 minutes |
| Full system rollback | 30-60 minutes |
| With data migration | 60-120 minutes |

## Emergency Rollback

If immediate rollback required:

```bash
# Quick rollback script
#!/bin/bash
set -e

echo "Starting emergency rollback..."

# Stop services
docker-compose -f docker-compose.production.yml down

# Restore last known good version
git checkout <last-known-good-commit>

# Restore database
docker-compose -f docker-compose.production.yml exec backend python manage.py restore_backup <last-backup>

# Start services
docker-compose -f docker-compose.production.yml up -d

echo "Rollback complete"
```

## Troubleshooting

### Rollback Fails

**Code won't checkout:**
```bash
# Force checkout
git checkout -f <commit-hash>

# Or reset to specific commit
git reset --hard <commit-hash>
```

**Database restore fails:**
```bash
# Check backup file integrity
ls -lh backups/

# Try alternative backup
docker-compose -f docker-compose.production.yml exec backend python manage.py restore_backup <alternative-backup>

# Manual restore
gunzip -c <backup-file> | psql -U matchhire -d matchhire
```

**Services won't start:**
```bash
# Check logs
docker-compose -f docker-compose.production.yml logs backend

# Check configuration
docker-compose -f docker-compose.production.yml config

# Rebuild without cache
docker-compose -f docker-compose.production.yml build --no-cache
```

## Rollback Decision Criteria

Rollback should be considered when:

- Critical functionality broken
- Data corruption detected
- Security vulnerability identified
- Performance degradation > 50%
- Error rate > 10%
- User impact severe

Continue with fix when:

- Minor cosmetic issues
- Non-critical functionality
- Performance degradation < 20%
- Error rate < 5%
- Workaround available

## Rollback Prevention

To minimize rollback need:

- Comprehensive testing in staging
- Gradual rollout (canary deployment)
- Feature flags for new features
- Database migration testing
- Performance testing
- Monitoring and alerting

## Documentation

After rollback, document:

- Rollback timestamp
- Rollback reason
- Rollback procedure used
- Issues encountered
- Resolution steps
- Lessons learned
- Action items

## Contacts

- On-Call Engineer: [contact]
- Engineering Lead: [contact]
- DevOps: [contact]
- Database Admin: [contact]
