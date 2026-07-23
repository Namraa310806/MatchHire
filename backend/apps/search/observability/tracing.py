"""
Distributed Tracing with OpenTelemetry Compatibility.

This module provides distributed tracing capabilities compatible with
OpenTelemetry. It supports span creation, context propagation, and
export to various backends (OTLP, Jaeger, Zipkin).
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading
import time
import uuid
from contextlib import contextmanager
from .core import ObservabilityConfig, ObservabilityEvent, EventType, ObservabilityComponent, ObservabilityContext


class SpanKind(Enum):
    """Types of spans."""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


@dataclass
class SpanContext:
    """
    Context for span propagation.
    
    Contains trace ID, span ID, and other context needed for
    distributed tracing across service boundaries.
    """
    
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "baggage": self.baggage,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpanContext":
        """Create SpanContext from dictionary."""
        return cls(
            trace_id=data.get("trace_id", ""),
            span_id=data.get("span_id", ""),
            parent_span_id=data.get("parent_span_id"),
            baggage=data.get("baggage", {}),
        )


@dataclass
class Span:
    """
    A single span in a trace.
    
    Represents a unit of work in a distributed system with timing,
    attributes, and links to other spans.
    """
    
    name: str
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: Optional[str] = None
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    kind: SpanKind = SpanKind.INTERNAL
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status: str = "ok"
    status_message: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    links: List[Dict[str, Any]] = field(default_factory=list)
    component: Optional[ObservabilityComponent] = None
    
    def end(self) -> None:
        """End the span and calculate duration."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
    
    def set_attribute(self, key: str, value: Any) -> None:
        """
        Set an attribute on the span.
        
        Args:
            key: Attribute key
            value: Attribute value
        """
        self.attributes[key] = value
    
    def set_attributes(self, attributes: Dict[str, Any]) -> None:
        """
        Set multiple attributes on the span.
        
        Args:
            attributes: Dictionary of attributes
        """
        self.attributes.update(attributes)
    
    def add_event(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        """
        Add an event to the span.
        
        Args:
            name: Event name
            attributes: Event attributes
            timestamp: Event timestamp (defaults to current time)
        """
        self.events.append({
            "name": name,
            "attributes": attributes or {},
            "timestamp": timestamp or time.time(),
        })
    
    def set_status(self, status: str, message: Optional[str] = None) -> None:
        """
        Set the span status.
        
        Args:
            status: Status (ok, error)
            message: Status message
        """
        self.status = status
        self.status_message = message
    
    def record_exception(self, exception: Exception) -> None:
        """
        Record an exception on the span.
        
        Args:
            exception: Exception to record
        """
        self.set_status("error", str(exception))
        self.add_event(
            name="exception",
            attributes={
                "exception.type": type(exception).__name__,
                "exception.message": str(exception),
            },
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "trace_id": self.trace_id,
            "kind": self.kind.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "status_message": self.status_message,
            "attributes": self.attributes,
            "events": self.events,
            "links": self.links,
            "component": self.component.value if self.component else None,
        }


class TracingManager:
    """
    Distributed tracing manager with OpenTelemetry compatibility.
    
    This manager creates and manages spans, handles context propagation,
    and exports traces to various backends.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """
        Initialize the tracing manager.
        
        Args:
            config: Observability configuration
        """
        self._config = config
        self._spans: Dict[str, Span] = {}
        self._active_spans: Dict[str, Span] = {}
        self._lock = threading.Lock()
        
        # Span storage for export
        self._span_buffer: List[Span] = []
        self._buffer_lock = threading.Lock()
        
        # Initialize OpenTelemetry if enabled
        self._otel_tracer = None
        if config.opentelemetry_enabled and config.tracing_enabled:
            self._initialize_opentelemetry()
    
    def _initialize_opentelemetry(self) -> None:
        """Initialize OpenTelemetry tracer."""
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            
            # Configure exporter based on config
            if self._config.trace_exporter == "otlp" and self._config.otlp_endpoint:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter(endpoint=self._config.otlp_endpoint)
            elif self._config.trace_exporter == "jaeger" and self._config.jaeger_endpoint:
                from opentelemetry.exporter.jaeger.thrift import JaegerExporter
                exporter = JaegerExporter(agent_host_name=self._config.jaeger_endpoint)
            elif self._config.trace_exporter == "zipkin" and self._config.zipkin_endpoint:
                from opentelemetry.exporter.zipkin.proto.http import ZipkinExporter
                exporter = ZipkinExporter(endpoint=self._config.zipkin_endpoint)
            else:
                # Console exporter for testing
                from opentelemetry.sdk.trace.export import ConsoleSpanExporter
                exporter = ConsoleSpanExporter()
            
            # Configure provider
            provider = TracerProvider()
            provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            
            self._otel_tracer = trace.get_tracer(__name__)
        except ImportError:
            # OpenTelemetry not installed, fall back to internal implementation
            self._otel_tracer = None
    
    def start_span(
        self,
        name: str,
        component: ObservabilityComponent,
        context: Optional[ObservabilityContext] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        parent_span_id: Optional[str] = None,
        **attributes
    ) -> Span:
        """
        Start a new span.
        
        Args:
            name: Span name
            component: Component type
            context: Observability context
            kind: Span kind
            parent_span_id: Parent span ID
            **attributes: Span attributes
            
        Returns:
            Span object
        """
        if not self._config.tracing_enabled:
            return Span(name=name, component=component)
        
        span_id = str(uuid.uuid4())
        
        # Use trace ID from context or generate new
        if context and context.trace_id:
            trace_id = context.trace_id
        else:
            trace_id = str(uuid.uuid4())
        
        # Use parent span ID from context or parameter
        if parent_span_id is None and context:
            parent_span_id = context.span_id
        
        span = Span(
            name=name,
            span_id=span_id,
            parent_span_id=parent_span_id,
            trace_id=trace_id,
            kind=kind,
            component=component,
            attributes=attributes,
        )
        
        # Add component attribute
        span.set_attribute("component", component.value)
        
        # Store active span
        with self._lock:
            self._active_spans[span_id] = span
            self._spans[span_id] = span
        
        # Update context
        if context:
            context.span_id = span_id
            context.trace_id = trace_id
        
        # Start OpenTelemetry span if available
        if self._otel_tracer:
            try:
                otel_span = self._otel_tracer.start_span(name)
                otel_span.set_attributes(attributes)
                span._otel_span = otel_span
            except Exception:
                pass
        
        return span
    
    def end_span(self, span: Span) -> None:
        """
        End a span.
        
        Args:
            span: Span to end
        """
        if not self._config.tracing_enabled:
            return
        
        span.end()
        
        # Remove from active spans
        with self._lock:
            if span.span_id in self._active_spans:
                del self._active_spans[span.span_id]
        
        # Add to buffer for export
        with self._buffer_lock:
            self._span_buffer.append(span)
        
        # End OpenTelemetry span if available
        if hasattr(span, '_otel_span'):
            try:
                span._otel_span.end()
            except Exception:
                pass
    
    @contextmanager
    def span_context(
        self,
        name: str,
        component: ObservabilityComponent,
        context: Optional[ObservabilityContext] = None,
        **attributes
    ):
        """
        Context manager for automatic span lifecycle management.
        
        Args:
            name: Span name
            component: Component type
            context: Observability context
            **attributes: Span attributes
            
        Yields:
            Span object
        """
        span = self.start_span(name, component, context, **attributes)
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            raise
        finally:
            self.end_span(span)
    
    def get_active_span(self, span_id: str) -> Optional[Span]:
        """
        Get an active span by ID.
        
        Args:
            span_id: Span ID
            
        Returns:
            Span object or None
        """
        return self._active_spans.get(span_id)
    
    def get_span(self, span_id: str) -> Optional[Span]:
        """
        Get a span by ID.
        
        Args:
            span_id: Span ID
            
        Returns:
            Span object or None
        """
        return self._spans.get(span_id)
    
    def get_trace(self, trace_id: str) -> List[Span]:
        """
        Get all spans in a trace.
        
        Args:
            trace_id: Trace ID
            
        Returns:
            List of spans in the trace
        """
        with self._lock:
            return [span for span in self._spans.values() if span.trace_id == trace_id]
    
    def record_span(self, event: ObservabilityEvent) -> None:
        """
        Record a span from an event.
        
        Args:
            event: Observability event
        """
        if event.event_type != EventType.TRACE:
            return
        
        span_data = event.data
        span = Span(
            name=span_data.get("name", "unknown"),
            span_id=span_data.get("span_id", str(uuid.uuid4())),
            parent_span_id=span_data.get("parent_span_id"),
            trace_id=span_data.get("trace_id", str(uuid.uuid4())),
            kind=SpanKind(span_data.get("kind", "internal")),
            start_time=span_data.get("start_time", time.time()),
            end_time=span_data.get("end_time"),
            duration_ms=span_data.get("duration_ms"),
            status=span_data.get("status", "ok"),
            attributes=span_data.get("attributes", {}),
            component=event.component,
        )
        
        with self._lock:
            self._spans[span.span_id] = span
        
        with self._buffer_lock:
            self._span_buffer.append(span)
    
    def export_spans(self) -> List[Span]:
        """
        Export buffered spans.
        
        Returns:
            List of exported spans
        """
        with self._buffer_lock:
            spans = self._span_buffer.copy()
            self._span_buffer.clear()
        
        # Export to configured backend
        if self._config.opentelemetry_enabled:
            # OpenTelemetry handles export automatically
            pass
        
        return spans
    
    def get_span_buffer(self) -> List[Span]:
        """
        Get buffered spans without clearing.
        
        Returns:
            List of buffered spans
        """
        with self._buffer_lock:
            return self._span_buffer.copy()
    
    def clear_old_spans(self, retention_seconds: int = 3600) -> None:
        """
        Clear old spans from storage.
        
        Args:
            retention_seconds: Retention period in seconds
        """
        cutoff = time.time() - retention_seconds
        
        with self._lock:
            to_remove = [
                span_id for span_id, span in self._spans.items()
                if span.start_time < cutoff
            ]
            for span_id in to_remove:
                del self._spans[span_id]
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """
        Get a summary of a trace.
        
        Args:
            trace_id: Trace ID
            
        Returns:
            Trace summary dictionary
        """
        spans = self.get_trace(trace_id)
        
        if not spans:
            return {}
        
        total_duration = max(
            (s.end_time or s.start_time) - s.start_time
            for s in spans
            if s.end_time
        )
        
        return {
            "trace_id": trace_id,
            "span_count": len(spans),
            "total_duration_ms": total_duration * 1000,
            "root_span": spans[0].name if spans else None,
            "components": list(set(s.component.value for s in spans if s.component)),
            "status": "error" if any(s.status == "error" for s in spans) else "ok",
        }
    
    def shutdown(self) -> None:
        """Shutdown the tracing manager."""
        # Export remaining spans
        self.export_spans()
        
        # Shutdown OpenTelemetry if enabled
        if self._otel_tracer:
            try:
                from opentelemetry.sdk.trace import TracerProvider
                # OpenTelemetry shutdown is handled by the provider
            except Exception:
                pass
