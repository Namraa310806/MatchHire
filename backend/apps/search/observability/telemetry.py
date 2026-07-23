"""
Telemetry Collector.

This module provides the telemetry collector that aggregates metrics,
traces, logs, and other observability data from all components.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import queue
from .core import ObservabilityConfig, ObservabilityEvent, EventType


@dataclass
class TelemetryData:
    """Container for collected telemetry data."""
    
    metrics: Dict[str, Any] = field(default_factory=dict)
    traces: List[Dict[str, Any]] = field(default_factory=list)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    audits: List[Dict[str, Any]] = field(default_factory=list)
    diagnostics: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "metrics": self.metrics,
            "traces": self.traces,
            "logs": self.logs,
            "audits": self.audits,
            "diagnostics": self.diagnostics,
            "errors": self.errors,
        }


class TelemetryCollector:
    """
    Collects and aggregates telemetry data from all observability components.
    
    This collector runs in the background to collect events from metrics,
    tracing, logging, audit, and diagnostics components. It provides
    a unified view of all observability data.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """
        Initialize the telemetry collector.
        
        Args:
            config: Observability configuration
        """
        self._config = config
        self._data = TelemetryData()
        self._event_queue = queue.Queue(maxsize=10000)
        self._lock = threading.Lock()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        
        # Aggregated metrics by component
        self._component_metrics: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: defaultdict(list)
        )
        
        # Time-series data for metrics
        self._time_series: Dict[str, List[tuple]] = defaultdict(list)
        
        # Start background worker if enabled
        if config.enabled:
            self._start_worker()
    
    def _start_worker(self) -> None:
        """Start the background worker thread."""
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._process_events,
            daemon=True,
            name="TelemetryCollectorWorker"
        )
        self._worker_thread.start()
    
    def _process_events(self) -> None:
        """Process events from the queue in the background."""
        while self._running:
            try:
                event = self._event_queue.get(timeout=1.0)
                self._process_event(event)
            except queue.Empty:
                continue
            except Exception as e:
                # Log error but continue processing
                print(f"Error processing telemetry event: {e}")
    
    def _process_event(self, event: ObservabilityEvent) -> None:
        """
        Process a single event.
        
        Args:
            event: Event to process
        """
        with self._lock:
            if event.event_type == EventType.METRIC:
                self._process_metric(event)
            elif event.event_type == EventType.TRACE:
                self._process_trace(event)
            elif event.event_type == EventType.LOG:
                self._process_log(event)
            elif event.event_type == EventType.AUDIT:
                self._process_audit(event)
            elif event.event_type == EventType.DIAGNOSTIC:
                self._process_diagnostic(event)
            
            if event.error:
                self._process_error(event)
    
    def _process_metric(self, event: ObservabilityEvent) -> None:
        """
        Process a metric event.
        
        Args:
            event: Metric event
        """
        metric_name = event.data.get("name", "unknown")
        metric_value = event.data.get("value", 0.0)
        metric_type = event.data.get("type", "gauge")
        tags = event.data.get("tags", {})
        
        # Store in component metrics
        component = event.component.value if event.component else "unknown"
        self._component_metrics[component][metric_name].append({
            "value": metric_value,
            "type": metric_type,
            "tags": tags,
            "timestamp": event.timestamp.isoformat(),
        })
        
        # Store in time series
        timestamp = event.timestamp.timestamp()
        self._time_series[metric_name].append((timestamp, metric_value))
        
        # Keep time series bounded (last 1000 points)
        if len(self._time_series[metric_name]) > 1000:
            self._time_series[metric_name] = self._time_series[metric_name][-1000:]
    
    def _process_trace(self, event: ObservabilityEvent) -> None:
        """
        Process a trace event.
        
        Args:
            event: Trace event
        """
        self._data.traces.append(event.to_dict())
        
        # Keep traces bounded (last 1000)
        if len(self._data.traces) > 1000:
            self._data.traces = self._data.traces[-1000:]
    
    def _process_log(self, event: ObservabilityEvent) -> None:
        """
        Process a log event.
        
        Args:
            event: Log event
        """
        self._data.logs.append(event.to_dict())
        
        # Keep logs bounded (last 1000)
        if len(self._data.logs) > 1000:
            self._data.logs = self._data.logs[-1000:]
    
    def _process_audit(self, event: ObservabilityEvent) -> None:
        """
        Process an audit event.
        
        Args:
            event: Audit event
        """
        self._data.audits.append(event.to_dict())
        
        # Keep audit records bounded (last 1000)
        if len(self._data.audits) > 1000:
            self._data.audits = self._data.audits[-1000:]
    
    def _process_diagnostic(self, event: ObservabilityEvent) -> None:
        """
        Process a diagnostic event.
        
        Args:
            event: Diagnostic event
        """
        self._data.diagnostics.append(event.to_dict())
        
        # Keep diagnostics bounded (last 1000)
        if len(self._data.diagnostics) > 1000:
            self._data.diagnostics = self._data.diagnostics[-1000:]
    
    def _process_error(self, event: ObservabilityEvent) -> None:
        """
        Process an error event.
        
        Args:
            event: Error event
        """
        self._data.errors.append(event.to_dict())
        
        # Keep errors bounded (last 1000)
        if len(self._data.errors) > 1000:
            self._data.errors = self._data.errors[-1000:]
    
    def collect(self, event: ObservabilityEvent) -> None:
        """
        Collect an event for telemetry.
        
        Args:
            event: Event to collect
        """
        try:
            self._event_queue.put_nowait(event)
        except queue.Full:
            # Queue is full, drop event
            print("Telemetry queue full, dropping event")
    
    def get_telemetry(self) -> Dict[str, Any]:
        """
        Get all collected telemetry data.
        
        Returns:
            Telemetry data dictionary
        """
        with self._lock:
            return {
                "data": self._data.to_dict(),
                "component_metrics": dict(self._component_metrics),
                "time_series": dict(self._time_series),
                "queue_size": self._event_queue.qsize(),
            }
    
    def get_component_metrics(self, component: str) -> Dict[str, Any]:
        """
        Get metrics for a specific component.
        
        Args:
            component: Component name
            
        Returns:
            Component metrics dictionary
        """
        with self._lock:
            return dict(self._component_metrics.get(component, {}))
    
    def get_time_series(
        self,
        metric_name: str,
        since_seconds: Optional[int] = None,
    ) -> List[tuple]:
        """
        Get time series data for a metric.
        
        Args:
            metric_name: Name of the metric
            since_seconds: Only return data since N seconds ago
            
        Returns:
            List of (timestamp, value) tuples
        """
        with self._lock:
            series = self._time_series.get(metric_name, []).copy()
            
            if since_seconds is not None:
                cutoff = datetime.utcnow().timestamp() - since_seconds
                series = [(ts, val) for ts, val in series if ts >= cutoff]
            
            return series
    
    def get_metric_summary(self, metric_name: str) -> Dict[str, float]:
        """
        Get summary statistics for a metric.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Summary statistics dictionary
        """
        series = self.get_time_series(metric_name)
        
        if not series:
            return {}
        
        values = [val for _, val in series]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "sum": sum(values),
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent errors.
        
        Args:
            limit: Maximum number of errors to return
            
        Returns:
            List of error dictionaries
        """
        with self._lock:
            return self._data.errors[-limit:]
    
    def get_recent_logs(
        self,
        level: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get recent logs.
        
        Args:
            level: Optional log level filter
            limit: Maximum number of logs to return
            
        Returns:
            List of log dictionaries
        """
        with self._lock:
            logs = self._data.logs
            
            if level:
                logs = [log for log in logs if log.get("level") == level]
            
            return logs[-limit:]
    
    def clear_old_data(self, retention_seconds: int = 3600) -> None:
        """
        Clear old telemetry data.
        
        Args:
            retention_seconds: Retention period in seconds
        """
        cutoff = datetime.utcnow().timestamp() - retention_seconds
        
        with self._lock:
            # Clear old time series data
            for metric_name in self._time_series:
                self._time_series[metric_name] = [
                    (ts, val) for ts, val in self._time_series[metric_name]
                    if ts >= cutoff
                ]
    
    def shutdown(self) -> None:
        """Shutdown the telemetry collector."""
        self._running = False
        
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
        
        # Process remaining events
        while not self._event_queue.empty():
            try:
                event = self._event_queue.get_nowait()
                self._process_event(event)
            except queue.Empty:
                break
