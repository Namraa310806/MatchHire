"""
Observability Core Architecture.

This module provides the core observability components that serve as the
foundation for the entire observability platform. These components are
provider-independent and orthogonal to business logic.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import threading
from contextlib import contextmanager


class ObservabilityComponent(Enum):
    """Types of observability components."""
    SEARCH = "search"
    RANKING = "ranking"
    RECOMMENDATION = "recommendation"
    PROVIDER = "provider"
    CACHE = "cache"
    PIPELINE = "pipeline"
    SIGNAL = "signal"
    BUSINESS_RULE = "business_rule"
    DIVERSIFICATION = "diversification"
    EXPLANATION = "explanation"


class EventType(Enum):
    """Types of observability events."""
    REQUEST_START = "request_start"
    REQUEST_END = "request_end"
    ERROR = "error"
    WARNING = "warning"
    METRIC = "metric"
    TRACE = "trace"
    LOG = "log"
    AUDIT = "audit"
    HEALTH_CHECK = "health_check"
    DIAGNOSTIC = "diagnostic"


@dataclass
class ObservabilityConfig:
    """Configuration for the observability system."""
    
    # General settings
    enabled: bool = True
    sampling_rate: float = 1.0
    environment: str = "production"
    service_name: str = "matchhire-search"
    
    # Metrics settings
    metrics_enabled: bool = True
    metrics_export_interval_seconds: int = 60
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    
    # Tracing settings
    tracing_enabled: bool = True
    opentelemetry_enabled: bool = True
    trace_exporter: str = "otlp"  # otlp, jaeger, zipkin
    jaeger_endpoint: Optional[str] = None
    zipkin_endpoint: Optional[str] = None
    otlp_endpoint: Optional[str] = None
    
    # Logging settings
    logging_enabled: bool = True
    log_level: str = "INFO"
    log_format: str = "json"
    log_to_file: bool = False
    log_file_path: Optional[str] = None
    
    # Audit settings
    audit_enabled: bool = True
    audit_retention_days: int = 90
    
    # Diagnostics settings
    diagnostics_enabled: bool = True
    slow_query_threshold_ms: float = 1000.0
    slow_ranking_threshold_ms: float = 500.0
    slow_recommendation_threshold_ms: float = 2000.0
    
    # Health settings
    health_check_interval_seconds: int = 30
    
    # Profiling settings
    profiling_enabled: bool = False
    profiling_interval_seconds: int = 60
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "enabled": self.enabled,
            "sampling_rate": self.sampling_rate,
            "environment": self.environment,
            "service_name": self.service_name,
            "metrics_enabled": self.metrics_enabled,
            "metrics_export_interval_seconds": self.metrics_export_interval_seconds,
            "prometheus_enabled": self.prometheus_enabled,
            "prometheus_port": self.prometheus_port,
            "tracing_enabled": self.tracing_enabled,
            "opentelemetry_enabled": self.opentelemetry_enabled,
            "trace_exporter": self.trace_exporter,
            "jaeger_endpoint": self.jaeger_endpoint,
            "zipkin_endpoint": self.zipkin_endpoint,
            "otlp_endpoint": self.otlp_endpoint,
            "logging_enabled": self.logging_enabled,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "log_to_file": self.log_to_file,
            "log_file_path": self.log_file_path,
            "audit_enabled": self.audit_enabled,
            "audit_retention_days": self.audit_retention_days,
            "diagnostics_enabled": self.diagnostics_enabled,
            "slow_query_threshold_ms": self.slow_query_threshold_ms,
            "slow_ranking_threshold_ms": self.slow_ranking_threshold_ms,
            "slow_recommendation_threshold_ms": self.slow_recommendation_threshold_ms,
            "health_check_interval_seconds": self.health_check_interval_seconds,
            "profiling_enabled": self.profiling_enabled,
            "profiling_interval_seconds": self.profiling_interval_seconds,
        }


@dataclass
class ObservabilityContext:
    """
    Context for observability operations.
    
    Contains contextual information that flows through the entire
    observability pipeline, including correlation IDs, trace IDs,
    and user information.
    """
    
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    user_id: Optional[str] = None
    recruiter_id: Optional[str] = None
    session_id: Optional[str] = None
    component: Optional[ObservabilityComponent] = None
    provider: Optional[str] = None
    entity_type: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "user_id": self.user_id,
            "recruiter_id": self.recruiter_id,
            "session_id": self.session_id,
            "component": self.component.value if self.component else None,
            "provider": self.provider,
            "entity_type": self.entity_type,
            "tags": self.tags,
            "metadata": self.metadata,
        }
    
    def with_tag(self, key: str, value: str) -> "ObservabilityContext":
        """Add a tag to the context."""
        self.tags[key] = value
        return self
    
    def with_metadata(self, key: str, value: Any) -> "ObservabilityContext":
        """Add metadata to the context."""
        self.metadata[key] = value
        return self
    
    def create_child(self) -> "ObservabilityContext":
        """Create a child context with inherited trace ID."""
        child = ObservabilityContext(
            trace_id=self.trace_id,
            parent_span_id=self.span_id,
            user_id=self.user_id,
            recruiter_id=self.recruiter_id,
            session_id=self.session_id,
            tags=self.tags.copy(),
            metadata=self.metadata.copy(),
        )
        return child


@dataclass
class ObservabilityEvent:
    """
    Event model for observability data.
    
    Represents a single observability event that can be a metric,
    trace, log, audit entry, or diagnostic.
    """
    
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Optional[ObservabilityContext] = None
    component: Optional[ObservabilityComponent] = None
    level: str = "INFO"
    message: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context.to_dict() if self.context else None,
            "component": self.component.value if self.component else None,
            "level": self.level,
            "message": self.message,
            "data": self.data,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "stack_trace": self.stack_trace,
        }


class ObservabilityManager:
    """
    Central observability manager for MatchHire search.
    
    This managercoordinates all observability components including
    metrics, tracing, logging, audit, and diagnostics. It provides
    a unified interface for observability operations.
    """
    
    _instance: Optional["ObservabilityManager"] = None
    _lock = threading.Lock()
    
    def __new__(cls, config: Optional[ObservabilityConfig] = None):
        """Create or return the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[ObservabilityConfig] = None):
        """Initialize the observability manager."""
        if self._initialized:
            return
        
        self._config = config or ObservabilityConfig()
        
        # Initialize components
        from .telemetry import TelemetryCollector
        from .metrics import MetricsRegistry
        from .tracing import TracingManager
        from .logging import LoggingManager
        from .audit import AuditManager
        from .diagnostics import DiagnosticsManager
        from .health import HealthMonitor
        
        self._telemetry_collector = TelemetryCollector(self._config)
        self._metrics_registry = MetricsRegistry(self._config)
        self._tracing_manager = TracingManager(self._config)
        self._logging_manager = LoggingManager(self._config)
        self._audit_manager = AuditManager(self._config)
        self._diagnostics_manager = DiagnosticsManager(self._config)
        self._health_monitor = HealthMonitor(self._config)
        
        # Context storage (thread-local)
        self._context_storage = threading.local()
        
        self._initialized = True
    
    @property
    def config(self) -> ObservabilityConfig:
        """Get the observability configuration."""
        return self._config
    
    @property
    def telemetry(self) -> "TelemetryCollector":
        """Get the telemetry collector."""
        return self._telemetry_collector
    
    @property
    def metrics(self) -> "MetricsRegistry":
        """Get the metrics registry."""
        return self._metrics_registry
    
    @property
    def tracing(self) -> "TracingManager":
        """Get the tracing manager."""
        return self._tracing_manager
    
    @property
    def logging(self) -> "LoggingManager":
        """Get the logging manager."""
        return self._logging_manager
    
    @property
    def audit(self) -> "AuditManager":
        """Get the audit manager."""
        return self._audit_manager
    
    @property
    def diagnostics(self) -> "DiagnosticsManager":
        """Get the diagnostics manager."""
        return self._diagnostics_manager
    
    @property
    def health(self) -> "HealthMonitor":
        """Get the health monitor."""
        return self._health_monitor
    
    def get_context(self) -> ObservabilityContext:
        """
        Get the current observability context.
        
        Returns:
            Current context or creates a new one
        """
        if not hasattr(self._context_storage, 'context'):
            self._context_storage.context = ObservabilityContext()
        return self._context_storage.context
    
    def set_context(self, context: ObservabilityContext) -> None:
        """
        Set the current observability context.
        
        Args:
            context: Context to set
        """
        self._context_storage.context = context
    
    def clear_context(self) -> None:
        """Clear the current observability context."""
        if hasattr(self._context_storage, 'context'):
            delattr(self._context_storage, 'context')
    
    @contextmanager
    def context_scope(self, context: ObservabilityContext):
        """
        Context manager for setting a temporary context.
        
        Args:
            context: Context to use within the scope
        """
        old_context = None
        if hasattr(self._context_storage, 'context'):
            old_context = self._context_storage.context
        
        self._context_storage.context = context
        
        try:
            yield context
        finally:
            if old_context is not None:
                self._context_storage.context = old_context
            else:
                self.clear_context()
    
    def record_event(self, event: ObservabilityEvent) -> None:
        """
        Record an observability event.
        
        Args:
            event: Event to record
        """
        if not self._config.enabled:
            return
        
        # Apply sampling
        import random
        if random.random() > self._config.sampling_rate:
            return
        
        # Route to appropriate component
        if event.event_type == EventType.METRIC:
            self._metrics_registry.record_metric(event)
        elif event.event_type == EventType.TRACE:
            self._tracing_manager.record_span(event)
        elif event.event_type == EventType.LOG:
            self._logging_manager.log(event)
        elif event.event_type == EventType.AUDIT:
            self._audit_manager.record_audit(event)
        elif event.event_type == EventType.DIAGNOSTIC:
            self._diagnostics_manager.record_diagnostic(event)
        
        # Always send to telemetry collector
        self._telemetry_collector.collect(event)
    
    def start_span(
        self,
        name: str,
        component: ObservabilityComponent,
        **kwargs
    ) -> "Span":
        """
        Start a new tracing span.
        
        Args:
            name: Span name
            component: Component type
            **kwargs: Additional span attributes
            
        Returns:
            Span object
        """
        context = self.get_context()
        return self._tracing_manager.start_span(
            name=name,
            component=component,
            context=context,
            **kwargs
        )
    
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: str = "gauge",
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record a metric.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric (counter, gauge, histogram, summary)
            tags: Optional tags
        """
        context = self.get_context()
        event = ObservabilityEvent(
            event_type=EventType.METRIC,
            context=context,
            data={
                "name": name,
                "value": value,
                "type": metric_type,
                "tags": tags or {},
            },
        )
        self.record_event(event)
    
    def log(
        self,
        level: str,
        message: str,
        **kwargs
    ) -> None:
        """
        Log a message.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            **kwargs: Additional log data
        """
        context = self.get_context()
        event = ObservabilityEvent(
            event_type=EventType.LOG,
            context=context,
            level=level,
            message=message,
            data=kwargs,
        )
        self.record_event(event)
    
    def audit(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        **kwargs
    ) -> None:
        """
        Record an audit event.
        
        Args:
            action: Action performed
            entity_type: Type of entity
            entity_id: ID of entity
            **kwargs: Additional audit data
        """
        context = self.get_context()
        event = ObservabilityEvent(
            event_type=EventType.AUDIT,
            context=context,
            data={
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                **kwargs,
            },
        )
        self.record_event(event)
    
    def get_telemetry(self) -> Dict[str, Any]:
        """
        Get collected telemetry data.
        
        Returns:
            Telemetry data dictionary
        """
        return self._telemetry_collector.get_telemetry()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get metrics summary.
        
        Returns:
            Metrics summary dictionary
        """
        return self._metrics_registry.get_summary()
    
    def get_diagnostics_report(self) -> Dict[str, Any]:
        """
        Get diagnostics report.
        
        Returns:
            Diagnostics report dictionary
        """
        return self._diagnostics_manager.get_report()
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status.
        
        Returns:
            Health status dictionary
        """
        return self._health_monitor.get_status()
    
    def shutdown(self) -> None:
        """Shutdown the observability manager and cleanup resources."""
        self._telemetry_collector.shutdown()
        self._metrics_registry.shutdown()
        self._tracing_manager.shutdown()
        self._logging_manager.shutdown()
        self._audit_manager.shutdown()
        self._diagnostics_manager.shutdown()
        self._health_monitor.shutdown()


# Global instance
_global_manager: Optional[ObservabilityManager] = None


def get_manager(config: Optional[ObservabilityConfig] = None) -> ObservabilityManager:
    """
    Get the global observability manager instance.
    
    Args:
        config: Optional configuration (only used on first call)
        
    Returns:
        ObservabilityManager singleton instance
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = ObservabilityManager(config)
    return _global_manager
