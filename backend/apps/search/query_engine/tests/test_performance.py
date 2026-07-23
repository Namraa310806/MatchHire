"""
Tests for the Performance optimization system.
"""

import unittest
from datetime import datetime, timedelta
from apps.search.query_engine.performance import (
    QueryCache,
    QueryOptimizer,
    PerformanceConfig,
    CacheStrategy,
    CacheEntry,
)


class TestCacheStrategy(unittest.TestCase):
    """Test cases for CacheStrategy enum."""
    
    def test_cache_strategy_values(self):
        """Test cache strategy enum values."""
        self.assertEqual(CacheStrategy.LRU.value, "lru")
        self.assertEqual(CacheStrategy.LFU.value, "lfu")
        self.assertEqual(CacheStrategy.TTL.value, "ttl")
        self.assertEqual(CacheStrategy.NONE.value, "none")


class TestPerformanceConfig(unittest.TestCase):
    """Test cases for PerformanceConfig."""
    
    def test_default_config(self):
        """Test default performance configuration."""
        config = PerformanceConfig()
        self.assertEqual(config.query_timeout_ms, 30000)
        self.assertEqual(config.max_query_depth, 10)
        self.assertEqual(config.cache_enabled, True)
    
    def test_custom_config(self):
        """Test custom performance configuration."""
        config = PerformanceConfig(
            query_timeout_ms=60000,
            max_query_depth=20,
            cache_enabled=False
        )
        self.assertEqual(config.query_timeout_ms, 60000)
        self.assertEqual(config.max_query_depth, 20)
        self.assertEqual(config.cache_enabled, False)
    
    def test_config_to_dict(self):
        """Test config serialization."""
        config = PerformanceConfig()
        config_dict = config.to_dict()
        self.assertEqual(config_dict["query_timeout_ms"], 30000)
        self.assertEqual(config_dict["cache_enabled"], True)


class TestCacheEntry(unittest.TestCase):
    """Test cases for CacheEntry."""
    
    def test_basic_entry(self):
        """Test basic cache entry."""
        entry = CacheEntry(key="test_key", value={"data": "test"})
        self.assertEqual(entry.key, "test_key")
        self.assertEqual(entry.value, {"data": "test"})
        self.assertEqual(entry.access_count, 0)
    
    def test_entry_is_expired(self):
        """Test entry expiration check."""
        entry = CacheEntry(key="test_key", value={"data": "test"})
        self.assertFalse(entry.is_expired(ttl_seconds=3600))
    
    def test_entry_is_expired_true(self):
        """Test entry expiration check with old entry."""
        entry = CacheEntry(key="test_key", value={"data": "test"})
        entry.created_at = datetime.now() - timedelta(seconds=400)
        self.assertTrue(entry.is_expired(ttl_seconds=300))
    
    def test_entry_touch(self):
        """Test entry touch."""
        entry = CacheEntry(key="test_key", value={"data": "test"})
        entry.touch()
        self.assertEqual(entry.access_count, 1)
        self.assertIsNotNone(entry.last_accessed)


class TestQueryCache(unittest.TestCase):
    """Test cases for QueryCache."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = PerformanceConfig(cache_enabled=True, cache_max_size=10)
        self.cache = QueryCache(self.config)
    
    def test_cache_get_miss(self):
        """Test cache get miss."""
        result = self.cache.get(
            entity_type="job",
            query="software engineer"
        )
        self.assertIsNone(result)
    
    def test_cache_set_and_get(self):
        """Test cache set and get."""
        value = {"results": [{"id": 1}]}
        self.cache.set(
            entity_type="job",
            query="software engineer",
            value=value
        )
        result = self.cache.get(
            entity_type="job",
            query="software engineer"
        )
        self.assertIsNotNone(result)
        self.assertEqual(result, value)
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        key1 = self.cache._generate_key(
            entity_type="job",
            query="software engineer",
            filters={"location": "SF"}
        )
        key2 = self.cache._generate_key(
            entity_type="job",
            query="software engineer",
            filters={"location": "SF"}
        )
        self.assertEqual(key1, key2)
    
    def test_cache_key_different_params(self):
        """Test cache key generation with different parameters."""
        key1 = self.cache._generate_key(
            entity_type="job",
            query="software engineer",
            filters={"location": "SF"}
        )
        key2 = self.cache._generate_key(
            entity_type="job",
            query="software engineer",
            filters={"location": "NY"}
        )
        self.assertNotEqual(key1, key2)
    
    def test_cache_disabled(self):
        """Test cache when disabled."""
        config = PerformanceConfig(cache_enabled=False)
        cache = QueryCache(config)
        
        cache.set(
            entity_type="job",
            query="software engineer",
            value={"results": []}
        )
        result = cache.get(
            entity_type="job",
            query="software engineer"
        )
        self.assertIsNone(result)
    
    def test_cache_invalidate_all(self):
        """Test cache invalidation of all entries."""
        self.cache.set(
            entity_type="job",
            query="software engineer",
            value={"results": []}
        )
        self.cache.invalidate()
        result = self.cache.get(
            entity_type="job",
            query="software engineer"
        )
        self.assertIsNone(result)
    
    def test_cache_invalidate_entity_type(self):
        """Test cache invalidation by entity type."""
        self.cache.set(
            entity_type="job",
            query="software engineer",
            value={"results": []}
        )
        self.cache.set(
            entity_type="candidate",
            query="python developer",
            value={"results": []}
        )
        
        self.cache.invalidate(entity_type="job")
        
        job_result = self.cache.get(
            entity_type="job",
            query="software engineer"
        )
        candidate_result = self.cache.get(
            entity_type="candidate",
            query="python developer"
        )
        
        self.assertIsNone(job_result)
        self.assertIsNotNone(candidate_result)
    
    def test_cache_eviction_lru(self):
        """Test cache eviction with LRU strategy."""
        config = PerformanceConfig(cache_max_size=3)
        cache = QueryCache(config)
        
        # Add 4 entries (should evict the oldest)
        for i in range(4):
            cache.set(
                entity_type="job",
                query=f"query{i}",
                value={"results": i}
            )
        
        # Access the first entry to make it recently used
        cache.get(entity_type="job", query="query0")
        
        # Add another entry
        cache.set(
            entity_type="job",
            query="query4",
            value={"results": 4}
        )
        
        # Query1 should be evicted (least recently used)
        result1 = cache.get(entity_type="job", query="query1")
        result0 = cache.get(entity_type="job", query="query0")
        
        self.assertIsNone(result1)
        self.assertIsNotNone(result0)
    
    def test_cache_stats(self):
        """Test cache statistics."""
        self.cache.set(
            entity_type="job",
            query="software engineer",
            value={"results": []}
        )
        
        # Hit
        self.cache.get(entity_type="job", query="software engineer")
        
        # Miss
        self.cache.get(entity_type="job", query="python developer")
        
        stats = self.cache.get_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["size"], 1)
    
    def test_cache_clear(self):
        """Test cache clear."""
        self.cache.set(
            entity_type="job",
            query="software engineer",
            value={"results": []}
        )
        
        self.cache.clear()
        
        stats = self.cache.get_stats()
        self.assertEqual(stats["size"], 0)
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)


class TestQueryOptimizer(unittest.TestCase):
    """Test cases for QueryOptimizer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = PerformanceConfig()
        self.optimizer = QueryOptimizer(self.config)
    
    def test_optimize_query(self):
        """Test query optimization."""
        optimized = self.optimizer.optimize_query(
            query="  software  engineer  ",
            filters={"status": "active"}
        )
        
        self.assertEqual(optimized["query"], "software engineer")
        self.assertEqual(optimized["filters"]["status"], "active")
    
    def test_optimize_query_string(self):
        """Test query string optimization."""
        optimized = self.optimizer._optimize_querystring("  software  engineer  ")
        self.assertEqual(optimized, "software engineer")
    
    def test_optimize_query_string_truncate(self):
        """Test query string truncation."""
        long_query = "a" * 2000
        optimized = self.optimizer._optimize_querystring(long_query)
        self.assertEqual(len(optimized), 1000)
    
    def test_optimize_filters(self):
        """Test filter optimization."""
        filters = {
            "status": "active",
            "skills": ["python", "python", "javascript"],
            "empty": None
        }
        
        optimized = self.optimizer._optimize_filters(filters)
        
        self.assertEqual(optimized["status"], "active")
        self.assertEqual(len(optimized["skills"]), 2)  # Deduplicated
        self.assertNotIn("empty", optimized)  # None removed
    
    def test_optimize_filters_list_limit(self):
        """Test filter list size limit."""
        filters = {"skills": [str(i) for i in range(150)]}
        optimized = self.optimizer._optimize_filters(filters)
        self.assertEqual(len(optimized["skills"]), 100)
    
    def test_validate_query_depth(self):
        """Test query depth validation."""
        simple_query = {"match": {"title": "software"}}
        self.assertTrue(self.optimizer.validate_query_depth(simple_query))
    
    def test_validate_query_depth_exceeded(self):
        """Test query depth validation exceeded."""
        deep_query = {"level1": {"level2": {"level3": {"level4": {"level5": {"level6": {"level7": {"level8": {"level9": {"level10": {"level11": {}}}}}}}}}}}}}}
        self.assertFalse(self.optimizer.validate_query_depth(deep_query))
    
    def test_validate_clause_count(self):
        """Test clause count validation."""
        simple_query = {"bool": {"must": [{"match": {"title": "software"}}]}}
        self.assertTrue(self.optimizer.validate_clause_count(simple_query))
    
    def test_count_clauses(self):
        """Test clause counting."""
        query = {
            "bool": {
                "must": [
                    {"match": {"title": "software"}},
                    {"match": {"description": "engineer"}}
                ],
                "should": [
                    {"match": {"skills": "python"}}
                ]
            }
        }
        count = self.optimizer._count_clauses(query)
        self.assertEqual(count, 3)
    
    def test_optimize_pagination(self):
        """Test pagination optimization."""
        pagination = {"offset": 5, "limit": 20}
        optimized = self.optimizer.optimize_pagination(pagination, total_results=100)
        self.assertEqual(optimized["offset"], 5)
        self.assertEqual(optimized["limit"], 20)
    
    def test_optimize_pagination_max_window(self):
        """Test pagination optimization with max window."""
        config = PerformanceConfig(max_result_window=100)
        optimizer = QueryOptimizer(config)
        
        pagination = {"offset": 150, "limit": 20}
        optimized = optimizer.optimize_pagination(pagination, total_results=100)
        self.assertEqual(optimized["offset"], 100)
    
    def test_optimize_pagination_large_result(self):
        """Test pagination optimization for large results."""
        config = PerformanceConfig(
            large_result_threshold=100,
            enable_large_result_protection=True
        )
        optimizer = QueryOptimizer(config)
        
        pagination = {"offset": 0, "limit": 200}
        optimized = optimizer.optimize_pagination(pagination, total_results=500)
        self.assertEqual(optimized["limit"], 100)
    
    def test_check_query_complexity(self):
        """Test query complexity check."""
        query = {
            "bool": {
                "must": [{"match": {"title": "software"}}]
            }
        }
        complexity = self.optimizer.check_query_complexity(query)
        self.assertIn("depth", complexity)
        self.assertIn("clauses", complexity)
        self.assertIn("is_complex", complexity)
    
    def test_calculate_query_depth(self):
        """Test query depth calculation."""
        query = {"level1": {"level2": {"level3": {}}}}
        depth = self.optimizer._calculate_query_depth(query)
        self.assertEqual(depth, 3)


if __name__ == "__main__":
    unittest.main()
