# Backup & Recovery Guide

## Overview

This guide covers backup and recovery procedures for the MatchHire backend production deployment.

## Backup Strategy

### Database Backups (PostgreSQL)

**Backup Frequency:**
- Daily full backups at 2:00 AM UTC
- Hourly incremental backups (WAL archiving)
- Retention: 7 days daily, 4 weeks weekly, 12 months monthly

**Manual Backup:**
```bash
# Full database backup
docker exec matchhire_db_prod pg_dump -U matchhire matchhire > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
docker exec matchhire_db_prod pg_dump -U matchhire matchhire | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

**Automated Backup Script:**
```bash
#!/bin/bash
# scripts/backup_db.sh

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/matchhire_$TIMESTAMP.sql.gz"

mkdir -p $BACKUP_DIR

# Create backup
docker exec matchhire_db_prod pg_dump -U matchhire matchhire | gzip > $BACKUP_FILE

# Retention policy (keep last 7 days)
find $BACKUP_DIR -name "matchhire_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
```

**Cron Job:**
```cron
0 2 * * * /path/to/scripts/backup_db.sh >> /var/log/backup.log 2>&1
```

### Redis Backups

**Current Configuration:**
- Redis persistence: AOF (Append Only File) enabled
- Max memory: 256MB with LRU eviction policy
- Data directory: `/data` (Docker volume)

**Manual Backup:**
```bash
# Trigger AOF rewrite
docker exec matchhire_redis_prod redis-cli BGREWRITEAOF

# Copy AOF file
docker cp matchhire_redis_prod:/data/appendonly.aof /backups/redis/appendonly_$(date +%Y%m%d_%H%M%S).aof
```

**Automated Backup Script:**
```bash
#!/bin/bash
# scripts/backup_redis.sh

BACKUP_DIR="/backups/redis"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/appendonly_$TIMESTAMP.aof"

mkdir -p $BACKUP_DIR

# Trigger AOF rewrite
docker exec matchhire_redis_prod redis-cli BGREWRITEAOF

# Wait for rewrite to complete
sleep 5

# Copy AOF file
docker cp matchhire_redis_prod:/data/appendonly.aof $BACKUP_FILE

# Retention policy (keep last 7 days)
find $BACKUP_DIR -name "appendonly_*.aof" -mtime +7 -delete

echo "Redis backup completed: $BACKUP_FILE"
```

### Media File Backups

**Media Directory:**
- Location: `/app/backend/media` (Docker volume)
- Content: User-uploaded resumes, profile pictures

**Manual Backup:**
```bash
# Create tar archive
docker run --rm -v media_volume_prod:/data -v /backups:/backup alpine tar czf /backup/media_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

# Using rsync for incremental backups
rsync -avz --delete /path/to/media/ /backups/media/
```

**Automated Backup Script:**
```bash
#!/bin/bash
# scripts/backup_media.sh

BACKUP_DIR="/backups/media"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/media_$TIMESTAMP.tar.gz"

mkdir -p $BACKUP_DIR

# Create archive
docker run --rm -v media_volume_prod:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/media_$TIMESTAMP.tar.gz -C /data .

# Retention policy (keep last 7 days)
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +7 -delete

echo "Media backup completed: $BACKUP_FILE"
```

## Restore Procedures

### Database Restore

**From SQL Backup:**
```bash
# Stop application
docker-compose -f docker-compose.prod.yml stop web celery_worker celery_beat

# Restore database
docker exec -i matchhire_db_prod psql -U matchhire matchhire < backup_20260101_020000.sql

# Or from compressed backup
gunzip -c backup_20260101_020000.sql.gz | docker exec -i matchhire_db_prod psql -U matchhire matchhire

# Restart application
docker-compose -f docker-compose.prod.yml start web celery_worker celery_beat
```

**Point-in-Time Recovery (PITR):**
```bash
# Stop PostgreSQL
docker-compose -f docker-compose.prod.yml stop db

# Restore base backup
docker run --rm -v postgres_data_prod:/var/lib/postgresql/data -v /backups:/backup alpine sh -c "rm -rf /var/lib/postgresql/data/* && tar xzf /backup/base_backup.tar.gz -C /var/lib/postgresql/data"

# Copy WAL files
docker run --rm -v postgres_data_prod:/var/lib/postgresql/data -v /backups/wal:/backup alpine sh -c "cp /backup/*.wal /var/lib/postgresql/data/pg_wal/"

# Create recovery.conf
docker run --rm -v postgres_data_prod:/var/lib/postgresql/data alpine sh -c "echo 'restore_command = \"cp /backups/wal/%f %p\"' > /var/lib/postgresql/data/recovery.conf"

# Start PostgreSQL
docker-compose -f docker-compose.prod.yml start db
```

### Redis Restore

**From AOF Backup:**
```bash
# Stop Redis
docker-compose -f docker-compose.prod.yml stop redis

# Copy backup file
docker cp /backups/redis/appendonly_20260101_020000.aof matchhire_redis_prod:/data/appendonly.aof

# Start Redis
docker-compose -f docker-compose.prod.yml start redis
```

### Media Restore

**From Tar Archive:**
```bash
# Extract archive to volume
docker run --rm -v media_volume_prod:/data -v /backups:/backup alpine sh -c "rm -rf /data/* && tar xzf /backup/media_20260101_020000.tar.gz -C /data"
```

## Backup Verification

### Database Integrity Check

```bash
# Check backup file integrity
docker exec matchhire_db_prod pg_restore --list backup_20260101_020000.sql

# Test restore to temporary database
docker exec matchhire_db_prod psql -U matchhire -c "CREATE DATABASE test_restore;"
docker exec -i matchhire_db_prod psql -U matchhire test_restore < backup_20260101_020000.sql
docker exec matchhire_db_prod psql -U matchhire -c "DROP DATABASE test_restore;"
```

### Redis Integrity Check

```bash
# Check AOF file
docker exec matchhire_redis_prod redis-cli AOFCHECK
```

### Media Integrity Check

```bash
# Verify archive
tar tzf media_20260101_020000.tar.gz | head -20

# Test extraction
tar xzf media_20260101_020000.tar.gz -C /tmp/test_media
```

## Disaster Recovery

### Scenario 1: Complete Data Loss

**Steps:**
1. Provision new infrastructure
2. Install Docker and Docker Compose
3. Clone repository
4. Configure environment variables
5. Start infrastructure services (db, redis)
6. Restore latest database backup
7. Restore Redis backup
8. Restore media backup
9. Start application services
10. Verify health checks
11. Update DNS if needed

**Estimated Recovery Time:** 2-4 hours

### Scenario 2: Database Corruption

**Steps:**
1. Stop application services
2. Stop PostgreSQL
3. Restore from last known good backup
4. Start PostgreSQL
5. Verify database integrity
6. Start application services
7. Monitor for errors

**Estimated Recovery Time:** 30-60 minutes

### Scenario 3: Media Volume Failure

**Steps:**
1. Stop application services
2. Create new media volume
3. Restore from backup
4. Update volume references
5. Start application services
6. Verify file access

**Estimated Recovery Time:** 30-45 minutes

## Backup Testing Schedule

**Weekly:**
- Verify backup files exist
- Check backup file sizes
- Test database restore to temporary database

**Monthly:**
- Full disaster recovery drill
- Document any issues
- Update procedures if needed

**Quarterly:**
- Review retention policies
- Update backup scripts if needed
- Test off-site backup restoration

## Off-Site Backup

**Recommended Strategy:**
- Sync backups to cloud storage (AWS S3, Google Cloud Storage, Azure Blob)
- Use encryption for sensitive data
- Implement lifecycle policies for cost optimization

**Example (AWS S3):**
```bash
# Sync to S3
aws s3 sync /backups/ s3://matchhire-backups/$(date +%Y/%m/%d)/ --storage-class STANDARD_IA

# Lifecycle policy (via AWS Console or CLI)
# Transition to Glacier after 30 days
# Delete after 1 year
```

## Monitoring

**Metrics to Monitor:**
- Backup job success/failure
- Backup file sizes
- Backup duration
- Disk space usage
- Restore test results

**Alerting:**
- Alert on backup job failure
- Alert on disk space < 20%
- Alert on backup duration > 2x normal

## Compliance

**Data Retention:**
- Follow GDPR requirements for user data
- Implement data anonymization for long-term backups
- Document data retention policies

**Backup Security:**
- Encrypt backups at rest
- Restrict backup access to authorized personnel
- Use secure transfer protocols
- Audit backup access logs

## References

- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- [Redis Persistence Documentation](https://redis.io/docs/manual/persistence/)
- [Docker Volume Backup](https://docs.docker.com/storage/volumes/#backup-restore-or-migrate-data-volumes)
