# Capacity Planning Guide

## Overview
This guide provides capacity planning recommendations for MatchHire production deployment.

## Baseline Metrics

### Single Instance Capacity
- **CPU**: 2 cores minimum, 4 cores recommended
- **Memory**: 4GB minimum, 8GB recommended
- **Database**: 100 concurrent connections
- **Cache**: 512MB memory
- **Throughput**: ~100 RPS per instance

### Scaling Factors

### Request Volume
| Users | Requests/Day | Peak RPS | Instances Needed |
|-------|--------------|----------|------------------|
| 1K    | 50K          | 10       | 1                |
| 10K   | 500K         | 100      | 2-3              |
| 100K  | 5M           | 1000     | 10-15            |
| 1M    | 50M          | 10000    | 100-150          |

### Database Capacity
| Data Size | RAM Needed | Storage Needed | Backup Size |
|-----------|------------|----------------|-------------|
| 1GB       | 2GB        | 5GB            | 500MB       |
| 10GB      | 8GB        | 50GB           | 5GB         |
| 100GB     | 32GB       | 500GB          | 50GB        |
| 1TB       | 128GB      | 5TB            | 500GB       |

### Cache Capacity
| Cache Size | Memory Needed | Hit Rate Target |
|------------|---------------|-----------------|
| 100K keys  | 500MB         | 80%             |
| 1M keys    | 5GB           | 85%             |
| 10M keys   | 50GB          | 90%             |

## Component Sizing

### Backend (Django/Gunicorn)
- **Workers**: 2-4 per CPU core
- **Worker connections**: 1000
- **Max requests per worker**: 1000
- **Timeout**: 30s

### Database (PostgreSQL)
- **max_connections**: 200
- **shared_buffers**: 25% of RAM
- **effective_cache_size**: 50-75% of RAM
- **maintenance_work_mem**: 64MB-1GB
- **work_mem**: (RAM - shared_buffers) / max_connections

### Cache (Redis)
- **maxmemory**: 512MB-50GB based on workload
- **maxmemory-policy**: allkeys-lru
- **timeout**: 300s
- **tcp-keepalive**: 300

### Elasticsearch
- **Heap size**: 50% of available RAM, max 30GB
- **Shards**: 1 per 50GB data
- **Replicas**: 1 for production
- **Refresh interval**: 30s

## Auto-scaling Recommendations

### Horizontal Scaling Triggers
- CPU > 70% for 5 minutes
- Memory > 80% for 5 minutes
- Request latency > 500ms for 5 minutes
- Queue depth > 100

### Scaling Policies
- **Scale up**: Add 2 instances when trigger hit
- **Scale down**: Remove instances when CPU < 30% for 15 minutes
- **Minimum instances**: 2
- **Maximum instances**: 20

## Monitoring Thresholds

### Alerts
| Metric | Warning | Critical |
|--------|---------|----------|
| CPU %  | 70      | 90       |
| Memory % | 80    | 95       |
| Disk % | 80      | 90       |
| Response time | 500ms | 2s |
| Error rate | 1% | 5% |
| Database connections | 150 | 190 |

## Cost Optimization

### Right-sizing
- Start with recommended baseline
- Monitor actual usage for 2 weeks
- Adjust based on real metrics
- Use spot instances for non-critical workloads

### Reserved Instances
- Purchase reserved instances for steady-state workload
- Use on-demand for burst capacity
- Consider savings plans for predictable workloads

## Disaster Recovery Capacity

### Backup Storage
- Daily backups: 7 days retention
- Weekly backups: 4 weeks retention
- Monthly backups: 12 months retention
- Estimated backup size: 50% of database size

### Failover Capacity
- Hot standby: 50% of production capacity
- Cold standby: 25% of production capacity
- Recovery time objective (RTO): 1 hour
- Recovery point objective (RPO): 5 minutes

## Growth Planning

### Quarterly Reviews
- Review capacity utilization
- Update projections based on growth
- Adjust auto-scaling thresholds
- Plan for seasonal variations

### Annual Planning
- Review architecture for scaling limits
- Plan for major feature launches
- Budget for infrastructure growth
- Evaluate new technologies for efficiency
