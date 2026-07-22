# Alerting Recommendations for MatchHire Backend

This document provides recommended alerting rules for monitoring the MatchHire backend in production.

## Alerting Principles

- **Alert on symptoms, not causes**: Alert on user-facing issues, not internal metrics
- **Avoid alert fatigue**: Only alert on issues that require immediate action
- **Set appropriate thresholds**: Use baselines to determine normal vs. abnormal behavior
- **Include runbook links**: Each alert should link to relevant documentation
- **Use severity levels**: Distinguish between critical, warning, and informational alerts

## Critical Alerts (P1)

### High Error Rate

**Condition**: Error rate > 5% for 5 minutes

**Query**: 
```promql
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100 > 5
```

**Severity**: Critical

**Response Time**: Immediate (within 5 minutes)

**Runbook**: [High Error Rate Runbook](../runbooks/high-error-rate.md)

**Notification Channels**: PagerDuty, Slack #alerts-critical

**Impact**: Users are experiencing errors when using the application

---

### Database Unavailable

**Condition**: Database health check fails for 2 consecutive checks

**Query**: 
```promql
health_check{check="database"} == 0
```

**Severity**: Critical

**Response Time**: Immediate (within 2 minutes)

**Runbook**: [Database Outage Runbook](../runbooks/database-outage.md)

**Notification Channels**: PagerDuty, Slack #alerts-critical

**Impact**: Application cannot function without database connectivity

---

### Redis Unavailable

**Condition**: Redis health check fails for 2 consecutive checks

**Query**: 
```promql
health_check{check="redis"} == 0
```

**Severity**: Critical

**Response Time**: Immediate (within 2 minutes)

**Runbook**: [Redis Outage Runbook](../runbooks/redis-outage.md)

**Notification Channels**: PagerDuty, Slack #alerts-critical

**Impact**: Caching and task queue operations are degraded

---

### High Latency (P95)

**Condition**: P95 request duration > 2 seconds for 5 minutes

**Query**: 
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
```

**Severity**: Critical

**Response Time**: Within 10 minutes

**Runbook**: [High Latency Runbook](../runbooks/high-latency.md)

**Notification Channels**: Slack #alerts-critical, Email

**Impact**: Users are experiencing slow response times

---

## Warning Alerts (P2)

### Queue Backlog

**Condition**: Celery queue length > 1000 tasks for 10 minutes

**Query**: 
```promql
celery_queue_length{queue="default"} > 1000
```

**Severity**: Warning

**Response Time**: Within 30 minutes

**Runbook**: [Queue Backlog Runbook](../runbooks/queue-backlog.md)

**Notification Channels**: Slack #alerts-warning

**Impact**: Background tasks are delayed

---

### Worker Offline

**Condition**: No active Celery workers for 5 minutes

**Query**: 
```promql
celery_worker_active_tasks == 0
```

**Severity**: Warning

**Response Time**: Within 15 minutes

**Runbook**: [Worker Offline Runbook](../runbooks/worker-offline.md)

**Notification Channels**: Slack #alerts-warning

**Impact**: Background tasks are not being processed

---

### Low Cache Hit Rate

**Condition**: Cache hit rate < 70% for 15 minutes

**Query**: 
```promql
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) * 100 < 70
```

**Severity**: Warning

**Response Time**: Within 1 hour

**Runbook**: [Low Cache Hit Rate Runbook](../runbooks/low-cache-hit-rate.md)

**Notification Channels**: Slack #alerts-warning

**Impact**: Increased load on database, potential performance degradation

---

### High Memory Usage

**Condition**: Container memory usage > 80% for 10 minutes

**Query**: 
```promql
container_memory_usage_bytes / container_spec_memory_limit_bytes * 100 > 80
```

**Severity**: Warning

**Response Time**: Within 30 minutes

**Runbook**: [High Memory Usage Runbook](../runbooks/high-memory-usage.md)

**Notification Channels**: Slack #alerts-warning

**Impact**: Potential OOM kills, service instability

---

### High CPU Usage

**Condition**: Container CPU usage > 80% for 10 minutes

**Query**: 
```promql
rate(container_cpu_usage_seconds_total[5m]) * 100 > 80
```

**Severity**: Warning

**Response Time**: Within 30 minutes

**Runbook**: [High CPU Usage Runbook](../runbooks/high-cpu-usage.md)

**Notification Channels**: Slack #alerts-warning

**Impact**: Performance degradation, potential service instability

---

## Informational Alerts (P3)

### Disk Space Low

**Condition**: Disk usage > 80%

**Query**: 
```promql
(disk_used / disk_total) * 100 > 80
```

**Severity**: Info

**Response Time**: Within 4 hours

**Runbook**: [Disk Space Low Runbook](../runbooks/disk-space-low.md)

**Notification Channels**: Slack #alerts-info, Email

**Impact**: Potential inability to write logs or store files

---

### SSL Certificate Expiring

**Condition**: SSL certificate expires in < 30 days

**Severity**: Info

**Response Time**: Within 24 hours

**Runbook**: [SSL Certificate Renewal](../runbooks/ssl-certificate-renewal.md)

**Notification Channels**: Email, Slack #alerts-info

**Impact**: Potential service disruption if certificate expires

---

## Business Metrics Alerts

### Zero Business Activity

**Condition**: No resume uploads for 1 hour during business hours

**Query**: 
```promql
rate(resumes_uploaded_total[1h]) == 0
```

**Severity**: Warning

**Response Time**: Within 2 hours

**Runbook**: [Zero Business Activity Runbook](../runbooks/zero-business-activity.md)

**Notification Channels**: Slack #alerts-warning

**Impact**: May indicate application issues or unusual traffic patterns

---

## Alert Suppression Rules

### Maintenance Windows

Suppress all non-critical alerts during scheduled maintenance windows.

**Condition**: During maintenance window (defined by label)

**Action**: Set alert state to "suppressed"

---

### Known Issues

Suppress alerts for known issues being investigated.

**Condition**: Issue tracked in incident management system

**Action**: Set alert state to "suppressed" with reference to incident ID

---

## Alert Escalation Policy

### P1 (Critical)
- **First notification**: Immediate (PagerDuty + Slack)
- **Escalation**: After 15 minutes without acknowledgment
- **Escalation to**: Engineering manager + CTO

### P2 (Warning)
- **First notification**: Within 15 minutes (Slack)
- **Escalation**: After 1 hour without acknowledgment
- **Escalation to**: Engineering lead

### P3 (Info)
- **First notification**: Within 4 hours (Email + Slack)
- **Escalation**: After 24 hours without acknowledgment
- **Escalation to**: Engineering lead

## Alert Testing

### Weekly
- Test critical alerting channels (PagerDuty, Slack)
- Verify alert routing and escalation

### Monthly
- Test all alert conditions in staging environment
- Review and adjust thresholds based on recent data

### Quarterly
- Full alerting system audit
- Review alert fatigue and adjust as needed
- Update runbooks based on learnings

## Alert Documentation Requirements

Each alert must include:
- Clear description of the condition
- Impact statement
- Relevant runbook link
- Severity level
- Response time expectation
- Notification channels
- Related metrics/graphs

## Alert Noise Reduction

### Deduplication
- Group similar alerts within a time window
- Send single notification with aggregated information

### Rate Limiting
- Limit notifications for the same alert to once per hour
- Send summary for recurring issues

### Smart Suppression
- Suppress alerts during deployments
- Suppress alerts during known traffic patterns (e.g., daily peaks)
