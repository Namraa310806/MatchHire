"""
Cache Performance Benchmarks

Benchmarks for cache operations including get/set performance,
hit rates, and tiered cache performance.
"""

import time
from typing import Dict, List, Any
from dataclasses import dataclass

from django.core.cache import cache
from matchhire_backend.core.performance import BenchmarkRunner, performance_manager


@dataclass
class CacheBenchmarkConfig:
    """Configuration for cache benchmarks."""
    operation_count: int = 1000
    key_size: int = 50
    value_size: int = 1000
    warmup_iterations: int = 10


class CacheBenchmarks:
    """
    Cache performance benchmarks.
    """
    
    def __init__(self, config: CacheBenchmarkConfig = None):
        self.config = config or CacheBenchmarkConfig()
        self.benchmark_runner = BenchmarkRunner(performance_manager)
        
    def benchmark_cache_set(self) -> Dict[str, Any]:
        """
        Benchmark cache set operations.
        
        Returns:
            Benchmark results
        """
        test_value = "x" * self.config.value_size
        
        def cache_set():
            for i in range(100):
                cache.set(f"bench_key_{i}", test_value, 300)
                
        result = self.benchmark_runner.run_benchmark(
            func=cache_set,
            name="cache_set",
            iterations=100,
            warmup=self.config.warmup_iterations,
        )
        
        return {
            "name": "Cache Set",
            "result": result,
            "config": {
                "operations_per_iteration": 100,
                "value_size": self.config.value_size,
            },
        }
        
    def benchmark_cache_get(self) -> Dict[str, Any]:
        """
        Benchmark cache get operations.
        
        Returns:
            Benchmark results
        """
        # Pre-populate cache
        for i in range(100):
            cache.set(f"bench_key_{i}", f"value_{i}", 300)
            
        def cache_get():
            for i in range(100):
                cache.get(f"bench_key_{i}")
                
        result = self.benchmark_runner.run_benchmark(
            func=cache_get,
            name="cache_get",
            iterations=100,
            warmup=self.config.warmup_iterations,
        )
        
        return {
            "name": "Cache Get",
            "result": result,
            "config": {
                "operations_per_iteration": 100,
            },
        }
        
    def benchmark_cache_hit_rate(self) -> Dict[str, Any]:
        """
        Benchmark cache hit rate with mixed hits/misses.
        
        Returns:
            Benchmark results
        """
        # Pre-populate half the keys
        for i in range(50):
            cache.set(f"bench_key_{i}", f"value_{i}", 300)
            
        def cache_mixed():
            for i in range(100):
                cache.get(f"bench_key_{i}")
                
        result = self.benchmark_runner.run_benchmark(
            func=cache_mixed,
            name="cache_hit_rate",
            iterations=100,
            warmup=self.config.warmup_iterations,
        )
        
        return {
            "name": "Cache Hit Rate",
            "result": result,
            "config": {
                "operations_per_iteration": 100,
                "hit_rate": 0.5,
            },
        }
        
    def benchmark_cache_delete(self) -> Dict[str, Any]:
        """
        Benchmark cache delete operations.
        
        Returns:
            Benchmark results
        """
        # Pre-populate cache
        for i in range(100):
            cache.set(f"bench_key_{i}", f"value_{i}", 300)
            
        def cache_delete():
            for i in range(100):
                cache.delete(f"bench_key_{i}")
                
        result = self.benchmark_runner.run_benchmark(
            func=cache_delete,
            name="cache_delete",
            iterations=100,
            warmup=self.config.warmup_iterations,
        )
        
        return {
            "name": "Cache Delete",
            "result": result,
            "config": {
                "operations_per_iteration": 100,
            },
        }
        
    def benchmark_tiered_cache(self) -> Dict[str, Any]:
        """
        Benchmark tiered cache performance.
        
        Returns:
            Benchmark results
        """
        from matchhire_backend.core.caching import tiered_cache
        
        test_value = "x" * self.config.value_size
        
        def tiered_cache_ops():
            for i in range(50):
                tiered_cache.set(f"tiered_key_{i}", test_value, 300)
                tiered_cache.get(f"tiered_key_{i}")
                
        result = self.benchmark_runner.run_benchmark(
            func=tiered_cache_ops,
            name="tiered_cache",
            iterations=50,
            warmup=5,
        )
        
        return {
            "name": "Tiered Cache",
            "result": result,
            "config": {
                "operations_per_iteration": 50,
                "value_size": self.config.value_size,
            },
        }
        
    def benchmark_concurrent_cache(self) -> Dict[str, Any]:
        """
        Benchmark concurrent cache operations.
        
        Returns:
            Benchmark results
        """
        def cache_ops():
            for i in range(20):
                cache.set(f"concurrent_key_{i}", f"value_{i}", 300)
                cache.get(f"concurrent_key_{i}")
                
        result = self.benchmark_runner.run_concurrent_benchmark(
            func=cache_ops,
            name="cache_concurrent",
            concurrency=10,
            iterations_per_worker=10,
        )
        
        return {
            "name": "Concurrent Cache",
            "result": result,
            "config": {
                "concurrency": 10,
                "iterations_per_worker": 10,
            },
        }
        
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """
        Run all cache benchmarks.
        
        Returns:
            All benchmark results
        """
        logger.info("Running cache benchmarks...")
        
        results = {
            "timestamp": time.time(),
            "benchmarks": [],
        }
        
        # Run benchmarks
        results["benchmarks"].append(self.benchmark_cache_set())
        results["benchmarks"].append(self.benchmark_cache_get())
        results["benchmarks"].append(self.benchmark_cache_hit_rate())
        results["benchmarks"].append(self.benchmark_cache_delete())
        results["benchmarks"].append(self.benchmark_tiered_cache())
        results["benchmarks"].append(self.benchmark_concurrent_cache())
        
        # Calculate summary
        total_duration = sum(b["result"].total_duration for b in results["benchmarks"])
        avg_throughput = sum(b["result"].throughput for b in results["benchmarks"]) / len(results["benchmarks"])
        
        results["summary"] = {
            "total_duration": total_duration,
            "avg_throughput": avg_throughput,
            "benchmark_count": len(results["benchmarks"]),
        }
        
        logger.info(f"Cache benchmarks completed: {len(results['benchmarks'])} benchmarks")
        
        return results


def run_cache_benchmarks() -> Dict[str, Any]:
    """
    Run cache benchmarks and return results.
    
    Returns:
        Benchmark results
    """
    benchmarks = CacheBenchmarks()
    return benchmarks.run_all_benchmarks()
