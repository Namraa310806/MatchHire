# Capacity Planning Guide

## Overview

This guide provides capacity planning recommendations for the MatchHire backend in production.

## Baseline Metrics

### Single Instance Capacity

- **CPU:** 2 vCPUs
- **Memory:** 4 GB RAM
- **Database Connections:** 100 max
- **Concurrent Requests:** 500
- **Throughput:** ~100 RPS per instance

### Service Requirements

| Service | CPU | Memory | Storage |
|---------|-----|--------|---------|
| Backend | 2 vCPUs | 4 GB | 20 GB |
| PostgreSQL | 4 vCPUs | 8 GB | 100 GB |
| Redis | 1 vCPU | 2 GB | 10 GB |
| Elasticsearch | 2 vCPUs | 4 GB | 50 GB |
| Celery Worker | 1 vCPU | 2 GB | 10 GB |

## Scaling Strategies

### Horizontal Scaling

**Backend:**
- Start with 2 instances
- Scale based on CPU > 70%
- Target: 4-6 instances for production
- Use load balancer for distribution

**Celery Workers:**
- Start with 2 workers
- Scale based on queue length
- Target: 4-8 workers for production
- Separate queues for different task types

### Vertical Scaling

**Database:**
- Start with 4 vCPUs, 8 GB RAM
- Scale based on connection pool usage
- Target: 8 vCPUs, 16 GB RAM for high load
- Consider read replicas for read-heavy workloads

**Redis:**
- Start with 1 vCPU, 2 GB RAM
- Scale based on memory usage
- Target: 2 vCPUs, 4 GB RAM for production
- Consider Redis Cluster for high availability

## Capacity Planning Calculations

### User Growth Model

**Assumptions:**
- 1,000 active users initially
- 10% month-over-month growth
- 10 requests per user per day
- Peak traffic: 5x average

**Formula:**
```
Monthly Users = Initial Users × (1 + Growth Rate)^Months
Peak RPS = (Monthly Users × Requests Per User / Days In Month) × Peak Factor / Seconds In Day
```

**Example:**
```
Month 1: 1,000 users → ~0.6 RPS peak
Month 6: 1,771 users → ~1.0 RPS peak
Month 12: 3,138 users → ~1.8 RPS peak
```

### Instance Sizing

**Required Instances:**
```
Instances = Target RPS / RPS Per Instance
```

**With Headroom:**
```
Instances = (Target RPS × 1.5) / RPS Per Instance
```

### Database Sizing

**Connection Pool:**
```
Max Connections = Instances × Connections Per Instance
Recommended: 200 connections for 4 instances
```

**Storage Growth:**
```
Monthly Storage = Users × Storage Per User
Recommended: 100 GB initial, 50 GB growth per year
```

## Monitoring Thresholds

### Alerts

| Metric | Warning | Critical |
|--------|---------|----------|
| CPU Usage | 70% | 90% |
| Memory Usage | 80% | 95% |
| Disk Usage | 80% | 90% |
| Database Connections | 150 | 180 |
| Response Time P95 | 500ms | 1000ms |
| Error Rate | 1% | 5% |

### Scaling Triggers

**Scale Up When:**
- CPU > 70% for 5 minutes
- Memory > 80% for 5 minutes
- Queue length > 100
- Response time P95 > 500ms

**Scale Down When:**
- CPU < 30% for 15 minutes
- Memory < 40% for 15 minutes
- Queue length < 10

## Cost Optimization

### Right-Sizing

**Development:**
- 1 backend instance (small)
- 1 database instance (medium)
- 1 Redis instance (small)

**Staging:**
- 2 backend instances (medium)
- 1 database instance (medium)
- 1 Redis instance (small)

**Production:**
- 4-6 backend instances (medium)
- 1 database instance (large)
- 1 Redis instance (medium)
- 2-4 Celery workers (medium)

### Reserved Instances

- Purchase reserved instances for predictable workloads
- Save 30-50% compared to on-demand
- Commit to 1-3 year terms for stable workloads

### Auto-Scaling

**Configuration:**
```yaml
Min Instances: 2
Max Instances: 10
Scale Up Threshold: 70% CPU
Scale Down Threshold: 30% CPU
Cooldown: 5 minutes
```

## Disaster Recovery Capacity

### Backup Storage

**Requirements:**
- Daily backups: 30 days retention
- Weekly backups: 12 weeks retention
- Monthly backups: 12 months retention
- Estimated: 500 GB backup storage

### Failover Capacity

**Hot Standby:**
- 1 full production environment in different region
- 50% of production capacity
- Ready for immediate failover

**Cold Standby:**
- Infrastructure provisioned but not running
- Full capacity available
- 1-2 hours to activate

## Performance Benchmarks

### Target Performance

| Operation | Target P50 | Target P95 | Target P99 |
|-----------|------------|------------|------------|
| Health Check | 10ms | 20ms | 50ms |
| API Request | 100ms | 300ms | 500ms |
| Search Query | 200ms | 500ms | 1000ms |
| Database Query | 50ms | 150ms | 300ms |
| Cache Get | 5ms | 10ms | 20ms |

### Load Testing

**Test Scenarios:**
- Normal load: 100 RPS
- Peak load: 500 RPS
- Stress test: 1000 RPS
- Soak test: 100 RPS for 24 hours

## Review Schedule

**Monthly:**
- Review capacity metrics
- Update forecasts
- Adjust scaling policies

**Quarterly:**
- Review growth assumptions
- Update cost projections
- Evaluate new instance types

**Annually:**
- Complete capacity review
- Update architecture
- Plan for next year's growth

## Tools and Commands

### Capacity Assessment

```bash
# Check current resource usage
docker stats

# Check database connections
docker-compose -f docker-compose.production.yml exec postgres psql -U matchhire -d matchhire -c "SELECT count(*) FROM pg_stat_activity;"

# Check database size
docker-compose -f docker-compose.production.yml exec postgres psql -U matchhire -d matchhire -c "SELECT pg_size_pretty(pg_database_size('matchhire'));"

# Check Redis memory
docker-compose -f docker-compose.production.yml exec redis redis-cli INFO memory

# Check Elasticsearch stats
curl http://localhost:9200/_cluster/stats
```

### Load Testing

```bash
# Run load test with k6
k6 run --vus 100 --duration 5m loadtesting/scenarios/api.js

# Run stress test
k6 run --vus 500 --duration 10m loadtesting/scenarios/stress.js
```

## Contact

For capacity planning questions:
- DevOps Team: devops@matchhire.com
- Engineering Lead: eng-lead@matchhire.com
