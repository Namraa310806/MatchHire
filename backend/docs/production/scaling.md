# Scaling Guide

## Overview
This guide covers scaling strategies for MatchHire backend in production.

## Horizontal Scaling

### Application Scaling
- **Strategy**: Scale backend instances behind load balancer
- **Tools**: Docker Compose scale, Kubernetes HPA, or cloud auto-scaling
- **Triggers**: CPU > 70%, Memory > 80%, Response time > 500ms
- **Cooldown**: 5 minutes between scale events

### Database Scaling
- **Read Replicas**: Add read replicas for read-heavy workloads
- **Connection Pooling**: Use PgBouncer for connection management
- **Sharding**: Consider sharding for very large datasets (>1TB)

### Cache Scaling
- **Cluster Mode**: Use Redis Cluster for distributed caching
- **Sentinel**: Use Redis Sentinel for high availability
- **Partitioning**: Partition cache by key prefix

### Elasticsearch Scaling
- **Horizontal Scaling**: Add more data nodes
- **Sharding**: Increase shard count based on data size
- **Replicas**: Increase replica count for query throughput

## Vertical Scaling

### Resource Allocation
- **Backend**: Start with 2 CPU, 4GB RAM per instance
- **Database**: Start with 4 CPU, 16GB RAM
- **Redis**: Start with 2 CPU, 4GB RAM
- **Elasticsearch**: Start with 4 CPU, 16GB RAM

### When to Scale Vertically
- Single instance bottlenecks
- Memory-intensive operations
- CPU-bound operations that can't be parallelized

## Auto-scaling Configuration

### Docker Compose
```yaml
services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Kubernetes HPA
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Scaling Best Practices

### Database
- Use connection pooling (max 200 connections)
- Enable query caching
- Optimize slow queries
- Regular maintenance (VACUUM, ANALYZE)

### Cache
- Use appropriate TTL values
- Implement cache warming
- Monitor hit/miss ratio
- Use tiered caching (L1/L2)

### Application
- Stateless design
- Session storage in Redis
- File storage in S3/MinIO
- Background tasks in Celery

## Monitoring Scaling

### Key Metrics
- CPU utilization per instance
- Memory usage per instance
- Request rate
- Response time (p50, p95, p99)
- Error rate
- Queue depth

### Alerts
- Scale up: CPU > 70% for 5 minutes
- Scale down: CPU < 30% for 15 minutes
- Critical: CPU > 90% or Memory > 95%

## Cost Optimization

### Right-sizing
- Monitor actual resource usage
- Adjust instance sizes based on metrics
- Use spot instances for non-critical workloads
- Reserved instances for baseline capacity

### Scaling Strategies
- Scale horizontally for stateless services
- Scale vertically for stateful services
- Use auto-scaling to match demand
- Implement scheduled scaling for predictable patterns
