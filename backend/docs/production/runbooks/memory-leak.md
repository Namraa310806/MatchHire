# Memory Leak Runbook

## Severity
High

## Symptoms
- Gradual memory increase over time
- OOM (Out of Memory) kills
- Container restarts
- High memory usage (>90%)

## Immediate Actions

### 1. Check Memory Usage
```bash
# Check container memory usage
docker stats matchhire-backend

# Check memory within container
docker exec matchhire-backend free -h

# Check Python memory usage
docker exec matchhire-backend python -c "import psutil; print(psutil.virtual_memory())"
```

### 2. Check for Memory Leaks
```bash
# Enable memory profiling
# Set feature flag: performance.profiling = True

# Run memory leak detection
python manage.py detect_memory_leaks
```

### 3. Restart Affected Services
```bash
# Restart to free memory
docker-compose restart backend celery-worker celery-beat
```

### 4. Check Memory Limits
```bash
# Check Docker memory limits
docker inspect matchhire-backend | grep -i memory
```

## Root Cause Analysis

### Check Memory Patterns
- Gradual increase (likely leak)
- Sudden spikes (likely large operations)
- Periodic increases (likely periodic tasks)

### Common Causes
1. **Unclosed connections** - Database/cache connections not closed
2. **Circular references** - Python object cycles
3. **Large object caching** - Caching too much data
4. **Background task accumulation** - Celery task results not cleaned

## Resolution Steps

### For Connection Leaks
```bash
# Check connection pool settings
# Ensure connections are properly closed in code
# Use context managers for connections
```

### For Large Object Caching
```bash
# Check cache size
docker exec matchhire-redis redis-cli INFO memory

# Clear cache if needed
docker exec matchhire-redis redis-cli FLUSHALL

# Adjust cache TTL values
# Implement cache size limits
```

### For Background Task Accumulation
```bash
# Check Celery task results
docker exec matchhire-celery-worker celery -A matchhire_backend.celery inspect active

# Clean up old task results
# Set CELERY_TASK_RESULT_EXPIRES
```

## Prevention
- Enable memory profiling in production
- Set up memory usage alerts
- Regular memory leak detection
- Use connection pooling
- Implement cache size limits
- Clean up task results
- Use weak references where appropriate
- Profile code before deployment

## Escalation
- If unresolved in 30 minutes: Escalate to engineering team
- If frequent OOM: Request memory increase
- If persistent leaks: Code review required
