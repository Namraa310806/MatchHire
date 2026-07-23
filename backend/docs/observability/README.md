# Observability Platform Documentation

## Overview

The MatchHire Observability Platform provides production-grade monitoring, tracing, logging, and diagnostics for the search, ranking, and recommendation systems. The platform is designed to be:

- **Provider-independent**: Works with any search provider (PostgreSQL, Elasticsearch, etc.)
- **Orthogonal to business logic**: Uses decorators, middleware, hooks, and adapters
- **OpenTelemetry-compatible**: Supports distributed tracing with OpenTelemetry
- **Prometheus-compatible**: Metrics export in Prometheus format
- **Production-ready**: Built for scale and reliability

## Architecture

### Core Components

- **ObservabilityManager**: Central orchestrator for all observability operations
- **TelemetryCollector**: Aggregates metrics, traces, logs, and diagnostics
- **MetricsRegistry**: Registry for all metrics (Counter, Gauge, Histogram, Summary)
- **TracingManager**: Distributed tracing with OpenTelemetry support
- **LoggingManager**: Structured logging with JSON format
- **AuditManager**: Audit trail for compliance and security
- **DiagnosticsManager**: Diagnostic information and issue detection
- **HealthMonitor**: Health monitoring for all components

### Key Design Principles

1. **Orthogonality**: Observability is completely separate from business logic
2. **Provider Independence**: Works with any search provider
3. **Extensibility**: Easy to add new metrics, traces, and diagnostics
4. **Performance**: Minimal overhead on production systems
5. **Reliability**: Observability failures don't impact core functionality

## Quick Start

### Initialization

```python
from apps.search.observability import get_manager, ObservabilityConfig

# Initialize with custom configuration
config = ObservabilityConfig(
    enabled=True,
    sampling_rate=1.0,
    environment="production",
    metrics_enabled=True,
    tracing_enabled=True,
    logging_enabled=True,
)

manager = get_manager(config)
```

### Instrumenting Code

```python
from apps.search.observability.instrumentation import instrument_search

@instrument_search
def search_function(query):
    # Your search logic here
    return results
```

### Recording Metrics

```python
manager = get_manager()

# Record a metric
manager.record_metric(
    name="custom_metric",
    value=42.0,
    metric_type="gauge",
    tags={"component": "search"},
)
```

### Logging

```python
manager = get_manager()

# Log a message
manager.log(
    level="INFO",
    message="Search completed successfully",
    duration_ms=123.45,
)
```

### Tracing

```python
from apps.search.observability.instrumentation import observe_operation
from apps.search.observability.core import ObservabilityComponent

with observe_operation(
    operation_name="custom_operation",
    component=ObservabilityComponent.SEARCH,
) as span:
    # Your operation logic here
    span.set_attribute("custom_attr", "value")
```

## Metrics

### Available Metrics

#### Search Metrics
- `search_requests_total`: Total number of search requests
- `search_latency_seconds`: Search request latency histogram
- `search_errors_total`: Total number of search errors

#### Ranking Metrics
- `ranking_requests_total`: Total number of ranking requests
- `ranking_latency_seconds`: Ranking request latency histogram
- `ranking_signals_active`: Number of active ranking signals

#### Recommendation Metrics
- `recommendation_requests_total`: Total number of recommendation requests
- `recommendation_latency_seconds`: Recommendation request latency histogram
- `recommendations_generated_total`: Total number of recommendations generated

#### Provider Metrics
- `provider_requests_total`: Total number of provider requests
- `provider_latency_seconds`: Provider request latency histogram
- `provider_health`: Provider health status gauge

#### Cache Metrics
- `cache_hits_total`: Total number of cache hits
- `cache_misses_total`: Total number of cache misses
- `cache_size`: Current cache size

### Custom Metrics

```python
from apps.search.observability import get_manager

manager = get_manager()

# Register a custom counter
counter = manager.metrics.register_counter(
    name="custom_counter",
    description="Custom counter metric",
    tags={"component": "custom"},
)

# Increment the counter
counter.inc(5.0)

# Or use the convenience method
manager.metrics.increment_counter("custom_counter", 5.0)
```

### Prometheus Export

```python
from apps.search.observability import get_manager

manager = get_manager()
prometheus_export = manager.metrics.export_prometheus()

print(prometheus_export)
```

## Tracing

### Distributed Tracing

The observability platform supports distributed tracing with OpenTelemetry compatibility:

```python
from apps.search.observability import get_manager
from apps.search.observability.core import ObservabilityComponent

manager = get_manager()

# Start a span
span = manager.start_span(
    name="search_operation",
    component=ObservabilityComponent.SEARCH,
)

# Add attributes
span.set_attribute("query", "python developer")
span.set_attribute("filters", {"location": "remote"})

# Add events
span.add_event("cache_lookup", {"hit": True})

# End the span
manager.tracing.end_span(span)
```

### Context Propagation

Context is automatically propagated across components:

```python
from apps.search.observability import get_manager

manager = get_manager()

# Get current context
context = manager.get_context()

# Create child context for sub-operations
child_context = context.create_child()

# Use in operations
manager.set_context(child_context)
```

### OpenTelemetry Integration

To enable OpenTelemetry export:

```python
from apps.search.observability import ObservabilityConfig

config = ObservabilityConfig(
    opentelemetry_enabled=True,
    trace_exporter="otlp",
    otlp_endpoint="http://localhost:4317",
)
```

## Logging

### Structured Logging

All logs are structured in JSON format:

```python
from apps.search.observability import get_manager

manager = get_manager()

# Log at different levels
manager.logging.debug("Debug message")
manager.logging.info("Info message")
manager.logging.warning("Warning message")
manager.logging.error("Error message")
manager.logging.critical("Critical message")
```

### Log Context

Logs automatically include observability context:

```python
from apps.search.observability import get_manager
from apps.search.observability.core import ObservabilityContext

manager = get_manager()
context = ObservabilityContext()
context.with_tag("user_id", "12345")

manager.set_context(context)

manager.logging.info("User action", action="search")
```

## Diagnostics

### Automatic Diagnostics

The platform automatically detects and records diagnostics:

- Slow queries (>1s threshold)
- Slow ranking (>500ms threshold)
- Slow recommendations (>2s threshold)
- Provider failures
- High error rates (>5% threshold)
- Cache failures

### Manual Diagnostics

```python
from apps.search.observability import get_manager
from apps.search.observability.core import ObservabilityComponent

manager = get_manager()

# Record a diagnostic
manager.diagnostics.record_diagnostic(
    diagnostic_type=manager.diagnostics.DiagnosticType.SLOW_QUERY,
    severity=manager.diagnostics.Severity.WARNING,
    message="Custom diagnostic",
    component=ObservabilityComponent.SEARCH,
)
```

### Diagnostic Reports

```python
from apps.search.observability import get_manager

manager = get_manager()
report = manager.get_diagnostics_report()

print(report)
```

## Health Monitoring

### Health Checks

Health checks run automatically for all components:

```python
from apps.search.observability import get_manager

manager = get_manager()
status = manager.get_health_status()

print(status)
```

### Custom Health Checks

```python
from apps.search.observability.health import HealthCheck, HealthMonitor

def custom_check():
    # Your health check logic
    return {"status": "healthy", "details": {}}

check = HealthCheck(
    name="custom_check",
    component=ObservabilityComponent.CUSTOM,
    check_function=custom_check,
)

monitor.health.register_health_check(check)
```

## Dashboards

### Available Dashboards

- **Search Dashboard**: Search operations, latency, errors
- **Ranking Dashboard**: Ranking pipeline, signals, performance
- **Recommendation Dashboard**: Recommendations, strategies, diversity
- **Infrastructure Dashboard**: Providers, cache, indexing
- **Performance Dashboard**: Overall performance metrics
- **Operations Dashboard**: Health, errors, diagnostics
- **Quality Dashboard**: CTR, acceptance, diversity scores

### Exporting Dashboards

```python
from apps.search.observability.dashboards import DashboardRegistry

registry = DashboardRegistry()

# Export to Grafana format
grafana_dashboard = registry.export_grafana("Search Dashboard")
```

## Alerts

### Available Alerts

- High latency (search, ranking, recommendation)
- High error rate
- Provider unavailable
- Cache failures
- Pipeline failures
- Health degradation
- Slow indexing

### Alert Configuration

```python
from apps.search.observability.alerts import AlertRegistry

registry = AlertRegistry()

# Export to Prometheus Alertmanager format
prometheus_alerts = registry.export_prometheus()
```

## Quality Metrics

### Quality Hooks

Quality metrics hooks track business-level metrics:

- **CTR Hook**: Click-through rate
- **Acceptance Hook**: Recommendation acceptance rate
- **Success Hook**: Search success rate
- **Abandonment Hook**: Search abandonment rate
- **Diversity Hook**: Recommendation diversity score
- **Coverage Hook**: Recommendation coverage score

### Recording Quality Metrics

```python
from apps.search.observability.quality_metrics import QualityMetricsCollector

collector = QualityMetricsCollector(config)

# Record a click
collector.record_click(
    user_id="123",
    result_id="456",
    position=1,
    session_id="abc",
)

# Record recommendation acceptance
collector.record_recommendation_acceptance(
    user_id="123",
    recommendation_id="789",
    entity_type="job",
    entity_id="101",
)
```

## Performance Profiling

### CPU Profiling

```python
from apps.search.observability.profiling import Profiler
from apps.search.observability.core import ObservabilityComponent

profiler = Profiler(config)

with profiler.profile_cpu(ObservabilityComponent.SEARCH, "test_operation"):
    # Your operation here
    pass
```

### Memory Profiling

```python
from apps.search.observability.profiling import Profiler

profiler = Profiler(config)

with profiler.profile_memory(ObservabilityComponent.SEARCH, "test_operation"):
    # Your operation here
    pass
```

### Query Profiling

```python
from apps.search.observability.profiling import QueryProfiler

profiler = QueryProfiler(config)

profile = profiler.profile_query_execution(
    query="python developer",
    filters={"location": "remote"},
    component=ObservabilityComponent.SEARCH,
)
```

## Configuration

### Configuration Options

```python
from apps.search.observability import ObservabilityConfig

config = ObservabilityConfig(
    # General
    enabled=True,
    sampling_rate=1.0,
    environment="production",
    service_name="matchhire-search",
    
    # Metrics
    metrics_enabled=True,
    metrics_export_interval_seconds=60,
    prometheus_enabled=True,
    prometheus_port=9090,
    
    # Tracing
    tracing_enabled=True,
    opentelemetry_enabled=True,
    trace_exporter="otlp",
    otlp_endpoint="http://localhost:4317",
    
    # Logging
    logging_enabled=True,
    log_level="INFO",
    log_format="json",
    
    # Diagnostics
    diagnostics_enabled=True,
    slow_query_threshold_ms=1000.0,
    slow_ranking_threshold_ms=500.0,
    slow_recommendation_threshold_ms=2000.0,
    
    # Health
    health_check_interval_seconds=30,
    
    # Profiling
    profiling_enabled=False,
)
```

## Best Practices

### 1. Use Instrumentation Decorators

Always use the provided decorators for automatic instrumentation:

```python
@instrument_search
def search_function(query):
    # Your logic
    pass
```

### 2. Add Context

Always add relevant context to operations:

```python
context = ObservabilityContext()
context.with_tag("user_id", user_id)
context.with_metadata("query_type", "advanced")
manager.set_context(context)
```

### 3. Use Structured Logging

Use structured logging with key-value pairs:

```python
manager.logging.info(
    "Search completed",
    query=query,
    result_count=len(results),
    duration_ms=latency,
)
```

### 4. Monitor Key Metrics

Focus on key metrics for your component:

- Latency (p50, p95, p99)
- Error rate
- Throughput
- Resource usage

### 5. Set Appropriate Thresholds

Configure thresholds based on your SLAs:

```python
config = ObservabilityConfig(
    slow_query_threshold_ms=1000.0,  # Your SLA
    slow_ranking_threshold_ms=500.0,
)
```

## Troubleshooting

### Observability Not Working

1. Check if observability is enabled: `config.enabled`
2. Check sampling rate: `config.sampling_rate`
3. Check component-specific flags
4. Review logs for initialization errors

### High Overhead

1. Reduce sampling rate
2. Disable expensive profiling
3. Adjust metrics export interval
4. Filter unnecessary metrics

### Missing Traces

1. Ensure tracing is enabled
2. Check OpenTelemetry configuration
3. Verify context propagation
4. Review exporter connectivity

## Extension Guide

### Adding Custom Metrics

```python
# Register custom metric
manager.metrics.register_counter(
    name="my_custom_metric",
    description="My custom metric",
    tags={"component": "my_component"},
)
```

### Adding Custom Diagnostics

```python
# Create custom diagnostic check
def check_custom_condition():
    if condition:
        manager.diagnostics.record_diagnostic(
            diagnostic_type=DiagnosticType.CUSTOM,
            severity=Severity.WARNING,
            message="Custom condition detected",
        )
```

### Adding Custom Health Checks

```python
# Register custom health check
check = HealthCheck(
    name="my_check",
    component=ObservabilityComponent.CUSTOM,
    check_function=my_check_function,
)
manager.health.register_health_check(check)
```

## References

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
