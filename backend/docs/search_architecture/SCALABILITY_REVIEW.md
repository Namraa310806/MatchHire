# Scalability Review
## Phase 5.0 - Search Architecture & Domain Design

**Date:** 2026-07-23
**Status:** Complete

---

## Overview

This document reviews the scalability of the search architecture for the MatchHire platform. The review covers scaling from 100K to 10M candidates, horizontal scaling strategies, caching, index synchronization, background indexing, and distributed search capabilities.

---

## Scale Targets

### Current Scale (Phase 1)
- **Candidates:** 1K - 10K
- **Jobs:** 500 - 5K
- **Resumes:** 1K - 10K
- **Applications:** 5K - 50K
- **Search Queries:** 10 - 100 QPS

### Target Scale (Phase 2)
- **Candidates:** 100K
- **Jobs:** 50K
- **Resumes:** 100K
- **Applications:** 500K
- **Search Queries:** 1K QPS

### Growth Scale (Phase 3)
- **Candidates:** 1M
- **Jobs:** 500K
- **Resumes:** 1M
- **Applications:** 5M
- **Search Queries:** 10K QPS

### Enterprise Scale (Phase 4)
- **Candidates:** 10M
- **Jobs:** 5M
- **Resumes:** 10M
- **Applications:** 50M
- **Search Queries:** 100K QPS

---

## Horizontal Scaling Strategy

### Search Cluster Scaling

#### Elasticsearch Cluster Architecture

**Small Scale (100K candidates)**
- **Nodes:** 3 nodes (1 master + 2 data)
- **CPU:** 4 cores per node
- **Memory:** 16GB per node
- **Storage:** 500GB SSD per node
- **Shards:** 3 per index
- **Replicas:** 1 per index

**Medium Scale (1M candidates)**
- **Nodes:** 6 nodes (3 master + 3 data)
- **CPU:** 8 cores per node
- **Memory:** 32GB per node
- **Storage:** 2TB SSD per node
- **Shards:** 5-10 per index
- **Replicas:** 1-2 per index

**Large Scale (10M candidates)**
- **Nodes:** 15 nodes (3 master + 12 data)
- **CPU:** 16 cores per node
- **Memory:** 64GB per node
- **Storage:** 5TB SSD per node
- **Shards:** 20-50 per index
- **Replicas:** 2-3 per index

#### Node Types
- **Master Nodes:** Cluster management, no data storage
- **Data Nodes:** Data storage and search
- **Coordinating Nodes:** Query routing, no data storage
- **ML Nodes:** Machine learning operations (future)

---

### Application Server Scaling

#### Django Application Servers

**Small Scale (100K candidates)**
- **Instances:** 2 instances
- **CPU:** 2 cores per instance
- **Memory:** 4GB per instance
- **Load Balancer:** Nginx or AWS ALB

**Medium Scale (1M candidates)**
- **Instances:** 4-6 instances
- **CPU:** 4 cores per instance
- **Memory:** 8GB per instance
- **Load Balancer:** AWS ALB with auto-scaling

**Large Scale (10M candidates)**
- **Instances:** 12-20 instances
- **CPU:** 8 cores per instance
- **Memory**: 16GB per instance
- **Load Balancer:** AWS ALB with auto-scaling groups

---

### Database Scaling

#### PostgreSQL Database

**Small Scale (100K candidates)**
- **Instance:** db.t3.medium (2 vCPU, 4GB RAM)
- **Storage:** 100GB SSD
- **Read Replicas:** 0

**Medium Scale (1M candidates)**
- **Instance:** db.r5.large (2 vCPU, 16GB RAM)
- **Storage:** 500GB SSD
- **Read Replicas:** 1-2

**Large Scale (10M candidates)**
- **Instance:** db.r5.xlarge (4 vCPU, 32GB RAM)
- **Storage:** 2TB SSD
- **Read Replicas:** 3-5

#### Connection Pooling
- **PgBouncer:** Connection pooler for PostgreSQL
- **Pool Size:** 20-100 connections per pool
- **Max Connections:** 500-1000 total

---

## Caching Strategy

### Multi-Level Caching

#### Level 1: Application Cache (Redis)
- **Purpose:** Cache search results, recommendations
- **TTL:** 5-15 minutes for search results
- **Size:** 1-10GB
- **Eviction:** LRU

#### Level 2: Query Cache (Elasticsearch)
- **Purpose:** Cache frequently executed queries
- **TTL:** 1-5 minutes
- **Size:** 10-50% of JVM heap
- **Eviction:** LRU

#### Level 3: OS Cache (File System)
- **Purpose:** Cache index segments
- **Managed by:** OS and Elasticsearch
- **Size:** Available memory

### Cache Hit Rate Targets
- **Search Results:** 60-80% hit rate
- **Autocomplete:** 80-95% hit rate
- **Recommendations:** 70-90% hit rate
- **Facets:** 50-70% hit rate

### Cache Invalidation Strategy
- **Time-Based:** TTL expiration
- **Event-Based:** Invalidate on data changes
- **Manual:** Admin-triggered invalidation
- **Selective:** Invalidate only affected keys

---

## Index Synchronization

### Real-Time Indexing

#### Synchronous Indexing
- **Use Case:** Critical data updates (job status, application status)
- **Latency:** < 1 second
- **Implementation:** Django signals → Elasticsearch API
- **Risk:** Increased request latency

#### Asynchronous Indexing
- **Use Case:** Non-critical data updates (profile updates, resume uploads)
- **Latency:** 1-5 seconds
- **Implementation:** Django signals → Celery → Elasticsearch bulk API
- **Risk:** Slight delay in search results

### Batch Indexing

#### Full Reindex
- **Trigger:** Schema changes, major data migration
- **Strategy:** Create new index, reindex data, switch alias
- **Downtime:** Zero (using index aliases)
- **Duration:** 1-10 hours depending on data size

#### Incremental Reindex
- **Trigger:** Field mapping changes
- **Strategy:** Update by query, reindex affected documents
- **Downtime:** Zero
- **Duration:** Minutes to hours

### Index Consistency

#### Eventual Consistency
- **Acceptable Delay:** 1-5 seconds for most updates
- **Critical Updates:** < 1 second (synchronous)
- **Non-Critical Updates:** 1-60 seconds (asynchronous)

#### Consistency Checks
- **Daily:** Compare database count vs index count
- **Weekly:** Sample data validation
- **Monthly:** Full consistency audit

---

## Background Indexing

### Celery-Based Indexing

#### Task Queue Architecture
- **Queue:** search_indexing
- **Workers:** 4-8 workers
- **Concurrency:** 2-4 tasks per worker
- **Priority:** High for critical updates, Low for bulk operations

#### Task Types
- **Index Document:** Index single document
- **Bulk Index:** Index multiple documents
- **Delete Document:** Delete from index
- **Reindex Entity:** Reindex all documents for entity

#### Task Priorities
- **High:** Job status changes, application status changes
- **Medium:** Profile updates, resume uploads
- **Low:** Full reindex, bulk operations

### Performance Optimization

#### Bulk Indexing
- **Batch Size:** 100-1000 documents per batch
- **Parallel Batches:** 2-4 concurrent batches
- **Refresh Interval:** 30s during bulk indexing
- **Replicas:** 0 during bulk indexing, restore after

#### Indexing Throughput
- **Small Documents:** 1000-5000 docs/second
- **Large Documents:** 100-500 docs/second
- **Nested Documents:** 50-200 docs/second

---

## Distributed Search

### Search Routing

#### Query Routing
- **Round Robin:** Distribute queries across nodes
- **Least Connections:** Route to least busy node
- **Geo-Based:** Route to nearest data center (multi-region)

#### Shard Routing
- **Primary Shard:** Query primary shards only (faster, less accurate)
- **Replica Shard:** Query replica shards (load balancing)
- **Preference:** Local, _primary, _primary_first

### Multi-Region Deployment

#### Architecture
- **Primary Region:** US-East (write operations)
- **Secondary Regions:** US-West, EU (read operations)
- **Data Sync:** Cross-cluster replication (CCR)

#### Latency Targets
- **Same Region:** < 100ms
- **Cross Region:** < 300ms
- **Global:** < 500ms

### Disaster Recovery

#### Backup Strategy
- **Snapshots:** Daily snapshots to S3
- **Retention:** 30 days
- **Restore Time:** 1-4 hours depending on data size

#### Failover
- **Automatic:** Master node election
- **Manual:** Region failover
- **RTO:** 1-4 hours
- **RPO:** 0-15 minutes

---

## Performance Optimization

### Query Optimization

#### Query Optimization Strategies
- **Filter Before Search:** Apply filters before full-text search
- **Field Selection:** Return only required fields
- **Pagination:** Use search_after instead of offset for deep pagination
- **Caching:** Cache frequent queries
- **Query DSL Optimization:** Use efficient query structures

#### Slow Query Detection
- **Threshold:** > 1 second
- **Logging:** Log slow queries with query DSL
- **Analysis:** Analyze slow query patterns
- **Optimization:** Optimize or cache slow queries

### Index Optimization

#### Index Optimization Strategies
- **Shard Sizing:** 10-50GB per shard
- **Replica Placement:** Spread replicas across nodes
- **Refresh Interval:** Balance between freshness and performance
- **Merge Policy:** Optimize for search or indexing

#### Index Lifecycle Management
- **Hot Phase:** High refresh, more replicas (0-7 days)
- **Warm Phase:** Lower refresh, fewer replicas (7-30 days)
- **Cold Phase:** Minimal replicas, compressed (30-90 days)
- **Delete Phase:** Delete index (> 90 days)

---

## Monitoring and Alerting

### Metrics to Monitor

#### Cluster Health
- **Cluster Status:** Green, Yellow, Red
- **Node Health:** CPU, Memory, Disk, Network
- **JVM Health:** Heap usage, GC pauses
- **Index Health:** Index status, shard status

#### Search Performance
- **Query Latency:** p50, p95, p99
- **Query Throughput:** QPS
- **Error Rate:** Failed queries
- **Cache Hit Rate:** Cache effectiveness

#### Indexing Performance
- **Indexing Latency:** Time to index documents
- **Indexing Throughput:** Docs/second
- **Index Size:** Index size over time
- **Index Freshness:** Lag between DB and index

### Alerting Rules

#### Critical Alerts
- **Cluster Status Red:** Immediate alert
- **Node Down:** Immediate alert
- **Query Latency > 1s:** Alert
- **Error Rate > 5%:** Alert

#### Warning Alerts
- **Cluster Status Yellow:** Warning
- **High CPU Usage > 80%:** Warning
- **High Memory Usage > 80%:** Warning
- **Disk Usage > 80%:** Warning

#### Info Alerts
- **Index Size Growth:** Info
- **Query Pattern Changes:** Info
- **Cache Hit Rate Changes:** Info

---

## Cost Optimization

### Infrastructure Cost Optimization

#### Right-Sizing
- **Start Small:** Begin with minimum resources
- **Scale Up:** Add resources as needed
- **Auto-Scale:** Use auto-scaling groups
- **Reserved Instances:** Use reserved instances for baseline load

#### Storage Optimization
- **Lifecycle Policies:** Move old data to cheaper storage
- **Compression:** Compress old indices
- **Tiered Storage:** Hot data on SSD, cold on HDD
- **Snapshot Cleanup:** Delete old snapshots

### Query Cost Optimization

#### Query Efficiency
- **Optimize Queries:** Reduce query complexity
- **Cache Results:** Reduce repeated queries
- **Rate Limiting:** Prevent abuse
- **Query Timeouts:** Limit long-running queries

---

## Scale Testing

### Load Testing Strategy

#### Tools
- **K6:** Load testing framework
- **JMeter:** Load testing tool
- **Locust:** Python-based load testing

#### Test Scenarios
- **Search Load:** 1000-100000 concurrent search queries
- **Indexing Load:** 100-10000 concurrent indexing operations
- **Mixed Load:** Combination of search and indexing

#### Metrics to Measure
- **Throughput:** QPS, indexing rate
- **Latency:** p50, p95, p99
- **Error Rate:** Failed requests
- **Resource Usage:** CPU, Memory, Disk, Network

### Performance Benchmarks

#### Search Performance Targets
| Scale | Target QPS | Target Latency (p95) |
|-------|------------|---------------------|
| 100K | 1K | 100ms |
| 1M | 10K | 200ms |
| 10M | 100K | 300ms |

#### Indexing Performance Targets
| Scale | Target Docs/sec | Target Latency |
|-------|-----------------|----------------|
| 100K | 1000 | < 1s |
| 1M | 5000 | < 2s |
| 10M | 10000 | < 5s |

---

## Migration Path

### Phase 1: Current State (PostgreSQL Only)
- **Scale:** 10K candidates
- **Search:** Django ORM with icontains
- **Caching:** Redis for recommendations only
- **Indexing:** N/A (direct database queries)

### Phase 2: Elasticsearch Deployment (Next)
- **Scale:** 100K candidates
- **Search:** Elasticsearch for all search operations
- **Caching:** Multi-level caching (Redis + Elasticsearch)
- **Indexing:** Real-time + batch indexing

### Phase 3: Vector Search (Future)
- **Scale:** 1M candidates
- **Search:** Elasticsearch + Vector DB (Pinecone/pgvector)
- **Caching:** Enhanced caching with semantic cache
- **Indexing:** Vector embedding generation

### Phase 4: Distributed Search (Future)
- **Scale:** 10M candidates
- **Search:** Multi-region Elasticsearch cluster
- **Caching:** Distributed caching (Redis Cluster)
- **Indexing:** Event-driven indexing with message queue

---

## Summary

The scalability review covers:

1. **Scale Targets:**
   - Current: 10K candidates, 100 QPS
   - Target: 100K candidates, 1K QPS
   - Growth: 1M candidates, 10K QPS
   - Enterprise: 10M candidates, 100K QPS

2. **Horizontal Scaling:**
   - Elasticsearch cluster scaling (3-15 nodes)
   - Application server scaling (2-20 instances)
   - Database scaling with read replicas (0-5 replicas)
   - Connection pooling with PgBouncer

3. **Caching Strategy:**
   - Multi-level caching (Redis, Elasticsearch, OS)
   - Cache hit rate targets (60-95%)
   - Cache invalidation strategies (time-based, event-based)

4. **Index Synchronization:**
   - Real-time indexing (synchronous for critical, async for non-critical)
   - Batch indexing (full reindex, incremental reindex)
   - Consistency checks (daily, weekly, monthly)

5. **Background Indexing:**
   - Celery-based task queue
   - Bulk indexing optimization
   - Indexing throughput targets (100-5000 docs/sec)

6. **Distributed Search:**
   - Query routing strategies
   - Multi-region deployment
   - Disaster recovery (snapshots, failover)

7. **Performance Optimization:**
   - Query optimization strategies
   - Index optimization strategies
   - Slow query detection

8. **Monitoring and Alerting:**
   - Cluster health metrics
   - Search performance metrics
   - Indexing performance metrics
   - Alerting rules (critical, warning, info)

9. **Cost Optimization:**
   - Infrastructure cost optimization
   - Query cost optimization
   - Storage optimization

10. **Scale Testing:**
    - Load testing strategy
    - Performance benchmarks
    - Migration path (4 phases)

The scalability review demonstrates that the search architecture is designed to scale from 10K to 10M candidates with clear strategies for horizontal scaling, caching, index synchronization, background indexing, and distributed search.
