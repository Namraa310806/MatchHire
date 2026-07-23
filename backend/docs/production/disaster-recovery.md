# Disaster Recovery Guide

## Overview
This guide covers disaster recovery procedures for MatchHire backend.

## Recovery Objectives

### RTO (Recovery Time Objective)
- **Critical services**: 1 hour
- **Important services**: 4 hours
- **Non-critical services**: 24 hours

### RPO (Recovery Point Objective)
- **Database**: 5 minutes
- **Elasticsearch**: 15 minutes
- **Files**: 1 hour
- **Configuration**: 24 hours

## Backup Strategy

### Database Backups
- **Full backups**: Daily at 2 AM
- **Incremental backups**: Hourly
- **Retention**: 7 days daily, 4 weeks weekly, 12 months monthly
- **Storage**: Local + offsite (S3/GCS)
- **Encryption**: AES-256

### Elasticsearch Snapshots
- **Frequency**: Daily at 3 AM
- **Retention**: 30 days
- **Storage**: Shared file system + cloud
- **Verification**: Weekly restore test

### File Backups
- **Media files**: Daily
- **Static files**: Weekly
- **Retention**: 90 days
- **Storage**: S3/GCS with versioning

### Configuration Backups
- **Frequency**: Weekly
- **Retention**: 12 months
- **Storage**: Git repository + cloud

## Disaster Scenarios

### Scenario 1: Complete Server Failure
**Severity**: Critical
**RTO**: 1 hour

**Recovery Steps**:
1. Declare disaster
2. Activate DR site
3. Restore database from latest backup
4. Restore Elasticsearch snapshot
5. Restore configuration
6. Update DNS to point to DR site
7. Verify all services
8. Monitor for issues

### Scenario 2: Database Corruption
**Severity**: Critical
**RTO**: 2 hours

**Recovery Steps**:
1. Stop application services
2. Identify corruption extent
3. Restore from last known good backup
4. Verify data integrity
5. Replay transaction logs if available
6. Restart services
7. Monitor for issues

### Scenario 3: Ransomware Attack
**Severity**: Critical
**RTO**: 4 hours

**Recovery Steps**:
1. Isolate affected systems
2. Identify attack scope
3. Wipe and rebuild systems
4. Restore from clean backups
5. Change all credentials
6. Patch vulnerabilities
7. Monitor for reinfection
8. Conduct security review

### Scenario 4: Data Center Outage
**Severity**: High
**RTO**: 4 hours

**Recovery Steps**:
1. Confirm data center outage
2. Activate DR site in different region
3. Restore from offsite backups
4. Update DNS
5. Verify services
6. Monitor performance

### Scenario 5: Major Data Loss
**Severity**: Critical
**RTO**: 8 hours

**Recovery Steps**:
1. Identify data loss scope
2. Determine cause
3. Restore from appropriate backup
4. Recover from logs if possible
5. Verify data integrity
6. Implement preventive measures
7. Document lessons learned

## Recovery Procedures

### Pre-Recovery Checklist
- [ ] DR site available and tested
- [ ] Backups verified and accessible
- [ ] Team notified and assembled
- [ ] Communication plan activated
- [ ] Stakeholders informed

### Database Recovery
```bash
# Stop application
docker-compose stop backend celery-worker celery-beat

# Restore from backup
pg_restore -d matchhire /backups/matchhire_backup_YYYYMMDD.sql.gz

# Verify data
python manage.py check_database_integrity

# Restart application
docker-compose up -d backend celery-worker celery-beat
```

### Elasticsearch Recovery
```bash
# Restore snapshot
curl -X POST "localhost:9200/_snapshot/backups/snapshot_1/_restore"

# Verify indices
curl "localhost:9200/_cat/indices?v"

# Rebuild if needed
python manage.py rebuild_search_index
```

### Configuration Recovery
```bash
# Restore from Git
git checkout production-config

# Apply environment variables
source .env.production

# Verify configuration
python manage.py check --deploy
```

## Testing

### Regular Testing
- **Backup verification**: Weekly
- **Restore test**: Monthly
- **DR site test**: Quarterly
- **Full disaster drill**: Annually

### Test Scenarios
- Database restore
- Elasticsearch restore
- Application failover
- DNS failover
- Complete site recovery

## Communication

### Internal Communication
- **Team**: Slack bridge channel
- **Management**: Email + conference call
- **Updates**: Every 30 minutes during incident

### External Communication
- **Users**: Status page updates
- **Customers**: Email for SLA breaches
- **Public**: Social media for major outages

### Post-Incident
- **Internal**: Post-mortem within 24 hours
- **External**: Summary within 48 hours
- **Stakeholders**: Detailed report within 1 week

## Prevention

### High Availability
- Multi-region deployment
- Database replication
- Load balancing
- Auto-scaling
- Health checks

### Monitoring
- Proactive alerting
- Regular health checks
- Capacity monitoring
- Performance monitoring
- Security monitoring

### Documentation
- Up-to-date runbooks
- Contact information
- System documentation
- Recovery procedures
- Lessons learned

## Continuous Improvement

### Post-Incident Review
- What happened?
- Why did it happen?
- What did we do well?
- What could we improve?
- Action items

### Regular Reviews
- Monthly: Backup and recovery review
- Quarterly: DR plan update
- Annually: Full DR assessment

### Training
- New hire: DR training
- Annual: DR drill participation
- Ongoing: Runbook updates
