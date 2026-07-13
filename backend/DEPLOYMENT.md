# MatchHire Backend - Production Deployment Guide

This guide covers deploying the MatchHire backend to production.

## Table of Contents

1. [Production Environment Variables](#production-environment-variables)
2. [Docker Deployment](#docker-deployment)
3. [Celery Workers](#celery-workers)
4. [Database Migration](#database-migration)
5. [Collect Static](#collect-static)
6. [Health Endpoints](#health-endpoints)
7. [Production Checklist](#production-checklist)
8. [Recovery Procedure](#recovery-procedure)

---

## Production Environment Variables

The following environment variables must be set in production:

### Required Variables

```bash
# Django Settings
DJANGO_SETTINGS_MODULE=matchhire_backend.settings.prod
SECRET_KEY=<your-secret-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_NAME=matchhire_prod
DB_USER=matchhire_user
DB_PASSWORD=<secure-password>
DB_HOST=postgres
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# JWT
JWT_ACCESS_COOKIE_NAME=access_token
JWT_REFRESH_COOKIE_NAME=refresh_token
```

### Optional Variables

```bash
# Override default Celery result backend if needed
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

---

## Docker Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Docker Compose Configuration

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build: .
    command: gunicorn matchhire_backend.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready/"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery_worker:
    build: .
    command: celery -A matchhire_backend worker -l info --concurrency=4
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  celery_beat:
    build: .
    command: celery -A matchhire_backend beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### Deployment Steps

1. **Create environment file:**
   ```bash
   cp .env.example .env.production
   # Edit .env.production with production values
   ```

2. **Build and start services:**
   ```bash
   docker compose -f docker-compose.prod.yml build
   docker compose -f docker-compose.prod.yml up -d
   ```

3. **Run database migrations:**
   ```bash
   docker compose exec web python manage.py migrate
   ```

4. **Collect static files:**
   ```bash
   docker compose exec web python manage.py collectstatic --noinput
   ```

5. **Create superuser:**
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

---

## Celery Workers

### Worker Configuration

Celery workers handle asynchronous tasks including:
- Resume parsing
- PDF processing
- Email notifications
- Analytics aggregation

### Scaling Workers

Adjust worker count based on load:

```yaml
# For high load
celery_worker:
  command: celery -A matchhire_backend worker -l info --concurrency=8

# For low load
celery_worker:
  command: celery -A matchhire_backend worker -l info --concurrency=2
```

### Monitoring Celery

Monitor Celery with Flower (optional):

```yaml
flower:
  build: .
  command: celery -A matchhire_backend flower --port=5555
  ports:
    - "5555:5555"
  env_file:
    - .env.production
```

---

## Database Migration

### Running Migrations

```bash
# Check for pending migrations
docker compose exec web python manage.py makemigrations --check

# Apply migrations
docker compose exec web python manage.py migrate

# Create migration for model changes
docker compose exec web python manage.py makemigrations
```

### Migration Best Practices

- Always test migrations in staging first
- Never modify applied migrations
- Use `--check` in CI/CD to detect unapplied migrations
- Backup database before major migrations

### Rollback Procedure

```bash
# List migrations
docker compose exec web python manage.py showmigrations

# Rollback to specific migration
docker compose exec web python manage.py migrate <app> <migration_name>
```

---

## Collect Static

### Static Files Collection

```bash
docker compose exec web python manage.py collectstatic --noinput
```

### Static File Serving

In production, serve static files via:
- Nginx (recommended)
- CloudFront/CDN
- Gunicorn (not recommended for production)

### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /app/media/;
        expires 30d;
    }

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Health Endpoints

The backend provides three health endpoints for monitoring:

### `/health/`

General health check. Returns:

```json
{
    "status": "healthy"
}
```

### `/health/live/`

Liveness probe. Checks if the application is running. Returns:

```json
{
    "status": "healthy"
}
```

### `/health/ready/`

Readiness probe. Checks database connectivity. Returns:

```json
{
    "status": "healthy",
    "database": true
}
```

Or if unhealthy:

```json
{
    "status": "unhealthy",
    "database": false
}
```

### Kubernetes Health Checks

```yaml
livenessProbe:
  httpGet:
    path: /health/live/
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready/
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

---

## Production Checklist

### Pre-Deployment

- [ ] All environment variables set in production
- [ ] SECRET_KEY is strong and unique
- [ ] DEBUG=False in production settings
- [ ] ALLOWED_HOSTS configured correctly
- [ ] Database credentials are secure
- [ ] Redis is accessible
- [ ] SSL/TLS certificates configured
- [ ] CORS origins set to production domains
- [ ] Static files collected
- [ ] Database migrations applied
- [ ] Superuser account created

### Post-Deployment

- [ ] Health endpoints responding
- [ ] Database connectivity verified
- [ ] Redis connectivity verified
- [ ] Celery workers running
- [ ] Celery beat running
- [ ] Logs are being generated
- [ ] Request ID middleware working
- [ ] Error logging functional
- [ ] API documentation accessible
- [ ] Admin panel accessible

### Monitoring Setup

- [ ] Application logs monitored
- [ ] Error alerts configured
- [ ] Database performance monitored
- [ ] Redis performance monitored
- [ ] Celery task monitoring
- [ ] Health check monitoring
- [ ] Resource usage alerts

---

## Recovery Procedure

### Database Recovery

1. **Stop application:**
   ```bash
   docker compose stop web celery_worker celery_beat
   ```

2. **Restore from backup:**
   ```bash
   docker compose exec postgres pg_restore -U matchhire_user -d matchhire_prod backup.sql
   ```

3. **Restart application:**
   ```bash
   docker compose start web celery_worker celery_beat
   ```

### Redis Recovery

1. **Flush Redis (if needed):**
   ```bash
   docker compose exec redis redis-cli FLUSHALL
   ```

2. **Restart Celery workers:**
   ```bash
   docker compose restart celery_worker celery_beat
   ```

### Application Rollback

1. **Rollback to previous image:**
   ```bash
   docker compose pull web:<previous-tag>
   docker compose up -d web
   ```

2. **Rollback migrations if needed:**
   ```bash
   docker compose exec web python manage.py migrate <app> <previous_migration>
   ```

### Emergency Procedures

**If application is unresponsive:**

1. Check health endpoints: `curl http://localhost:8000/health/ready/`
2. Check logs: `docker compose logs web`
3. Restart services: `docker compose restart`
4. Check resource usage: `docker stats`

**If database connection fails:**

1. Verify PostgreSQL is running: `docker compose ps postgres`
2. Check database logs: `docker compose logs postgres`
3. Verify credentials in environment variables
4. Test connection: `docker compose exec postgres psql -U matchhire_user -d matchhire_prod`

**If Celery workers fail:**

1. Check worker logs: `docker compose logs celery_worker`
2. Verify Redis is accessible: `docker compose exec redis redis-cli ping`
3. Restart workers: `docker compose restart celery_worker celery_beat`

---

## Logging

### Log Locations

- Application logs: `docker compose logs web`
- Celery logs: `docker compose logs celery_worker`
- Database logs: `docker compose logs postgres`
- Redis logs: `docker compose logs redis`

### Structured Logging Format

Logs include:
- Timestamp
- Log level
- Module name
- Message
- Request ID (for HTTP requests)

Example:
```
ERROR 2024-01-15 10:30:45 matchhire.exceptions Exception | type=ValidationError | user_id=123 | endpoint=/api/v1/jobs/ | method=POST | request_id=abc-123-def | message=Invalid data
```

---

## Security Considerations

1. **Never commit `.env.production` to version control**
2. **Rotate SECRET_KEY regularly**
3. **Use strong database passwords**
4. **Enable SSL/TLS for all connections**
5. **Keep dependencies updated**
6. **Regular security audits**
7. **Monitor for unauthorized access**
8. **Implement rate limiting**
9. **Use HTTPS only in production**
10. **Configure firewall rules**

---

## Support

For deployment issues:
1. Check logs first
2. Verify health endpoints
3. Review this documentation
4. Check Django error pages
5. Review Celery logs
