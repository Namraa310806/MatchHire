"""
Performance Engineering Module

Provides comprehensive performance monitoring, profiling, and benchmarking capabilities.
"""

import asyncio
import cProfile
import io
import logging
import memory_profiler
import pstats
import psutil
import resource
import statistics
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    operation: str
    duration: float
    memory_used: int
    cpu_percent: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""
    name: str
    iterations: int
    total_duration: float
    avg_duration: float
    min_duration: float
    max_duration: float
    p50_duration: float
    p95_duration: float
    p99_duration: float
    throughput: float
    memory_peak: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceManager:
    """
    Central performance management system.
    
    Tracks and analyzes performance metrics across the application.
    """
    
    def __init__(self):
        self._metrics: List[PerformanceMetrics] = []
        self._benchmarks: Dict[str, BenchmarkResult] = {}
        self._enabled = True
        self._max_metrics = 10000
        
    def enable(self):
        """Enable performance tracking."""
        self._enabled = True
        logger.info("Performance tracking enabled")
        
    def disable(self):
        """Disable performance tracking."""
        self._enabled = False
        logger.info("Performance tracking disabled")
        
    def record_metric(self, operation: str, duration: float, 
                     memory_used: int = 0, cpu_percent: float = 0,
                     metadata: Dict[str, Any] = None) -> None:
        """
        Record a performance metric.
        
        Args:
            operation: Operation name
            duration: Duration in seconds
            memory_used: Memory used in bytes
            cpu_percent: CPU usage percentage
            metadata: Additional metadata
        """
        if not self._enabled:
            return
            
        metric = PerformanceMetrics(
            operation=operation,
            duration=duration,
            memory_used=memory_used,
            cpu_percent=cpu_percent,
            metadata=metadata or {}
        )
        
        self._metrics.append(metric)
        
        # Prune old metrics if needed
        if len(self._metrics) > self._max_metrics:
            self._metrics = self._metrics[-self._max_metrics:]
            
    def get_metrics(self, operation: str = None, 
                   since: datetime = None) -> List[PerformanceMetrics]:
        """
        Get metrics with optional filtering.
        
        Args:
            operation: Filter by operation name
            since: Filter by timestamp
            
        Returns:
            List of matching metrics
        """
        metrics = self._metrics
        
        if operation:
            metrics = [m for m in metrics if m.operation == operation]
            
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
            
        return metrics
        
    def get_statistics(self, operation: str) -> Dict[str, Any]:
        """
        Get statistical summary for an operation.
        
        Args:
            operation: Operation name
            
        Returns:
            Dictionary with statistics
        """
        metrics = self.get_metrics(operation)
        
        if not metrics:
            return {}
            
        durations = [m.duration for m in metrics]
        memory = [m.memory_used for m in metrics]
        cpu = [m.cpu_percent for m in metrics]
        
        return {
            "operation": operation,
            "count": len(metrics),
            "duration": {
                "total": sum(durations),
                "avg": statistics.mean(durations),
                "min": min(durations),
                "max": max(durations),
                "p50": statistics.median(durations),
                "p95": np.percentile(durations, 95),
                "p99": np.percentile(durations, 99),
            },
            "memory": {
                "avg": statistics.mean(memory),
                "max": max(memory),
            },
            "cpu": {
                "avg": statistics.mean(cpu),
                "max": max(cpu),
            },
        }
        
    def clear_metrics(self, operation: str = None) -> None:
        """
        Clear metrics.
        
        Args:
            operation: Clear only specific operation, or all if None
        """
        if operation:
            self._metrics = [m for m in self._metrics if m.operation != operation]
        else:
            self._metrics = []
            
    def store_benchmark(self, result: BenchmarkResult) -> None:
        """Store a benchmark result."""
        self._benchmarks[result.name] = result
        
    def get_benchmark(self, name: str) -> Optional[BenchmarkResult]:
        """Get a benchmark result by name."""
        return self._benchmarks.get(name)
        
    def list_benchmarks(self) -> List[str]:
        """List all benchmark names."""
        return list(self._benchmarks.keys())


class PerformanceProfiler:
    """
    Performance profiling utilities.
    
    Provides CPU and memory profiling capabilities.
    """
    
    @staticmethod
    @contextmanager
    def profile_cpu(operation: str = "operation"):
        """
        Context manager for CPU profiling.
        
        Args:
            operation: Operation name for identification
        """
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            yield profiler
        finally:
            profiler.disable()
            
    @staticmethod
    def get_profile_stats(profiler: cProfile.Profile, 
                         sort_by: str = "cumulative") -> str:
        """
        Get formatted profile statistics.
        
        Args:
            profiler: cProfile profiler instance
            sort_by: Sort key (cumulative, time, etc.)
            
        Returns:
            Formatted statistics string
        """
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats(sort_by)
        ps.print_stats()
        return s.getvalue()
        
    @staticmethod
    @contextmanager
    def profile_memory():
        """Context manager for memory profiling."""
        tracemalloc.start()
        
        try:
            yield
        finally:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """
        Get current memory usage statistics.
        
        Returns:
            Dictionary with memory statistics in MB
        """
        process = psutil.Process()
        mem_info = process.memory_info()
        
        return {
            "rss": mem_info.rss / 1024 / 1024,  # Resident Set Size
            "vms": mem_info.vms / 1024 / 1024,  # Virtual Memory Size
            "percent": process.memory_percent(),
        }
        
    @staticmethod
    def get_cpu_usage() -> float:
        """
        Get current CPU usage.
        
        Returns:
            CPU usage percentage
        """
        return psutil.cpu_percent(interval=0.1)
        
    @staticmethod
    def get_system_stats() -> Dict[str, Any]:
        """
        Get system-wide statistics.
        
        Returns:
            Dictionary with system statistics
        """
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "cpu_count": psutil.cpu_count(),
            "memory": {
                "total": psutil.virtual_memory().total / 1024 / 1024 / 1024,
                "available": psutil.virtual_memory().available / 1024 / 1024 / 1024,
                "percent": psutil.virtual_memory().percent,
            },
            "disk": {
                "total": psutil.disk_usage('/').total / 1024 / 1024 / 1024,
                "used": psutil.disk_usage('/').used / 1024 / 1024 / 1024,
                "free": psutil.disk_usage('/').free / 1024 / 1024 / 1024,
                "percent": psutil.disk_usage('/').percent,
            },
        }


class BenchmarkRunner:
    """
    Benchmark execution framework.
    
    Runs benchmarks and collects performance data.
    """
    
    def __init__(self, performance_manager: PerformanceManager = None):
        self.performance_manager = performance_manager or PerformanceManager()
        
    def run_benchmark(self, func: Callable, name: str, 
                     iterations: int = 100, warmup: int = 10,
                     **kwargs) -> BenchmarkResult:
        """
        Run a benchmark on a function.
        
        Args:
            func: Function to benchmark
            name: Benchmark name
            iterations: Number of iterations
            warmup: Number of warmup iterations
            **kwargs: Arguments to pass to function
            
        Returns:
            BenchmarkResult with performance data
        """
        logger.info(f"Running benchmark: {name} (iterations={iterations}, warmup={warmup})")
        
        # Warmup
        for _ in range(warmup):
            try:
                func(**kwargs)
            except Exception:
                pass
                
        # Benchmark
        durations = []
        tracemalloc.start()
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            try:
                func(**kwargs)
            except Exception as e:
                logger.warning(f"Benchmark iteration failed: {e}")
                continue
            duration = time.perf_counter() - start_time
            durations.append(duration)
            
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        if not durations:
            raise RuntimeError("All benchmark iterations failed")
            
        durations_array = np.array(durations)
        total_duration = sum(durations)
        
        result = BenchmarkResult(
            name=name,
            iterations=len(durations),
            total_duration=total_duration,
            avg_duration=statistics.mean(durations),
            min_duration=min(durations),
            max_duration=max(durations),
            p50_duration=statistics.median(durations),
            p95_duration=np.percentile(durations_array, 95),
            p99_duration=np.percentile(durations_array, 99),
            throughput=len(durations) / total_duration if total_duration > 0 else 0,
            memory_peak=peak,
        )
        
        self.performance_manager.store_benchmark(result)
        logger.info(f"Benchmark completed: {name} - avg={result.avg_duration:.4f}s, "
                   f"p95={result.p95_duration:.4f}s, throughput={result.throughput:.2f}/s")
        
        return result
        
    def run_concurrent_benchmark(self, func: Callable, name: str,
                                concurrency: int = 10, 
                                iterations_per_worker: int = 10,
                                **kwargs) -> BenchmarkResult:
        """
        Run a benchmark with concurrent workers.
        
        Args:
            func: Function to benchmark
            name: Benchmark name
            concurrency: Number of concurrent workers
            iterations_per_worker: Iterations per worker
            **kwargs: Arguments to pass to function
            
        Returns:
            BenchmarkResult with performance data
        """
        logger.info(f"Running concurrent benchmark: {name} (concurrency={concurrency})")
        
        durations = []
        tracemalloc.start()
        start_time = time.perf_counter()
        
        def worker():
            worker_durations = []
            for _ in range(iterations_per_worker):
                iter_start = time.perf_counter()
                try:
                    func(**kwargs)
                except Exception as e:
                    logger.warning(f"Concurrent benchmark iteration failed: {e}")
                    continue
                worker_durations.append(time.perf_counter() - iter_start)
            return worker_durations
            
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(worker) for _ in range(concurrency)]
            for future in as_completed(futures):
                durations.extend(future.result())
                
        total_duration = time.perf_counter() - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        if not durations:
            raise RuntimeError("All concurrent benchmark iterations failed")
            
        durations_array = np.array(durations)
        
        result = BenchmarkResult(
            name=f"{name}_concurrent",
            iterations=len(durations),
            total_duration=total_duration,
            avg_duration=statistics.mean(durations),
            min_duration=min(durations),
            max_duration=max(durations),
            p50_duration=statistics.median(durations),
            p95_duration=np.percentile(durations_array, 95),
            p99_duration=np.percentile(durations_array, 99),
            throughput=len(durations) / total_duration if total_duration > 0 else 0,
            memory_peak=peak,
            metadata={"concurrency": concurrency},
        )
        
        self.performance_manager.store_benchmark(result)
        logger.info(f"Concurrent benchmark completed: {name} - throughput={result.throughput:.2f}/s")
        
        return result


class LoadTestingFramework:
    """
    Load testing framework.
    
    Simulates realistic load patterns for testing.
    """
    
    def __init__(self, performance_manager: PerformanceManager = None):
        self.performance_manager = performance_manager or PerformanceManager()
        
    def run_load_test(self, func: Callable, name: str,
                     duration: int = 60, target_rps: float = 10,
                     ramp_up: int = 10, **kwargs) -> Dict[str, Any]:
        """
        Run a load test.
        
        Args:
            func: Function to test
            name: Test name
            duration: Test duration in seconds
            target_rps: Target requests per second
            ramp_up: Ramp-up time in seconds
            **kwargs: Arguments to pass to function
            
        Returns:
            Dictionary with load test results
        """
        logger.info(f"Running load test: {name} (duration={duration}s, target_rps={target_rps})")
        
        results = {
            "name": name,
            "duration": duration,
            "target_rps": target_rps,
            "requests": [],
            "errors": [],
            "start_time": datetime.utcnow(),
        }
        
        interval = 1.0 / target_rps
        end_time = time.time() + duration
        ramp_up_end = time.time() + ramp_up
        
        request_count = 0
        error_count = 0
        
        while time.time() < end_time:
            # Calculate current RPS based on ramp-up
            if time.time() < ramp_up_end:
                current_rps = target_rps * ((time.time() - (end_time - duration)) / ramp_up)
                current_interval = 1.0 / current_rps if current_rps > 0 else interval
            else:
                current_interval = interval
                
            start = time.perf_counter()
            try:
                func(**kwargs)
                duration_sec = time.perf_counter() - start
                results["requests"].append({
                    "timestamp": datetime.utcnow(),
                    "duration": duration_sec,
                    "success": True,
                })
                request_count += 1
            except Exception as e:
                duration_sec = time.perf_counter() - start
                results["requests"].append({
                    "timestamp": datetime.utcnow(),
                    "duration": duration_sec,
                    "success": False,
                    "error": str(e),
                })
                results["errors"].append(str(e))
                error_count += 1
                
            sleep_time = current_interval - duration_sec
            if sleep_time > 0:
                time.sleep(sleep_time)
                
        results["end_time"] = datetime.utcnow()
        results["total_requests"] = request_count
        results["total_errors"] = error_count
        results["error_rate"] = error_count / request_count if request_count > 0 else 0
        results["actual_rps"] = request_count / duration
        
        if results["requests"]:
            durations = [r["duration"] for r in results["requests"]]
            results["latency"] = {
                "avg": statistics.mean(durations),
                "min": min(durations),
                "max": max(durations),
                "p50": statistics.median(durations),
                "p95": np.percentile(durations, 95),
                "p99": np.percentile(durations, 99),
            }
            
        logger.info(f"Load test completed: {name} - rps={results['actual_rps']:.2f}, "
                   f"error_rate={results['error_rate']:.2%}")
        
        return results


class StressTestingFramework:
    """
    Stress testing framework.
    
    Tests system behavior under extreme conditions.
    """
    
    def __init__(self, performance_manager: PerformanceManager = None):
        self.performance_manager = performance_manager or PerformanceManager()
        
    def run_stress_test(self, func: Callable, name: str,
                       max_concurrency: int = 100,
                       step: int = 10, duration_per_step: int = 10,
                       **kwargs) -> Dict[str, Any]:
        """
        Run a stress test with increasing concurrency.
        
        Args:
            func: Function to test
            name: Test name
            max_concurrency: Maximum concurrency level
            step: Concurrency increment per step
            duration_per_step: Duration per step in seconds
            **kwargs: Arguments to pass to function
            
        Returns:
            Dictionary with stress test results
        """
        logger.info(f"Running stress test: {name} (max_concurrency={max_concurrency})")
        
        results = {
            "name": name,
            "steps": [],
            "start_time": datetime.utcnow(),
        }
        
        for concurrency in range(step, max_concurrency + 1, step):
            logger.info(f"Stress test step: concurrency={concurrency}")
            
            step_results = {
                "concurrency": concurrency,
                "requests": [],
                "errors": [],
                "start_time": datetime.utcnow(),
            }
            
            end_time = time.time() + duration_per_step
            request_count = 0
            error_count = 0
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = []
                
                while time.time() < end_time:
                    future = executor.submit(func, **kwargs)
                    futures.append((future, time.perf_counter()))
                    
                    # Limit queue size
                    if len(futures) > concurrency * 2:
                        for f, start in futures[:concurrency]:
                            try:
                                f.result(timeout=1)
                                duration = time.perf_counter() - start
                                step_results["requests"].append({
                                    "duration": duration,
                                    "success": True,
                                })
                                request_count += 1
                            except Exception as e:
                                duration = time.perf_counter() - start
                                step_results["requests"].append({
                                    "duration": duration,
                                    "success": False,
                                    "error": str(e),
                                })
                                step_results["errors"].append(str(e))
                                error_count += 1
                        futures = futures[concurrency:]
                        
                # Wait for remaining futures
                for f, start in futures:
                    try:
                        f.result(timeout=5)
                        duration = time.perf_counter() - start
                        step_results["requests"].append({
                            "duration": duration,
                            "success": True,
                        })
                        request_count += 1
                    except Exception as e:
                        duration = time.perf_counter() - start
                        step_results["requests"].append({
                            "duration": duration,
                            "success": False,
                            "error": str(e),
                        })
                        step_results["errors"].append(str(e))
                        error_count += 1
                        
            step_results["end_time"] = datetime.utcnow()
            step_results["total_requests"] = request_count
            step_results["total_errors"] = error_count
            step_results["error_rate"] = error_count / request_count if request_count > 0 else 0
            
            if step_results["requests"]:
                durations = [r["duration"] for r in step_results["requests"]]
                step_results["latency"] = {
                    "avg": statistics.mean(durations),
                    "p95": np.percentile(durations, 95),
                    "p99": np.percentile(durations, 99),
                }
                
            results["steps"].append(step_results)
            
            # Stop if error rate is too high
            if step_results["error_rate"] > 0.5:
                logger.warning(f"Stress test stopped at concurrency={concurrency} due to high error rate")
                break
                
        results["end_time"] = datetime.utcnow()
        logger.info(f"Stress test completed: {name}")
        
        return results


class CapacityPlanner:
    """
    Capacity planning utilities.
    
    Helps estimate resource requirements based on performance data.
    """
    
    @staticmethod
    def estimate_capacity(benchmark: BenchmarkResult, 
                         target_rps: float,
                         headroom: float = 0.2) -> Dict[str, Any]:
        """
        Estimate capacity requirements.
        
        Args:
            benchmark: Benchmark result
            target_rps: Target requests per second
            headroom: Additional headroom percentage
            
        Returns:
            Dictionary with capacity estimates
        """
        # Calculate required resources
        required_rps = target_rps * (1 + headroom)
        current_throughput = benchmark.throughput
        
        if current_throughput == 0:
            raise ValueError("Benchmark throughput is zero")
            
        instances = required_rps / current_throughput
        
        # Memory per instance
        memory_per_instance = benchmark.memory_peak / 1024 / 1024  # Convert to MB
        total_memory = memory_per_instance * instances
        
        # CPU estimation (rough approximation)
        cpu_per_instance = 0.5  # Assume 50% CPU per instance
        total_cpu = cpu_per_instance * instances
        
        return {
            "target_rps": target_rps,
            "required_rps": required_rps,
            "current_throughput": current_throughput,
            "instances_needed": max(1, round(instances)),
            "memory_per_instance_mb": round(memory_per_instance, 2),
            "total_memory_mb": round(total_memory, 2),
            "cpu_per_instance": cpu_per_instance,
            "total_cpu": round(total_cpu, 2),
            "headroom": headroom,
        }
        
    @staticmethod
    def calculate_scaling_factor(current_load: float, 
                                max_capacity: float) -> float:
        """
        Calculate scaling factor based on load.
        
        Args:
            current_load: Current load (RPS)
            max_capacity: Maximum capacity (RPS)
            
        Returns:
            Scaling factor (1.0 = no scaling needed)
        """
        if max_capacity == 0:
            return 2.0  # Default to doubling
            
        utilization = current_load / max_capacity
        
        if utilization < 0.5:
            return 0.5  # Scale down
        elif utilization < 0.7:
            return 1.0  # No change
        elif utilization < 0.9:
            return 1.5  # Scale up moderately
        else:
            return 2.0  # Scale up aggressively


class QueryBenchmarkRunner:
    """
    Benchmark runner for search queries.
    
    Specialized benchmarks for query performance.
    """
    
    def __init__(self, performance_manager: PerformanceManager = None):
        self.performance_manager = performance_manager or PerformanceManager()
        self.benchmark_runner = BenchmarkRunner(performance_manager)
        
    def benchmark_search_query(self, query_func: Callable, query: str,
                               iterations: int = 100) -> BenchmarkResult:
        """
        Benchmark a search query.
        
        Args:
            query_func: Function that executes the query
            query: Query string
            iterations: Number of iterations
            
        Returns:
            BenchmarkResult
        """
        return self.benchmark_runner.run_benchmark(
            func=query_func,
            name=f"search_query:{query[:20]}",
            iterations=iterations,
            query=query
        )
        
    def benchmark_filter_query(self, query_func: Callable, filters: Dict,
                                iterations: int = 100) -> BenchmarkResult:
        """
        Benchmark a filtered query.
        
        Args:
            query_func: Function that executes the query
            filters: Filter dictionary
            iterations: Number of iterations
            
        Returns:
            BenchmarkResult
        """
        return self.benchmark_runner.run_benchmark(
            func=query_func,
            name=f"filter_query:{len(filters)}_filters",
            iterations=iterations,
            filters=filters
        )


class RankingBenchmarkRunner:
    """
    Benchmark runner for ranking operations.
    
    Specialized benchmarks for ranking performance.
    """
    
    def __init__(self, performance_manager: PerformanceManager = None):
        self.performance_manager = performance_manager or PerformanceManager()
        self.benchmark_runner = BenchmarkRunner(performance_manager)
        
    def benchmark_ranking(self, ranking_func: Callable, candidates: List,
                         iterations: int = 100) -> BenchmarkResult:
        """
        Benchmark a ranking operation.
        
        Args:
            ranking_func: Function that performs ranking
            candidates: List of candidates to rank
            iterations: Number of iterations
            
        Returns:
            BenchmarkResult
        """
        return self.benchmark_runner.run_benchmark(
            func=ranking_func,
            name=f"ranking:{len(candidates)}_candidates",
            iterations=iterations,
            candidates=candidates
        )
        
    def benchmark_signal_calculation(self, signal_func: Callable,
                                    iterations: int = 100) -> BenchmarkResult:
        """
        Benchmark a signal calculation.
        
        Args:
            signal_func: Function that calculates a signal
            iterations: Number of iterations
            
        Returns:
            BenchmarkResult
        """
        return self.benchmark_runner.run_benchmark(
            func=signal_func,
            name="signal_calculation",
            iterations=iterations
        )


class RecommendationBenchmarkRunner:
    """
    Benchmark runner for recommendation operations.
    
    Specialized benchmarks for recommendation performance.
    """
    
    def __init__(self, performance_manager: PerformanceManager = None):
        self.performance_manager = performance_manager or PerformanceManager()
        self.benchmark_runner = BenchmarkRunner(performance_manager)
        
    def benchmark_recommendation_generation(self, rec_func: Callable, user_id: int,
                                           iterations: int = 50) -> BenchmarkResult:
        """
        Benchmark recommendation generation.
        
        Args:
            rec_func: Function that generates recommendations
            user_id: User ID
            iterations: Number of iterations
            
        Returns:
            BenchmarkResult
        """
        return self.benchmark_runner.run_benchmark(
            func=rec_func,
            name=f"recommendation:user_{user_id}",
            iterations=iterations,
            user_id=user_id
        )
        
    def benchmark_batch_recommendations(self, rec_func: Callable, user_ids: List[int],
                                        iterations: int = 20) -> BenchmarkResult:
        """
        Benchmark batch recommendation generation.
        
        Args:
            rec_func: Function that generates batch recommendations
            user_ids: List of user IDs
            iterations: Number of iterations
            
        Returns:
            BenchmarkResult
        """
        return self.benchmark_runner.run_benchmark(
            func=rec_func,
            name=f"batch_recommendation:{len(user_ids)}_users",
            iterations=iterations,
            user_ids=user_ids
        )


class BulkIndexingBenchmarkRunner:
    """
    Benchmark runner for bulk indexing operations.
    
    Specialized benchmarks for indexing performance.
    """
    
    def __init__(self, performance_manager: PerformanceManager = None):
        self.performance_manager = performance_manager or PerformanceManager()
        self.benchmark_runner = BenchmarkRunner(performance_manager)
        
    def benchmark_bulk_index(self, index_func: Callable, documents: List,
                           iterations: int = 10) -> BenchmarkResult:
        """
        Benchmark bulk indexing.
        
        Args:
            index_func: Function that performs bulk indexing
            documents: List of documents to index
            iterations: Number of iterations
            
        Returns:
            BenchmarkResult
        """
        return self.benchmark_runner.run_benchmark(
            func=index_func,
            name=f"bulk_index:{len(documents)}_docs",
            iterations=iterations,
            documents=documents
        )
        
    def benchmark_single_index(self, index_func: Callable, document: Dict,
                              iterations: int = 100) -> BenchmarkResult:
        """
        Benchmark single document indexing.
        
        Args:
            index_func: Function that indexes a single document
            document: Document to index
            iterations: Number of iterations
            
        Returns:
            BenchmarkResult
        """
        return self.benchmark_runner.run_benchmark(
            func=index_func,
            name="single_index",
            iterations=iterations,
            document=document
        )


class MemoryBenchmarkRunner:
    """
    Benchmark runner for memory operations.
    
    Specialized benchmarks for memory performance.
    """
    
    def __init__(self, performance_manager: PerformanceManager = None):
        self.performance_manager = performance_manager or PerformanceManager()
        
    def benchmark_memory_usage(self, func: Callable, **kwargs) -> Dict[str, Any]:
        """
        Benchmark memory usage of a function.
        
        Args:
            func: Function to benchmark
            **kwargs: Arguments to pass to function
            
        Returns:
            Dictionary with memory statistics
        """
        tracemalloc.start()
        
        try:
            func(**kwargs)
            current, peak = tracemalloc.get_traced_memory()
            
            return {
                "current_mb": current / 1024 / 1024,
                "peak_mb": peak / 1024 / 1024,
                "peak_bytes": peak,
            }
        finally:
            tracemalloc.stop()
            
    def benchmark_memory_leaks(self, func: Callable, iterations: int = 100,
                              **kwargs) -> Dict[str, Any]:
        """
        Benchmark for memory leaks.
        
        Args:
            func: Function to benchmark
            iterations: Number of iterations
            **kwargs: Arguments to pass to function
            
        Returns:
            Dictionary with memory leak statistics
        """
        memory_samples = []
        
        for i in range(iterations):
            tracemalloc.start()
            try:
                func(**kwargs)
                _, peak = tracemalloc.get_traced_memory()
                memory_samples.append(peak)
            finally:
                tracemalloc.stop()
                
        # Calculate memory growth
        if len(memory_samples) > 1:
            growth_rate = (memory_samples[-1] - memory_samples[0]) / len(memory_samples)
        else:
            growth_rate = 0
            
        return {
            "samples": memory_samples,
            "initial_bytes": memory_samples[0] if memory_samples else 0,
            "final_bytes": memory_samples[-1] if memory_samples else 0,
            "growth_rate_bytes_per_iteration": growth_rate,
            "potential_leak": growth_rate > 1000,  # More than 1KB growth per iteration
        }


class CPUBenchmarkRunner:
    """
    Benchmark runner for CPU operations.
    
    Specialized benchmarks for CPU performance.
    """
    
    def __init__(self, performance_manager: PerformanceManager = None):
        self.performance_manager = performance_manager or PerformanceManager()
        
    def benchmark_cpu_usage(self, func: Callable, duration: int = 10,
                          **kwargs) -> Dict[str, Any]:
        """
        Benchmark CPU usage of a function.
        
        Args:
            func: Function to benchmark
            duration: Duration to monitor in seconds
            **kwargs: Arguments to pass to function
            
        Returns:
            Dictionary with CPU statistics
        """
        cpu_samples = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            func(**kwargs)
            cpu_samples.append(psutil.cpu_percent(interval=0.1))
            
        return {
            "avg_cpu_percent": statistics.mean(cpu_samples) if cpu_samples else 0,
            "max_cpu_percent": max(cpu_samples) if cpu_samples else 0,
            "min_cpu_percent": min(cpu_samples) if cpu_samples else 0,
            "samples": cpu_samples,
        }


# Global performance manager instance
performance_manager = PerformanceManager()


def track_performance(operation: str):
    """
    Decorator to track performance of a function.
    
    Args:
        operation: Operation name for tracking
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            start_memory = memory_profiler.memory_usage()[0] if memory_profiler else None
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start_time
                end_memory = memory_profiler.memory_usage()[0] if memory_profiler else None
                memory_used = int((end_memory - start_memory) * 1024 * 1024) if start_memory else 0
                cpu_percent = PerformanceProfiler.get_cpu_usage()
                
                performance_manager.record_metric(
                    operation=operation,
                    duration=duration,
                    memory_used=memory_used,
                    cpu_percent=cpu_percent,
                )
                
        return wrapper
    return decorator


# Global benchmark runners
query_benchmark_runner = QueryBenchmarkRunner()
ranking_benchmark_runner = RankingBenchmarkRunner()
recommendation_benchmark_runner = RecommendationBenchmarkRunner()
bulk_indexing_benchmark_runner = BulkIndexingBenchmarkRunner()
memory_benchmark_runner = MemoryBenchmarkRunner()
cpu_benchmark_runner = CPUBenchmarkRunner()
