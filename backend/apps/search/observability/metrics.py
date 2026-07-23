"""
Metrics Registry and Collection.

This module provides a comprehensive metrics collection system compatible
with Prometheus and other monitoring systems. It supports counters,
gauges, histograms, and summaries.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading
import time
from collections import defaultdict
import statistics
from .core import ObservabilityConfig, ObservabilityEvent, EventType, ObservabilityComponent


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Base metric class."""
    
    name: str
    metric_type: MetricType
    description: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.metric_type.value,
            "description": self.description,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Counter(Metric):
    """
    Counter metric - monotonically increasing value.
    
    Counters are used for things like request counts, error counts,
    etc. They can only increase.
    """
    
    value: float = 0.0
    
    def inc(self, amount: float = 1.0) -> None:
        """
        Increment the counter.
        
        Args:
            amount: Amount to increment by
        """
        if amount < 0:
            raise ValueError("Counter can only be incremented by positive values")
        self.value += amount
    
    def get(self) -> float:
        """Get the current value."""
        return self.value
    
    def reset(self) -> None:
        """Reset the counter to zero."""
        self.value = 0.0


@dataclass
class Gauge(Metric):
    """
    Gauge metric - value that can go up or down.
    
    Gauges are used for things like current queue size, memory usage,
    active connections, etc.
    """
    
    value: float = 0.0
    
    def set(self, value: float) -> None:
        """
        Set the gauge value.
        
        Args:
            value: New value
        """
        self.value = value
    
    def inc(self, amount: float = 1.0) -> None:
        """
        Increment the gauge.
        
        Args:
            amount: Amount to increment by
        """
        self.value += amount
    
    def dec(self, amount: float = 1.0) -> None:
        """
        Decrement the gauge.
        
        Args:
            amount: Amount to decrement by
        """
        self.value -= amount
    
    def get(self) -> float:
        """Get the current value."""
        return self.value


@dataclass
class Histogram(Metric):
    """
    Histogram metric - distribution of values.
    
    Histograms track the distribution of values over configurable
    buckets. Used for things like request latency, response sizes, etc.
    """
    
    value: float = 0.0
    sum: float = 0.0
    count: int = 0
    buckets: Dict[float, int] = field(default_factory=dict)
    default_buckets: List[float] = field(default_factory=lambda: [
        0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0
    ])
    
    def __post_init__(self):
        """Initialize buckets."""
        if not self.buckets:
            for bucket in self.default_buckets:
                self.buckets[bucket] = 0
    
    def observe(self, value: float) -> None:
        """
        Observe a value.
        
        Args:
            value: Value to observe
        """
        self.value = value
        self.sum += value
        self.count += 1
        
        # Update buckets
        for bucket in sorted(self.buckets.keys()):
            if value <= bucket:
                self.buckets[bucket] += 1
    
    def get_bucket(self, bucket: float) -> int:
        """
        Get count for a specific bucket.
        
        Args:
            bucket: Bucket value
            
        Returns:
            Count in bucket
        """
        return self.buckets.get(bucket, 0)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get histogram summary."""
        return {
            "count": self.count,
            "sum": self.sum,
            "avg": self.sum / self.count if self.count > 0 else 0.0,
            "buckets": self.buckets,
        }


@dataclass
class Summary(Metric):
    """
    Summary metric - sliding window of values with quantiles.
    
    Summaries track a sliding window of values and compute quantiles.
    Used for things like request latency with p50, p95, p99.
    """
    
    values: List[float] = field(default_factory=list)
    max_age_seconds: int = 600  # 10 minutes
    max_size: int = 1000
    quantiles: List[float] = field(default_factory=lambda: [0.5, 0.9, 0.95, 0.99])
    
    def observe(self, value: float) -> None:
        """
        Observe a value.
        
        Args:
            value: Value to observe
        """
        self.values.append(value)
        
        # Trim old values
        cutoff = time.time() - self.max_age_seconds
        # (Simplified - in production would track timestamps)
        
        # Trim by size
        if len(self.values) > self.max_size:
            self.values = self.values[-self.max_size:]
    
    def get_quantile(self, quantile: float) -> float:
        """
        Get value at a specific quantile.
        
        Args:
            quantile: Quantile (0-1)
            
        Returns:
            Value at quantile
        """
        if not self.values:
            return 0.0
        
        sorted_values = sorted(self.values)
        index = int(quantile * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_summary(self) -> Dict[str, float]:
        """Get summary with quantiles."""
        return {
            "count": len(self.values),
            "sum": sum(self.values),
            "avg": statistics.mean(self.values) if self.values else 0.0,
            **{f"p{int(q*100)}": self.get_quantile(q) for q in self.quantiles},
        }


class MetricsRegistry:
    """
    Registry for all metrics.
    
    This registry manages all metrics in the system, providing
    a centralized location for metric creation, retrieval, and
    export to Prometheus and other systems.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """
        Initialize the metrics registry.
        
        Args:
            config: Observability configuration
        """
        self._config = config
        self._metrics: Dict[str, Metric] = {}
        self._lock = threading.Lock()
        
        # Initialize default metrics
        self._initialize_default_metrics()
    
    def _initialize_default_metrics(self) -> None:
        """Initialize default metrics for the system."""
        # Search metrics
        self.register_counter(
            name="search_requests_total",
            description="Total number of search requests",
            tags={"component": "search"},
        )
        self.register_histogram(
            name="search_latency_seconds",
            description="Search request latency in seconds",
            tags={"component": "search"},
        )
        self.register_counter(
            name="search_errors_total",
            description="Total number of search errors",
            tags={"component": "search"},
        )
        
        # Ranking metrics
        self.register_counter(
            name="ranking_requests_total",
            description="Total number of ranking requests",
            tags={"component": "ranking"},
        )
        self.register_histogram(
            name="ranking_latency_seconds",
            description="Ranking request latency in seconds",
            tags={"component": "ranking"},
        )
        self.register_gauge(
            name="ranking_signals_active",
            description="Number of active ranking signals",
            tags={"component": "ranking"},
        )
        
        # Recommendation metrics
        self.register_counter(
            name="recommendation_requests_total",
            description="Total number of recommendation requests",
            tags={"component": "recommendation"},
        )
        self.register_histogram(
            name="recommendation_latency_seconds",
            description="Recommendation request latency in seconds",
            tags={"component": "recommendation"},
        )
        self.register_counter(
            name="recommendations_generated_total",
            description="Total number of recommendations generated",
            tags={"component": "recommendation"},
        )
        
        # Provider metrics
        self.register_counter(
            name="provider_requests_total",
            description="Total number of provider requests",
            tags={"component": "provider"},
        )
        self.register_histogram(
            name="provider_latency_seconds",
            description="Provider request latency in seconds",
            tags={"component": "provider"},
        )
        self.register_gauge(
            name="provider_health",
            description="Provider health status (1=healthy, 0=unhealthy)",
            tags={"component": "provider"},
        )
        
        # Cache metrics
        self.register_counter(
            name="cache_hits_total",
            description="Total number of cache hits",
            tags={"component": "cache"},
        )
        self.register_counter(
            name="cache_misses_total",
            description="Total number of cache misses",
            tags={"component": "cache"},
        )
        self.register_gauge(
            name="cache_size",
            description="Current cache size",
            tags={"component": "cache"},
        )
        
        # Pipeline metrics
        self.register_counter(
            name="pipeline_executions_total",
            description="Total number of pipeline executions",
            tags={"component": "pipeline"},
        )
        self.register_histogram(
            name="pipeline_latency_seconds",
            description="Pipeline execution latency in seconds",
            tags={"component": "pipeline"},
        )
    
    def register_counter(
        self,
        name: str,
        description: str = "",
        tags: Optional[Dict[str, str]] = None,
    ) -> Counter:
        """
        Register a counter metric.
        
        Args:
            name: Metric name
            description: Metric description
            tags: Metric tags
            
        Returns:
            Counter instance
        """
        with self._lock:
            if name in self._metrics:
                return self._metrics[name]
            
            counter = Counter(
                name=name,
                metric_type=MetricType.COUNTER,
                description=description,
                tags=tags or {},
            )
            self._metrics[name] = counter
            return counter
    
    def register_gauge(
        self,
        name: str,
        description: str = "",
        tags: Optional[Dict[str, str]] = None,
    ) -> Gauge:
        """
        Register a gauge metric.
        
        Args:
            name: Metric name
            description: Metric description
            tags: Metric tags
            
        Returns:
            Gauge instance
        """
        with self._lock:
            if name in self._metrics:
                return self._metrics[name]
            
            gauge = Gauge(
                name=name,
                metric_type=MetricType.GAUGE,
                description=description,
                tags=tags or {},
            )
            self._metrics[name] = gauge
            return gauge
    
    def register_histogram(
        self,
        name: str,
        description: str = "",
        tags: Optional[Dict[str, str]] = None,
        buckets: Optional[List[float]] = None,
    ) -> Histogram:
        """
        Register a histogram metric.
        
        Args:
            name: Metric name
            description: Metric description
            tags: Metric tags
            buckets: Custom buckets
            
        Returns:
            Histogram instance
        """
        with self._lock:
            if name in self._metrics:
                return self._metrics[name]
            
            histogram = Histogram(
                name=name,
                metric_type=MetricType.HISTOGRAM,
                description=description,
                tags=tags or {},
                default_buckets=buckets or [],
            )
            self._metrics[name] = histogram
            return histogram
    
    def register_summary(
        self,
        name: str,
        description: str = "",
        tags: Optional[Dict[str, str]] = None,
        quantiles: Optional[List[float]] = None,
    ) -> Summary:
        """
        Register a summary metric.
        
        Args:
            name: Metric name
            description: Metric description
            tags: Metric tags
            quantiles: Custom quantiles
            
        Returns:
            Summary instance
        """
        with self._lock:
            if name in self._metrics:
                return self._metrics[name]
            
            summary = Summary(
                name=name,
                metric_type=MetricType.SUMMARY,
                description=description,
                tags=tags or {},
                quantiles=quantiles or [],
            )
            self._metrics[name] = summary
            return summary
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """
        Get a metric by name.
        
        Args:
            name: Metric name
            
        Returns:
            Metric instance or None
        """
        return self._metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all registered metrics."""
        return self._metrics.copy()
    
    def record_metric(self, event: ObservabilityEvent) -> None:
        """
        Record a metric from an event.
        
        Args:
            event: Observability event
        """
        metric_name = event.data.get("name")
        metric_value = event.data.get("value")
        metric_type = event.data.get("type", "gauge")
        
        if not metric_name or metric_value is None:
            return
        
        metric = self.get_metric(metric_name)
        if not metric:
            # Auto-register metric
            if metric_type == "counter":
                metric = self.register_counter(metric_name)
            elif metric_type == "gauge":
                metric = self.register_gauge(metric_name)
            elif metric_type == "histogram":
                metric = self.register_histogram(metric_name)
            elif metric_type == "summary":
                metric = self.register_summary(metric_name)
        
        # Update metric
        if isinstance(metric, Counter):
            metric.inc(metric_value)
        elif isinstance(metric, Gauge):
            metric.set(metric_value)
        elif isinstance(metric, Histogram):
            metric.observe(metric_value)
        elif isinstance(metric, Summary):
            metric.observe(metric_value)
    
    def increment_counter(self, name: str, amount: float = 1.0) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            amount: Amount to increment
        """
        metric = self.get_metric(name)
        if metric and isinstance(metric, Counter):
            metric.inc(amount)
    
    def set_gauge(self, name: str, value: float) -> None:
        """
        Set a gauge metric.
        
        Args:
            name: Metric name
            value: Value to set
        """
        metric = self.get_metric(name)
        if metric and isinstance(metric, Gauge):
            metric.set(value)
    
    def observe_histogram(self, name: str, value: float) -> None:
        """
        Observe a value for a histogram metric.
        
        Args:
            name: Metric name
            value: Value to observe
        """
        metric = self.get_metric(name)
        if metric and isinstance(metric, Histogram):
            metric.observe(value)
    
    def observe_summary(self, name: str, value: float) -> None:
        """
        Observe a value for a summary metric.
        
        Args:
            name: Metric name
            value: Value to observe
        """
        metric = self.get_metric(name)
        if metric and isinstance(metric, Summary):
            metric.observe(value)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all metrics.
        
        Returns:
            Metrics summary dictionary
        """
        summary = {}
        for name, metric in self._metrics.items():
            if isinstance(metric, Counter):
                summary[name] = {"type": "counter", "value": metric.get()}
            elif isinstance(metric, Gauge):
                summary[name] = {"type": "gauge", "value": metric.get()}
            elif isinstance(metric, Histogram):
                summary[name] = {"type": "histogram", "summary": metric.get_summary()}
            elif isinstance(metric, Summary):
                summary[name] = {"type": "summary", "summary": metric.get_summary()}
        
        return summary
    
    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus format.
        
        Returns:
            Prometheus-formatted metrics string
        """
        lines = []
        
        for name, metric in self._metrics.items():
            # Add HELP and TYPE
            if metric.description:
                lines.append(f"# HELP {name} {metric.description}")
            lines.append(f"# TYPE {name} {metric.metric_type.value}")
            
            # Add metric value
            if isinstance(metric, Counter):
                lines.append(f"{name} {metric.get()}")
            elif isinstance(metric, Gauge):
                lines.append(f"{name} {metric.get()}")
            elif isinstance(metric, Histogram):
                for bucket, count in metric.buckets.items():
                    lines.append(f'{name}_bucket{{le="{bucket}"}} {count}')
                lines.append(f"{name}_sum {metric.sum}")
                lines.append(f"{name}_count {metric.count}")
            elif isinstance(metric, Summary):
                for quantile in metric.quantiles:
                    value = metric.get_quantile(quantile)
                    lines.append(f'{name}{{quantile="{quantile}"}} {value}')
                lines.append(f"{name}_sum {sum(metric.values)}")
                lines.append(f"{name}_count {len(metric.values)}")
        
        return "\n".join(lines)
    
    def reset_metric(self, name: str) -> None:
        """
        Reset a metric to its initial state.
        
        Args:
            name: Metric name
        """
        metric = self.get_metric(name)
        if metric and isinstance(metric, Counter):
            metric.reset()
    
    def reset_all(self) -> None:
        """Reset all metrics to their initial state."""
        with self._lock:
            for metric in self._metrics.values():
                if isinstance(metric, Counter):
                    metric.reset()
    
    def shutdown(self) -> None:
        """Shutdown the metrics registry."""
        # Cleanup if needed
        pass
