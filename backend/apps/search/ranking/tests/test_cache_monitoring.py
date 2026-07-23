"""
Tests for ranking cache and monitoring.
"""

import unittest
import time
from datetime import datetime, timedelta
from apps.search.ranking.cache import (
    RankingCache,
    CacheKey,
    CacheEntry,
    CacheStats,
)
from apps.search.ranking.monitoring import (
    RankingMonitor,
    SignalMetrics,
    PipelineMetrics,
    CacheMetrics,
    RankingMetrics,
)


class TestCacheKey(unittest.TestCase):
    """Test cases for CacheKey."""
    
    def test_key_creation(self):
        """Test creating a cache key."""
        key = CacheKey(
            entity_type="job",
            query="engineer",
            profile_name="candidate_search",
            filters_hash="abc123",
            sort_hash="def456",
        )
        
        self.assertEqual(key.entity_type, "job")
        self.assertEqual(key.query, "engineer")
    
    def test_key_to_dict(self):
        """Test converting key to dictionary."""
        key = CacheKey(
            entity_type="job",
            query="engineer",
            profile_name="candidate_search",
            filters_hash="abc123",
            sort_hash="def456",
        )
        
        key_dict = key.to_dict()
        self.assertEqual(key_dict["entity_type"], "job")
        self.assertEqual(key_dict["query"], "engineer")
    
    def test_key_equality(self):
        """Test key equality."""
        key1 = CacheKey("job", "engineer", "candidate_search", "abc", "def")
        key2 = CacheKey("job", "engineer", "candidate_search", "abc", "def")
        key3 = CacheKey("job", "developer", "candidate_search", "abc", "def")
        
        self.assertEqual(key1, key2)
        self.assertNotEqual(key1, key3)


class TestCacheEntry(unittest.TestCase):
    """Test cases for CacheEntry."""
    
    def test_entry_creation(self):
        """Test creating a cache entry."""
        key = CacheKey("job", "engineer", "candidate_search", "abc", "def")
        entry = CacheEntry(
            key=key,
            value={"results": []},
            created_at=datetime.now(),
            ttl_seconds=300,
        )
        
        self.assertEqual(entry.key, key)
        self.assertEqual(entry.ttl_seconds, 300)
    
    def test_is_expired(self):
        """Test expiration check."""
        key = CacheKey("job", "engineer", "candidate_search", "abc", "def")
        
        # Not expired
        entry = CacheEntry(
            key=key,
            value={"results": []},
            created_at=datetime.now(),
            ttl_seconds=300,
        )
        self.assertFalse(entry.is_expired())
        
        # Expired
        entry = CacheEntry(
            key=key,
            value={"results": []},
            created_at=datetime.now() - timedelta(seconds=400),
            ttl_seconds=300,
        )
        self.assertTrue(entry.is_expired())
        
        # No expiration
        entry = CacheEntry(
            key=key,
            value={"results": []},
            created_at=datetime.now() - timedelta(seconds=400),
            ttl_seconds=0,
        )
        self.assertFalse(entry.is_expired())


class TestCacheStats(unittest.TestCase):
    """Test cases for CacheStats."""
    
    def test_stats_creation(self):
        """Test creating cache stats."""
        stats = CacheStats()
        
        self.assertEqual(stats.hits, 0)
        self.assertEqual(stats.misses, 0)
        self.assertEqual(stats.max_size, 1000)
    
    def test_hit_rate(self):
        """Test hit rate calculation."""
        stats = CacheStats()
        stats.hits = 80
        stats.misses = 20
        
        self.assertEqual(stats.hit_rate(), 0.8)
    
    def test_hit_rate_no_requests(self):
        """Test hit rate with no requests."""
        stats = CacheStats()
        
        self.assertEqual(stats.hit_rate(), 0.0)
    
    def test_miss_rate(self):
        """Test miss rate calculation."""
        stats = CacheStats()
        stats.hits = 80
        stats.misses = 20
        
        self.assertEqual(stats.miss_rate(), 0.2)


class TestRankingCache(unittest.TestCase):
    """Test cases for RankingCache."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cache = RankingCache(max_size=10, default_ttl=300)
    
    def test_cache_creation(self):
        """Test creating a ranking cache."""
        self.assertIsNotNone(self.cache)
        self.assertEqual(self.cache._max_size, 10)
        self.assertEqual(self.cache._default_ttl, 300)
    
    def test_cache_set_get(self):
        """Test setting and getting values."""
        self.cache.set(
            entity_type="job",
            query="engineer",
            profile_name="candidate_search",
            value={"results": ["job1", "job2"]},
        )
        
        result = self.cache.get(
            entity_type="job",
            query="engineer",
            profile_name="candidate_search",
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result["results"]), 2)
    
    def test_cache_miss(self):
        """Test cache miss."""
        result = self.cache.get(
            entity_type="job",
            query="engineer",
            profile_name="candidate_search",
        )
        
        self.assertIsNone(result)
    
    def test_cache_delete(self):
        """Test deleting from cache."""
        self.cache.set(
            entity_type="job",
            query="engineer",
            profile_name="candidate_search",
            value={"results": []},
        )
        
        deleted = self.cache.delete(
            entity_type="job",
            query="engineer",
            profile_name="candidate_search",
        )
        
        self.assertTrue(deleted)
        
        result = self.cache.get(
            entity_type="job",
            query="engineer",
            profile_name="candidate_search",
        )
        
        self.assertIsNone(result)
    
    def test_cache_invalidate_entity_type(self):
        """Test invalidating by entity type."""
        self.cache.set(
            entity_type="job",
            query="engineer",
            profile_name="candidate_search",
            value={"results": []},
        )
        
        count = self.cache.invalidate_entity_type("job")
        
        self.assertEqual(count, 1)
    
    def test_cache_invalidate_profile(self):
        """Test invalidating by profile."""
        self.cache.set(
            entity_type="job",
            query="engineer",
            profile_name="candidate_search",
            value={"results": []},
        )
        
        count = self.cache.invalidate_profile("candidate_search")
        
        self.assertEqual(count, 1)
    
    def test_cache_clear(self):
        """Test clearing cache."""
        self.cache.set(
            entity_type="job",
            query="engineer",
            profile_name="candidate_search",
            value={"results": []},
        )
        
        self.cache.clear()
        
        self.assertEqual(len(self.cache._cache), 0)
    
    def test_cache_cleanup_expired(self):
        """Test cleaning up expired entries."""
        self.cache.set(
            entity_type="job",
            query="engineer",
            profile_name="candidate_search",
            value={"results": []},
            ttl=1,
        )
        
        time.sleep(2)
        
        count = self.cache.cleanup_expired()
        
        self.assertEqual(count, 1)
    
    def test_cache_stats(self):
        """Test getting cache stats."""
        self.cache.set(
            entity_type="job",
            query="engineer",
            profile_name="candidate_search",
            value={"results": []},
        )
        
        self.cache.get(
            entity_type="job",
            query="engineer",
            profile_name="candidate_search",
        )
        
        self.cache.get(
            entity_type="job",
            query="developer",
            profile_name="candidate_search",
        )
        
        stats = self.cache.get_stats()
        
        self.assertEqual(stats.hits, 1)
        self.assertEqual(stats.misses, 1)


class TestSignalMetrics(unittest.TestCase):
    """Test cases for SignalMetrics."""
    
    def test_metrics_creation(self):
        """Test creating signal metrics."""
        metrics = SignalMetrics(signal_name="lexical")
        
        self.assertEqual(metrics.signal_name, "lexical")
        self.assertEqual(metrics.total_calls, 0)
    
    def test_metrics_update(self):
        """Test updating metrics."""
        metrics = SignalMetrics(signal_name="lexical")
        
        metrics.update(duration_ms=10.0, cached=False)
        
        self.assertEqual(metrics.total_calls, 1)
        self.assertEqual(metrics.total_time_ms, 10.0)
        self.assertEqual(metrics.avg_time_ms, 10.0)
        self.assertEqual(metrics.cache_misses, 1)
    
    def test_metrics_update_cached(self):
        """Test updating metrics with cache hit."""
        metrics = SignalMetrics(signal_name="lexical")
        
        metrics.update(duration_ms=5.0, cached=True)
        
        self.assertEqual(metrics.cache_hits, 1)
        self.assertEqual(metrics.cache_misses, 0)
    
    def test_metrics_record_error(self):
        """Test recording error."""
        metrics = SignalMetrics(signal_name="lexical")
        
        metrics.record_error()
        
        self.assertEqual(metrics.error_count, 1)
    
    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = SignalMetrics(signal_name="lexical")
        metrics.update(duration_ms=10.0, cached=False)
        
        metrics_dict = metrics.to_dict()
        
        self.assertEqual(metrics_dict["signal_name"], "lexical")
        self.assertEqual(metrics_dict["total_calls"], 1)


class TestPipelineMetrics(unittest.TestCase):
    """Test cases for PipelineMetrics."""
    
    def test_metrics_creation(self):
        """Test creating pipeline metrics."""
        metrics = PipelineMetrics()
        
        self.assertEqual(metrics.total_executions, 0)
    
    def test_metrics_update(self):
        """Test updating metrics."""
        metrics = PipelineMetrics()
        
        metrics.update(
            duration_ms=100.0,
            stage_times={"stage1": 50.0, "stage2": 50.0},
            parallel=True,
        )
        
        self.assertEqual(metrics.total_executions, 1)
        self.assertEqual(metrics.total_time_ms, 100.0)
        self.assertEqual(metrics.parallel_executions, 1)
    
    def test_metrics_record_early_termination(self):
        """Test recording early termination."""
        metrics = PipelineMetrics()
        
        metrics.record_early_termination()
        
        self.assertEqual(metrics.early_terminations, 1)
    
    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = PipelineMetrics()
        metrics.update(
            duration_ms=100.0,
            stage_times={"stage1": 50.0},
        )
        
        metrics_dict = metrics.to_dict()
        
        self.assertEqual(metrics_dict["total_executions"], 1)
        self.assertIn("stage_avg_times_ms", metrics_dict)


class TestCacheMetrics(unittest.TestCase):
    """Test cases for CacheMetrics."""
    
    def test_metrics_creation(self):
        """Test creating cache metrics."""
        metrics = CacheMetrics()
        
        self.assertEqual(metrics.hits, 0)
        self.assertEqual(metrics.misses, 0)
    
    def test_hit_rate(self):
        """Test hit rate calculation."""
        metrics = CacheMetrics()
        metrics.hits = 80
        metrics.misses = 20
        
        self.assertEqual(metrics.hit_rate(), 0.8)


class TestRankingMetrics(unittest.TestCase):
    """Test cases for RankingMetrics."""
    
    def test_metrics_creation(self):
        """Test creating ranking metrics."""
        metrics = RankingMetrics()
        
        self.assertEqual(metrics.total_rankings, 0)
    
    def test_metrics_update(self):
        """Test updating metrics."""
        metrics = RankingMetrics()
        
        metrics.update(duration_ms=50.0, document_count=10)
        
        self.assertEqual(metrics.total_rankings, 1)
        self.assertEqual(metrics.total_documents_ranked, 10)
        self.assertEqual(metrics.avg_documents_per_ranking, 10.0)
    
    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = RankingMetrics()
        metrics.update(duration_ms=50.0, document_count=10)
        
        metrics_dict = metrics.to_dict()
        
        self.assertEqual(metrics_dict["total_rankings"], 1)
        self.assertEqual(metrics_dict["total_documents_ranked"], 10)


class TestRankingMonitor(unittest.TestCase):
    """Test cases for RankingMonitor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = RankingMonitor()
    
    def test_monitor_creation(self):
        """Test creating a ranking monitor."""
        self.assertIsNotNone(self.monitor)
        self.assertIsNotNone(self.monitor._start_time)
    
    def test_record_signal_execution(self):
        """Test recording signal execution."""
        self.monitor.record_signal_execution(
            signal_name="lexical",
            duration_ms=10.0,
            cached=False,
        )
        
        metrics = self.monitor.get_signal_metrics("lexical")
        
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.total_calls, 1)
    
    def test_record_signal_error(self):
        """Test recording signal error."""
        self.monitor.record_signal_error(signal_name="lexical")
        
        metrics = self.monitor.get_signal_metrics("lexical")
        
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.error_count, 1)
    
    def test_record_pipeline_execution(self):
        """Test recording pipeline execution."""
        self.monitor.record_pipeline_execution(
            duration_ms=100.0,
            stage_times={"stage1": 50.0},
            parallel=True,
        )
        
        metrics = self.monitor.get_pipeline_metrics()
        
        self.assertEqual(metrics.total_executions, 1)
    
    def test_record_ranking(self):
        """Test recording ranking."""
        self.monitor.record_ranking(duration_ms=50.0, document_count=10)
        
        metrics = self.monitor.get_ranking_metrics()
        
        self.assertEqual(metrics.total_rankings, 1)
    
    def test_update_cache_metrics(self):
        """Test updating cache metrics."""
        cache_stats = {"hits": 80, "misses": 20, "evictions": 5, "size": 100}
        
        self.monitor.update_cache_metrics(cache_stats)
        
        metrics = self.monitor.get_cache_metrics()
        
        self.assertEqual(metrics.hits, 80)
        self.assertEqual(metrics.misses, 20)
    
    def test_get_all_signal_metrics(self):
        """Test getting all signal metrics."""
        self.monitor.record_signal_execution("lexical", 10.0)
        self.monitor.record_signal_execution("metadata", 15.0)
        
        metrics = self.monitor.get_all_signal_metrics()
        
        self.assertEqual(len(metrics), 2)
        self.assertIn("lexical", metrics)
        self.assertIn("metadata", metrics)
    
    def test_get_summary(self):
        """Test getting summary."""
        self.monitor.record_signal_execution("lexical", 10.0)
        self.monitor.record_pipeline_execution(100.0, {"stage1": 50.0})
        self.monitor.record_ranking(50.0, 10)
        
        summary = self.monitor.get_summary()
        
        self.assertIn("ranking_metrics", summary)
        self.assertIn("pipeline_metrics", summary)
        self.assertIn("cache_metrics", summary)
        self.assertIn("signal_metrics", summary)
    
    def test_reset(self):
        """Test resetting metrics."""
        self.monitor.record_signal_execution("lexical", 10.0)
        
        self.monitor.reset()
        
        metrics = self.monitor.get_all_signal_metrics()
        self.assertEqual(len(metrics), 0)


if __name__ == "__main__":
    unittest.main()
