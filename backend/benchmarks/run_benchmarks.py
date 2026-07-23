"""
Benchmark Runner

Main entry point for running all performance benchmarks.
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Any

from benchmarks.search_benchmarks import run_search_benchmarks
from benchmarks.recommendation_benchmarks import run_recommendation_benchmarks
from benchmarks.cache_benchmarks import run_cache_benchmarks

logger = logging.getLogger(__name__)


class BenchmarkSuite:
    """
    Complete benchmark suite for MatchHire backend.
    """
    
    def __init__(self):
        self.results = {}
        
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """
        Run all benchmark suites.
        
        Returns:
            Complete benchmark results
        """
        logger.info("=" * 60)
        logger.info("Starting Complete Benchmark Suite")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # Run search benchmarks
        logger.info("Running search benchmarks...")
        self.results["search"] = run_search_benchmarks()
        
        # Run recommendation benchmarks
        logger.info("Running recommendation benchmarks...")
        self.results["recommendations"] = run_recommendation_benchmarks()
        
        # Run cache benchmarks
        logger.info("Running cache benchmarks...")
        self.results["cache"] = run_cache_benchmarks()
        
        # Calculate overall summary
        total_duration = time.time() - start_time
        
        self.results["summary"] = {
            "total_duration": total_duration,
            "timestamp": datetime.utcnow().isoformat(),
            "suites_run": len(self.results) - 1,
        }
        
        logger.info("=" * 60)
        logger.info(f"Benchmark Suite Completed in {total_duration:.2f}s")
        logger.info("=" * 60)
        
        return self.results
        
    def save_results(self, filepath: str = "benchmark_results.json") -> None:
        """
        Save benchmark results to file.
        
        Args:
            filepath: Path to save results
        """
        with open(filepath, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"Benchmark results saved to {filepath}")
        
    def print_summary(self) -> None:
        """Print benchmark summary to console."""
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        
        for suite_name, suite_results in self.results.items():
            if suite_name == "summary":
                continue
                
            print(f"\n{suite_name.upper()}")
            print("-" * 40)
            
            for benchmark in suite_results.get("benchmarks", []):
                result = benchmark.get("result")
                if result and hasattr(result, "avg_duration"):
                    print(f"  {benchmark['name']}:")
                    print(f"    Avg Duration: {result.avg_duration*1000:.2f}ms")
                    print(f"    P95 Duration: {result.p95_duration*1000:.2f}ms")
                    print(f"    Throughput: {result.throughput:.2f} ops/s")
                    
        print("\n" + "=" * 60)
        print(f"Total Duration: {self.results['summary']['total_duration']:.2f}s")
        print("=" * 60 + "\n")


def main():
    """Main entry point for running benchmarks."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    suite = BenchmarkSuite()
    results = suite.run_all_benchmarks()
    suite.save_results()
    suite.print_summary()
    
    return results


if __name__ == "__main__":
    main()
