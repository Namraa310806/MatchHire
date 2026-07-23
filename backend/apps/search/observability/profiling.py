"""
Performance Profiling Utilities.

This module provides profiling utilities for analyzing performance
bottlenecks in search, ranking, and recommendation systems.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import time
import threading
import cProfile
import pstats
import io
from contextlib import contextmanager
from .core import ObservabilityConfig, ObservabilityComponent


class ProfileType(Enum):
    """Types of profiling."""
    CPU = "cpu"
    MEMORY = "memory"
    QUERY = "query"
    RANKING = "ranking"
    RECOMMENDATION = "recommendation"


@dataclass
class ProfileResult:
    """Result of a profiling operation."""
    
    profile_type: ProfileType
    component: ObservabilityComponent
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    function_calls: int = 0
    total_time: float = 0.0
    top_functions: List[Dict[str, Any]] = field(default_factory=list)
    memory_usage: Optional[Dict[str, float]] = None
    cpu_usage: Optional[Dict[str, float]] = None
    execution_breakdown: Dict[str, float] = field(default_factory=dict)
    bottlenecks: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "profile_type": self.profile_type.value,
            "component": self.component.value,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
            "function_calls": self.function_calls,
            "total_time": self.total_time,
            "top_functions": self.top_functions,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "execution_breakdown": self.execution_breakdown,
            "bottlenecks": self.bottlenecks,
        }


class Profiler:
    """
    Performance profiler for analyzing execution.
    
    This profiler can profile CPU usage, memory usage, and execution
    breakdown for search, ranking, and recommendation operations.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """
        Initialize the profiler.
        
        Args:
            config: Observability configuration
        """
        self._config = config
        self._profiles: List[ProfileResult] = []
        self._lock = threading.Lock()
    
    @contextmanager
    def profile_cpu(
        self,
        component: ObservabilityComponent,
        operation_name: str,
    ):
        """
        Context manager for CPU profiling.
        
        Args:
            component: Component being profiled
            operation_name: Name of operation
            
        Yields:
            ProfileResult
        """
        if not self._config.profiling_enabled:
            yield None
            return
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        start_time = time.time()
        
        try:
            yield
        finally:
            profiler.disable()
            duration_ms = (time.time() - start_time) * 1000
            
            # Process profiling results
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
            ps.print_stats(20)  # Top 20 functions
            
            # Parse top functions
            top_functions = self._parse_profile_stats(s.getvalue())
            
            # Create profile result
            result = ProfileResult(
                profile_type=ProfileType.CPU,
                component=component,
                duration_ms=duration_ms,
                function_calls=ps.total_calls,
                total_time=ps.total_tt,
                top_functions=top_functions,
                execution_breakdown=self._get_execution_breakdown(top_functions),
                bottlenecks=self._identify_bottlenecks(top_functions),
            )
            
            with self._lock:
                self._profiles.append(result)
    
    def _parse_profile_stats(self, stats_output: str) -> List[Dict[str, Any]]:
        """
        Parse profile stats output.
        
        Args:
            stats_output: Profile stats string
            
        Returns:
            List of function stats
        """
        functions = []
        lines = stats_output.split('\n')
        
        for line in lines:
            if line.strip() and not line.startswith(('ncalls', ' ', '\t')):
                # Parse function line
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        functions.append({
                            "calls": parts[0],
                            "total_time": float(parts[1]),
                            "per_call_time": float(parts[2]) if len(parts) > 2 else 0.0,
                            "cumulative_time": float(parts[3]) if len(parts) > 3 else 0.0,
                            "filename": parts[4] if len(parts) > 4 else "",
                            "line": parts[5] if len(parts) > 5 else "",
                            "function": ' '.join(parts[6:]) if len(parts) > 6 else "",
                        })
                    except (ValueError, IndexError):
                        continue
        
        return functions[:10]  # Return top 10
    
    def _get_execution_breakdown(self, functions: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Get execution breakdown by function.
        
        Args:
            functions: Function stats
            
        Returns:
            Dictionary of function to time
        """
        breakdown = {}
        total_time = sum(f.get("cumulative_time", 0) for f in functions)
        
        for func in functions:
            func_name = func.get("function", "unknown")
            func_time = func.get("cumulative_time", 0)
            if total_time > 0:
                breakdown[func_name] = (func_time / total_time) * 100
        
        return breakdown
    
    def _identify_bottlenecks(self, functions: List[Dict[str, Any]]) -> List[str]:
        """
        Identify performance bottlenecks.
        
        Args:
            functions: Function stats
            
        Returns:
            List of bottleneck descriptions
        """
        bottlenecks = []
        
        if not functions:
            return bottlenecks
        
        total_time = sum(f.get("cumulative_time", 0) for f in functions)
        
        for func in functions:
            func_time = func.get("cumulative_time", 0)
            if total_time > 0 and (func_time / total_time) > 0.2:  # > 20% of total time
                bottlenecks.append(
                    f"{func.get('function', 'unknown')} takes {func_time / total_time * 100:.1f}% of total time"
                )
        
        return bottlenecks
    
    @contextmanager
    def profile_memory(
        self,
        component: ObservabilityComponent,
        operation_name: str,
    ):
        """
        Context manager for memory profiling.
        
        Args:
            component: Component being profiled
            operation_name: Name of operation
            
        Yields:
            ProfileResult
        """
        if not self._config.profiling_enabled:
            yield None
            return
        
        import tracemalloc
        import gc
        
        tracemalloc.start()
        gc.collect()
        
        start_time = time.time()
        snapshot1 = tracemalloc.take_snapshot()
        
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            snapshot2 = tracemalloc.take_snapshot()
            
            # Calculate memory difference
            top_stats = snapshot2.compare_to(snapshot1, 'lineno')
            
            # Parse memory stats
            memory_usage = {}
            for stat in top_stats[:10]:
                memory_usage[f"{stat.traceback[0].filename}:{stat.traceback[0].lineno}"] = stat.size_diff / 1024  # KB
            
            total_memory = sum(stat.size_diff for stat in top_stats) / 1024  # KB
            
            result = ProfileResult(
                profile_type=ProfileType.MEMORY,
                component=component,
                duration_ms=duration_ms,
                memory_usage={
                    "total_kb": total_memory,
                    "details": memory_usage,
                },
            )
            
            with self._lock:
                self._profiles.append(result)
            
            tracemalloc.stop()
    
    def profile_query(
        self,
        query: str,
        component: ObservabilityComponent,
    ) -> ProfileResult:
        """
        Profile a search query.
        
        Args:
            query: Query string
            component: Component
            
        Returns:
            ProfileResult
        """
        start_time = time.time()
        
        with self.profile_cpu(component, "query"):
            # This would execute the actual query
            # For now, simulate execution
            time.sleep(0.01)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Get the last profile result
        with self._lock:
            if self._profiles:
                result = self._profiles[-1]
                result.profile_type = ProfileType.QUERY
                return result
        
        return ProfileResult(
            profile_type=ProfileType.QUERY,
            component=component,
            duration_ms=duration_ms,
        )
    
    def profile_ranking(
        self,
        results: List[Dict[str, Any]],
        component: ObservabilityComponent,
    ) -> ProfileResult:
        """
        Profile a ranking operation.
        
        Args:
            results: Results to rank
            component: Component
            
        Returns:
            ProfileResult
        """
        start_time = time.time()
        
        with self.profile_cpu(component, "ranking"):
            # This would execute the actual ranking
            # For now, simulate execution
            time.sleep(0.01)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Get the last profile result
        with self._lock:
            if self._profiles:
                result = self._profiles[-1]
                result.profile_type = ProfileType.RANKING
                return result
        
        return ProfileResult(
            profile_type=ProfileType.RANKING,
            component=component,
            duration_ms=duration_ms,
        )
    
    def profile_recommendation(
        self,
        request: Dict[str, Any],
        component: ObservabilityComponent,
    ) -> ProfileResult:
        """
        Profile a recommendation operation.
        
        Args:
            request: Recommendation request
            component: Component
            
        Returns:
            ProfileResult
        """
        start_time = time.time()
        
        with self.profile_cpu(component, "recommendation"):
            # This would execute the actual recommendation
            # For now, simulate execution
            time.sleep(0.01)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Get the last profile result
        with self._lock:
            if self._profiles:
                result = self._profiles[-1]
                result.profile_type = ProfileType.RECOMMENDATION
                return result
        
        return ProfileResult(
            profile_type=ProfileType.RECOMMENDATION,
            component=component,
            duration_ms=duration_ms,
        )
    
    def get_profiles(
        self,
        profile_type: Optional[ProfileType] = None,
        component: Optional[ObservabilityComponent] = None,
        limit: int = 100,
    ) -> List[ProfileResult]:
        """
        Get profiling results with optional filters.
        
        Args:
            profile_type: Optional profile type filter
            component: Optional component filter
            limit: Maximum number of profiles to return
            
        Returns:
            List of profile results
        """
        with self._lock:
            profiles = self._profiles
            
            if profile_type:
                profiles = [p for p in profiles if p.profile_type == profile_type]
            
            if component:
                profiles = [p for p in profiles if p.component == component]
            
            return profiles[-limit:]
    
    def get_bottlenecks(self, limit: int = 10) -> List[str]:
        """
        Get identified bottlenecks.
        
        Args:
            limit: Maximum number of bottlenecks to return
            
        Returns:
            List of bottleneck descriptions
        """
        bottlenecks = []
        
        with self._lock:
            for profile in self._profiles:
                bottlenecks.extend(profile.bottlenecks)
        
        # Count and sort bottlenecks
        from collections import Counter
        bottleneck_counts = Counter(bottlenecks)
        
        return [b for b, _ in bottleneck_counts.most_common(limit)]
    
    def clear_old_profiles(self, retention_hours: int = 24) -> None:
        """
        Clear old profiling results.
        
        Args:
            retention_hours: Retention period in hours
        """
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(hours=retention_hours)
        
        with self._lock:
            self._profiles = [
                profile for profile in self._profiles
                if profile.timestamp >= cutoff
            ]


class QueryProfiler:
    """
    Specialized profiler for search queries.
    
    Provides detailed profiling of query execution including
    query complexity, filter analysis, and execution breakdown.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """
        Initialize the query profiler.
        
        Args:
            config: Observability configuration
        """
        self._config = config
        self._profiles: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def profile_query_execution(
        self,
        query: str,
        filters: Dict[str, Any],
        component: ObservabilityComponent,
    ) -> Dict[str, Any]:
        """
        Profile query execution.
        
        Args:
            query: Query string
            filters: Query filters
            component: Component
            
        Returns:
            Profile data
        """
        start_time = time.time()
        
        # Analyze query complexity
        complexity = self._analyze_query_complexity(query, filters)
        
        # Simulate execution
        time.sleep(0.01)
        
        duration_ms = (time.time() - start_time) * 1000
        
        profile = {
            "query": query,
            "filters": filters,
            "complexity": complexity,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat(),
            "component": component.value,
        }
        
        with self._lock:
            self._profiles.append(profile)
        
        return profile
    
    def _analyze_query_complexity(self, query: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze query complexity.
        
        Args:
            query: Query string
            filters: Query filters
            
        Returns:
            Complexity metrics
        """
        return {
            "query_length": len(query),
            "filter_count": len(filters),
            "has_wildcard": "*" in query or "?" in query,
            "has_boolean": "AND" in query.upper() or "OR" in query.upper(),
            "has_range": any(":" in str(v) for v in filters.values()),
            "estimated_complexity": self._estimate_complexity(query, filters),
        }
    
    def _estimate_complexity(self, query: str, filters: Dict[str, Any]) -> int:
        """
        Estimate query complexity score.
        
        Args:
            query: Query string
            filters: Query filters
            
        Returns:
            Complexity score (1-10)
        """
        score = 1
        
        # Query length contributes
        score += min(len(query) // 50, 3)
        
        # Filter count contributes
        score += min(len(filters), 3)
        
        # Wildcards increase complexity
        if "*" in query or "?" in query:
            score += 2
        
        # Boolean operators increase complexity
        if "AND" in query.upper() or "OR" in query.upper():
            score += 1
        
        return min(score, 10)
    
    def get_slow_queries(self, threshold_ms: float = 1000.0, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get slow queries.
        
        Args:
            threshold_ms: Latency threshold
            limit: Maximum number to return
            
        Returns:
            List of slow query profiles
        """
        with self._lock:
            slow = [
                profile for profile in self._profiles
                if profile.get("duration_ms", 0) > threshold_ms
            ]
            return slow[-limit:]
    
    def get_complex_queries(self, threshold: int = 5, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get complex queries.
        
        Args:
            threshold: Complexity threshold
            limit: Maximum number to return
            
        Returns:
            List of complex query profiles
        """
        with self._lock:
            complex_queries = [
                profile for profile in self._profiles
                if profile.get("complexity", {}).get("estimated_complexity", 0) > threshold
            ]
            return complex_queries[-limit:]
