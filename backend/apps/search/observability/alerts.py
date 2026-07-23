"""
Alert Definitions.

This module provides alert definitions for monitoring the search,
ranking, and recommendation systems. Alerts are defined in a format
compatible with Prometheus Alertmanager and other alerting systems.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertState(Enum):
    """Alert states."""
    PENDING = "pending"
    FIRING = "firing"
    RESOLVED = "resolved"


@dataclass
class AlertCondition:
    """Alert condition definition."""
    
    name: str
    query: str
    description: str
    severity: AlertSeverity
    duration: str = "5m"  # How long condition must be true before alerting
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "alert": self.name,
            "expr": self.query,
            "for": self.duration,
            "labels": self.labels,
            "annotations": {
                "description": self.description,
                **self.annotations,
            },
        }


@dataclass
class AlertRule:
    """Alert rule definition."""
    
    name: str
    conditions: List[AlertCondition] = field(default_factory=list)
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "conditions": [condition.to_dict() for condition in self.conditions],
        }


@dataclass
class Alert:
    """Active alert instance."""
    
    name: str
    state: AlertState
    severity: AlertSeverity
    message: str
    timestamp: Any  # datetime
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    value: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "state": self.state.value,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if hasattr(self.timestamp, 'isoformat') else str(self.timestamp),
            "labels": self.labels,
            "annotations": self.annotations,
            "value": self.value,
        }


class AlertRegistry:
    """
    Registry for alert definitions.
    
    This registry provides pre-configured alert rules for monitoring
    the search, ranking, and recommendation systems.
    """
    
    def __init__(self):
        """Initialize the alert registry."""
        self._alert_rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._register_default_alerts()
    
    def _register_default_alerts(self) -> None:
        """Register default alert rules."""
        self.register_alert_rule(self._create_latency_alerts())
        self.register_alert_rule(self._create_error_rate_alerts())
        self.register_alert_rule(self._create_provider_alerts())
        self.register_alert_rule(self._create_cache_alerts())
        self.register_alert_rule(self._create_pipeline_alerts())
        self.register_alert_rule(self._create_recommendation_alerts())
        self.register_alert_rule(self._create_health_alerts())
        self.register_alert_rule(self._create_infrastructure_alerts())
    
    def _create_latency_alerts(self) -> AlertRule:
        """Create latency-related alerts."""
        conditions = [
            AlertCondition(
                name="HighSearchLatency",
                query="histogram_quantile(0.95, rate(search_latency_seconds_bucket[5m])) > 1.0",
                description="Search p95 latency is above 1 second",
                severity=AlertSeverity.WARNING,
                duration="5m",
                labels={"component": "search"},
            ),
            AlertCondition(
                name="CriticalSearchLatency",
                query="histogram_quantile(0.95, rate(search_latency_seconds_bucket[5m])) > 5.0",
                description="Search p95 latency is critically high (>5s)",
                severity=AlertSeverity.CRITICAL,
                duration="2m",
                labels={"component": "search"},
            ),
            AlertCondition(
                name="HighRankingLatency",
                query="histogram_quantile(0.95, rate(ranking_latency_seconds_bucket[5m])) > 0.5",
                description="Ranking p95 latency is above 500ms",
                severity=AlertSeverity.WARNING,
                duration="5m",
                labels={"component": "ranking"},
            ),
            AlertCondition(
                name="CriticalRankingLatency",
                query="histogram_quantile(0.95, rate(ranking_latency_seconds_bucket[5m])) > 2.0",
                description="Ranking p95 latency is critically high (>2s)",
                severity=AlertSeverity.CRITICAL,
                duration="2m",
                labels={"component": "ranking"},
            ),
            AlertCondition(
                name="HighRecommendationLatency",
                query="histogram_quantile(0.95, rate(recommendation_latency_seconds_bucket[5m])) > 2.0",
                description="Recommendation p95 latency is above 2 seconds",
                severity=AlertSeverity.WARNING,
                duration="5m",
                labels={"component": "recommendation"},
            ),
            AlertCondition(
                name="CriticalRecommendationLatency",
                query="histogram_quantile(0.95, rate(recommendation_latency_seconds_bucket[5m])) > 10.0",
                description="Recommendation p95 latency is critically high (>10s)",
                severity=AlertSeverity.CRITICAL,
                duration="2m",
                labels={"component": "recommendation"},
            ),
        ]
        
        return AlertRule(
            name="LatencyAlerts",
            conditions=conditions,
        )
    
    def _create_error_rate_alerts(self) -> AlertRule:
        """Create error rate alerts."""
        conditions = [
            AlertCondition(
                name="HighSearchErrorRate",
                query="rate(search_errors_total[5m]) / rate(search_requests_total[5m]) > 0.05",
                description="Search error rate is above 5%",
                severity=AlertSeverity.WARNING,
                duration="5m",
                labels={"component": "search"},
            ),
            AlertCondition(
                name="CriticalSearchErrorRate",
                query="rate(search_errors_total[5m]) / rate(search_requests_total[5m]) > 0.10",
                description="Search error rate is critically high (>10%)",
                severity=AlertSeverity.CRITICAL,
                duration="2m",
                labels={"component": "search"},
            ),
            AlertCondition(
                name="HighRankingErrorRate",
                query="rate(ranking_errors_total[5m]) / rate(ranking_requests_total[5m]) > 0.05",
                description="Ranking error rate is above 5%",
                severity=AlertSeverity.WARNING,
                duration="5m",
                labels={"component": "ranking"},
            ),
            AlertCondition(
                name="HighRecommendationErrorRate",
                query="rate(recommendation_errors_total[5m]) / rate(recommendation_requests_total[5m]) > 0.05",
                description="Recommendation error rate is above 5%",
                severity=AlertSeverity.WARNING,
                duration="5m",
                labels={"component": "recommendation"},
            ),
        ]
        
        return AlertRule(
            name="ErrorRateAlerts",
            conditions=conditions,
        )
    
    def _create_provider_alerts(self) -> AlertRule:
        """Create provider-related alerts."""
        conditions = [
            AlertCondition(
                name="ProviderUnavailable",
                query="provider_health == 0",
                description="Search provider is unavailable",
                severity=AlertSeverity.CRITICAL,
                duration="1m",
                labels={"component": "provider"},
            ),
            AlertCondition(
                name="HighProviderLatency",
                query="histogram_quantile(0.95, rate(provider_latency_seconds_bucket[5m])) > 2.0",
                description="Provider p95 latency is above 2 seconds",
                severity=AlertSeverity.WARNING,
                duration="5m",
                labels={"component": "provider"},
            ),
            AlertCondition(
                name="ProviderConnectionPoolExhausted",
                query="provider_active_connections / provider_max_connections > 0.9",
                description="Provider connection pool is nearly exhausted (>90%)",
                severity=AlertSeverity.WARNING,
                duration="5m",
                labels={"component": "provider"},
            ),
        ]
        
        return AlertRule(
            name="ProviderAlerts",
            conditions=conditions,
        )
    
    def _create_cache_alerts(self) -> AlertRule:
        """Create cache-related alerts."""
        conditions = [
            AlertCondition(
                name="LowCacheHitRate",
                query="rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) < 0.5",
                description="Cache hit rate is below 50%",
                severity=AlertSeverity.WARNING,
                duration="10m",
                labels={"component": "cache"},
            ),
            AlertCondition(
                name="CacheSizeExceeded",
                query="cache_size > cache_max_size * 0.9",
                description="Cache size is above 90% of maximum",
                severity=AlertSeverity.WARNING,
                duration="5m",
                labels={"component": "cache"},
            ),
            AlertCondition(
                name="CacheEvictionRateHigh",
                query="rate(cache_evictions_total[5m]) > 100",
                description="Cache eviction rate is high (>100/sec)",
                severity=AlertSeverity.WARNING,
                duration="5m",
                labels={"component": "cache"},
            ),
        ]
        
        return AlertRule(
            name="CacheAlerts",
            conditions=conditions,
        )
    
    def _create_pipeline_alerts(self) -> AlertRule:
        """Create pipeline-related alerts."""
        conditions = [
            AlertCondition(
                name="PipelineFailureRate",
                query="rate(pipeline_failures_total[5m]) / rate(pipeline_executions_total[5m]) > 0.05",
                description="Pipeline failure rate is above 5%",
                severity=AlertSeverity.WARNING,
                duration="5m",
                labels={"component": "pipeline"},
            ),
            AlertCondition(
                name="PipelineStalled",
                query="pipeline_queue_size > 1000",
                description="Pipeline queue size is high (>1000)",
                severity=AlertSeverity.WARNING,
                duration="5m",
                labels={"component": "pipeline"},
            ),
            AlertCondition(
                name="SlowPipelineStage",
                query="pipeline_stage_duration_seconds > 10",
                description="Pipeline stage execution time is high (>10s)",
                severity=AlertSeverity.WARNING,
                duration="5m",
                labels={"component": "pipeline"},
            ),
        ]
        
        return AlertRule(
            name="PipelineAlerts",
            conditions=conditions,
        )
    
    def _create_recommendation_alerts(self) -> AlertRule:
        """Create recommendation-specific alerts."""
        conditions = [
            AlertCondition(
                name="LowRecommendationAcceptance",
                query="rate(recommendation_acceptances_total[1h]) / rate(recommendations_generated_total[1h]) < 0.1",
                description="Recommendation acceptance rate is below 10%",
                severity=AlertSeverity.WARNING,
                duration="1h",
                labels={"component": "recommendation"},
            ),
            AlertCondition(
                name="LowRecommendationDiversity",
                query="recommendation_diversity_score < 0.3",
                description="Recommendation diversity score is low (<0.3)",
                severity=AlertSeverity.WARNING,
                duration="30m",
                labels={"component": "recommendation"},
            ),
            AlertCondition(
                name="ZeroRecommendations",
                query="rate(zero_recommendations_total[5m]) > 0.1",
                description="Rate of zero-result recommendations is high (>10%)",
                severity=AlertSeverity.WARNING,
                duration="5m",
                labels={"component": "recommendation"},
            ),
        ]
        
        return AlertRule(
            name="RecommendationAlerts",
            conditions=conditions,
        )
    
    def _create_health_alerts(self) -> AlertRule:
        """Create health-related alerts."""
        conditions = [
            AlertCondition(
                name="ComponentUnhealthy",
                query="component_health != 1",
                description="Component health status is unhealthy",
                severity=AlertSeverity.CRITICAL,
                duration="2m",
                labels={"component": "health"},
            ),
            AlertCondition(
                name="SystemDegraded",
                query="system_health < 0.8",
                description="Overall system health is degraded (<80%)",
                severity=AlertSeverity.WARNING,
                duration="5m",
                labels={"component": "health"},
            ),
            AlertCondition(
                name="HighDiagnosticCount",
                query="diagnostics_total > 100",
                description="Number of active diagnostics is high (>100)",
                severity=AlertSeverity.WARNING,
                duration="5m",
                labels={"component": "health"},
            ),
        ]
        
        return AlertRule(
            name="HealthAlerts",
            conditions=conditions,
        )
    
    def _create_infrastructure_alerts(self) -> AlertRule:
        """Create infrastructure-related alerts."""
        conditions = [
            AlertCondition(
                name="HighMemoryUsage",
                query="memory_usage_percent > 90",
                description="Memory usage is critically high (>90%)",
                severity=AlertSeverity.CRITICAL,
                duration="5m",
                labels={"component": "infrastructure"},
            ),
            AlertCondition(
                name="HighCPUUsage",
                query="cpu_usage_percent > 80",
                description="CPU usage is high (>80%)",
                severity=AlertSeverity.WARNING,
                duration="10m",
                labels={"component": "infrastructure"},
            ),
            AlertCondition(
                name="DiskSpaceLow",
                query="disk_usage_percent > 85",
                description="Disk usage is high (>85%)",
                severity=AlertSeverity.WARNING,
                duration="5m",
                labels={"component": "infrastructure"},
            ),
            AlertCondition(
                name="SlowIndexing",
                query="indexing_latency_seconds > 60",
                description="Indexing latency is high (>60s)",
                severity=AlertSeverity.WARNING,
                duration="10m",
                labels={"component": "infrastructure"},
            ),
        ]
        
        return AlertRule(
            name="InfrastructureAlerts",
            conditions=conditions,
        )
    
    def register_alert_rule(self, alert_rule: AlertRule) -> None:
        """
        Register an alert rule.
        
        Args:
            alert_rule: Alert rule to register
        """
        self._alert_rules[alert_rule.name] = alert_rule
    
    def unregister_alert_rule(self, name: str) -> None:
        """
        Unregister an alert rule.
        
        Args:
            name: Name of alert rule to unregister
        """
        if name in self._alert_rules:
            del self._alert_rules[name]
    
    def get_alert_rule(self, name: str) -> Optional[AlertRule]:
        """
        Get an alert rule by name.
        
        Args:
            name: Alert rule name
            
        Returns:
            Alert rule or None
        """
        return self._alert_rules.get(name)
    
    def get_all_alert_rules(self) -> Dict[str, AlertRule]:
        """Get all registered alert rules."""
        return self._alert_rules.copy()
    
    def trigger_alert(
        self,
        name: str,
        severity: AlertSeverity,
        message: str,
        value: Optional[float] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Alert:
        """
        Trigger an alert.
        
        Args:
            name: Alert name
            severity: Alert severity
            message: Alert message
            value: Alert value
            labels: Alert labels
            
        Returns:
            Alert instance
        """
        from datetime import datetime
        
        alert = Alert(
            name=name,
            state=AlertState.FIRING,
            severity=severity,
            message=message,
            timestamp=datetime.utcnow(),
            labels=labels or {},
            value=value,
        )
        
        self._active_alerts[name] = alert
        return alert
    
    def resolve_alert(self, name: str) -> Optional[Alert]:
        """
        Resolve an alert.
        
        Args:
            name: Alert name
            
        Returns:
            Resolved alert or None
        """
        if name in self._active_alerts:
            alert = self._active_alerts[name]
            alert.state = AlertState.RESOLVED
            return alert
        return None
    
    def get_active_alerts(self) -> List[Alert]:
        """
        Get all active alerts.
        
        Returns:
            List of active alerts
        """
        return [
            alert for alert in self._active_alerts.values()
            if alert.state == AlertState.FIRING
        ]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """
        Get alerts by severity.
        
        Args:
            severity: Alert severity
            
        Returns:
            List of alerts
        """
        return [
            alert for alert in self._active_alerts.values()
            if alert.severity == severity
        ]
    
    def export_prometheus(self) -> str:
        """Export alert rules in Prometheus format."""
        groups = []
        
        for rule_name, alert_rule in self._alert_rules.items():
            if not alert_rule.enabled:
                continue
            
            group = {
                "name": rule_name,
                "rules": [condition.to_dict() for condition in alert_rule.conditions],
            }
            groups.append(group)
        
        import yaml
        return yaml.dump({"groups": groups}, default_flow_style=False)
    
    def evaluate_conditions(self, metrics: Dict[str, float]) -> List[Alert]:
        """
        Evaluate alert conditions against current metrics.
        
        Args:
            metrics: Current metric values
            
        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        
        for alert_rule in self._alert_rules.values():
            if not alert_rule.enabled:
                continue
            
            for condition in alert_rule.conditions:
                # This would evaluate the Prometheus query against metrics
                # For now, this is a placeholder
                # In production, you would use a Prometheus client to evaluate queries
                pass
        
        return triggered_alerts
