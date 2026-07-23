# Upgrade Guide

## Overview

This guide provides procedures for upgrading the MatchHire backend to new versions.

## Pre-Upgrade Checklist

- [ ] Review release notes
- [ ] Check for breaking changes
- [ ] Review migration files
- [ ] Test in staging environment
- [ ] Create backup
- [ ] Notify stakeholders
- [ ] Schedule maintenance window
- [ ] Prepare rollback plan

## Upgrade Procedure

### 1. Preparation

```bash
# SSH into production server
ssh user@production-server

# Navigate to application directory
cd /opt/matchhire/backend

# Create backup
docker-compose -f docker-compose.production.yml exec backend python manage.py create_backup

# Verify backup
ls -lh backups/
```

### 2. Staging Deployment

```bash
# Deploy to staging first
git checkout <new-version>
docker-compose -f docker-compose.staging.yml build
docker-compose -f docker-compose.staging.yml up -d

# Run migrations
docker-compose -f docker-compose.staging.yml exec backend python manage.py migrate

# Run tests
docker-compose -f docker-compose.staging.yml exec backend python manage.py test

# Verify functionality
# (manual testing)
```

### 3. Production Deployment

```bash
# Notify users of maintenance
# (via status page, email, etc.)

# Stop services
docker-compose -f docker-compose.production.yml down

# Pull new code
git checkout <new-version>
git pull origin main

# Build new images
docker-compose -f docker-compose.production.yml build

# Start services
docker-compose -f docker-compose.production.yml up -d

# Run migrations
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate

# Collect static files
docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput

# Verify deployment
curl http://localhost:8000/health/
```

### 4. Post-Upgrade Verification

```bash
# Check service health
docker-compose -f docker-compose.production.yml ps

# Check logs
docker-compose -f docker-compose.production.yml logs -f backend

# Verify database
docker-compose -f docker-compose.production.yml exec backend python manage.py dbshell

# Verify cache
docker-compose -f docker-compose.production.yml exec redis redis-cli ping

# Verify search
curl http://localhost:9200/_cluster/health
```

### 5. Warm Up

```bash
# Warm up cache
docker-compose -f docker-compose.production.yml exec backend python manage.py warmup_cache

# Reindex search if needed
docker-compose -f docker-compose.production.yml exec backend python manage.py reindex_search
```

## Rollback Procedure

If upgrade fails:

```bash
# Stop new deployment
docker-compose -f docker-compose.production.yml down

# Restore previous version
git checkout <previous-version>

# Rebuild and start
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d

# Restore database if needed
docker-compose -f docker-compose.production.yml exec backend python manage.py restore_backup <backup-file>

# Verify rollback
curl http://localhost:8000/health/
```

## Zero-Downtime Upgrade

For zero-downtime upgrades:

### Blue-Green Deployment

```bash
# Deploy to green environment
docker-compose -f docker-compose.green.yml up -d

# Verify green environment
curl http://localhost:8001/health/

# Switch traffic to green
# (via load balancer)

# Stop blue environment
docker-compose -f docker-compose.blue.yml down
```

### Rolling Update

```bash
# Update one instance at a time
docker-compose -f docker-compose.production.yml up -d --no-deps --scale backend=1 backend
# Verify
docker-compose -f docker-compose.production.yml up -d --no-deps --scale backend=2 backend
# Verify
# Continue until all instances updated
```

## Database Migration Guidelines

### Review Migrations

```bash
# Review pending migrations
docker-compose -f docker-compose.production.yml exec backend python manage.py showmigrations

# Review migration SQL
docker-compose -f docker-compose.production.yml exec backend python manage.py sqlmigrate <app> <migration>
```

### Safe Migration Practices

- Run migrations during low-traffic periods
- Test migrations in staging first
- Have rollback SQL ready
- Monitor database performance during migration
- Lock tables if necessary to prevent data inconsistency

### Migration Checklist

- [ ] Migration reviewed
- [ ] Migration tested in staging
- [ ] Rollback plan prepared
- [ ] Maintenance window scheduled
- [ ] Database backup created
- [ ] Monitoring configured

## Dependency Updates

### Python Dependencies

```bash
# Update requirements.txt
pip install --upgrade <package>
pip freeze > requirements.txt

# Test in staging
docker-compose -f docker-compose.staging.yml build
docker-compose -f docker-compose.staging.yml up -d

# Run tests
docker-compose -f docker-compose.staging.yml exec backend python manage.py test
```

### System Dependencies

```bash
# Update Docker base images
# Update Dockerfile FROM lines

# Rebuild
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d
```

## Major Version Upgrades

### Django Version Upgrade

1. Review Django release notes
2. Update requirements.txt
3. Update deprecated code
4. Run Django upgrade checker
5. Test thoroughly in staging
6. Plan for potential breaking changes

### Database Version Upgrade

1. Review database release notes
2. Test upgrade in staging
3. Create full backup
4. Schedule extended maintenance window
5. Upgrade database
6. Verify compatibility
7. Update connection settings

## Troubleshooting

### Migration Fails

```bash
# Check migration status
docker-compose -f docker-compose.production.yml exec backend python manage.py showmigrations

# Fake migration if needed
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate <app> <migration> --fake

# Rollback migration
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate <app> <migration> --fake
```

### Service Won't Start After Upgrade

```bash
# Check logs
docker-compose -f docker-compose.production.yml logs backend

# Check configuration
docker-compose -f docker-compose.production.yml exec backend python manage.py check

# Check dependencies
docker-compose -f docker-compose.production.yml exec backend pip list
```

### Performance Degradation

```bash
# Check resource usage
docker stats

# Check database performance
docker-compose -f docker-compose.production.yml exec postgres psql -U matchhire -d matchhire -c "SELECT * FROM pg_stat_activity;"

# Check cache hit rate
docker-compose -f docker-compose.production.yml exec redis redis-cli INFO stats

# Enable feature flags to disable new features
```

## Communication

### Pre-Upgrade

- Notify stakeholders 1 week in advance
- Schedule maintenance window
- Update status page
- Send email notification

### During Upgrade

- Update status page with progress
- Provide estimated completion time
- Communicate any delays

### Post-Upgrade

- Confirm successful upgrade
- Update status page
- Send completion notification
- Document any issues

## Upgrade Checklist

- [ ] Release notes reviewed
- [ ] Breaking changes identified
- [ ] Staging deployment successful
- [ ] Backup created
- [ ] Maintenance window scheduled
- [ ] Stakeholders notified
- [ ] Rollback plan prepared
- [ ] Production deployment completed
- [ ] Migrations applied
- [ ] Services verified
- [ ] Cache warmed
- [ ] Monitoring confirmed
- [ ] Status page updated
- [ ] Stakeholders notified of completion

## Emergency Contacts

- On-Call Engineer: [contact]
- Engineering Lead: [contact]
- DevOps: [contact]
