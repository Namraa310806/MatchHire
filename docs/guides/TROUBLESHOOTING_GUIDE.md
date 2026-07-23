# MatchHire Troubleshooting Guide

This guide provides solutions to common issues encountered when setting up, running, or deploying MatchHire.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Docker Issues](#docker-issues)
3. [Database Issues](#database-issues)
4. [Search Issues](#search-issues)
5. [Performance Issues](#performance-issues)
6. [Frontend Issues](#frontend-issues)
7. [Backend Issues](#backend-issues)
8. [Deployment Issues](#deployment-issues)
9. [Testing Issues](#testing-issues)

## Installation Issues

### Python Version Mismatch

**Problem**: `ModuleNotFoundError` or import errors after installation.

**Solution**:
```bash
# Check Python version
python --version  # Should be 3.11+

# Install correct Python version
# On macOS with Homebrew
brew install python@3.11

# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv

# On Windows
# Download from https://www.python.org/downloads/
```

### Node.js Version Mismatch

**Problem**: Frontend build fails with dependency errors.

**Solution**:
```bash
# Check Node.js version
node --version  # Should be 18+

# Install correct Node.js version
# On macOS with Homebrew
brew install node@20

# On Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# On Windows
# Download from https://nodejs.org/
```

### Dependency Installation Failures

**Problem**: `pip install` or `npm install` fails.

**Solution**:
```bash
# Backend dependencies
cd backend
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir

# Frontend dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install --force
```

## Docker Issues

### Container Won't Start

**Problem**: Docker containers fail to start or crash immediately.

**Solution**:
```bash
# Check container logs
docker compose logs web
docker compose logs db
docker compose logs redis

# Check container status
docker compose ps

# Restart containers
docker compose down
docker compose up -d

# Rebuild containers
docker compose down
docker compose up --build -d
```

### Port Conflicts

**Problem**: `Port is already allocated` error.

**Solution**:
```bash
# Check what's using the port
# On macOS/Linux
lsof -i :8000
lsof -i :5432
lsof -i :6379

# On Windows
netstat -ano | findstr :8000

# Change ports in docker-compose.yml
# Or stop conflicting services
```

### Out of Memory

**Problem**: Containers crash due to insufficient memory.

**Solution**:
```bash
# Increase Docker memory allocation
# Docker Desktop → Settings → Resources → Memory
# Set to at least 8GB

# Check container resource usage
docker stats

# Reduce container memory limits in docker-compose.yml
```

### Volume Permission Issues

**Problem**: Permission denied errors when accessing volumes.

**Solution**:
```bash
# On Linux, fix permissions
sudo chown -R $USER:$USER .

# On Windows, ensure WSL2 is configured correctly
# Docker Desktop → Settings → Resources → WSL Integration
```

## Database Issues

### Database Connection Refused

**Problem**: `could not connect to server: Connection refused`.

**Solution**:
```bash
# Check if PostgreSQL container is running
docker compose ps db

# Check PostgreSQL logs
docker compose logs db

# Wait for database to be ready
docker compose exec db pg_isready -U matchhire

# Restart database container
docker compose restart db

# Check database connection from web container
docker compose exec web python manage.py check --database default
```

### Migration Errors

**Problem**: Database migrations fail or get stuck.

**Solution**:
```bash
# Check current migration status
docker compose exec web python manage.py showmigrations

# Fake initial migration if needed
docker compose exec web python manage.py migrate --fake-initial

# Reset migrations (WARNING: This deletes data)
docker compose exec web python manage.py migrate zero
docker compose exec web python manage.py migrate

# Create new migrations
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

### Database Lock Issues

**Problem**: `database is locked` or deadlocks.

**Solution**:
```bash
# Check for long-running transactions
docker compose exec db psql -U matchhire -d matchhire -c "SELECT * FROM pg_stat_activity WHERE state != 'idle';"

# Kill stuck connections
docker compose exec db psql -U matchhire -d matchhire -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state != 'idle';"

# Restart database
docker compose restart db
```

## Search Issues

### Elasticsearch Connection Failed

**Problem**: Cannot connect to Elasticsearch.

**Solution**:
```bash
# Check if Elasticsearch is running
docker compose ps elasticsearch

# Check Elasticsearch logs
docker compose logs elasticsearch

# Test Elasticsearch connection
curl -X GET "localhost:9200/_cluster/health"

# Restart Elasticsearch
docker compose restart elasticsearch
```

### Search Returns No Results

**Problem**: Search queries return empty results.

**Solution**:
```bash
# Check if documents are indexed
curl -X GET "localhost:9200/jobs/_search?pretty"

# Rebuild search indexes
docker compose exec web python manage.py search_index --action rebuild

# Index specific models
docker compose exec web python manage.py search_index --model jobs.Job --action index
docker compose exec web python manage.py search_index --model users.CandidateProfile --action index

# Check search configuration
docker compose exec web python manage.py check
```

### Search Performance Issues

**Problem**: Search queries are slow.

**Solution**:
```bash
# Check Elasticsearch cluster health
curl -X GET "localhost:9200/_cluster/health?pretty"

# Check index statistics
curl -X GET "localhost:9200/jobs/_stats?pretty"

# Optimize indexes
curl -X POST "localhost:9200/jobs/_forcemerge?max_num_segments=1"

# Increase Elasticsearch memory in docker-compose.yml
```

## Performance Issues

### Slow API Response Times

**Problem**: API endpoints take too long to respond.

**Solution**:
```bash
# Check database query performance
docker compose exec web python manage.py debugsqlshell

# Enable query logging in settings
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}

# Add database indexes
docker compose exec web python manage.py db_index

# Use Django Debug Toolbar for development
pip install django-debug-toolbar
```

### High Memory Usage

**Problem**: Application consumes too much memory.

**Solution**:
```bash
# Check memory usage
docker stats

# Reduce Gunicorn workers
# In gunicorn.conf.py
workers = multiprocessing.cpu_count()  # Reduce from 2*CPU+1

# Enable connection pooling
# In settings.py
CONN_MAX_AGE = 600

# Clear Redis cache
docker compose exec redis redis-cli FLUSHALL
```

### Slow Frontend Load Times

**Problem**: Frontend takes too long to load.

**Solution**:
```bash
# Build production bundle
cd frontend
npm run build

# Enable code splitting
# Check vite.config.ts for manualChunks configuration

# Analyze bundle size
npm run build -- --mode production
# Open dist/stats.html in browser

# Enable caching in nginx
# Check nginx configuration for cache headers
```

## Frontend Issues

### Build Fails

**Problem**: `npm run build` fails with errors.

**Solution**:
```bash
# Clear cache
rm -rf node_modules .vite dist
npm install

# Check TypeScript errors
npm run typecheck

# Check for dependency conflicts
npm audit fix

# Try building with verbose output
npm run build -- --debug
```

### Runtime Errors in Browser

**Problem**: Application shows errors in browser console.

**Solution**:
```bash
# Check browser console (F12)
# Look for specific error messages

# Check network tab for failed API calls
# Verify API URL is correct

# Clear browser cache and localStorage
# Or use incognito mode

# Check environment variables
# Ensure VITE_API_URL is set correctly
```

### Hot Module Replacement Not Working

**Problem**: Changes don't reflect in development server.

**Solution**:
```bash
# Restart dev server
cd frontend
npm run dev

# Check Vite configuration
# Ensure HMR is enabled in vite.config.ts

# Clear Vite cache
rm -rf node_modules/.vite
```

## Backend Issues

### Import Errors

**Problem**: `ModuleNotFoundError` for Django apps.

**Solution**:
```bash
# Check PYTHONPATH
echo $PYTHONPATH

# Set PYTHONPATH
export PYTHONPATH=/app/backend

# Check Django settings
docker compose exec web python manage.py check --settings=matchhire_backend.settings.development

# Reinstall dependencies
docker compose exec web pip install -r requirements.txt --force-reinstall
```

### Celery Tasks Not Running

**Problem**: Background tasks don't execute.

**Solution**:
```bash
# Check Celery worker status
docker compose logs celery_worker

# Check Celery beat status
docker compose logs celery_beat

# Restart Celery services
docker compose restart celery_worker celery_beat

# Check Redis connection
docker compose exec redis redis-cli ping

# Inspect active tasks
docker compose exec web celery -A matchhire_backend inspect active
```

### Static Files Not Loading

**Problem**: CSS/JS files return 404.

**Solution**:
```bash
# Collect static files
docker compose exec web python manage.py collectstatic --noinput

# Check static files directory
docker compose exec web ls -la /app/backend/staticfiles

# Check nginx configuration
# Ensure static files path is correct

# Restart nginx
docker compose restart nginx
```

## Deployment Issues

### AWS Deployment Fails

**Problem**: ECS tasks fail to start on AWS.

**Solution**:
```bash
# Check CloudWatch logs
aws logs tail /ecs/matchhire-backend --follow

# Check task definition
aws ecs describe-task-definition --task-definition matchhire-backend

# Check container insights
aws ecs describe-tasks --cluster matchhire-cluster --tasks <task-id>

# Verify security groups allow traffic
aws ec2 describe-security-groups --group-ids <sg-id>

# Check IAM roles have proper permissions
aws iam get-role-policy --role-name matchhire-ecs-task-role --policy-name <policy-name>
```

### SSL Certificate Issues

**Problem**: HTTPS not working or certificate errors.

**Solution**:
```bash
# Request ACM certificate
aws acm request-certificate \
  --domain-name matchhire.com \
  --validation-method DNS

# Validate certificate
# Add CNAME records to Route53

# Update nginx configuration
# Ensure SSL paths are correct

# Test SSL configuration
openssl s_client -connect matchhire.com:443
```

### Database Connection in Production

**Problem**: Cannot connect to RDS in production.

**Solution**:
```bash
# Check RDS instance status
aws rds describe-db-instances --db-instance-identifier matchhire-db

# Check security group allows ECS access
aws ec2 describe-security-groups --group-ids <sg-id>

# Test connection from ECS task
docker compose exec web psql -h <rds-endpoint> -U matchhire -d matchhire

# Check VPC configuration
# Ensure ECS and RDS are in same VPC
```

## Testing Issues

### Tests Fail Locally

**Problem**: Unit tests pass but integration tests fail.

**Solution**:
```bash
# Run tests with verbose output
docker compose exec web python manage.py test --verbosity=2

# Run specific test
docker compose exec web python manage.py test apps.jobs.tests.test_models

# Check test database
docker compose exec web python manage.py test --settings=matchhire_backend.settings.test

# Clear test database
docker compose exec web python manage.py test --flush
```

### E2E Tests Fail

**Problem**: Playwright tests fail in CI.

**Solution**:
```bash
# Run tests locally
cd frontend
npx playwright test

# Run with debug mode
npx playwright test --debug

# Check browser installation
npx playwright install --with-deps chromium

# Increase timeout in playwright.config.ts
```

### Coverage Reports Missing

**Problem**: Coverage reports not generated.

**Solution**:
```bash
# Run tests with coverage
docker compose exec web coverage run --source='.' manage.py test
docker compose exec web coverage report
docker compose exec web coverage html

# Check .coveragerc configuration
# Ensure correct paths are included
```

## Getting Help

If you're still experiencing issues after trying these solutions:

1. **Check the logs**: Always check container logs first
2. **Search existing issues**: Check GitHub Issues for similar problems
3. **Create a minimal reproducible example**: Isolate the problem
4. **Provide detailed information**: Include error messages, logs, and environment details
5. **Contact support**: See [SUPPORT.md](../SUPPORT.md) for support options

## Additional Resources

- [Developer Guide](../development/developer-guide.md)
- [Deployment Guide](../deployment/)
- [API Documentation](../api/)
- [Demo Guide](DEMO_GUIDE.md)
