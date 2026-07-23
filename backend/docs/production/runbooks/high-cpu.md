# High CPU Usage Runbook

## Severity
Medium

## Symptoms
- High CPU utilization (>80%)
- Slow response times
- Increased latency
- System load alerts

## Immediate Actions

### 1. Identify High CPU Processes
```bash
# Check container CPU usage
docker stats

# Check process CPU usage within container
docker exec matchhire-backend top -b -n 1 | head -20

# Check Python processes
docker exec matchhire-backend ps aux | grep python
```

### 2. Check Application Metrics
```bash
# Check request rate
docker logs matchhire-backend | grep -i "request" | tail -100

# Check for long-running operations
docker logs matchhire-backend | grep -i "slow\|timeout"
```

### 3. Scale Application
```bash
# Scale horizontally to distribute load
docker-compose up -d --scale backend=3
docker-compose up -d --scale celery-worker=3
```

### 4. Enable Rate Limiting
```bash
# Rate limiting is already enabled via middleware
# Check rate limit configuration
docker logs matchhire-backend | grep -i "rate limit"
```

## Root Cause Analysis

### Check System Metrics
- CPU per core utilization
- Context switch rate
- System vs user CPU time
- I/O wait time

### Common Causes
1. **High request rate** - Scale horizontally
2. **Inefficient queries** - Optimize database queries
3. **CPU-intensive operations** - Offload to background tasks
4. **Memory pressure causing swapping** - Add memory or optimize

## Resolution Steps

### For High Request Rate
```bash
# Scale services
docker-compose up -d --scale backend=5 --scale celery-worker=5

# Enable caching (if not already)
# Check cache hit rate
docker exec matchhire-redis redis-cli INFO stats | grep keyspace
```

### For Inefficient Operations
```bash
# Enable performance profiling
# Set feature flag: performance.profiling = True

# Run benchmarks to identify bottlenecks
python manage.py benchmark_search
python manage.py benchmark_ranking
```

### For Memory Pressure
```bash
# Check memory usage
docker stats matchhire-backend

# If swapping, add memory or optimize memory usage
# Check for memory leaks using memory_profiler
```

## Prevention
- Set up CPU usage alerts
- Implement auto-scaling
- Use caching to reduce CPU load
- Optimize database queries
- Profile and optimize code
- Use connection pooling
- Implement rate limiting

## Escalation
- If unresolved in 20 minutes: Escalate to platform team
- If persistent high CPU: Review architecture
- If need more resources: Request capacity increase
