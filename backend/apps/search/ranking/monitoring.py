"""
Ranking Monitoring.

This module provides monitoring and metrics for ranking operations.
Tracks latency, signal contribution, cache performance, and pipeline health.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import time


@dataclass
class SignalMetrics:
    """Metrics for a single ranking signal."""
    
    signal_name: str
    total_calls: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    error_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def update(self, duration_ms: float, cached: bool = False) -> None:
        """Update metrics with a new measurement."""
        self.total_calls += 1
        self.total_time_ms += duration_ms
        self.avg_time_ms = self.total_time_ms / self.total_calls
        self.min_time_ms = min(self.min_time_ms, duration_ms)
        self.max_time_ms = max(self.max_time_ms, duration_ms)
        
        if cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def record_error(self) -> None:
        """Record an error."""
        self.error_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "signal_name": self.signal_name,
            "total_calls": self.total_calls,
            "total_time_ms": self.total_time_ms,
            "avg_time_ms": self.avg_time_ms,
            "min_time_ms": self.min_time_ms if self.min_time_ms != float('inf') else 0.0,
            "max_time_ms": self.max_time_ms,
            "error_count": self.error_count,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0.0,
        }


@dataclass
class PipelineMetrics:
    """Metrics for ranking pipeline execution."""
    
    total_executions: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    stage_times_ms: Dict[str, List[float]] = field(default_factory=dict)
    early_terminations: int = 0
    parallel_executions: int = 0
    sequential_executions: int = 0
    
    def update(self, duration_ms: float, stage_times: Dict[str, float], parallel: bool = False) -> None:
        """Update metrics with a new execution."""
        self.total_executions += 1
        self.total_time_ms += duration_ms
        self.avg_time_ms = self.total_time_ms / self.total_executions
        self.min_time_ms = min(self.min_time_ms, duration_ms)
        self.max_time_ms = max(self.max_time_ms, duration_ms)
        
        for stage_name, stage_time in stage_times.items():
            if stage_name not in self.stage_times_ms:
                self.stage_times_ms[stage_name] = []
            self.stage_times_ms[stage_name].append(stage_time)
        
        if parallel:
            self.parallel_executions += 1
        else:
            self.sequential_executions += 1
    
    def record_early_termination(self) -> None:
        """Record an early termination event."""
        self.early_terminations += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        stage_avg_times = {}
        for stage_name, times in self.stage_times_ms.items():
            if times:
                stage_avg_times[stage_name] = sum(times) / len(times)
        
        return {
            "total_executions": self.total_executions,
            "total_time_ms": self.total_time_ms,
            "avg_time_ms": self.avg_time_ms,
            "min_time_ms": self.min_time_ms if self.min_time_ms != float('inf') else 0.0,
            "max_time_ms": self.max_time_ms,
            "stage_avg_times_ms": stage_avg_times,
            "early_terminations": self.early_terminations,
            "parallel_executions": self.parallel_executions,
            "sequential_executions": self.sequential_executions,
        }


@dataclass
class CacheMetrics:
    """Metrics for cache performance."""
    
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 1000
    
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "size": self.size,
            "max_size": self.max_size,
            "hit_rate": self.hit_rate(),
            "miss_rate": 1.0 - self.hit_rate(),
        }


@dataclass
class RankingMetrics:
    """Overall ranking metrics."""
    
    total_rankings: int = 0
    total_documents_ranked: int = 0
    avg_documents_per_ranking: float = 0.0
    ranking_latency_p50: float = 0.0
    ranking_latency_p95: float = 0.0
    ranking_latency_p99: float = 0.0
    ranking_latencies: List[float] = field(default_factory=list)
    
    def update(self, duration_ms: float, document_count: int) -> None:
        """Update metrics with a new ranking."""
        self.total_rankings += 1
        self.total_documents_ranked += document_count
        self.avg_documents_per_ranking = self.total_documents_ranked / self.total_rankings
        self.ranking_latencies.append(duration_ms)
        
        # Keep only last 1000 latencies for percentile calculation
        if len(self.ranking_latencies) > 1000:
            self.ranking_latencies = self.ranking_latencies[-1000:]
        
        self._calculate_percentiles()
    
    def _calculate_percentiles(self) -> None:
        """Calculate latency percentiles."""
        if not self.ranking_latencies:
            return
        
        sorted_latencies = sorted(self.ranking_latencies)
        n = len(sorted_latencies)
        
        self.ranking_latency_p50 = sorted_latencies[int(n * 0.5)]
        self.ranking_latency_p95 = sorted_latencies[int(n * 0.95)]
        self.ranking_latency_p99 = sorted_latencies[int(n * 0.99)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total_rankings": self.total_rankings,
            "total_documents_ranked": self.total_documents_ranked,
            "avg_documents_per_ranking": self.avg_documents_per_ranking,
            "ranking_latency_p50_ms": self.ranking_latency_p50,
            "ranking_latency_p95_ms": self.ranking_latency_p95,
            "ranking_latency_p99_ms": self.ranking_latency_p99,
        }


class RankingMonitor:
    """
    Monitor for ranking operations.
    
    Collects metrics on ranking performance, signal execution,
    pipeline health, and cache performance.
    """
    
    def __init__(self):
        """Initialize the ranking monitor."""
        self._signal_metrics: Dict[str, SignalMetrics] = {}
        self._pipeline_metrics = PipelineMetrics()
        self._cache_metrics = CacheMetrics()
        self._ranking_metrics = RankingMetrics()
        self._lock = threading.RLock()
        self._start_time = datetime.now()
    
    def record_signal_execution(
        self,
        signal_name: str,
        duration_ms: float,
        cached: bool = False,
    ) -> None:
        """
        Record a signal execution.
        
        Args:
            signal_name: Name of the signal
            duration_ms: Execution duration in milliseconds
            cached: Whether the result was cached
        """
        with self._lock:
            if signal_name not in self._signal_metrics:
                self._signal_metrics[signal_name] = SignalMetrics(signal_name=signal_name)
            
            self._signal_metrics[signal_name].update(duration_ms, cached)
    
    def record_signal_error(self, signal_name: str) -> None:
        """
        Record a signal error.
        
        Args:
            signal_name: Name of the signal
        """
        with self._lock:
            if signal_name not in self._signal_metrics:
                self._signal_metrics[signal_name] = SignalMetrics(signal_name=signal_name)
            
            self._signal_metrics[signal_name].record_error()
    
    def record_pipeline_execution(
        self,
        duration_ms: float,
        stage_times: Dict[str, float],
        parallel: bool = False,
    ) -> None:
        """
        Record a pipeline execution.
        
        Args:
            duration_ms: Total execution duration in milliseconds
            stage_times: Duration of each stage
            parallel: Whether execution was parallel
        """
        with self._lock:
            self._pipeline_metrics.update(duration_ms, stage_times, parallel)
    
    def record_early_termination(self) -> None:
        """Record an early termination event."""
        with self._lock:
            self._pipeline_metrics.record_early_termination()
    
    def record_ranking(self, duration_ms: float, document_count: int) -> None:
        """
        Record a ranking operation.
        
        Args:
            duration_ms: Ranking duration in milliseconds
            document_count: Number of documents ranked
        """
        with self._lock:
            self._ranking_metrics.update(duration_ms, document_count)
    
    def update_cache_metrics(self, cache_stats: Dict[str, Any]) -> None:
        """
        Update cache metrics.
        
        Args:
            cache_stats: Cache statistics dictionary
        """
        with self._lock:
            self._cache_metrics.hits = cache_stats.get("hits", 0)
            self._cache_metrics.misses = cache_stats.get("misses", 0)
            self._cache_metrics.evictions = cache_stats.get("evictions", 0)
            self._cache_metrics.size = cache_stats.get("size", 0)
            self._cache_metrics.max_size = cache_stats.get("max_size", 1000)
    
    def get_signal_metrics(self, signal_name: str) -> Optional[SignalMetrics]:
        """
        Get metrics for a specific signal.
        
        Args:
            signal_name: Name of the signal
            
        Returns:
            Signal metrics or None if not found
        """
        with self._lock:
            return self._signal_metrics.get(signal_name)
    
    def get_all_signal_metrics(self) -> Dict[str, SignalMetrics]:
        """
        Get metrics for all signals.
        
        Returns:
            Dictionary of signal name to metrics
        """
        with self._lock:
            return self._signal_metrics.copy()
    
    def get_pipeline_metrics(self) -> PipelineMetrics:
        """
        Get pipeline metrics.
        
        Returns:
            Pipeline metrics
        """
        with self._lock:
            return PipelineMetrics(
                total_executions=self._pipeline_metrics.total_executions,
                total_time_ms=self._pipeline_metrics.total_time_ms,
                avg_time_ms=self._pipeline_metrics.avg_time_ms,
                min_time_ms=self._pipeline_metrics.min_time_ms,
                max_time_ms=self._pipeline_metrics.max_time_ms,
                stage_times_ms=self._pipeline_metrics.stage_times_ms.copy(),
                early_terminations=self._pipeline_metrics.early_terminations,
                parallel_executions=self._pipeline_metrics.parallel_executions,
                sequential_executions=self._pipeline_metrics.sequential_executions,
            )
    
    def get_cache_metrics(self) -> CacheMetrics:
        """
        Get cache metrics.
        
        Returns:
            Cache metrics
        """
        with self._lock:
            return CacheMetrics(
                hits=self._cache_metrics.hits,
                misses=self._cache_metrics.misses,
                evictions=self._cache_metrics.evictions,
                size=self._cache_metrics.size,
                max_size=self._cache_metrics.max_size,
            )
    
    def get_ranking_metrics(self) -> RankingMetrics:
        """
        Get ranking metrics.
        
        Returns:
            Ranking metrics
        """
        with self._lock:
            return RankingMetrics(
                total_rankings=self._ranking_metrics.total_rankings,
                total_documents_ranked=self._ranking_metrics.total_documents_ranked,
                avg_documents_per_ranking=self._ranking_metrics.avg_documents_per_ranking,
                ranking_latency_p50=self._ranking_metrics.ranking_latency_p50,
                ranking_latency_p95=self._ranking_metrics.ranking_latency_p95,
                ranking_latency_p99=self._ranking_metrics.ranking_latency_p99,
                ranking_latencies=self._ranking_metrics.ranking_latencies.copy(),
            )
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all metrics.
        
        Returns:
            Summary dictionary
        """
        with self._lock:
            uptime = datetime.now() - self._start_time
            
            return {
                "uptime_seconds": uptime.total_seconds(),
                "ranking_metrics": self._ranking_metrics.to_dict(),
                "pipeline_metrics": self._pipeline_metrics.to_dict(),
                "cache_metrics": self._cache_metrics.to_dict(),
                "signal_metrics": {
                    name: metrics.to_dict()
                    for name, metrics in self._signal_metrics.items()
                },
                "top_signals_by_calls": self._get_top_signals_by_calls(5),
                "slowest_signals": self._get_slowest_signals(5),
                "highest_error_signals": self._get_highest_error_signals(5),
            }
    
    def _get_top_signals_by_calls(self, n: int) -> List[Dict[str, Any]]:
        """Get top signals by call count."""
        sorted_signals = sorted(
            self._signal_metrics.items(),
            key=lambda x: x[1].total_calls,
            reverse=True,
        )
        return [
            {"signal_name": name, "total_calls": metrics.total_calls}
            for name, metrics in sorted_signals[:n]
        ]
    
    def _get_slowest_signals(self, n: int) -> List[Dict[str, Any]]:
        """Get slowest signals by average time."""
        sorted_signals = sorted(
            self._signal_metrics.items(),
            key=lambda x: x[1].avg_time_ms,
            reverse=True,
        )
        return [
            {"signal_name": name, "avg_time_ms": metrics.avg_time_ms}
            for name, metrics in sorted_signals[:n]
        ]
    
    def _get_highest_error_signals(self, n: int) -> List[Dict[str, Any]]:
        """Get signals with highest error rates."""
        sorted_signals = sorted(
            self._signal_metrics.items(),
            key=lambda x: x[1].error_count,
            reverse=True,
        )
        return [
            {"signal_name": name, "error_count": metrics.error_count}
            for name, metrics in sorted_signals[:n]
        ]
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._signal_metrics.clear()
            self._pipeline_metrics = PipelineMetrics()
            self._cache_metrics = CacheMetrics()
            self._ranking_metrics = RankingMetrics()
            self._start_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert monitor state to dictionary representation."""
        return self.get_summary()
