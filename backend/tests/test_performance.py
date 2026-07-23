"""
Performance Tests

Comprehensive tests for performance monitoring, benchmarking,
and profiling functionality.
"""

import pytest
import time
from unittest.mock import Mock, patch

from matchhire_backend.core.performance import (
    PerformanceManager,
    BenchmarkRunner,
    BenchmarkResult,
    PerformanceProfiler,
    LoadTestingFramework,
    StressTestingFramework,
    CapacityPlanner,
    QueryBenchmarkRunner,
    RankingBenchmarkRunner,
    RecommendationBenchmarkRunner,
    performance_manager,
    track_performance,
)


class TestPerformanceManager:
    """Test performance manager functionality."""
    
    def test_record_metric(self):
        """Test recording performance metrics."""
        manager = PerformanceManager()
        
        manager.record_metric(
            operation="test_operation",
            duration=0.1,
            memory_used=1024,
            cpu_percent=50.0
        )
        
        metrics = manager.get_metrics("test_operation")
        assert len(metrics) == 1
        assert metrics[0]["duration"] == 0.1
    
    def test_get_statistics(self):
        """Test getting performance statistics."""
        manager = PerformanceManager()
        
        # Record multiple metrics
        for i in range(10):
            manager.record_metric(
                operation="test_operation",
                duration=0.1 + i * 0.01,
                memory_used=1024,
                cpu_percent=50.0
            )
        
        stats = manager.get_statistics("test_operation")
        assert stats["count"] == 10
        assert "avg_duration" in stats
        assert "p95_duration" in stats
        assert "p99_duration" in stats
    
    def test_clear_metrics(self):
        """Test clearing metrics."""
        manager = PerformanceManager()
        
        manager.record_metric(
            operation="test_operation",
            duration=0.1,
            memory_used=1024,
            cpu_percent=50.0
        )
        
        manager.clear_metrics("test_operation")
        metrics = manager.get_metrics("test_operation")
        assert len(metrics) == 0


class TestBenchmarkRunner:
    """Test benchmark runner functionality."""
    
    def test_run_benchmark(self):
        """Test running a benchmark."""
        manager = PerformanceManager()
        runner = BenchmarkRunner(manager)
        
        def test_func():
            time.sleep(0.01)
            return "result"
        
        result = runner.run_benchmark(test_func, "test_benchmark", iterations=5)
        
        assert isinstance(result, BenchmarkResult)
        assert result.name == "test_benchmark"
        assert result.iterations == 5
        assert result.success is True
        assert result.avg_duration > 0
    
    def test_benchmark_with_error(self):
        """Test benchmark with function error."""
        manager = PerformanceManager()
        runner = BenchmarkRunner(manager)
        
        def failing_func():
            raise Exception("Test error")
        
        result = runner.run_benchmark(failing_func, "test_benchmark", iterations=5)
        
        assert result.success is False
        assert result.error is not None


class TestPerformanceProfiler:
    """Test performance profiler functionality."""
    
    def test_profile_function(self):
        """Test profiling a function."""
        profiler = PerformanceProfiler()
        
        def test_func():
            time.sleep(0.01)
            return "result"
        
        result = profiler.profile_function(test_func)
        
        assert "duration" in result
        assert "cpu_percent" in result
        assert result["duration"] > 0
    
    def test_profile_memory(self):
        """Test memory profiling."""
        profiler = PerformanceProfiler()
        
        def test_func():
            data = [i for i in range(1000)]
            return data
        
        result = profiler.profile_memory(test_func)
        
        assert "memory_before" in result
        assert "memory_after" in result
        assert "memory_used" in result


class TestLoadTestingFramework:
    """Test load testing framework."""
    
    def test_load_test(self):
        """Test load testing."""
        manager = PerformanceManager()
        framework = LoadTestingFramework(manager)
        
        def test_func():
            time.sleep(0.001)
            return "result"
        
        result = framework.run_load_test(test_func, concurrent_users=5, requests_per_user=10)
        
        assert "total_requests" in result
        assert "successful_requests" in result
        assert "failed_requests" in result
        assert "avg_response_time" in result
        assert result["total_requests"] == 50


class TestStressTestingFramework:
    """Test stress testing framework."""
    
    def test_stress_test(self):
        """Test stress testing."""
        manager = PerformanceManager()
        framework = StressTestingFramework(manager)
        
        def test_func():
            time.sleep(0.001)
            return "result"
        
        result = framework.run_stress_test(test_func, max_users=20, duration=2)
        
        assert "peak_users" in result
        assert "total_requests" in result
        assert "error_rate" in result


class TestCapacityPlanner:
    """Test capacity planning."""
    
    def test_capacity_calculation(self):
        """Test capacity calculation."""
        planner = CapacityPlanner()
        
        result = planner.calculate_capacity(
            current_rps=100,
            target_rps=1000,
            avg_response_time=0.1
        )
        
        assert "instances_needed" in result
        assert "scaling_factor" in result
        assert result["instances_needed"] >= 1
    
    def test_resource_estimation(self):
        """Test resource estimation."""
        planner = CapacityPlanner()
        
        result = planner.estimate_resources(
            users=10000,
            requests_per_user=10,
            avg_response_time=0.1
        )
        
        assert "cpu_cores" in result
        assert "memory_gb" in result
        assert "storage_gb" in result


class TestQueryBenchmarkRunner:
    """Test query benchmark runner."""
    
    def test_benchmark_search_query(self):
        """Test search query benchmark."""
        runner = QueryBenchmarkRunner()
        
        def query_func(query):
            time.sleep(0.01)
            return ["result1", "result2"]
        
        result = runner.benchmark_search_query(query_func, "test query", iterations=5)
        
        assert result.name == "search_query:test query"
        assert result.success is True


class TestRankingBenchmarkRunner:
    """Test ranking benchmark runner."""
    
    def test_benchmark_ranking(self):
        """Test ranking benchmark."""
        runner = RankingBenchmarkRunner()
        
        def ranking_func(candidates):
            time.sleep(0.01)
            return sorted(candidates, reverse=True)
        
        result = runner.benchmark_ranking(ranking_func, [1, 2, 3, 4, 5], iterations=5)
        
        assert result.name == "ranking:5_candidates"
        assert result.success is True


class TestRecommendationBenchmarkRunner:
    """Test recommendation benchmark runner."""
    
    def test_benchmark_recommendation_generation(self):
        """Test recommendation generation benchmark."""
        runner = RecommendationBenchmarkRunner()
        
        def rec_func(user_id):
            time.sleep(0.01)
            return [{"job_id": i} for i in range(10)]
        
        result = runner.benchmark_recommendation_generation(rec_func, 123, iterations=5)
        
        assert result.name == "recommendation:user_123"
        assert result.success is True


class TestPerformanceDecorator:
    """Test performance tracking decorator."""
    
    def test_track_performance_decorator(self):
        """Test track_performance decorator."""
        @track_performance("test_operation")
        def test_func():
            time.sleep(0.01)
            return "result"
        
        result = test_func()
        assert result == "result"
        
        metrics = performance_manager.get_metrics("test_operation")
        assert len(metrics) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
