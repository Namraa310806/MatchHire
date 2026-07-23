"""
Observability Platform for MatchHire Search, Ranking, and Recommendations.

This module provides a production-grade observability platform that is:
- Provider-independent (works with any search provider)
- Orthogonal to business logic (uses decorators, middleware, hooks)
- OpenTelemetry-compatible
- Prometheus-compatible
- Production-ready

Key components:
- ObservabilityManager: Central orchestrator
- TelemetryCollector: Collects metrics, traces, logs
- MetricsRegistry: Registry for all metrics
- TracingManager: Distributed tracing with OpenTelemetry
- LoggingManager: Structured logging
- AuditManager: Audit trail for operations
- DiagnosticsManager: Diagnostic information
- ObservabilityContext: Context for observability operations
- ObservabilityEvent: Event model for observability data
"""

from .core import (
    ObservabilityManager,
    ObservabilityContext,
    ObservabilityEvent,
    ObservabilityConfig,
)
from .telemetry import (
    TelemetryCollector,
    TelemetryData,
)
from .metrics import (
    MetricsRegistry,
    Metric,
    Counter,
    Gauge,
    Histogram,
    Summary,
)
from .tracing import (
    TracingManager,
    Span,
    SpanContext,
)
from .logging import (
    LoggingManager,
    StructuredLogger,
)
from .audit import (
    AuditManager,
    AuditEvent,
)
from .diagnostics import (
    DiagnosticsManager,
    DiagnosticReport,
)
from .health import (
    HealthMonitor,
    HealthStatus,
    HealthCheck,
)
from .instrumentation import (
    instrument_search,
    instrument_ranking,
    instrument_recommendation,
    instrument_provider,
)
from .quality_metrics import (
    QualityMetricsCollector,
    QualityMetric,
    QualityMetricType,
)
from .dashboards import (
    DashboardRegistry,
    Dashboard,
    DashboardPanel,
)
from .alerts import (
    AlertRegistry,
    Alert,
    AlertRule,
    AlertSeverity,
)
from .profiling import (
    Profiler,
    QueryProfiler,
    ProfileResult,
)

__all__ = [
    # Core
    "ObservabilityManager",
    "ObservabilityContext",
    "ObservabilityEvent",
    "ObservabilityConfig",
    # Telemetry
    "TelemetryCollector",
    "TelemetryData",
    # Metrics
    "MetricsRegistry",
    "Metric",
    "Counter",
    "Gauge",
    "Histogram",
    "Summary",
    # Tracing
    "TracingManager",
    "Span",
    "SpanContext",
    # Logging
    "LoggingManager",
    "StructuredLogger",
    # Audit
    "AuditManager",
    "AuditEvent",
    # Diagnostics
    "DiagnosticsManager",
    "DiagnosticReport",
    # Health
    "HealthMonitor",
    "HealthStatus",
    "HealthCheck",
    # Instrumentation
    "instrument_search",
    "instrument_ranking",
    "instrument_recommendation",
    "instrument_provider",
    # Quality Metrics
    "QualityMetricsCollector",
    "QualityMetric",
    "QualityMetricType",
    # Dashboards
    "DashboardRegistry",
    "Dashboard",
    "DashboardPanel",
    # Alerts
    "AlertRegistry",
    "Alert",
    "AlertRule",
    "AlertSeverity",
    # Profiling
    "Profiler",
    "QueryProfiler",
    "ProfileResult",
]
