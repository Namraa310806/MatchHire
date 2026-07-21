# MatchHire Disaster Recovery Guide

This guide provides procedures for backup, restore, and recovery operations for MatchHire production deployments.

## Table of Contents

1. [Backup Strategy](#backup-strategy)
2. [Database Backup](#database-backup)
3. [Database Restore](#database-restore)
4. [Media Backup](#media-backup)
5. [Media Restore](#media-restore)
6. [Environment Recovery](#environment-recovery)
7. [Deployment Rollback](#deployment-rollback)
8. [Complete Disaster Recovery](#complete-disaster-recovery)

## Backup Strategy

### Backup Schedule

- **Database**: Daily automated backups at 2:00 AM UTC
- **Media Files**: Weekly backups on Sundays at 3:00 AM UTC
- **Configuration**: On any change
- **Retention**: 30 days for daily backups, 90 days for weekly backups

### Backup Locations

- **Local**: `/opt/matchhire/backups/`
- **Remote**: S3 or equivalent cloud storage (recommended)
- **Off-site**: Separate geographic location (recommended)

### Backup Types

1. **Full Database Backup**: Complete PostgreSQL dump
2. **Incremental Media Backup**: Changed files only
3. **Configuration Backup**: Environment files and SSL certificates

## Database Backup

### Automated Daily Backup

Create a backup script at `/opt/matchhire/scripts/backup-db.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/opt/matchhire/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/matchhire_db_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform database backup
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U matchhire_user matchhire_prod > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "matchhire_db_*.sql.gz" -mtime +30 -delete

echo "Database backup completed: $BACKUP_FILE.gz"
```

Make it executable and add to crontab:

```bash
chmod +x /opt/matchhire/scripts/backup-db.sh

# Add to crontab for daily execution at 2:00 AM
crontab -e
# Add: 0 2 * * * /opt/matchhire/scripts/backup-db.sh >> /var/log/matchhire-backup.log 2>&1
```

### Manual Database Backup

```bash
# Create backup directory
mkdir -p backups

# Perform backup
docker compose -f docker-compose.prod.yml exec db pg_dump -U matchhire_user matchhire_prod > backups/matchhire_manual_$(date +%Y%m%d).sql

# Compress
gzip backups/matchhire_manual_$(date +%Y%m%d).sql
```

### Backup to Remote Storage

```bash
# Using AWS S3 (requires awscli)
aws s3 cp backups/matchhire_manual_$(date +%Y%m%d).sql.gz s3://your-bucket/matchhire/backups/

# Using rclone for other providers
rclone copy backups/matchhire_manual_$(date +%Y%m%d).sql.gz remote:matchhire/backups/
```

## Database Restore

### From Local Backup

```bash
# Stop application services
docker compose -f docker-compose.prod.yml stop web celery_worker celery_beat

# Restore database
gunzip -c backups/matchhire_manual_YYYYMMDD.sql.gz | docker compose -f docker-compose.prod.yml exec -T db psql -U matchhire_user matchhire_prod

# Restart services
docker compose -f docker-compose.prod.yml start web celery_worker celery_beat

# Verify
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### From Remote Backup

```bash
# Download backup
aws s3 cp s3://your-bucket/matchhire/backups/matchhire_manual_YYYYMMDD.sql.gz backups/

# Restore using the procedure above
gunzip -c backups/matchhire_manual_YYYYMMDD.sql.gz | docker compose -f docker-compose.prod.yml exec -T db psql -U matchhire_user matchhire_prod
```

### Point-in-Time Recovery (PITR)

For critical situations requiring PITR:

```bash
# This requires WAL archiving to be configured in PostgreSQL
# Contact database administrator for PITR procedures
```

## Media Backup

### Manual Media Backup

```bash
# Backup media files
tar -czf backups/media_$(date +%Y%m%d).tar.gz media/

# Backup static files (if customized)
tar -czf backups/static_$(date +%Y%m%d).tar.gz staticfiles/
```

### Automated Media Backup

Create `/opt/matchhire/scripts/backup-media.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/opt/matchhire/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup media volume
docker run --rm -v matchhire_media_volume_prod:/data -v $BACKUP_DIR:/backup alpine tar -czf /backup/media_$DATE.tar.gz -C /data .

# Backup static volume
docker run --rm -v matchhire_static_volume_prod:/data -v $BACKUP_DIR:/backup alpine tar -czf /backup/static_$DATE.tar.gz -C /data .

echo "Media backup completed"
```

Add to crontab for weekly execution:

```bash
chmod +x /opt/matchhire/scripts/backup-media.sh
# Add to crontab: 0 3 * * 0 /opt/matchhire/scripts/backup-media.sh >> /var/log/matchhire-backup.log 2>&1
```

## Media Restore

### Restore Media Files

```bash
# Extract backup
tar -xzf backups/media_YYYYMMDD.tar.gz -C /tmp/

# Copy to volume
docker run --rm -v matchhire_media_volume_prod:/data -v /tmp/media:/source alpine sh -c "cp -r /source/* /data/"
```

### Restore Static Files

```bash
# Extract backup
tar -xzf backups/static_YYYYMMDD.tar.gz -C /tmp/

# Copy to volume
docker run --rm -v matchhire_static_volume_prod:/data -v /tmp/static:/source alpine sh -c "cp -r /source/* /data/"
```

## Environment Recovery

### Backup Configuration Files

```bash
# Backup environment file
cp .env.production backups/env_production_$(date +%Y%mDD).bak

# Backup SSL certificates
tar -czf backups/ssl_$(date +%Y%mDD).tar.gz nginx/ssl/

# Backup Docker Compose configuration
cp docker-compose.prod.yml backups/
```

### Restore Configuration

```bash
# Restore environment file
cp backups/env_production_YYYYMMDD.bak .env.production

# Restore SSL certificates
tar -xzf backups/ssl_YYYYMMDD.tar.gz -C ./

# Restart services with new configuration
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

## Deployment Rollback

### Rollback to Previous Git Commit

```bash
# View commit history
git log --oneline -10

# Checkout previous commit
git checkout <previous-commit-hash>

# Rebuild and restart
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Run migrations (if needed)
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### Rollback Using Docker Tags

```bash
# Tag current working images
docker compose -f docker-compose.prod.yml ps

# If you have tagged previous versions:
# Edit docker-compose.prod.yml to use previous image tags
# docker compose -f docker-compose.prod.yml up -d
```

## Complete Disaster Recovery

### Scenario 1: Server Failure

1. **Provision new server** with same specifications
2. **Install Docker and Docker Compose** (see deployment guide)
3. **Clone repository** from Git
4. **Restore configuration files** from backup
5. **Restore database** from latest backup
6. **Restore media files** from latest backup
7. **Start services**:
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```
8. **Verify health**:
   ```bash
   curl http://localhost/health/ready/
   ```

### Scenario 2: Database Corruption

1. **Stop application services**:
   ```bash
   docker compose -f docker-compose.prod.yml stop web celery_worker celery_beat
   ```
2. **Identify last good backup**
3. **Restore database** (see Database Restore)
4. **Start services**:
   ```bash
   docker compose -f docker-compose.prod.yml start web celery_worker celery_beat
   ```
5. **Verify data integrity**

### Scenario 3: Ransomware Attack

1. **Immediately isolate** the server from network
2. **Do not pay ransom**
3. **Wipe affected server** completely
4. **Provision clean server**
5. **Restore from known good backups** (pre-attack)
6. **Change all credentials** and secrets
7. **Review security logs** for entry point
8. **Implement additional security measures**

### Scenario 4: Accidental Data Deletion

1. **Stop application services** immediately
2. **Restore database** from backup before deletion
3. **Verify data integrity**
4. **Resume operations**

## Testing Recovery Procedures

### Monthly Recovery Drill

Test backup integrity monthly:

```bash
# Test database restore to temporary database
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U matchhire_user matchhire_prod > /tmp/test_backup.sql
docker compose -f docker-compose.prod.yml exec -T db psql -U matchhire_user -d postgres -c "DROP DATABASE IF EXISTS matchhire_test;"
docker compose -f docker-compose.prod.yml exec -T db psql -U matchhire_user -d postgres -c "CREATE DATABASE matchhire_test;"
docker compose -f docker-compose.prod.yml exec -T db psql -U matchhire_user matchhire_test < /tmp/test_backup.sql
```

### Quarterly Full Recovery Test

Perform complete disaster recovery test on staging environment:

1. Deploy to staging server
2. Restore from production backups
3. Verify all functionality
4. Document any issues
5. Update procedures if needed

## Monitoring Backup Health

### Backup Verification Script

Create `/opt/matchhire/scripts/verify-backups.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR="/opt/matchhire/backups"
ALERT_EMAIL="admin@example.com"

# Check if latest backup exists and is not empty
LATEST_BACKUP=$(ls -t $BACKUP_DIR/matchhire_db_*.sql.gz | head -1)

if [ ! -f "$LATEST_BACKUP" ] || [ ! -s "$LATEST_BACKUP" ]; then
    echo "WARNING: Latest backup is missing or empty!" | mail -s "Backup Alert" $ALERT_EMAIL
    exit 1
fi

# Test backup integrity
if ! gzip -t $LATEST_BACKUP; then
    echo "WARNING: Backup file is corrupted!" | mail -s "Backup Alert" $ALERT_EMAIL
    exit 1
fi

echo "Backup verification passed: $LATEST_BACKUP"
```

## Emergency Contacts

- **Primary Admin**: admin@example.com
- **Database Administrator**: dba@example.com
- **Infrastructure Team**: infra@example.com
- **On-Call Rotation**: oncall@example.com

## Documentation Updates

Keep this document updated:
- After any backup procedure changes
- After any recovery procedure execution
- Quarterly review with team

## Support

For emergency assistance:
- Check logs: `docker compose -f docker-compose.prod.yml logs`
- Review this documentation
- Contact support team
