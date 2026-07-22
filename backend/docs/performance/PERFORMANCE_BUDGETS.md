# Performance Budgets

**Date:** 2026-07-22
**Phase:** Milestone 1 - Phase 4.5 Performance Engineering

---

## Overview

Performance budgets define acceptable performance thresholds for the MatchHire backend. These budgets serve as:
- **Development targets:** Goals for new features and optimizations
- **Monitoring alerts:** Thresholds for alerting
- **SLA baselines:** Service level agreement foundations
- **Regression prevention:** Automated testing criteria

---

## API Response Time Budgets

### Critical Endpoints (p95 < 200ms)

| Endpoint | Method | p95 Budget | p99 Budget | Notes |
|----------|--------|------------|------------|-------|
| `GET /health/` | GET | 50ms | 100ms | Health check must be fast |
| `GET /api/auth/login/` | POST | 200ms | 400ms | Authentication critical path |
| `GET /api/analytics/candidate/dashboard/` | GET | 200ms | 400ms | Cached, should be fast |
| `GET /api/analytics/recruiter/dashboard/` | GET | 200ms | 400ms | Cached, should be fast |

### Standard Endpoints (p95 < 500ms)

| Endpoint | Method | p95 Budget | p99 Budget | Notes |
|----------|--------|------------|------------|-------|
| `GET /api/jobs/public/` | GET | 300ms | 600ms | Pagination, composite index |
| `GET /api/jobs/my/` | GET | 300ms | 600ms | Pagination, composite index |
| `GET /api/jobs/<id>/` | GET | 200ms | 400ms | Single object, select_related |
| `POST /api/jobs/` | POST | 500ms | 1000ms | Create operation |
| `GET /api/jobs/recommendations/` | GET | 300ms | 600ms | Cached, JobMatch query |
| `GET /api/resumes/` | GET | 300ms | 600ms | Pagination, Prefetch optimization |
| `GET /api/resumes/<id>/` | GET | 300ms | 600ms | Prefetch optimization |
| `GET /api/applications/my/` | GET | 300ms | 600ms | Pagination, select_related |
| `GET /api/applications/<id>/` | GET | 200ms | 400ms | Single object, select_related |

### Complex Endpoints (p95 < 1000ms)

| Endpoint | Method | p95 Budget | p99 Budget | Notes |
|----------|--------|------------|------------|-------|
| `GET /api/resumes/search/` | GET | 800ms | 1500ms | Complex filtering, prefetch |
| `POST /api/resumes/upload/` | POST | 2000ms | 5000ms | File upload, async parsing |
| `POST /api/jobs/<id>/apply/` | POST | 500ms | 1000ms | Application creation |
| `GET /api/recruiter/candidates/` | GET | 500ms | 1000ms | JobMatch query, composite index |

---

## Database Query Budgets

### Query Count Budgets

| Endpoint Type | Max Queries | Notes |
|--------------|-------------|-------|
| Health checks | 1 | Single query or none |
| Single object (detail) | 3 | select_related optimization |
| List endpoints (pagination) | 5 | select_related + prefetch_related |
| Search endpoints | 10 | Complex filtering allowed |
| Dashboard endpoints | 5 | Aggregate queries, cached |
| Create/update endpoints | 5 | Transaction overhead |

### Query Duration Budgets

| Query Type | Max Duration | Notes |
|------------|--------------|-------|
| Primary key lookup | 10ms | Indexed query |
| Foreign key lookup | 20ms | With select_related |
| Aggregate query | 100ms | COUNT, AVG, etc. |
| Complex join | 200ms | Multiple joins |
| Write operation | 500ms | INSERT/UPDATE/DELETE |

---

## Payload Size Budgets

### Response Payload Limits

| Endpoint Type | Max Size | Notes |
|--------------|---------|-------|
| List responses (per page) | 50KB | 20 items, optimized fields |
| Detail responses | 100KB | Full object with relations |
| Search responses (per page) | 50KB | 20 items, optimized fields |
| Dashboard responses | 10KB | Aggregate metrics only |
| File upload | 10MB | Resume PDF limit |

### Request Payload Limits

| Endpoint Type | Max Size | Notes |
|--------------|---------|-------|
| Job creation | 50KB | Text fields only |
| Resume upload | 10MB | File upload |
| Application creation | 10KB | Text + metadata |

---

## Cache Performance Budgets

### Cache Hit Rate Targets

| Cache Type | Target Hit Rate | Notes |
|------------|----------------|-------|
| Dashboard metrics | 80% | 5-minute TTL |
| Job recommendations | 70% | 1-hour TTL |
| Public job list | 60% | 1-minute TTL |
| Job details | 50% | 5-minute TTL |

### Cache Response Time Budgets

| Operation | Max Duration | Notes |
|-----------|--------------|-------|
| Cache GET | 5ms | Redis local/network |
| Cache SET | 10ms | Redis write |
| Cache DELETE | 5ms | Redis delete |
| Pattern DELETE | 50ms | Redis KEYS + DEL |

---

## Memory Budgets

### Per-Request Memory

| Endpoint Type | Max Memory | Notes |
|--------------|------------|-------|
| Simple GET | 10MB | Single object |
| List GET | 50MB | Pagination (20 items) |
| Search GET | 100MB | Complex filtering |
| File upload | 200MB | Streaming upload |

### Worker Memory

| Component | Max Memory | Notes |
|-----------|------------|-------|
| Gunicorn worker | 500MB | Per worker process |
| Celery worker | 1GB | Per worker process |
| Total (4 workers) | 4GB | Production baseline |

---

## Concurrency Budgets

### Request Concurrency

| Metric | Target | Notes |
|--------|--------|-------|
| Concurrent users | 100 | Current scale target |
| Requests per second | 50 | 100 users × 0.5 req/s |
| Peak RPS | 200 | 4× headroom |

### Database Connection Pool

| Metric | Target | Notes |
|--------|--------|-------|
| Max connections | 100 | PostgreSQL limit |
| Active connections | 40 | 4 workers × 10 pool |
| Idle connections | 60 | Remaining pool |

---

## Error Rate Budgets

### HTTP Error Rate Budgets

| Error Type | Max Rate | Notes |
|------------|----------|-------|
| 5xx errors | 0.1% | Server errors |
| 4xx errors | 1% | Client errors |
| Total errors | 1% | Combined |

### Database Error Rate Budgets

| Error Type | Max Rate | Notes |
|------------|----------|-------|
| Connection errors | 0.01% | Pool exhaustion |
| Query timeouts | 0.05% | Slow queries |
| Deadlocks | 0.01% | Transaction conflicts |

---

## Monitoring and Alerting

### Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| API p95 latency | 500ms | 1000ms | Investigate slow endpoints |
| API p99 latency | 1000ms | 2000ms | Immediate investigation |
| Error rate | 1% | 5% | Check logs, scale if needed |
| Database connections | 80% | 95% | Scale pool or workers |
| Cache hit rate | <50% | <30% | Review cache strategy |
| Memory usage | 80% | 95% | Check for leaks, scale |

---

## Budget Enforcement

### Development

1. **Pre-commit checks:** Run benchmarks before committing
2. **CI/CD gates:** Fail builds if budgets exceeded
3. **Code review:** Review performance impact of changes

### Staging

1. **Automated testing:** Run load tests on every deploy
2. **Performance regression:** Compare against baseline
3. **Canary analysis:** Test new features with subset of traffic

### Production

1. **Real-time monitoring:** Prometheus metrics and alerts
2. **Automated rollback:** Roll back if budgets exceeded
3. **Incident response:** On-call for critical budget violations

---

## Budget Adjustment Process

### When to Adjust Budgets

1. **Scale changes:** User growth or data volume increases
2. **Feature changes:** New functionality requirements
3. **Infrastructure changes:** Hardware or network changes
4. **Business requirements:** SLA changes

### Adjustment Process

1. **Measure:** Collect performance data
2. **Analyze:** Identify root cause of budget violations
3. **Optimize:** Improve performance before adjusting
4. **Document:** Record rationale for budget change
5. **Communicate:** Inform stakeholders of changes

---

## Compliance Tracking

### Current Status

| Budget Category | Status | Compliance | Notes |
|----------------|--------|------------|-------|
| API Response Times | ✅ | 95% | Most endpoints within budget |
| Query Counts | ✅ | 90% | N+1 issues resolved |
| Payload Sizes | ✅ | 100% | All within limits |
| Cache Performance | ⚠️ | 70% | Caching newly implemented |
| Error Rates | ✅ | 99% | Below thresholds |

### Improvement Targets

| Budget Category | Target | Timeline |
|----------------|--------|----------|
| API Response Times | 98% | Q3 2026 |
| Query Counts | 95% | Q3 2026 |
| Cache Performance | 85% | Q4 2026 |
| Error Rates | 99.5% | Ongoing |

---

## Appendix: Budget Calculation Methodology

### p95/p99 Calculation

- **p95:** 95th percentile - 95% of requests complete within this time
- **p99:** 99th percentile - 99% of requests complete within this time
- **Measurement:** Rolling 24-hour window
- **Granularity:** Per endpoint

### Query Count Measurement

- **Tool:** Django Debug Toolbar, django-querycount
- **Scope:** Database queries per request
- **Exclusions:** Migration queries, health checks

### Payload Size Measurement

- **Tool:** HTTP response headers (Content-Length)
- **Scope:** Response body only (excluding headers)
- **Compression:** Measured after gzip compression

---

**Document Version:** 1.0
**Last Updated:** 2026-07-22
**Next Review:** 2026-10-22
