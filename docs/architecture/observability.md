# MatchHire Observability Architecture

## Overview

MatchHire implements a comprehensive observability platform following the three pillars of observability: **Logs**, **Metrics**, and **Traces**. This architecture enables engineers to understand system health, performance, failures, and usage patterns.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         MatchHire Backend                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Django     │    │   Celery     │    │   Workers    │      │
│  │   Application│    │   Tasks      │    │   Processes  │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                   │                   │              │
│         │                   │                   │              │
│  ┌──────▼───────────────────▼───────────────────▼───────┐      │
│  │              Observability Layer                      │      │
│  ├──────────────────────────────────────────────────────┤      │
│  │  • Structured JSON Logging                            │      │
│  │  • Request Correlation IDs                            │      │
│  │  • Prometheus Metrics                                 │      │
│  │  • Sentry Error Tracking                              │      │
│  │  • Health Endpoints                                    │      │
│  └──────┬───────────────────────────────────────────────┘      │
│         │                                                       │
│         │                                                       │
└─────────┼───────────────────────────────────────────────────────┘
          │
          │
┌─────────▼───────────────────────────────────────────────────────┐
│                    Data Collection                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Logs       │    │   Metrics    │    │   Errors     │      │
│  │  (JSON)      │    │ (Prometheus) │    │  (Sentry)    │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                   │                   │              │
│         │                   │                   │              │
└─────────┼───────────────────┼───────────────────┼──────────────┘
          │                   │                   │
┌─────────▼───────────────────▼───────────────────▼──────────────┐
│                    Monitoring Stack                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Loki/ELK    │    │  Prometheus  │    │   Sentry     │      │
│  │  (Logs)      │    │  (Metrics)   │    │  (Errors)    │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                   │                   │              │
│         │                   │                   │              │
└─────────┼───────────────────┼───────────────────┼──────────────┘
          │                   │                   │
┌─────────▼───────────────────▼───────────────────▼──────────────┐
│                  Visualization & Alerting                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Grafana    │    │  Alertmanager│    │   PagerDuty  │      │
│  │ (Dashboards) │    │   (Alerts)   │    │ (On-call)    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Structured Logging

**Purpose**: Capture detailed information about system events and operations.

**Implementation**:
- JSON-formatted logs for production
- Structured fields: timestamp, level, logger, request_id, user_id, service, environment
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log aggregation: Loki or ELK Stack

**Key Features**:
- Request correlation IDs for distributed tracing
- User context for security auditing
- Service identification for multi-service environments
- Environment tagging for multi-deployment scenarios

**Configuration**:
```python
# Production: JSON logging
LOGGING = {
    "formatters": {
        "json": {
            "()": "matchhire_backend.core.logging_config.JsonFormatter",
        }
    }
}

# Development: Human-readable logging
LOGGING = {
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {request_id} {message}",
        }
    }
}
```

**Log Fields**:
- `timestamp`: ISO 8601 format
- `level`: Log level (INFO, ERROR, etc.)
- `logger`: Logger name (e.g., "django.request")
- `message`: Log message
- `request_id`: Correlation ID for request tracing
- `user_id`: User ID (when available)
- `service`: Service name ("matchhire-backend")
- `environment`: Environment (production, development)
- `module`: Python module name
- `function`: Function name
- `process`: Process ID
- `thread`: Thread ID

### 2. Request Correlation

**Purpose**: Track requests across the system for debugging and analysis.

**Implementation**:
- Middleware generates or accepts X-Request-ID header
- Request ID propagated through all log statements
- Request ID included in response headers
- Request ID sent to Sentry for error correlation

**Middleware Flow**:
```
Request → RequestIDMiddleware → Generate/Validate UUID → 
Store in thread-local → Process Request → 
Include in logs → Include in response → Clear thread-local
```

**Benefits**:
- Trace requests across log streams
- Debug distributed issues
- Correlate errors with requests
- Performance analysis per request

### 3. Prometheus Metrics

**Purpose**: Quantitative measurement of system behavior and performance.

**Metric Types**:

**Counters** (monotonically increasing):
- `http_requests_total`: Total HTTP requests by method, endpoint, status
- `db_errors_total`: Total database errors by type
- `cache_hits_total`: Total cache hits
- `cache_misses_total`: Total cache misses
- `celery_tasks_total`: Total Celery tasks by task name, status
- `resumes_uploaded_total`: Total resumes uploaded
- `jobs_created_total`: Total jobs created
- `applications_submitted_total`: Total applications submitted
- `matching_operations_total`: Total matching operations
- `notifications_sent_total`: Total notifications sent by type
- `interviews_scheduled_total`: Total interviews scheduled

**Histograms** (distributions):
- `http_request_duration_seconds`: HTTP request duration by method, endpoint
- `db_query_duration_seconds`: Database query duration by operation
- `celery_task_duration_seconds`: Celery task duration by task name

**Gauges** (current values):
- `db_connections_active`: Active database connections
- `celery_worker_active_tasks`: Number of active Celery tasks
- `celery_queue_length`: Number of tasks in Celery queue by queue name
- `application_uptime_seconds`: Application uptime in seconds

**Info** (metadata):
- `application_info`: Application version, environment, service name

**Metrics Endpoint**:
```
GET /api/v1/metrics/
Content-Type: text/plain
```

**Scraping Configuration**:
```yaml
scrape_configs:
  - job_name: 'matchhire-backend'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/api/v1/metrics/'
    scrape_interval: 15s
```

### 4. Health Endpoints

**Purpose**: Provide system health status for orchestration and monitoring.

**Endpoints**:

**Basic Health Check**:
```
GET /api/v1/health/
Response: {"status": "healthy"}
```

**Liveness Probe**:
```
GET /api/v1/health/live
Response: {"status": "healthy"}
```

**Readiness Probe**:
```
GET /api/v1/health/ready
Response: {
    "status": "healthy",
    "checks": {
        "database": true,
        "redis": true,
        "celery": true
    }
}
```

**Detailed Health Check**:
```
GET /api/v1/health/detailed
Response: {
    "status": "healthy",
    "checks": {
        "database": true,
        "redis": true,
        "celery": true
    },
    "metrics": {
        "celery_workers": 2,
        "disk": {
            "total_gb": 100.0,
            "used_gb": 45.2,
            "free_gb": 54.8,
            "percent_used": 45.2
        },
        "uptime_seconds": 3600.5
    }
}
```

**Version Information**:
```
GET /api/v1/health/version
Response: {
    "version": "1.0.0",
    "commit": "abc123",
    "environment": "production",
    "service": "matchhire-backend",
    "uptime_seconds": 3600.5
}
```

### 5. Sentry Integration

**Purpose**: Error tracking, performance monitoring, and issue aggregation.

**Features**:
- Automatic exception capture
- Performance monitoring (traces)
- Release tracking
- User context
- Request context
- Breadcrumb tracking
- Alerting

**Configuration**:
```python
SENTRY_DSN = "https://..."
SENTRY_RELEASE = "1.0.0"
SENTRY_TRACES_SAMPLE_RATE = 0.1  # 10% of transactions
SENTRY_ERROR_SAMPLE_RATE = 1.0   # 100% of errors
```

**Integrations**:
- Django: HTTP requests, exceptions
- Celery: Task execution, failures
- Redis: Cache operations
- Logging: Log events as breadcrumbs

**Context Enrichment**:
- User ID and email
- Request ID for correlation
- Custom tags (service, environment)
- Custom extra data

## Data Flow

### Request Flow

```
1. User Request → Django Application
2. RequestIDMiddleware generates/validates request ID
3. MetricsMiddleware records start time
4. Request processed by views/services
5. Logs written with request ID and user context
6. Metrics recorded (request count, duration, status)
7. Response sent with X-Request-ID header
8. Sentry captures any exceptions with context
```

### Background Task Flow

```
1. Task queued in Redis
2. Celery worker picks up task
3. Task executed with request ID (if available)
4. Logs written with task context
5. Metrics recorded (task count, duration, status)
6. Sentry captures any task failures
7. Result stored in Redis
```

### Error Flow

```
1. Exception occurs in application
2. Exception caught by Django/Sentry
3. Sentry captures exception with:
   - Stack trace
   - Request context
   - User context
   - Request ID
   - Breadcrumbs
4. Alert sent to configured channels
5. Error logged to log stream
6. Metrics recorded (error count)
```

## Monitoring Stack

### Local Development
- Logs: Console output (human-readable)
- Metrics: Prometheus endpoint (manual scraping)
- Errors: Console output

### Staging
- Logs: Loki or ELK Stack
- Metrics: Prometheus + Grafana
- Errors: Sentry (test environment)

### Production
- Logs: Loki or ELK Stack (retention: 30 days)
- Metrics: Prometheus + Grafana (retention: 15 days)
- Errors: Sentry (production environment)
- Alerting: Alertmanager + PagerDuty + Slack

## Alerting Strategy

### Alert Levels

**P1 (Critical)**:
- High error rate (> 5%)
- Database unavailable
- Redis unavailable
- High latency (P95 > 2s)
- Response time: Immediate

**P2 (Warning)**:
- Queue backlog (> 1000 tasks)
- Worker offline
- Low cache hit rate (< 70%)
- High memory usage (> 80%)
- High CPU usage (> 80%)
- Response time: Within 30 minutes

**P3 (Info)**:
- Disk space low (> 80%)
- SSL certificate expiring
- Zero business activity
- Response time: Within 4 hours

### Alert Channels

**Critical**: PagerDuty + Slack #alerts-critical
**Warning**: Slack #alerts-warning
**Info**: Email + Slack #alerts-info

## Dashboards

### Overview Dashboard
- Request rate
- Request duration (P95)
- Error rate
- Status code distribution
- Database query duration
- Cache hit rate
- Celery queue length
- Application uptime

### Performance Dashboard
- Request duration by endpoint
- Database query performance
- Cache performance
- External service latency

### Business Metrics Dashboard
- Resumes uploaded rate
- Jobs created rate
- Applications submitted rate
- Interviews scheduled rate
- Notifications sent rate

### Infrastructure Dashboard
- Container CPU usage
- Container memory usage
- Disk usage
- Network I/O
- Database connections
- Redis memory usage

## Runbooks

Operational runbooks are provided for common incidents:
- [High Error Rate](../runbooks/high-error-rate.md)
- [Database Outage](../runbooks/database-outage.md)
- [High Latency](../runbooks/high-latency.md)
- [Redis Outage](../runbooks/redis-outage.md)
- [Queue Backlog](../runbooks/queue-backlog.md)
- [Worker Offline](../runbooks/worker-offline.md)
- [High CPU Usage](../runbooks/high-cpu-usage.md)
- [High Memory Usage](../runbooks/high-memory-usage.md)

## Best Practices

### Logging
- Use structured logging with consistent fields
- Include correlation IDs in all logs
- Log at appropriate levels (INFO for normal, ERROR for failures)
- Avoid logging sensitive data (passwords, tokens, PII)
- Use log aggregation for centralized analysis

### Metrics
- Use appropriate metric types (Counter, Histogram, Gauge)
- Label metrics with relevant dimensions
- Avoid high cardinality labels
- Monitor metric growth and retention
- Use histograms for distributions

### Error Tracking
- Capture all exceptions with context
- Include user and request context
- Use breadcrumbs for debugging
- Set appropriate sampling rates
- Configure alerting for critical errors

### Health Checks
- Implement liveness and readiness probes
- Check critical dependencies (database, Redis)
- Return appropriate HTTP status codes
- Include detailed information in detailed endpoint
- Use health checks for orchestration

## Future Enhancements

### Distributed Tracing
- OpenTelemetry integration
- Span propagation across services
- Trace visualization in Grafana
- Performance analysis across service boundaries

### Advanced Metrics
- Database connection pool metrics
- Redis connection metrics
- External service metrics
- Custom business metrics

### Log Analysis
- Log-based metrics (e.g., error rate from logs)
- Log anomaly detection
- Machine learning for log analysis
- Automated log parsing

### Alerting
- Machine learning-based anomaly detection
- Predictive alerting
- Dynamic threshold adjustment
- Alert noise reduction

## References

- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)
- [Sentry Documentation](https://docs.sentry.io/)
- [Django Logging Documentation](https://docs.djangoproject.com/en/stable/topics/logging/)
- [Alerting Recommendations](../monitoring/alerting-recommendations.md)
