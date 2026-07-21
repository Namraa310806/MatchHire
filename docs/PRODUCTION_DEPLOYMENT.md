# MatchHire Production Deployment Guide

This guide covers deploying MatchHire to production using Docker Compose on a Linux server.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Preparation](#server-preparation)
3. [Environment Configuration](#environment-configuration)
4. [Deployment](#deployment)
5. [Health Checks](#health-checks)
6. [Scaling Services](#scaling-services)
7. [Updating Deployments](#updating-deployments)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### Server Requirements

- **OS**: Ubuntu 22.04 LTS or equivalent Linux distribution
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB+ SSD
- **Network**: Public IP with ports 80 and 443 open

### Software Requirements

- Docker Engine 24.0+
- Docker Compose 2.20+
- Git
- SSL certificate (Let's Encrypt recommended)

## Server Preparation

### 1. Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

### 2. Configure Firewall

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. Clone Repository

```bash
git clone <your-repository-url> /opt/matchhire
cd /opt/matchhire
```

### 4. Create Required Directories

```bash
mkdir -p backups
mkdir -p nginx/ssl
```

## Environment Configuration

### 1. Create Production Environment File

```bash
cp .env.production.example .env.production
nano .env.production
```

### 2. Configure Required Variables

Edit `.env.production` with your actual values:

```bash
# Generate a strong secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Set the following variables:
SECRET_KEY=<generated-secret-key>
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database credentials
DB_NAME=matchhire_prod
DB_USER=matchhire_user
DB_PASSWORD=<strong-password>
```

### 3. Generate SSL Certificates (Optional but Recommended)

```bash
# Using Let's Encrypt with Certbot
sudo apt install certbot -y
sudo certbot certonly --standalone -d your-domain.com
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
sudo chmod 644 nginx/ssl/*.pem
```

## Deployment

### 1. Build Production Images

```bash
docker compose -f docker-compose.prod.yml build
```

### 2. Start Services

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 3. Run Database Migrations

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### 4. Collect Static Files

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### 5. Create Superuser (Optional)

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 6. Verify Deployment

```bash
# Check all services are running
docker compose -f docker-compose.prod.yml ps

# Check logs
docker compose -f docker-compose.prod.yml logs -f

# Test health endpoint
curl http://localhost/health
curl http://localhost/health/ready/
```

## Health Checks

### Built-in Health Endpoints

- **General Health**: `GET /health/`
- **Liveness**: `GET /health/live/`
- **Readiness**: `GET /health/ready/`
- **Version**: `GET /version/`

### Docker Health Checks

All services include built-in health checks:

```bash
# Check service health
docker compose -f docker-compose.prod.yml ps

# View health check logs
docker inspect matchhire_web_prod --format='{{json .State.Health}}'
```

## Scaling Services

### Scale Web Workers

```bash
# Edit docker-compose.prod.yml and deploy with a load balancer
# For horizontal scaling, use multiple instances behind a load balancer
```

### Scale Celery Workers

```bash
# Edit docker-compose.prod.yml to add more worker services
# Example:
celery_worker_2:
  <<: *celery_worker
  container_name: matchhire_celery_worker_2_prod
```

## Updating Deployments

### Zero-Downtime Deployment Strategy

```bash
# 1. Pull latest code
git pull origin main

# 2. Build new images
docker compose -f docker-compose.prod.yml build

# 3. Run migrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# 4. Collect static files
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# 5. Restart services gracefully
docker compose -f docker-compose.prod.yml up -d --no-deps --build web celery_worker celery_beat

# 6. Verify health
curl http://localhost/health/ready/
```

### Rollback Strategy

```bash
# Revert to previous commit
git checkout <previous-commit-hash>

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build
```

## Monitoring

### View Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f web

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 web
```

### Resource Monitoring

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Volume usage
docker volume ls
docker volume inspect matchhire_postgres_data_prod
```

## Troubleshooting

### Common Issues

#### Database Connection Failed

```bash
# Check database health
docker compose -f docker-compose.prod.yml exec db pg_isready

# View database logs
docker compose -f docker-compose.prod.yml logs db
```

#### Redis Connection Failed

```bash
# Check Redis health
docker compose -f docker-compose.prod.yml exec redis redis-cli ping

# View Redis logs
docker compose -f docker-compose.prod.yml logs redis
```

#### Service Not Starting

```bash
# Check service logs
docker compose -f docker-compose.prod.yml logs <service-name>

# Inspect container
docker inspect matchhire_<service>_prod

# Restart service
docker compose -f docker-compose.prod.yml restart <service-name>
```

#### Permission Issues

```bash
# Fix volume permissions
docker compose -f docker-compose.prod.yml down
sudo chown -R 1000:1000 /var/lib/docker/volumes/
docker compose -f docker-compose.prod.yml up -d
```

## Security Best Practices

1. **Never commit `.env.production`** to version control
2. **Use strong passwords** for database and Redis
3. **Enable SSL/TLS** for all connections
4. **Keep Docker images updated** regularly
5. **Restrict network access** using firewall rules
6. **Monitor logs** for suspicious activity
7. **Regular backups** of database and media files
8. **Use secrets management** for sensitive data in production

## Maintenance

### Regular Tasks

- **Daily**: Check logs and service health
- **Weekly**: Review disk usage and clean up old logs
- **Monthly**: Update Docker images and dependencies
- **Quarterly**: Review and rotate secrets/certificates

### Clean Up Old Resources

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes (careful!)
docker volume prune

# Remove unused networks
docker network prune
```

## Support

For issues or questions:
- Check logs: `docker compose -f docker-compose.prod.yml logs`
- Review documentation in `/docs`
- Open an issue on GitHub
