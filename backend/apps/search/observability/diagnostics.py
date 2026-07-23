"""
Diagnostics Manager.

This module provides diagnostic capabilities for identifying and
troubleshooting issues in the search, ranking, and recommendation systems.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
import statistics
from collections import defaultdict
from .core import ObservabilityConfig, ObservabilityEvent, EventType, ObservabilityComponent


class DiagnosticType(Enum):
    """Types of diagnostics."""
    SLOW_QUERY = "slow_query"
    SLOW_RANKING = "slow_ranking"
    SLOW_RECOMMENDATION = "slow_recommendation"
    PROVIDER_FAILURE = "provider_failure"
    CACHE_FAILURE = "cache_failure"
    TIMEOUT = "timeout"
    RETRY_ATTEMPT = "retry_attempt"
    PIPELINE_FAILURE = "pipeline_failure"
    INVALID_QUERY = "invalid_query"
    HIGH_ERROR_RATE = "high_error_rate"
    MEMORY_HIGH = "memory_high"
    CPU_HIGH = "cpu_high"


class Severity(Enum):
    """Diagnostic severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class DiagnosticRecord:
    """Diagnostic record."""
    
    diagnostic_type: DiagnosticType
    severity: Severity
    timestamp: datetime = field(default_factory=datetime.utcnow)
    component: Optional[ObservabilityComponent] = None
    provider: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "diagnostic_type": self.diagnostic_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "component": self.component.value if self.component else None,
            "provider": self.provider,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "message": self.message,
            "details": self.details,
            "metrics": self.metrics,
            "suggestions": self.suggestions,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


@dataclass
class DiagnosticReport:
    """Comprehensive diagnostic report."""
    
    generated_at: datetime = field(default_factory=datetime.utcnow)
    summary: Dict[str, Any] = field(default_factory=dict)
    diagnostics: List[DiagnosticRecord] = field(default_factory=list)
    component_health: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "summary": self.summary,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "component_health": self.component_health,
            "performance_metrics": self.performance_metrics,
            "recommendations": self.recommendations,
        }


class DiagnosticsManager:
    """
    Diagnostics manager for troubleshooting.
    
    This manager collects diagnostic information, identifies issues,
    and provides actionable recommendations.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """
        Initialize the diagnostics manager.
        
        Args:
            config: Observability configuration
        """
        self._config = config
        self._diagnostics: List[DiagnosticRecord] = []
        self._lock = threading.Lock()
        
        # Performance history for trend analysis
        self._performance_history: Dict[str, List[float]] = defaultdict(list)
        
        # Thresholds for diagnostics
        self._thresholds = {
            "slow_query_ms": config.slow_query_threshold_ms,
            "slow_ranking_ms": config.slow_ranking_threshold_ms,
            "slow_recommendation_ms": config.slow_recommendation_threshold_ms,
            "high_error_rate": 0.05,  # 5% error rate
            "high_memory_usage": 0.9,  # 90% memory usage
            "high_cpu_usage": 0.8,  # 80% CPU usage
        }
    
    def record_diagnostic(
        self,
        diagnostic_type: DiagnosticType,
        severity: Severity,
        message: str,
        component: Optional[ObservabilityComponent] = None,
        provider: Optional[str] = None,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, float]] = None,
        suggestions: Optional[List[str]] = None,
    ) -> DiagnosticRecord:
        """
        Record a diagnostic.
        
        Args:
            diagnostic_type: Type of diagnostic
            severity: Severity level
            message: Diagnostic message
            component: Component
            provider: Provider
            request_id: Request ID
            trace_id: Trace ID
            details: Additional details
            metrics: Related metrics
            suggestions: Suggestions for resolution
            
        Returns:
            DiagnosticRecord instance
        """
        if not self._config.diagnostics_enabled:
            return DiagnosticRecord(
                diagnostic_type=diagnostic_type,
                severity=severity,
                message=message,
            )
        
        record = DiagnosticRecord(
            diagnostic_type=diagnostic_type,
            severity=severity,
            component=component,
            provider=provider,
            request_id=request_id,
            trace_id=trace_id,
            message=message,
            details=details or {},
            metrics=metrics or {},
            suggestions=suggestions or [],
        )
        
        with self._lock:
            self._diagnostics.append(record)
            
            # Keep diagnostics bounded
            if len(self._diagnostics) > 10000:
                self._diagnostics = self._diagnostics[-10000:]
        
        return record
    
    def record_diagnostic_from_event(self, event: ObservabilityEvent) -> None:
        """
        Record diagnostic from an observability event.
        
        Args:
            event: Observability event
        """
        if event.event_type != EventType.DIAGNOSTIC:
            return
        
        diagnostic_type_str = event.data.get("diagnostic_type", "slow_query")
        try:
            diagnostic_type = DiagnosticType(diagnostic_type_str)
        except ValueError:
            diagnostic_type = DiagnosticType.SLOW_QUERY
        
        severity_str = event.data.get("severity", "warning")
        try:
            severity = Severity(severity_str)
        except ValueError:
            severity = Severity.WARNING
        
        self.record_diagnostic(
            diagnostic_type=diagnostic_type,
            severity=severity,
            message=event.data.get("message", ""),
            component=event.component,
            **{k: v for k, v in event.data.items() 
               if k not in ["diagnostic_type", "severity", "message"]},
        )
    
    def check_slow_query(
        self,
        latency_ms: float,
        query: str,
        component: ObservabilityComponent,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> Optional[DiagnosticRecord]:
        """
        Check if a query is slow and record diagnostic if so.
        
        Args:
            latency_ms: Query latency in milliseconds
            query: Query string
            component: Component
            request_id: Request ID
            trace_id: Trace ID
            
        Returns:
            DiagnosticRecord if slow, None otherwise
        """
        threshold = self._thresholds["slow_query_ms"]
        
        if latency_ms > threshold:
            suggestions = [
                "Consider adding indexes for frequently queried fields",
                "Review query complexity and consider simplification",
                "Check if query can be cached",
                "Consider pagination to reduce result set size",
            ]
            
            return self.record_diagnostic(
                diagnostic_type=DiagnosticType.SLOW_QUERY,
                severity=Severity.WARNING if latency_ms < threshold * 2 else Severity.ERROR,
                message=f"Slow query detected: {latency_ms:.2f}ms (threshold: {threshold}ms)",
                component=component,
                request_id=request_id,
                trace_id=trace_id,
                details={"query": query, "latency_ms": latency_ms},
                metrics={"latency_ms": latency_ms},
                suggestions=suggestions,
            )
        
        return None
    
    def check_slow_ranking(
        self,
        latency_ms: float,
        component: ObservabilityComponent,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> Optional[DiagnosticRecord]:
        """
        Check if ranking is slow and record diagnostic if so.
        
        Args:
            latency_ms: Ranking latency in milliseconds
            component: Component
            request_id: Request ID
            trace_id: Trace ID
            
        Returns:
            DiagnosticRecord if slow, None otherwise
        """
        threshold = self._thresholds["slow_ranking_ms"]
        
        if latency_ms > threshold:
            suggestions = [
                "Review the number of signals being computed",
                "Consider enabling signal caching",
                "Check if parallel scoring can be enabled",
                "Review signal complexity and optimize expensive signals",
            ]
            
            return self.record_diagnostic(
                diagnostic_type=DiagnosticType.SLOW_RANKING,
                severity=Severity.WARNING if latency_ms < threshold * 2 else Severity.ERROR,
                message=f"Slow ranking detected: {latency_ms:.2f}ms (threshold: {threshold}ms)",
                component=component,
                request_id=request_id,
                trace_id=trace_id,
                details={"latency_ms": latency_ms},
                metrics={"latency_ms": latency_ms},
                suggestions=suggestions,
            )
        
        return None
    
    def check_slow_recommendation(
        self,
        latency_ms: float,
        component: ObservabilityComponent,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> Optional[DiagnosticRecord]:
        """
        Check if recommendation generation is slow and record diagnostic if so.
        
        Args:
            latency_ms: Recommendation latency in milliseconds
            component: Component
            request_id: Request ID
            trace_id: Trace ID
            
        Returns:
            DiagnosticRecord if slow, None otherwise
        """
        threshold = self._thresholds["slow_recommendation_ms"]
        
        if latency_ms > threshold:
            suggestions = [
                "Review the recommendation strategy being used",
                "Consider enabling recommendation caching",
                "Check if candidate generation can be optimized",
                "Review diversification complexity",
            ]
            
            return self.record_diagnostic(
                diagnostic_type=DiagnosticType.SLOW_RECOMMENDATION,
                severity=Severity.WARNING if latency_ms < threshold * 2 else Severity.ERROR,
                message=f"Slow recommendation detected: {latency_ms:.2f}ms (threshold: {threshold}ms)",
                component=component,
                request_id=request_id,
                trace_id=trace_id,
                details={"latency_ms": latency_ms},
                metrics={"latency_ms": latency_ms},
                suggestions=suggestions,
            )
        
        return None
    
    def check_provider_failure(
        self,
        provider: str,
        error: str,
        component: ObservabilityComponent,
        request_id: Optional[str] = None,
    ) -> DiagnosticRecord:
        """
        Record a provider failure diagnostic.
        
        Args:
            provider: Provider name
            error: Error message
            component: Component
            request_id: Request ID
            
        Returns:
            DiagnosticRecord
        """
        suggestions = [
            "Check provider connectivity",
            "Review provider configuration",
            "Consider switching to backup provider if available",
            "Check provider logs for more details",
        ]
        
        return self.record_diagnostic(
            diagnostic_type=DiagnosticType.PROVIDER_FAILURE,
            severity=Severity.ERROR,
            message=f"Provider failure: {provider} - {error}",
            component=component,
            provider=provider,
            request_id=request_id,
            details={"error": error},
            suggestions=suggestions,
        )
    
    def check_high_error_rate(
        self,
        component: ObservabilityComponent,
        error_rate: float,
    ) -> Optional[DiagnosticRecord]:
        """
        Check if error rate is high and record diagnostic if so.
        
        Args:
            component: Component
            error_rate: Error rate (0-1)
            
        Returns:
            DiagnosticRecord if high, None otherwise
        """
        threshold = self._thresholds["high_error_rate"]
        
        if error_rate > threshold:
            suggestions = [
                "Review recent error logs for patterns",
                "Check if there are configuration issues",
                "Review recent deployments or changes",
                "Consider enabling circuit breaker pattern",
            ]
            
            return self.record_diagnostic(
                diagnostic_type=DiagnosticType.HIGH_ERROR_RATE,
                severity=Severity.ERROR if error_rate < threshold * 2 else Severity.CRITICAL,
                message=f"High error rate detected: {error_rate:.2%} (threshold: {threshold:.2%})",
                component=component,
                details={"error_rate": error_rate},
                metrics={"error_rate": error_rate},
                suggestions=suggestions,
            )
        
        return None
    
    def get_diagnostics(
        self,
        diagnostic_type: Optional[DiagnosticType] = None,
        severity: Optional[Severity] = None,
        component: Optional[ObservabilityComponent] = None,
        provider: Optional[str] = None,
        resolved: Optional[bool] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[DiagnosticRecord]:
        """
        Get diagnostics with optional filters.
        
        Args:
            diagnostic_type: Optional diagnostic type filter
            severity: Optional severity filter
            component: Optional component filter
            provider: Optional provider filter
            resolved: Optional resolved filter
            since: Optional start time filter
            limit: Maximum number of diagnostics to return
            
        Returns:
            List of diagnostic records
        """
        with self._lock:
            diagnostics = self._diagnostics
            
            if diagnostic_type:
                diagnostics = [d for d in diagnostics if d.diagnostic_type == diagnostic_type]
            
            if severity:
                diagnostics = [d for d in diagnostics if d.severity == severity]
            
            if component:
                diagnostics = [d for d in diagnostics if d.component == component]
            
            if provider:
                diagnostics = [d for d in diagnostics if d.provider == provider]
            
            if resolved is not None:
                diagnostics = [d for d in diagnostics if d.resolved == resolved]
            
            if since:
                diagnostics = [d for d in diagnostics if d.timestamp >= since]
            
            return diagnostics[-limit:]
    
    def get_unresolved_diagnostics(self, limit: int = 100) -> List[DiagnosticRecord]:
        """
        Get unresolved diagnostics.
        
        Args:
            limit: Maximum number of diagnostics to return
            
        Returns:
            List of unresolved diagnostic records
        """
        return self.get_diagnostics(resolved=False, limit=limit)
    
    def get_critical_diagnostics(self, limit: int = 100) -> List[DiagnosticRecord]:
        """
        Get critical diagnostics.
        
        Args:
            limit: Maximum number of diagnostics to return
            
        Returns:
            List of critical diagnostic records
        """
        return self.get_diagnostics(severity=Severity.CRITICAL, limit=limit)
    
    def resolve_diagnostic(self, diagnostic_id: str) -> bool:
        """
        Mark a diagnostic as resolved.
        
        Args:
            diagnostic_id: ID of diagnostic to resolve
            
        Returns:
            True if resolved, False if not found
        """
        with self._lock:
            for diagnostic in self._diagnostics:
                if diagnostic.request_id == diagnostic_id:
                    diagnostic.resolved = True
                    diagnostic.resolved_at = datetime.utcnow()
                    return True
        return False
    
    def get_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive diagnostic report.
        
        Returns:
            Diagnostic report dictionary
        """
        with self._lock:
            # Count by type
            type_counts = defaultdict(int)
            severity_counts = defaultdict(int)
            component_counts = defaultdict(int)
            
            for diagnostic in self._diagnostics:
                type_counts[diagnostic.diagnostic_type.value] += 1
                severity_counts[diagnostic.severity.value] += 1
                if diagnostic.component:
                    component_counts[diagnostic.component.value] += 1
            
            # Get unresolved diagnostics
            unresolved = [d for d in self._diagnostics if not d.resolved]
            
            # Generate recommendations
            recommendations = []
            if severity_counts.get("critical", 0) > 0:
                recommendations.append("Critical issues detected and require immediate attention")
            if severity_counts.get("error", 0) > 10:
                recommendations.append("High number of errors detected, review error logs")
            if type_counts.get("slow_query", 0) > 5:
                recommendations.append("Multiple slow queries detected, review query optimization")
            if type_counts.get("provider_failure", 0) > 3:
                recommendations.append("Multiple provider failures detected, review provider health")
            
            report = DiagnosticReport(
                summary={
                    "total_diagnostics": len(self._diagnostics),
                    "unresolved_count": len(unresolved),
                    "type_counts": dict(type_counts),
                    "severity_counts": dict(severity_counts),
                    "component_counts": dict(component_counts),
                },
                diagnostics=unresolved[:100],  # Include recent unresolved diagnostics
                component_health=self._get_component_health(),
                performance_metrics=self._get_performance_metrics(),
                recommendations=recommendations,
            )
        
        return report.to_dict()
    
    def _get_component_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for each component."""
        health = {}
        
        components = [
            ObservabilityComponent.SEARCH,
            ObservabilityComponent.RANKING,
            ObservabilityComponent.RECOMMENDATION,
            ObservabilityComponent.PROVIDER,
            ObservabilityComponent.CACHE,
        ]
        
        for component in components:
            component_diagnostics = [d for d in self._diagnostics if d.component == component]
            error_count = sum(1 for d in component_diagnostics if d.severity in [Severity.ERROR, Severity.CRITICAL])
            
            health[component.value] = {
                "status": "healthy" if error_count == 0 else "degraded" if error_count < 5 else "unhealthy",
                "error_count": error_count,
                "total_diagnostics": len(component_diagnostics),
            }
        
        return health
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics summary."""
        # This would aggregate performance data from metrics registry
        # For now, return placeholder
        return {
            "avg_search_latency_ms": 0.0,
            "avg_ranking_latency_ms": 0.0,
            "avg_recommendation_latency_ms": 0.0,
            "p95_search_latency_ms": 0.0,
            "p95_ranking_latency_ms": 0.0,
            "p95_recommendation_latency_ms": 0.0,
        }
    
    def clear_old_diagnostics(self, retention_days: int = 7) -> None:
        """
        Clear old diagnostics.
        
        Args:
            retention_days: Retention period in days
        """
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        
        with self._lock:
            self._diagnostics = [
                diagnostic for diagnostic in self._diagnostics
                if diagnostic.timestamp >= cutoff or not diagnostic.resolved
            ]
