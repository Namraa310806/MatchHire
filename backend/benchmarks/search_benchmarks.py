"""
Search Performance Benchmarks

Benchmarks for search operations including query performance,
indexing performance, and provider comparisons.
"""

import time
from typing import Dict, List, Any
from dataclasses import dataclass

from matchhire_backend.core.performance import BenchmarkRunner, performance_manager


@dataclass
class SearchBenchmarkConfig:
    """Configuration for search benchmarks."""
    query_count: int = 100
    indexing_count: int = 1000
    warmup_iterations: int = 10


class SearchBenchmarks:
    """
    Search performance benchmarks.
    """
    
    def __init__(self, config: SearchBenchmarkConfig = None):
        self.config = config or SearchBenchmarkConfig()
        self.benchmark_runner = BenchmarkRunner(performance_manager)
        
    def benchmark_simple_search(self) -> Dict[str, Any]:
        """
        Benchmark simple text search.
        
        Returns:
            Benchmark results
        """
        from apps.search.services.search_service import SearchService
        
        search_service = SearchService()
        
        def search_query():
            return search_service.search(
                query="software engineer",
                filters={},
                page=1,
                page_size=20,
            )
            
        result = self.benchmark_runner.run_benchmark(
            func=search_query,
            name="search_simple_query",
            iterations=self.config.query_count,
            warmup=self.config.warmup_iterations,
        )
        
        return {
            "name": "Simple Search",
            "result": result,
            "config": {
                "query_count": self.config.query_count,
                "query": "software engineer",
            },
        }
        
    def benchmark_filtered_search(self) -> Dict[str, Any]:
        """
        Benchmark search with filters.
        
        Returns:
            Benchmark results
        """
        from apps.search.services.search_service import SearchService
        
        search_service = SearchService()
        
        def search_query():
            return search_service.search(
                query="python developer",
                filters={
                    "experience_level": "senior",
                    "employment_type": "full-time",
                    "location": "remote",
                },
                page=1,
                page_size=20,
            )
            
        result = self.benchmark_runner.run_benchmark(
            func=search_query,
            name="search_filtered_query",
            iterations=self.config.query_count,
            warmup=self.config.warmup_iterations,
        )
        
        return {
            "name": "Filtered Search",
            "result": result,
            "config": {
                "query_count": self.config.query_count,
                "filters": ["experience_level", "employment_type", "location"],
            },
        }
        
    def benchmark_autocomplete(self) -> Dict[str, Any]:
        """
        Benchmark autocomplete queries.
        
        Returns:
            Benchmark results
        """
        from apps.search.services.search_service import SearchService
        
        search_service = SearchService()
        
        def autocomplete_query():
            return search_service.autocomplete(
                query="soft",
                limit=10,
            )
            
        result = self.benchmark_runner.run_benchmark(
            func=autocomplete_query,
            name="search_autocomplete",
            iterations=self.config.query_count,
            warmup=self.config.warmup_iterations,
        )
        
        return {
            "name": "Autocomplete",
            "result": result,
            "config": {
                "query_count": self.config.query_count,
                "query": "soft",
            },
        }
        
    def benchmark_bulk_indexing(self) -> Dict[str, Any]:
        """
        Benchmark bulk document indexing.
        
        Returns:
            Benchmark results
        """
        from apps.search.indexing.indexer import DocumentIndexer
        
        indexer = DocumentIndexer()
        
        # Generate test documents
        test_documents = [
            {
                "id": i,
                "title": f"Job Title {i}",
                "description": f"Job description for position {i}",
                "requirements": f"Requirements for job {i}",
            }
            for i in range(self.config.indexing_count)
        ]
        
        def bulk_index():
            return indexer.bulk_index(test_documents)
            
        result = self.benchmark_runner.run_benchmark(
            func=bulk_index,
            name="search_bulk_indexing",
            iterations=10,
            warmup=2,
        )
        
        return {
            "name": "Bulk Indexing",
            "result": result,
            "config": {
                "document_count": self.config.indexing_count,
            },
        }
        
    def benchmark_concurrent_search(self) -> Dict[str, Any]:
        """
        Benchmark concurrent search requests.
        
        Returns:
            Benchmark results
        """
        from apps.search.services.search_service import SearchService
        
        search_service = SearchService()
        
        def search_query():
            return search_service.search(
                query="data scientist",
                filters={},
                page=1,
                page_size=20,
            )
            
        result = self.benchmark_runner.run_concurrent_benchmark(
            func=search_query,
            name="search_concurrent",
            concurrency=10,
            iterations_per_worker=10,
        )
        
        return {
            "name": "Concurrent Search",
            "result": result,
            "config": {
                "concurrency": 10,
                "iterations_per_worker": 10,
            },
        }
        
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """
        Run all search benchmarks.
        
        Returns:
            All benchmark results
        """
        logger.info("Running search benchmarks...")
        
        results = {
            "timestamp": time.time(),
            "benchmarks": [],
        }
        
        # Run benchmarks
        results["benchmarks"].append(self.benchmark_simple_search())
        results["benchmarks"].append(self.benchmark_filtered_search())
        results["benchmarks"].append(self.benchmark_autocomplete())
        results["benchmarks"].append(self.benchmark_bulk_indexing())
        results["benchmarks"].append(self.benchmark_concurrent_search())
        
        # Calculate summary
        total_duration = sum(b["result"].total_duration for b in results["benchmarks"])
        avg_throughput = sum(b["result"].throughput for b in results["benchmarks"]) / len(results["benchmarks"])
        
        results["summary"] = {
            "total_duration": total_duration,
            "avg_throughput": avg_throughput,
            "benchmark_count": len(results["benchmarks"]),
        }
        
        logger.info(f"Search benchmarks completed: {len(results['benchmarks'])} benchmarks")
        
        return results


def run_search_benchmarks() -> Dict[str, Any]:
    """
    Run search benchmarks and return results.
    
    Returns:
        Benchmark results
    """
    benchmarks = SearchBenchmarks()
    return benchmarks.run_all_benchmarks()
