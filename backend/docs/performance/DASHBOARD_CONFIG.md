# Performance Dashboard Configuration

**Date:** 2026-07-22
**Phase:** Milestone 1 - Phase 4.5 Performance Engineering

---

## Overview

This document provides Grafana dashboard configurations for monitoring MatchHire backend performance. The dashboards visualize metrics from Prometheus to provide real-time observability.

---

## Prerequisites

- **Prometheus:** Metrics collection (already configured)
- **Grafana:** Visualization dashboard
- **Prometheus Data Source:** Configured in Grafana

---

## Dashboard 1: API Performance Overview

### JSON Configuration

```json
{
  "dashboard": {
    "title": "MatchHire API Performance",
    "uid": "matchhire-api-performance",
    "panels": [
      {
        "title": "Request Rate (RPS)",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[1m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time (p95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{endpoint}}"
          }
        ],
        "alert": {
          "conditions": [
            {
              "evaluator": {
                "params": [0.5],
                "type": "gt"
              },
              "operator": {
                "type": "and"
              },
              "query": {
                "params": ["A", "5m", "now"]
              },
              "reducer": {
                "params": [],
                "type": "avg"
              },
              "type": "query"
            }
          ],
          "executionErrorState": "alerting",
          "frequency": "1m",
          "handler": 1,
          "name": "High Response Time",
          "noDataState": "no_data",
          "notifications": []
        }
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[1m]) / rate(http_requests_total[1m])",
            "legendFormat": "5xx Error Rate"
          },
          {
            "expr": "rate(http_requests_total{status=~\"4..\"}[1m]) / rate(http_requests_total[1m])",
            "legendFormat": "4xx Error Rate"
          }
        ]
      },
      {
        "title": "Active Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "django_db_connections_active",
            "legendFormat": "Active DB Connections"
          },
          {
            "expr": "django_db_connections_idle",
            "legendFormat": "Idle DB Connections"
          }
        ]
      }
    ]
  }
}
```

---

## Dashboard 2: Database Performance

### JSON Configuration

```json
{
  "dashboard": {
    "title": "MatchHire Database Performance",
    "uid": "matchhire-db-performance",
    "panels": [
      {
        "title": "Query Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(django_db_query_duration_seconds_sum[5m]) / rate(django_db_query_duration_seconds_count[5m])",
            "legendFormat": "Avg Query Duration"
          }
        ]
      },
      {
        "title": "Query Count",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(django_db_queries_total[1m])",
            "legendFormat": "Queries per Second"
          }
        ]
      },
      {
        "title": "Slow Queries",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(django_db_slow_queries_total[5m])",
            "legendFormat": "Slow Queries per Second"
          }
        ]
      },
      {
        "title": "Connection Pool Usage",
        "type": "gauge",
        "targets": [
          {
            "expr": "django_db_connections_active / django_db_connections_max",
            "legendFormat": "Pool Usage %"
          }
        ]
      }
    ]
  }
}
```

---

## Dashboard 3: Cache Performance

### JSON Configuration

```json
{
  "dashboard": {
    "title": "MatchHire Cache Performance",
    "uid": "matchhire-cache-performance",
    "panels": [
      {
        "title": "Cache Hit Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))",
            "legendFormat": "Hit Rate"
          }
        ]
      },
      {
        "title": "Cache Operations",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(cache_hits_total[1m])",
            "legendFormat": "Hits/sec"
          },
          {
            "expr": "rate(cache_misses_total[1m])",
            "legendFormat": "Misses/sec"
          },
          {
            "expr": "rate(cache_sets_total[1m])",
            "legendFormat": "Sets/sec"
          },
          {
            "expr": "rate(cache_deletes_total[1m])",
            "legendFormat": "Deletes/sec"
          }
        ]
      },
      {
        "title": "Cache Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(cache_operation_duration_seconds_bucket[5m]))",
            "legendFormat": "p95 Cache Duration"
          }
        ]
      },
      {
        "title": "Redis Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "redis_memory_used_bytes",
            "legendFormat": "Memory Used"
          },
          {
            "expr": "redis_memory_max_bytes",
            "legendFormat": "Memory Max"
          }
        ]
      }
    ]
  }
}
```

---

## Dashboard 4: Celery Task Performance

### JSON Configuration

```json
{
  "dashboard": {
    "title": "MatchHire Celery Performance",
    "uid": "matchhire-celery-performance",
    "panels": [
      {
        "title": "Task Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(celery_tasks_total[1m])",
            "legendFormat": "Tasks/sec"
          }
        ]
      },
      {
        "title": "Task Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(celery_task_duration_seconds_bucket[5m]))",
            "legendFormat": "p95 Task Duration"
          }
        ]
      },
      {
        "title": "Task Failures",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(celery_task_failures_total[1m])",
            "legendFormat": "Failures/sec"
          }
        ]
      },
      {
        "title": "Queue Length",
        "type": "graph",
        "targets": [
          {
            "expr": "celery_queue_length",
            "legendFormat": "{{queue}}"
          }
        ]
      },
      {
        "title": "Worker Status",
        "type": "stat",
        "targets": [
          {
            "expr": "celery_workers_active",
            "legendFormat": "Active Workers"
          }
        ]
      }
    ]
  }
}
```

---

## Dashboard 5: System Resources

### JSON Configuration

```json
{
  "dashboard": {
    "title": "MatchHire System Resources",
    "uid": "matchhire-system-resources",
    "panels": [
      {
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(process_cpu_seconds_total[1m])",
            "legendFormat": "CPU Usage"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "process_resident_memory_bytes",
            "legendFormat": "Memory Used"
          }
        ]
      },
      {
        "title": "File Descriptors",
        "type": "graph",
        "targets": [
          {
            "expr": "process_open_fds",
            "legendFormat": "Open FDs"
          }
        ]
      },
      {
        "title": "Goroutines",
        "type": "graph",
        "targets": [
          {
            "expr": "go_goroutines",
            "legendFormat": "Goroutines"
          }
        ]
      }
    ]
  }
}
```

---

## Alert Rules

### Prometheus Alert Rules

```yaml
groups:
  - name: matchhire_api_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"
      
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow response time detected"
          description: "p95 response time is {{ $value }}s for the last 5 minutes"
      
      - alert: HighDatabaseConnections
        expr: django_db_connections_active / django_db_connections_max > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High database connection usage"
          description: "Database connection pool is {{ $value | humanizePercentage }} full"
      
      - alert: LowCacheHitRate
        expr: rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) < 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value | humanizePercentage }} for the last 10 minutes"
      
      - alert: CeleryTaskBacklog
        expr: celery_queue_length > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Celery task backlog detected"
          description: "Queue length is {{ $value }} tasks"
```

---

## Installation Instructions

### 1. Import Dashboards to Grafana

```bash
# Using Grafana CLI
grafana-cli dashboards import matchhire-api-performance.json
grafana-cli dashboards import matchhire-db-performance.json
grafana-cli dashboards import matchhire-cache-performance.json
grafana-cli dashboards import matchhire-celery-performance.json
grafana-cli dashboards import matchhire-system-resources.json
```

Or import manually via Grafana UI:
1. Navigate to Dashboards → Import
2. Upload JSON file
3. Select Prometheus data source
4. Click Import

### 2. Configure Prometheus Alert Rules

```bash
# Copy alert rules to Prometheus configuration
cp matchhire-alerts.yml /etc/prometheus/rules/

# Reload Prometheus
kill -HUP $(pidof prometheus)
```

### 3. Configure Alert Notifications

In Grafana:
1. Navigate to Alerting → Notification channels
2. Add notification channel (e.g., Slack, email, PagerDuty)
3. Configure alert routing in alert rules

---

## Dashboard Usage Guide

### API Performance Dashboard

**Purpose:** Monitor overall API health and performance

**Key Metrics:**
- Request Rate: Traffic volume
- Response Time (p95): Latency at 95th percentile
- Error Rate: 4xx and 5xx error percentages
- Active Connections: Database connection pool usage

**Alert Thresholds:**
- Response Time p95 > 500ms (warning)
- Response Time p95 > 1000ms (critical)
- Error Rate > 1% (warning)
- Error Rate > 5% (critical)

---

### Database Performance Dashboard

**Purpose:** Monitor database query performance and connection health

**Key Metrics:**
- Query Duration: Average query execution time
- Query Count: Queries per second
- Slow Queries: Queries exceeding threshold
- Connection Pool Usage: Percentage of pool in use

**Alert Thresholds:**
- Query Duration > 100ms (warning)
- Query Duration > 200ms (critical)
- Connection Pool > 80% (warning)
- Connection Pool > 95% (critical)

---

### Cache Performance Dashboard

**Purpose:** Monitor cache effectiveness and Redis health

**Key Metrics:**
- Cache Hit Rate: Percentage of cache hits
- Cache Operations: Hits, misses, sets, deletes per second
- Cache Response Time: Cache operation latency
- Redis Memory Usage: Memory consumption

**Alert Thresholds:**
- Cache Hit Rate < 50% (warning)
- Cache Hit Rate < 30% (critical)
- Redis Memory > 80% (warning)
- Redis Memory > 95% (critical)

---

### Celery Performance Dashboard

**Purpose:** Monitor background task processing

**Key Metrics:**
- Task Rate: Tasks processed per second
- Task Duration: Task execution time (p95)
- Task Failures: Failed tasks per second
- Queue Length: Pending tasks in queue
- Worker Status: Active worker count

**Alert Thresholds:**
- Task Duration p95 > 30s (warning)
- Task Duration p95 > 60s (critical)
- Queue Length > 100 (warning)
- Queue Length > 500 (critical)

---

### System Resources Dashboard

**Purpose:** Monitor application resource usage

**Key Metrics:**
- CPU Usage: Process CPU consumption
- Memory Usage: Process memory consumption
- File Descriptors: Open file descriptor count
- Goroutines: Active goroutine count (if using async)

**Alert Thresholds:**
- CPU Usage > 80% (warning)
- Memory Usage > 80% (warning)
- File Descriptors > 80% of limit (warning)

---

## Customization Guide

### Adding Custom Metrics

To add custom metrics to dashboards:

1. **Add metric to Prometheus exporter** (in `core/metrics_middleware.py`)
2. **Add panel to dashboard JSON**
3. **Import updated dashboard**

Example:
```python
from prometheus_client import Counter

custom_metric = Counter('custom_operations_total', 'Total custom operations')
custom_metric.inc()
```

### Adjusting Time Ranges

Modify the `range` parameter in query expressions:
- `[1m]` - 1 minute
- `[5m]` - 5 minutes
- `[1h]` - 1 hour
- `[1d]` - 1 day

### Modifying Alert Thresholds

Edit alert rule expressions in `matchhire-alerts.yml`:
```yaml
- alert: SlowResponseTime
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1.0  # Changed from 0.5
```

---

## Troubleshooting

### Dashboard Shows No Data

**Possible Causes:**
1. Prometheus not scraping metrics
2. Incorrect data source configuration
3. Metric names don't match

**Solutions:**
1. Check Prometheus targets: `http://prometheus:9090/targets`
2. Verify data source in Grafana settings
3. Check metric names in Prometheus UI

### Alerts Not Firing

**Possible Causes:**
1. Alert rules not loaded
2. Notification channel not configured
3. Alert conditions not met

**Solutions:**
1. Check Prometheus alert rules: `http://prometheus:9090/alerts`
2. Configure notification channel in Grafana
3. Verify alert expression syntax

### High Memory Usage in Grafana

**Possible Causes:**
1. Too many panels
2. Long time ranges
3. High query resolution

**Solutions:**
1. Reduce number of panels
2. Shorten time ranges
3. Increase query step interval

---

## Maintenance

### Regular Tasks

1. **Weekly:** Review dashboard metrics for anomalies
2. **Monthly:** Review and adjust alert thresholds
3. **Quarterly:** Audit dashboard relevance and add/remove panels
4. **Annually:** Review dashboard architecture and consider reorganization

### Backup and Restore

**Export Dashboards:**
```bash
grafana-cli admin export-dashboard <uid>
```

**Import Dashboards:**
```bash
grafana-cli admin import-dashboard <file>
```

---

## Conclusion

These dashboards provide comprehensive visibility into MatchHire backend performance. Regular monitoring and alerting will ensure:

1. **Proactive Issue Detection:** Catch problems before users do
2. **Performance Trend Analysis:** Identify degradation over time
3. **Capacity Planning:** Plan for growth based on metrics
4. **Incident Response:** Quick diagnosis during outages

**Next Steps:**
1. Import dashboards to Grafana
2. Configure Prometheus alert rules
3. Set up notification channels
4. Train team on dashboard usage
5. Establish regular review cadence

---

**Document Version:** 1.0
**Last Updated:** 2026-07-22
