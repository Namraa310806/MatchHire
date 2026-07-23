# Deployment Runbook

## Overview

This runbook provides step-by-step instructions for deploying the MatchHire backend to production.

## Prerequisites

- Docker and Docker Compose installed
- Access to production server
- Environment variables configured
- Database backup completed
- SSH access to production server

## Pre-Deployment Checklist

- [ ] All tests passing in CI/CD
- [ ] Security scan completed with no critical issues
- [ ] Database migrations reviewed
- [ ] Backup created before deployment
- [ ] Feature flags configured
- [ ] Environment variables validated
- [ ] Rollback plan prepared

## Deployment Steps

### 1. Prepare Environment

```bash
# SSH into production server
ssh user@production-server

# Navigate to application directory
cd /opt/matchhire/backend

# Pull latest code
git pull origin main

# Verify commit
git log -1
```

### 2. Update Environment Variables

```bash
# Verify .env file
cat .env

# Update if needed
nano .env
```

### 3. Build and Deploy

```bash
# Stop existing services
docker-compose -f docker-compose.production.yml down

# Build new images
docker-compose -f docker-compose.production.yml build

# Start services
docker-compose -f docker-compose.production.yml up -d

# Verify services are running
docker-compose -f docker-compose.production.yml ps
```

### 4. Run Migrations

```bash
# Run database migrations
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate

# Verify migration status
docker-compose -f docker-compose.production.yml exec backend python manage.py showmigrations
```

### 5. Collect Static Files

```bash
# Collect static files
docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
```

### 6. Verify Deployment

```bash
# Check health endpoint
curl http://localhost:8000/health/

# Check logs
docker-compose -f docker-compose.production.yml logs -f backend

# Check service health
docker-compose -f docker-compose.production.yml ps
```

### 7. Warm Up Cache

```bash
# Execute cache warmup
docker-compose -f docker-compose.production.yml exec backend python manage.py warmup_cache
```

## Post-Deployment Verification

- [ ] Health endpoint returning healthy
- [ ] Database connectivity verified
- [ ] Cache connectivity verified
- [ ] Search functionality working
- [ ] API endpoints responding
- [ ] No errors in logs
- [ ] Metrics being collected

## Rollback Procedure

If deployment fails:

```bash
# Stop new deployment
docker-compose -f docker-compose.production.yml down

# Restore previous version
git checkout <previous-commit-hash>

# Rebuild and start
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d

# Restore database if needed
docker-compose -f docker-compose.production.yml exec backend python manage.py restore_backup <backup-file>
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.production.yml logs backend

# Check resource usage
docker stats

# Check disk space
df -h
```

### Database Connection Issues

```bash
# Verify database is running
docker-compose -f docker-compose.production.yml ps postgres

# Check database logs
docker-compose -f docker-compose.production.yml logs postgres

# Test connection
docker-compose -f docker-compose.production.yml exec backend python manage.py dbshell
```

### Cache Connection Issues

```bash
# Verify Redis is running
docker-compose -f docker-compose.production.yml ps redis

# Check Redis logs
docker-compose -f docker-compose.production.yml logs redis

# Test connection
docker-compose -f docker-compose.production.yml exec redis redis-cli ping
```

## Emergency Contacts

- Platform Lead: [contact]
- Database Admin: [contact]
- DevOps Engineer: [contact]
