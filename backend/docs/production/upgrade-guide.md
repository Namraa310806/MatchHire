# Upgrade Guide

## Overview
This guide covers upgrading MatchHire backend to new versions.

## Pre-Upgrade Preparation

### Backup
```bash
# Create database backup
python manage.py backup_database

# Create Elasticsearch snapshot
curl -X PUT "localhost:9200/_snapshot/backups/pre_upgrade_$(date +%Y%m%d)"

# Export configuration
docker-compose config > docker-compose.backup.yml
```

### Testing
- Test upgrade in staging environment
- Run full test suite
- Perform load testing
- Verify all integrations

### Planning
- Schedule maintenance window
- Notify stakeholders
- Prepare rollback plan
- Document current state

## Upgrade Process

### Minor Version Upgrade (X.Y.Z → X.Y.W)

#### 1. Pull latest code
```bash
git fetch origin
git checkout v<new-version>
```

#### 2. Update dependencies
```bash
pip install -r requirements.txt --upgrade
```

#### 3. Run migrations
```bash
python manage.py migrate --noinput
```

#### 4. Collect static files
```bash
python manage.py collectstatic --noinput
```

#### 5. Restart services
```bash
docker-compose down
docker-compose up -d
```

#### 6. Verify health
```bash
curl http://localhost:8000/health/
curl http://localhost:8000/health/ready/
```

### Major Version Upgrade (X.Y.Z → W.Y.Z)

#### 1. Review breaking changes
- Check CHANGELOG.md
- Review migration notes
- Identify deprecated features

#### 2. Update configuration
- Review new environment variables
- Update feature flags
- Adjust resource limits if needed

#### 3. Data migration
```bash
# Run any data migrations
python manage.py migrate_data
```

#### 4. Rebuild indexes
```bash
python manage.py rebuild_search_index
```

#### 5. Follow minor upgrade steps
- Complete steps 1-6 from minor upgrade

## Post-Upgrade Verification

### Health Checks
```bash
# Check all services
docker-compose ps

# Check logs
docker-compose logs --tail=100

# Check metrics
curl http://localhost:8000/metrics/
```

### Functional Testing
- Test search functionality
- Test recommendations
- Test API endpoints
- Test authentication
- Test file uploads

### Performance Testing
- Run load tests
- Compare with baseline
- Check query performance
- Verify cache hit rate

## Rollback Procedure

### Quick Rollback (if issues detected within 5 minutes)
```bash
# Revert code
git checkout <previous-version>

# Restore database
python manage.py restore_database <backup-file>

# Restart services
docker-compose down
docker-compose up -d
```

### Full Rollback (if major issues)
```bash
# Restore database backup
pg_restore -d matchhire matchhire_backup.sql.gz

# Restore Elasticsearch snapshot
curl -X POST "localhost:9200/_snapshot/backups/<snapshot>/_restore"

# Revert code
git checkout <previous-version>

# Rebuild Docker image
docker-compose build
docker-compose up -d
```

## Upgrade Best Practices

### Timing
- Upgrade during low-traffic periods
- Allow 2x estimated time for upgrades
- Have rollback plan ready
- Monitor for 1 hour after upgrade

### Communication
- Notify users 24 hours in advance
- Provide estimated downtime
- Share upgrade notes
- Post-upgrade announcement

### Testing
- Always test in staging first
- Run automated tests
- Perform manual smoke tests
- Monitor closely after upgrade

### Monitoring
- Enable enhanced monitoring
- Set up upgrade-specific alerts
- Log all upgrade steps
- Document any issues

## Common Issues and Solutions

### Migration Failures
```bash
# If migration fails, check current state
python manage.py showmigrations

# Fake migration if already applied
python manage.py migrate <app> <migration> --fake
```

### Dependency Conflicts
```bash
# Use pip-tools for dependency resolution
pip-compile requirements.in
pip-sync requirements.txt
```

### Cache Issues
```bash
# Clear cache after upgrade
docker exec matchhire-redis redis-cli FLUSHALL
```

### Performance Degradation
```bash
# Check for slow queries
python manage.py show_slow_queries

# Rebuild indexes
python manage.py rebuild_search_index
```

## Upgrade Schedule

### Regular Upgrades
- **Security patches**: Within 7 days of release
- **Minor versions**: Monthly
- **Major versions**: Quarterly planning

### Emergency Upgrades
- Critical security vulnerabilities: Immediate
- Data loss bugs: Immediate
- Performance regressions: Within 24 hours
