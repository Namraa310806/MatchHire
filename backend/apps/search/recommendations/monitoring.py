"""
Recommendation Monitoring.

This module provides monitoring and metrics for the recommendation engine,
tracking performance, acceptance rates, diversity, and other key metrics.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
from collections import defaultdict


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class Metric:
    """
    A metric for monitoring.
    
    Contains the metric value and metadata.
    """
    
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
        }


@dataclass
class RecommendationMetrics:
    """Metrics for recommendation operations."""
    
    total_recommendations: int = 0
    candidate_recommendations: int = 0
    job_recommendations: int = 0
    related_entity_recommendations: int = 0
    
    total_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0.0
    
    cache_hits: int = 0
    cache_misses: int = 0
    
    acceptance_rate: float = 0.0
    click_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        avg_latency = (
            self.total_latency_ms / self.total_recommendations
            if self.total_recommendations > 0 else 0.0
        )
        
        return {
            "total_recommendations": self.total_recommendations,
            "candidate_recommendations": self.candidate_recommendations,
            "job_recommendations": self.job_recommendations,
            "related_entity_recommendations": self.related_entity_recommendations,
            "avg_latency_ms": avg_latency,
            "min_latency_ms": self.min_latency_ms if self.min_latency_ms != float('inf') else 0.0,
            "max_latency_ms": self.max_latency_ms,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0.0,
            "acceptance_rate": self.acceptance_rate,
            "click_rate": self.click_rate,
        }


@dataclass
class StrategyMetrics:
    """Metrics for recommendation strategies."""
    
    strategy_usage: Dict[str, int] = field(default_factory=dict)
    strategy_performance: Dict[str, float] = field(default_factory=dict)
    strategy_latency: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "strategy_usage": self.strategy_usage,
            "strategy_performance": self.strategy_performance,
            "strategy_latency": self.strategy_latency,
        }


@dataclass
class PipelineMetrics:
    """Metrics for recommendation pipeline."""
    
    total_pipeline_executions: int = 0
    pipeline_failures: int = 0
    
    stage_times: Dict[str, List[float]] = field(default_factory=dict)
    stage_failures: Dict[str, int] = field(default_factory=dict)
    
    candidates_generated: int = 0
    candidates_filtered: int = 0
    candidates_ranked: int = 0
    candidates_diversified: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        avg_stage_times = {
            stage: sum(times) / len(times) if times else 0.0
            for stage, times in self.stage_times.items()
        }
        
        return {
            "total_pipeline_executions": self.total_pipeline_executions,
            "pipeline_failures": self.pipeline_failures,
            "failure_rate": self.pipeline_failures / self.total_pipeline_executions if self.total_pipeline_executions > 0 else 0.0,
            "avg_stage_times_ms": avg_stage_times,
            "stage_failures": self.stage_failures,
            "candidates_generated": self.candidates_generated,
            "candidates_filtered": self.candidates_filtered,
            "candidates_ranked": self.candidates_ranked,
            "candidates_diversified": self.candidates_diversified,
        }


@dataclass
class DiversificationMetrics:
    """Metrics for diversification."""
    
    total_diversifications: int = 0
    
    skill_diversity_score: float = 0.0
    company_diversity_score: float = 0.0
    location_diversity_score: float = 0.0
    experience_diversity_score: float = 0.0
    salary_diversity_score: float = 0.0
    industry_diversity_score: float = 0.0
    
    duplicates_removed: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total_diversifications": self.total_diversifications,
            "skill_diversity_score": self.skill_diversity_score,
            "company_diversity_score": self.company_diversity_score,
            "location_diversity_score": self.location_diversity_score,
            "experience_diversity_score": self.experience_diversity_score,
            "salary_diversity_score": self.salary_diversity_score,
            "industry_diversity_score": self.industry_diversity_score,
            "duplicates_removed": self.duplicates_removed,
        }


class RecommendationMonitor:
    """
    Monitor for recommendation operations.
    
    Tracks metrics for recommendations, strategies, pipeline, and diversification.
    """
    
    def __init__(self):
        """Initialize the recommendation monitor."""
        self._lock = threading.RLock()
        
        self._recommendation_metrics = RecommendationMetrics()
        self._strategy_metrics = StrategyMetrics()
        self._pipeline_metrics = PipelineMetrics()
        self._diversification_metrics = DiversificationMetrics()
        
        self._metrics_history: List[tuple] = []
        self._max_history_size = 1000
    
    def record_recommendation(
        self,
        recommendation_type: str,
        count: int,
        latency_ms: float,
    ) -> None:
        """
        Record a recommendation operation.
        
        Args:
            recommendation_type: Type of recommendation
            count: Number of recommendations returned
            latency_ms: Latency in milliseconds
        """
        with self._lock:
            self._recommendation_metrics.total_recommendations += 1
            
            if recommendation_type == "candidate":
                self._recommendation_metrics.candidate_recommendations += 1
            elif recommendation_type == "job":
                self._recommendation_metrics.job_recommendations += 1
            elif recommendation_type == "related_entity":
                self._recommendation_metrics.related_entity_recommendations += 1
            
            self._recommendation_metrics.total_latency_ms += latency_ms
            self._recommendation_metrics.min_latency_ms = min(
                self._recommendation_metrics.min_latency_ms,
                latency_ms,
            )
            self._recommendation_metrics.max_latency_ms = max(
                self._recommendation_metrics.max_latency_ms,
                latency_ms,
            )
    
    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        with self._lock:
            self._recommendation_metrics.cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        with self._lock:
            self._recommendation_metrics.cache_misses += 1
    
    def record_strategy_usage(
        self,
        strategy_name: str,
        performance: float,
        latency_ms: float,
    ) -> None:
        """
        Record strategy usage.
        
        Args:
            strategy_name: Name of the strategy
            performance: Performance score (0-1)
            latency_ms: Latency in milliseconds
        """
        with self._lock:
            self._strategy_metrics.strategy_usage[strategy_name] = \
                self._strategy_metrics.strategy_usage.get(strategy_name, 0) + 1
            
            # Update average performance
            current_perf = self._strategy_metrics.strategy_performance.get(strategy_name, 0.0)
            count = self._strategy_metrics.strategy_usage[strategy_name]
            new_perf = (current_perf * (count - 1) + performance) / count
            self._strategy_metrics.strategy_performance[strategy_name] = new_perf
            
            # Update average latency
            current_latency = self._strategy_metrics.strategy_latency.get(strategy_name, 0.0)
            new_latency = (current_latency * (count - 1) + latency_ms) / count
            self._strategy_metrics.strategy_latency[strategy_name] = new_latency
    
    def record_pipeline_execution(
        self,
        stage_times: Dict[str, float],
        candidates_generated: int,
        candidates_filtered: int,
        candidates_ranked: int,
        candidates_diversified: int,
        failed: bool = False,
    ) -> None:
        """
        Record pipeline execution.
        
        Args:
            stage_times: Time taken for each stage
            candidates_generated: Number of candidates generated
            candidates_filtered: Number of candidates filtered
            candidates_ranked: Number of candidates ranked
            candidates_diversified: Number of candidates diversified
            failed: Whether the pipeline failed
        """
        with self._lock:
            self._pipeline_metrics.total_pipeline_executions += 1
            
            if failed:
                self._pipeline_metrics.pipeline_failures += 1
            
            for stage, time_ms in stage_times.items():
                if stage not in self._pipeline_metrics.stage_times:
                    self._pipeline_metrics.stage_times[stage] = []
                self._pipeline_metrics.stage_times[stage].append(time_ms)
            
            self._pipeline_metrics.candidates_generated += candidates_generated
            self._pipeline_metrics.candidates_filtered += candidates_filtered
            self._pipeline_metrics.candidates_ranked += candidates_ranked
            self._pipeline_metrics.candidates_diversified += candidates_diversified
    
    def record_stage_failure(self, stage_name: str) -> None:
        """
        Record a pipeline stage failure.
        
        Args:
            stage_name: Name of the failed stage
        """
        with self._lock:
            self._pipeline_metrics.stage_failures[stage_name] = \
                self._pipeline_metrics.stage_failures.get(stage_name, 0) + 1
    
    def record_diversification(
        self,
        diversity_scores: Dict[str, float],
        duplicates_removed: int,
    ) -> None:
        """
        Record diversification metrics.
        
        Args:
            diversity_scores: Diversity scores for each dimension
            duplicates_removed: Number of duplicates removed
        """
        with self._lock:
            self._diversification_metrics.total_diversifications += 1
            
            self._diversification_metrics.skill_diversity_score = \
                diversity_scores.get("skill", 0.0)
            self._diversification_metrics.company_diversity_score = \
                diversity_scores.get("company", 0.0)
            self._diversification_metrics.location_diversity_score = \
                diversity_scores.get("location", 0.0)
            self._diversification_metrics.experience_diversity_score = \
                diversity_scores.get("experience", 0.0)
            self._diversification_metrics.salary_diversity_score = \
                diversity_scores.get("salary", 0.0)
            self._diversification_metrics.industry_diversity_score = \
                diversity_scores.get("industry", 0.0)
            
            self._diversification_metrics.duplicates_removed += duplicates_removed
    
    def record_acceptance(self, accepted: bool) -> None:
        """
        Record recommendation acceptance.
        
        Args:
            accepted: Whether the recommendation was accepted
        """
        with self._lock:
            # Update acceptance rate using exponential moving average
            current_rate = self._recommendation_metrics.acceptance_rate
            alpha = 0.1  # Smoothing factor
            new_rate = alpha * (1.0 if accepted else 0.0) + (1 - alpha) * current_rate
            self._recommendation_metrics.acceptance_rate = new_rate
    
    def record_click(self, clicked: bool) -> None:
        """
        Record recommendation click.
        
        Args:
            clicked: Whether the recommendation was clicked
        """
        with self._lock:
            # Update click rate using exponential moving average
            current_rate = self._recommendation_metrics.click_rate
            alpha = 0.1  # Smoothing factor
            new_rate = alpha * (1.0 if clicked else 0.0) + (1 - alpha) * current_rate
            self._recommendation_metrics.click_rate = new_rate
    
    def get_recommendation_metrics(self) -> RecommendationMetrics:
        """
        Get recommendation metrics.
        
        Returns:
            Recommendation metrics
        """
        with self._lock:
            return self._recommendation_metrics
    
    def get_strategy_metrics(self) -> StrategyMetrics:
        """
        Get strategy metrics.
        
        Returns:
            Strategy metrics
        """
        with self._lock:
            return self._strategy_metrics
    
    def get_pipeline_metrics(self) -> PipelineMetrics:
        """
        Get pipeline metrics.
        
        Returns:
            Pipeline metrics
        """
        with self._lock:
            return self._pipeline_metrics
    
    def get_diversification_metrics(self) -> DiversificationMetrics:
        """
        Get diversification metrics.
        
        Returns:
            Diversification metrics
        """
        with self._lock:
            return self._diversification_metrics
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get all monitoring statistics.
        
        Returns:
            All statistics
        """
        with self._lock:
            return {
                "recommendation": self._recommendation_metrics.to_dict(),
                "strategy": self._strategy_metrics.to_dict(),
                "pipeline": self._pipeline_metrics.to_dict(),
                "diversification": self._diversification_metrics.to_dict(),
            }
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._recommendation_metrics = RecommendationMetrics()
            self._strategy_metrics = StrategyMetrics()
            self._pipeline_metrics = PipelineMetrics()
            self._diversification_metrics = DiversificationMetrics()
            self._metrics_history.clear()
    
    def snapshot_metrics(self) -> None:
        """Take a snapshot of current metrics for historical tracking."""
        with self._lock:
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "recommendation": self._recommendation_metrics.to_dict(),
                "strategy": self._strategy_metrics.to_dict(),
                "pipeline": self._pipeline_metrics.to_dict(),
                "diversification": self._diversification_metrics.to_dict(),
            }
            
            self._metrics_history.append(snapshot)
            
            # Trim history if too large
            if len(self._metrics_history) > self._max_history_size:
                self._metrics_history = self._metrics_history[-self._max_history_size:]
    
    def get_metrics_history(
        self,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get metrics history.
        
        Args:
            limit: Maximum number of snapshots to return
            
        Returns:
            Metrics history
        """
        with self._lock:
            if limit:
                return self._metrics_history[-limit:]
            return self._metrics_history.copy()
