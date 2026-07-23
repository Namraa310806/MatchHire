# Deployment Guide

## Overview

This guide provides detailed instructions for deploying the MatchHire backend to production environments.

## Prerequisites

### Infrastructure Requirements

- **Server:** 4 vCPUs, 16 GB RAM minimum
- **Storage:** 100 GB SSD
- **Operating System:** Ubuntu 22.04 LTS or equivalent
- **Software:**
  - Docker 24.0+
  - Docker Compose 2.20+
  - Git
  - SSL certificates

### Access Requirements

- SSH access to production server
- Database credentials
- Redis credentials
- Elasticsearch credentials (if using)
- Secret key for Django
- Sentry DSN (optional)

## Pre-Deployment Setup

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER

# Verify installation
docker --version
docker-compose --version
```

### 2. Application Setup

```bash
# Clone repository
git clone <repository-url> /opt/matchhire/backend
cd /opt/matchhire/backend

# Create necessary directories
mkdir -p backups media staticfiles search_indexing_checkpoints logs

# Set permissions
sudo chown -R $USER:$USER /opt/matchhire/backend
chmod -R 755 /opt/matchhire/backend
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

Required environment variables:
```bash
# Django
SECRET_KEY=<generate-strong-secret-key>
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
ENVIRONMENT=production

# Database
DB_NAME=matchhire
DB_USER=matchhire
DB_PASSWORD=<strong-password>
DB_HOST=postgres
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Elasticsearch (optional)
ELASTICSEARCH_HOSTS=http://elasticsearch:9200
SEARCH_PROVIDER=elasticsearch

# CORS
CORS_ALLOWED_ORIGINS=https://your-domain.com

# Monitoring
SENTRY_DSN=<your-sentry-dsn>

# Security
JWT_COOKIE_SECURE=True
```

## Deployment Process

### 1. Build Docker Images

```bash
# Build production images
docker-compose -f docker-compose.production.yml build

# Verify build
docker images | grep matchhire
```

### 2. Database Initialization

```bash
# Start database only
docker-compose -f docker-compose.production.yml up -d postgres

# Wait for database to be ready
docker-compose -f docker-compose.production.yml logs -f postgres

# Run migrations
docker-compose -f docker-compose.production.yml run --rm backend python manage.py migrate

# Create superuser
docker-compose -f docker-compose.production.yml run --rm backend python manage.py createsuperuser
```

### 3. Start Services

```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Verify services are running
docker-compose -f docker-compose.production.yml ps
```

### 4. Static Files

```bash
# Collect static files
docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput

# Verify static files
ls -lh staticfiles/
```

### 5. Cache Warming

```bash
# Warm up cache
docker-compose -f docker-compose.production.yml exec backend python manage.py warmup_cache
```

### 6. Search Indexing

```bash
# Build search index
docker-compose -f docker-compose.production.yml exec backend python manage.py rebuild_search_index
```

## Verification

### Health Checks

```bash
# Check health endpoint
curl http://localhost:8000/health/

# Expected response:
# {
#   "status": "healthy",
#   "checks": [...]
# }
```

### Service Status

```bash
# Check all services
docker-compose -f docker-compose.production.yml ps

# Check logs
docker-compose -f docker-compose.production.yml logs -f backend
docker-compose -f docker-compose.production.yml logs -f postgres
docker-compose -f docker-compose.production.yml logs -f redis
```

### Database Connection

```bash
# Test database connection
docker-compose -f docker-compose.production.yml exec backend python manage.py dbshell
```

### Cache Connection

```bash
# Test Redis connection
docker-compose -f docker-compose.production.yml exec redis redis-cli ping
```

## SSL/TLS Configuration

### Using Nginx

```bash
# Install Nginx
sudo apt install nginx -y

# Obtain SSL certificate (Let's Encrypt)
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com

# Configure Nginx
sudo nano /etc/nginx/sites-available/matchhire
```

Nginx configuration:
```nginx
upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/matchhire/backend/staticfiles/;
    }

    location /media/ {
        alias /opt/matchhire/backend/media/;
    }
}
```

## Monitoring Setup

### Prometheus Metrics

```bash
# Access metrics endpoint
curl http://localhost:8000/metrics/
```

### Sentry Integration

Ensure Sentry DSN is configured in `.env`:
```bash
SENTRY_DSN=https://<key>@sentry.io/<project>
```

### Log Aggregation

```bash
# View logs
docker-compose -f docker-compose.production.yml logs -f

# Configure log rotation
sudo nano /etc/logrotate.d/matchhire
```

## Backup Configuration

### Automated Backups

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * cd /opt/matchhire/backend && docker-compose -f docker-compose.production.yml exec backend python manage.py create_backup

# Weekly backup cleanup
0 3 * * 0 cd /opt/matchhire/backend && docker-compose -f docker-compose.production.yml exec backend python manage.py cleanup_old_backups
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend instances
docker-compose -f docker-compose.production.yml up -d --scale backend=4

# Scale Celery workers
docker-compose -f docker-compose.production.yml up -d --scale celery-worker=4
```

### Vertical Scaling

Update resource limits in `docker-compose.production.yml`:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## Updates and Maintenance

### Zero-Downtime Deployment

```bash
# Pull latest code
git pull origin main

# Build new images
docker-compose -f docker-compose.production.yml build

# Rolling update
docker-compose -f docker-compose.production.yml up -d --no-deps --scale backend=1 backend
# Wait for health check
docker-compose -f docker-compose.production.yml up -d --no-deps --scale backend=2 backend
# Continue until all instances updated
```

### Database Migrations

```bash
# Check for pending migrations
docker-compose -f docker-compose.production.yml exec backend python manage.py showmigrations

# Run migrations
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate

# Verify migration
docker-compose -f docker-compose.production.yml exec backend python manage.py showmigrations
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
# Check database status
docker-compose -f docker-compose.production.yml ps postgres

# Check database logs
docker-compose -f docker-compose.production.yml logs postgres

# Restart database
docker-compose -f docker-compose.production.yml restart postgres
```

### High Memory Usage

```bash
# Check memory usage
docker stats

# Restart services
docker-compose -f docker-compose.production.yml restart backend

# Clear cache
docker-compose -f docker-compose.production.yml exec redis redis-cli FLUSHALL
```

## Security Checklist

- [ ] Strong SECRET_KEY configured
- [ ] DEBUG=False in production
- [ ] ALLOWED_HOSTS configured
- [ ] SSL/TLS enabled
- [ ] Firewall configured
- [ ] Regular security updates
- [ ] Database backups configured
- [ ] Access logs enabled
- [ ] Rate limiting enabled
- [ ] Security headers configured

## Performance Checklist

- [ ] Gunicorn workers optimized
- [ ] Database connection pooling configured
- [ ] Redis caching enabled
- [ ] Static files served via CDN
- [ ] Database indexes optimized
- [ ] N+1 queries eliminated
- [ ] Response time monitoring enabled
- [ ] CDN configured for static assets

## Support

For deployment issues:
- Documentation: docs/production/
- Runbooks: docs/production/runbooks/
- Architecture: docs/production/architecture.md
