"""
Recommendation Performance Benchmarks

Benchmarks for recommendation operations including candidate-job matching,
ranking performance, and strategy comparisons.
"""

import time
from typing import Dict, List, Any
from dataclasses import dataclass

from matchhire_backend.core.performance import BenchmarkRunner, performance_manager


@dataclass
class RecommendationBenchmarkConfig:
    """Configuration for recommendation benchmarks."""
    candidate_count: int = 100
    job_count: int = 1000
    warmup_iterations: int = 5


class RecommendationBenchmarks:
    """
    Recommendation performance benchmarks.
    """
    
    def __init__(self, config: RecommendationBenchmarkConfig = None):
        self.config = config or RecommendationBenchmarkConfig()
        self.benchmark_runner = BenchmarkRunner(performance_manager)
        
    def benchmark_candidate_recommendations(self) -> Dict[str, Any]:
        """
        Benchmark candidate-job recommendations.
        
        Returns:
            Benchmark results
        """
        from apps.search.recommendations.candidate_recommendations import CandidateRecommendationEngine
        
        engine = CandidateRecommendationEngine()
        
        def get_recommendations():
            return engine.get_recommendations(
                candidate_id=1,
                limit=10,
                strategy="match_score",
            )
            
        result = self.benchmark_runner.run_benchmark(
            func=get_recommendations,
            name="recommendation_candidate_jobs",
            iterations=50,
            warmup=self.config.warmup_iterations,
        )
        
        return {
            "name": "Candidate Recommendations",
            "result": result,
            "config": {
                "candidate_id": 1,
                "limit": 10,
                "strategy": "match_score",
            },
        }
        
    def benchmark_job_recommendations(self) -> Dict[str, Any]:
        """
        Benchmark job-candidate recommendations.
        
        Returns:
            Benchmark results
        """
        from apps.search.recommendations.candidate_recommendations import CandidateRecommendationEngine
        
        engine = CandidateRecommendationEngine()
        
        def get_recommendations():
            return engine.get_candidates_for_job(
                job_id=1,
                limit=20,
                strategy="match_score",
            )
            
        result = self.benchmark_runner.run_benchmark(
            func=get_recommendations,
            name="recommendation_job_candidates",
            iterations=50,
            warmup=self.config.warmup_iterations,
        )
        
        return {
            "name": "Job Recommendations",
            "result": result,
            "config": {
                "job_id": 1,
                "limit": 20,
                "strategy": "match_score",
            },
        }
        
    def benchmark_ranking_performance(self) -> Dict[str, Any]:
        """
        Benchmark ranking performance.
        
        Returns:
            Benchmark results
        """
        from apps.search.ranking.ranking_engine import RankingEngine
        
        ranking_engine = RankingEngine()
        
        # Generate test results
        test_results = [
            {"id": i, "score": 0.5 + (i % 10) * 0.05}
            for i in range(100)
        ]
        
        def rank_results():
            return ranking_engine.rank(
                results=test_results,
                strategy="match_score",
            )
            
        result = self.benchmark_runner.run_benchmark(
            func=rank_results,
            name="recommendation_ranking",
            iterations=100,
            warmup=self.config.warmup_iterations,
        )
        
        return {
            "name": "Ranking Performance",
            "result": result,
            "config": {
                "result_count": len(test_results),
                "strategy": "match_score",
            },
        }
        
    def benchmark_strategy_comparison(self) -> Dict[str, Any]:
        """
        Benchmark different recommendation strategies.
        
        Returns:
            Benchmark results
        """
        from apps.search.recommendations.candidate_recommendations import CandidateRecommendationEngine
        
        engine = CandidateRecommendationEngine()
        strategies = ["match_score", "bm25", "hybrid"]
        
        results = {}
        for strategy in strategies:
            def get_recommendations():
                return engine.get_recommendations(
                    candidate_id=1,
                    limit=10,
                    strategy=strategy,
                )
                
            result = self.benchmark_runner.run_benchmark(
                func=get_recommendations,
                name=f"recommendation_strategy_{strategy}",
                iterations=30,
                warmup=3,
            )
            results[strategy] = result
            
        return {
            "name": "Strategy Comparison",
            "results": results,
            "config": {
                "strategies": strategies,
            },
        }
        
    def benchmark_concurrent_recommendations(self) -> Dict[str, Any]:
        """
        Benchmark concurrent recommendation requests.
        
        Returns:
            Benchmark results
        """
        from apps.search.recommendations.candidate_recommendations import CandidateRecommendationEngine
        
        engine = CandidateRecommendationEngine()
        
        def get_recommendations():
            return engine.get_recommendations(
                candidate_id=1,
                limit=10,
                strategy="match_score",
            )
            
        result = self.benchmark_runner.run_concurrent_benchmark(
            func=get_recommendations,
            name="recommendation_concurrent",
            concurrency=5,
            iterations_per_worker=10,
        )
        
        return {
            "name": "Concurrent Recommendations",
            "result": result,
            "config": {
                "concurrency": 5,
                "iterations_per_worker": 10,
            },
        }
        
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """
        Run all recommendation benchmarks.
        
        Returns:
            All benchmark results
        """
        logger.info("Running recommendation benchmarks...")
        
        results = {
            "timestamp": time.time(),
            "benchmarks": [],
        }
        
        # Run benchmarks
        results["benchmarks"].append(self.benchmark_candidate_recommendations())
        results["benchmarks"].append(self.benchmark_job_recommendations())
        results["benchmarks"].append(self.benchmark_ranking_performance())
        results["benchmarks"].append(self.benchmark_strategy_comparison())
        results["benchmarks"].append(self.benchmark_concurrent_recommendations())
        
        # Calculate summary
        total_duration = sum(
            b.get("result", b).total_duration if isinstance(b.get("result"), object) else 0
            for b in results["benchmarks"]
        )
        
        results["summary"] = {
            "total_duration": total_duration,
            "benchmark_count": len(results["benchmarks"]),
        }
        
        logger.info(f"Recommendation benchmarks completed: {len(results['benchmarks'])} benchmarks")
        
        return results


def run_recommendation_benchmarks() -> Dict[str, Any]:
    """
    Run recommendation benchmarks and return results.
    
    Returns:
        Benchmark results
    """
    benchmarks = RecommendationBenchmarks()
    return benchmarks.run_all_benchmarks()
