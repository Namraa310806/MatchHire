"""
Quality Metrics Hooks.

This module provides hooks for tracking quality metrics like CTR,
recommendation acceptance, search success, and other business metrics.
These are interfaces for future ML-based quality tracking.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from abc import ABC, abstractmethod
import threading
from .core import ObservabilityConfig, ObservabilityEvent, EventType, ObservabilityComponent


class QualityMetricType(Enum):
    """Types of quality metrics."""
    CTR = "click_through_rate"
    CONVERSION = "conversion_rate"
    ACCEPTANCE = "acceptance_rate"
    ABANDONMENT = "abandonment_rate"
    SUCCESS = "success_rate"
    ZERO_RESULTS = "zero_results_rate"
    RANKING_CONSISTENCY = "ranking_consistency"
    DIVERSITY_SCORE = "diversity_score"
    COVERAGE_SCORE = "coverage_score"
    RELEVANCE_SCORE = "relevance_score"
    SATISFACTION = "satisfaction_score"


@dataclass
class QualityMetric:
    """Quality metric data point."""
    
    metric_type: QualityMetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Optional[Dict[str, Any]] = None
    component: Optional[ObservabilityComponent] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "metric_type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "component": self.component.value if self.component else None,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
        }


class QualityMetricHook(ABC):
    """
    Abstract base class for quality metric hooks.
    
    Hooks are called when specific events occur to track quality metrics.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """
        Initialize the hook.
        
        Args:
            config: Observability configuration
        """
        self._config = config
    
    @abstractmethod
    def on_event(self, event_data: Dict[str, Any]) -> Optional[QualityMetric]:
        """
        Handle an event and return quality metric if applicable.
        
        Args:
            event_data: Event data
            
        Returns:
            Quality metric or None
        """
        pass


class CTRHook(QualityMetricHook):
    """
    Click-through rate hook.
    
    Tracks when users click on search results or recommendations.
    """
    
    def on_event(self, event_data: Dict[str, Any]) -> Optional[QualityMetric]:
        """
        Handle click event.
        
        Args:
            event_data: Event data with click information
            
        Returns:
            CTR metric
        """
        # This would calculate CTR based on impressions and clicks
        # For now, return a placeholder
        return QualityMetric(
            metric_type=QualityMetricType.CTR,
            value=event_data.get("ctr", 0.0),
            context=event_data,
            component=ObservabilityComponent.SEARCH,
            user_id=event_data.get("user_id"),
            session_id=event_data.get("session_id"),
        )


class RecommendationAcceptanceHook(QualityMetricHook):
    """
    Recommendation acceptance hook.
    
    Tracks when users accept recommendations (e.g., apply to job, contact candidate).
    """
    
    def on_event(self, event_data: Dict[str, Any]) -> Optional[QualityMetric]:
        """
        Handle recommendation acceptance event.
        
        Args:
            event_data: Event data with acceptance information
            
        Returns:
            Acceptance metric
        """
        return QualityMetric(
            metric_type=QualityMetricType.ACCEPTANCE,
            value=event_data.get("accepted", 0.0),
            context=event_data,
            component=ObservabilityComponent.RECOMMENDATION,
            entity_type=event_data.get("entity_type"),
            entity_id=event_data.get("entity_id"),
            user_id=event_data.get("user_id"),
        )


class SearchAbandonmentHook(QualityMetricHook):
    """
    Search abandonment hook.
    
    Tracks when users abandon searches without taking action.
    """
    
    def on_event(self, event_data: Dict[str, Any]) -> Optional[QualityMetric]:
        """
        Handle search abandonment event.
        
        Args:
            event_data: Event data with abandonment information
            
        Returns:
            Abandonment metric
        """
        return QualityMetric(
            metric_type=QualityMetricType.ABANDONMENT,
            value=1.0 if event_data.get("abandoned", False) else 0.0,
            context=event_data,
            component=ObservabilityComponent.SEARCH,
            user_id=event_data.get("user_id"),
            session_id=event_data.get("session_id"),
        )


class SearchSuccessHook(QualityMetricHook):
    """
    Search success hook.
    
    Tracks when searches are successful (non-zero results, user engagement).
    """
    
    def on_event(self, event_data: Dict[str, Any]) -> Optional[QualityMetric]:
        """
        Handle search success event.
        
        Args:
            event_data: Event data with search results
            
        Returns:
            Success metric
        """
        result_count = event_data.get("result_count", 0)
        success = result_count > 0
        
        return QualityMetric(
            metric_type=QualityMetricType.SUCCESS,
            value=1.0 if success else 0.0,
            context=event_data,
            component=ObservabilityComponent.SEARCH,
            user_id=event_data.get("user_id"),
        )


class ZeroResultsHook(QualityMetricHook):
    """
    Zero results hook.
    
    Tracks searches that return zero results.
    """
    
    def on_event(self, event_data: Dict[str, Any]) -> Optional[QualityMetric]:
        """
        Handle zero results event.
        
        Args:
            event_data: Event data with search results
            
        Returns:
            Zero results metric
        """
        result_count = event_data.get("result_count", 0)
        zero_results = result_count == 0
        
        return QualityMetric(
            metric_type=QualityMetricType.ZERO_RESULTS,
            value=1.0 if zero_results else 0.0,
            context=event_data,
            component=ObservabilityComponent.SEARCH,
            user_id=event_data.get("user_id"),
        )


class RankingConsistencyHook(QualityMetricHook):
    """
    Ranking consistency hook.
    
    Tracks consistency of rankings across similar queries.
    """
    
    def on_event(self, event_data: Dict[str, Any]) -> Optional[QualityMetric]:
        """
        Handle ranking consistency event.
        
        Args:
            event_data: Event data with ranking information
            
        Returns:
            Ranking consistency metric
        """
        # This would calculate ranking consistency using statistical measures
        # For now, return a placeholder
        return QualityMetric(
            metric_type=QualityMetricType.RANKING_CONSISTENCY,
            value=event_data.get("consistency", 1.0),
            context=event_data,
            component=ObservabilityComponent.RANKING,
        )


class DiversityScoreHook(QualityMetricHook):
    """
    Diversity score hook.
    
    Tracks diversity of recommendations (skills, companies, locations, etc.).
    """
    
    def on_event(self, event_data: Dict[str, Any]) -> Optional[QualityMetric]:
        """
        Handle diversity score event.
        
        Args:
            event_data: Event data with recommendation diversity information
            
        Returns:
            Diversity score metric
        """
        return QualityMetric(
            metric_type=QualityMetricType.DIVERSITY_SCORE,
            value=event_data.get("diversity_score", 0.0),
            context=event_data,
            component=ObservabilityComponent.RECOMMENDATION,
        )


class CoverageScoreHook(QualityMetricHook):
    """
    Coverage score hook.
    
    Tracks coverage of recommendations (how many candidates/jobs are recommended).
    """
    
    def on_event(self, event_data: Dict[str, Any]) -> Optional[QualityMetric]:
        """
        Handle coverage score event.
        
        Args:
            event_data: Event data with coverage information
            
        Returns:
            Coverage score metric
        """
        return QualityMetric(
            metric_type=QualityMetricType.COVERAGE_SCORE,
            value=event_data.get("coverage_score", 0.0),
            context=event_data,
            component=ObservabilityComponent.RECOMMENDATION,
        )


class RelevanceScoreHook(QualityMetricHook):
    """
    Relevance score hook.
    
    Tracks relevance of search results and recommendations.
    
    This is an interface for future ML-based relevance scoring.
    """
    
    def on_event(self, event_data: Dict[str, Any]) -> Optional[QualityMetric]:
        """
        Handle relevance score event.
        
        Args:
            event_data: Event data with relevance information
            
        Returns:
            Relevance score metric
        """
        # This would use ML models to calculate relevance
        # For now, return a placeholder
        return QualityMetric(
            metric_type=QualityMetricType.RELEVANCE_SCORE,
            value=event_data.get("relevance_score", 0.0),
            context=event_data,
            component=event_data.get("component", ObservabilityComponent.SEARCH),
        )


class SatisfactionScoreHook(QualityMetricHook):
    """
    Satisfaction score hook.
    
    Tracks user satisfaction with search results and recommendations.
    
    This is an interface for future ML-based satisfaction scoring.
    """
    
    def on_event(self, event_data: Dict[str, Any]) -> Optional[QualityMetric]:
        """
        Handle satisfaction score event.
        
        Args:
            event_data: Event data with satisfaction information
            
        Returns:
            Satisfaction score metric
        """
        # This would use ML models or explicit user feedback
        # For now, return a placeholder
        return QualityMetric(
            metric_type=QualityMetricType.SATISFACTION,
            value=event_data.get("satisfaction_score", 0.0),
            context=event_data,
            component=event_data.get("component", ObservabilityComponent.SEARCH),
            user_id=event_data.get("user_id"),
        )


class QualityMetricsCollector:
    """
    Collector for quality metrics.
    
    This collector manages quality metric hooks and aggregates
    quality metrics for analysis.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """
        Initialize the quality metrics collector.
        
        Args:
            config: Observability configuration
        """
        self._config = config
        self._hooks: Dict[str, QualityMetricHook] = {}
        self._metrics: List[QualityMetric] = []
        self._lock = threading.Lock()
        
        # Register default hooks
        self._register_default_hooks()
    
    def _register_default_hooks(self) -> None:
        """Register default quality metric hooks."""
        self.register_hook("ctr", CTRHook(self._config))
        self.register_hook("acceptance", RecommendationAcceptanceHook(self._config))
        self.register_hook("abandonment", SearchAbandonmentHook(self._config))
        self.register_hook("success", SearchSuccessHook(self._config))
        self.register_hook("zero_results", ZeroResultsHook(self._config))
        self.register_hook("ranking_consistency", RankingConsistencyHook(self._config))
        self.register_hook("diversity", DiversityScoreHook(self._config))
        self.register_hook("coverage", CoverageScoreHook(self._config))
        self.register_hook("relevance", RelevanceScoreHook(self._config))
        self.register_hook("satisfaction", SatisfactionScoreHook(self._config))
    
    def register_hook(self, name: str, hook: QualityMetricHook) -> None:
        """
        Register a quality metric hook.
        
        Args:
            name: Hook name
            hook: Hook instance
        """
        self._hooks[name] = hook
    
    def unregister_hook(self, name: str) -> None:
        """
        Unregister a quality metric hook.
        
        Args:
            name: Hook name
        """
        if name in self._hooks:
            del self._hooks[name]
    
    def record_event(self, hook_name: str, event_data: Dict[str, Any]) -> Optional[QualityMetric]:
        """
        Record an event to a specific hook.
        
        Args:
            hook_name: Name of hook to use
            event_data: Event data
            
        Returns:
            Quality metric or None
        """
        hook = self._hooks.get(hook_name)
        if not hook:
            return None
        
        metric = hook.on_event(event_data)
        
        if metric:
            with self._lock:
                self._metrics.append(metric)
                
                # Keep metrics bounded
                if len(self._metrics) > 100000:
                    self._metrics = self._metrics[-100000:]
        
        return metric
    
    def record_click(
        self,
        user_id: str,
        result_id: str,
        position: int,
        session_id: Optional[str] = None,
    ) -> Optional[QualityMetric]:
        """
        Record a click event.
        
        Args:
            user_id: User ID
            result_id: ID of clicked result
            position: Position of clicked result
            session_id: Session ID
            
        Returns:
            CTR metric
        """
        return self.record_event(
            "ctr",
            {
                "user_id": user_id,
                "result_id": result_id,
                "position": position,
                "session_id": session_id,
                "ctr": 1.0,  # Simplified - would calculate actual CTR
            },
        )
    
    def record_recommendation_acceptance(
        self,
        user_id: str,
        recommendation_id: str,
        entity_type: str,
        entity_id: str,
    ) -> Optional[QualityMetric]:
        """
        Record a recommendation acceptance event.
        
        Args:
            user_id: User ID
            recommendation_id: Recommendation ID
            entity_type: Type of entity (job, candidate)
            entity_id: ID of entity
            
        Returns:
            Acceptance metric
        """
        return self.record_event(
            "acceptance",
            {
                "user_id": user_id,
                "recommendation_id": recommendation_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "accepted": 1.0,
            },
        )
    
    def record_search_abandonment(
        self,
        user_id: str,
        query: str,
        result_count: int,
        session_id: Optional[str] = None,
    ) -> Optional[QualityMetric]:
        """
        Record a search abandonment event.
        
        Args:
            user_id: User ID
            query: Search query
            result_count: Number of results
            session_id: Session ID
            
        Returns:
            Abandonment metric
        """
        return self.record_event(
            "abandonment",
            {
                "user_id": user_id,
                "query": query,
                "result_count": result_count,
                "session_id": session_id,
                "abandoned": True,
            },
        )
    
    def record_search_success(
        self,
        user_id: str,
        query: str,
        result_count: int,
    ) -> Optional[QualityMetric]:
        """
        Record a search success event.
        
        Args:
            user_id: User ID
            query: Search query
            result_count: Number of results
            
        Returns:
            Success metric
        """
        return self.record_event(
            "success",
            {
                "user_id": user_id,
                "query": query,
                "result_count": result_count,
            },
        )
    
    def record_zero_results(
        self,
        user_id: str,
        query: str,
    ) -> Optional[QualityMetric]:
        """
        Record a zero results event.
        
        Args:
            user_id: User ID
            query: Search query
            
        Returns:
            Zero results metric
        """
        return self.record_event(
            "zero_results",
            {
                "user_id": user_id,
                "query": query,
                "result_count": 0,
            },
        )
    
    def get_metrics(
        self,
        metric_type: Optional[QualityMetricType] = None,
        component: Optional[ObservabilityComponent] = None,
        user_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[QualityMetric]:
        """
        Get quality metrics with optional filters.
        
        Args:
            metric_type: Optional metric type filter
            component: Optional component filter
            user_id: Optional user ID filter
            since: Optional start time filter
            limit: Maximum number of metrics to return
            
        Returns:
            List of quality metrics
        """
        with self._lock:
            metrics = self._metrics
            
            if metric_type:
                metrics = [m for m in metrics if m.metric_type == metric_type]
            
            if component:
                metrics = [m for m in metrics if m.component == component]
            
            if user_id:
                metrics = [m for m in metrics if m.user_id == user_id]
            
            if since:
                metrics = [m for m in metrics if m.timestamp >= since]
            
            return metrics[-limit:]
    
    def get_metric_summary(self, metric_type: QualityMetricType) -> Dict[str, float]:
        """
        Get summary statistics for a metric type.
        
        Args:
            metric_type: Type of metric to summarize
            
        Returns:
            Summary statistics dictionary
        """
        metrics = self.get_metrics(metric_type=metric_type, limit=100000)
        
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        
        import statistics
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": statistics.mean(values),
            "median": statistics.median(values),
            "sum": sum(values),
        }
    
    def get_all_summaries(self) -> Dict[str, Dict[str, float]]:
        """
        Get summaries for all metric types.
        
        Returns:
            Dictionary of metric type to summary
        """
        summaries = {}
        
        for metric_type in QualityMetricType:
            summary = self.get_metric_summary(metric_type)
            if summary:
                summaries[metric_type.value] = summary
        
        return summaries
    
    def clear_old_metrics(self, retention_days: int = 30) -> None:
        """
        Clear old quality metrics.
        
        Args:
            retention_days: Retention period in days
        """
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        
        with self._lock:
            self._metrics = [
                metric for metric in self._metrics
                if metric.timestamp >= cutoff
            ]
