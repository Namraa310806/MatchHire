"""
Advanced Caching Module

Provides adaptive TTL, cache warming, invalidation, distributed cache interface,
and tiered caching capabilities.
"""

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from django.core.cache import cache
from django.core.cache.backends.base import BaseCache

logger = logging.getLogger(__name__)


class CacheTier(Enum):
    """Cache tier levels."""
    L1 = "l1"  # In-memory (fastest, smallest)
    L2 = "l2"  # Redis (fast, medium)
    L3 = "l3"  # Database (slowest, largest)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    ttl: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return (datetime.utcnow() - self.created_at).total_seconds() > self.ttl
        
    @property
    def age_seconds(self) -> float:
        """Get age of entry in seconds."""
        return (datetime.utcnow() - self.created_at).total_seconds()


class AdaptiveTTLStrategy:
    """
    Adaptive TTL strategy based on access patterns.
    
    Adjusts TTL based on:
    - Access frequency
    - Hit rate
    - Entry size
    - Time since last access
    """
    
    def __init__(self, base_ttl: int = 300, min_ttl: int = 60, max_ttl: int = 3600):
        self.base_ttl = base_ttl
        self.min_ttl = min_ttl
        self.max_ttl = max_ttl
        self._access_history: Dict[str, List[float]] = {}
        
    def calculate_ttl(self, key: str, entry: CacheEntry = None) -> int:
        """
        Calculate adaptive TTL for a cache key.
        
        Args:
            key: Cache key
            entry: Existing cache entry (if updating)
            
        Returns:
            TTL in seconds
        """
        # Get access history
        history = self._access_history.get(key, [])
        
        # Calculate access rate
        if len(history) > 1:
            time_span = history[-1] - history[0]
            access_rate = len(history) / time_span if time_span > 0 else 0
        else:
            access_rate = 0
            
        # Adjust TTL based on access rate
        if access_rate > 10:  # Very high access rate
            ttl_multiplier = 3.0
        elif access_rate > 5:  # High access rate
            ttl_multiplier = 2.0
        elif access_rate > 1:  # Medium access rate
            ttl_multiplier = 1.5
        else:  # Low access rate
            ttl_multiplier = 1.0
            
        # Adjust based on entry size (larger entries get shorter TTL)
        if entry and entry.size_bytes > 1024 * 1024:  # > 1MB
            ttl_multiplier *= 0.5
        elif entry and entry.size_bytes > 100 * 1024:  # > 100KB
            ttl_multiplier *= 0.7
            
        # Calculate final TTL
        ttl = int(self.base_ttl * ttl_multiplier)
        return max(self.min_ttl, min(self.max_ttl, ttl))
        
    def record_access(self, key: str) -> None:
        """Record an access to a cache key."""
        if key not in self._access_history:
            self._access_history[key] = []
            
        self._access_history[key].append(time.time())
        
        # Keep only last 100 accesses
        if len(self._access_history[key]) > 100:
            self._access_history[key] = self._access_history[key][-100:]
            
    def cleanup_history(self, key: str = None) -> None:
        """Clean up access history."""
        if key:
            self._access_history.pop(key, None)
        else:
            self._access_history.clear()


class CacheWarmer:
    """
    Cache warming utility.
    
    Pre-loads frequently accessed data into cache.
    """
    
    def __init__(self, cache_backend: BaseCache = None):
        self.cache_backend = cache_backend or cache
        self._warmup_tasks: List[Callable] = []
        
    def register_warmup_task(self, task: Callable) -> None:
        """
        Register a warmup task.
        
        Args:
            task: Callable that returns (key, value, ttl) tuple
        """
        self._warmup_tasks.append(task)
        
    async def warmup_cache(self) -> Dict[str, Any]:
        """
        Execute all warmup tasks.
        
        Returns:
            Dictionary with warmup results
        """
        results = {
            "total_tasks": len(self._warmup_tasks),
            "successful": 0,
            "failed": 0,
            "errors": [],
        }
        
        for task in self._warmup_tasks:
            try:
                key, value, ttl = task()
                self.cache_backend.set(key, value, ttl)
                results["successful"] += 1
                logger.info(f"Warmed up cache key: {key}")
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(str(e))
                logger.error(f"Failed to warm up cache: {e}")
                
        return results
        
    def warmup_key(self, key: str, value_func: Callable, ttl: int = 300) -> bool:
        """
        Warm up a specific cache key.
        
        Args:
            key: Cache key
            value_func: Function to generate value
            ttl: TTL in seconds
            
        Returns:
            True if successful
        """
        try:
            value = value_func()
            self.cache_backend.set(key, value, ttl)
            logger.info(f"Warmed up cache key: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to warm up key {key}: {e}")
            return False


class CacheInvalidator:
    """
    Cache invalidation utility.
    
    Provides various invalidation strategies.
    """
    
    def __init__(self, cache_backend: BaseCache = None):
        self.cache_backend = cache_backend or cache
        self._invalidation_patterns: Dict[str, List[str]] = {}
        
    def invalidate_key(self, key: str) -> bool:
        """
        Invalidate a specific cache key.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted
        """
        try:
            self.cache_backend.delete(key)
            logger.debug(f"Invalidated cache key: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate key {key}: {e}")
            return False
            
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate keys matching a pattern.
        
        Args:
            pattern: Key pattern (supports * wildcard)
            
        Returns:
            Number of keys invalidated
        """
        # This requires Redis-specific implementation
        # For Django cache, we'll use a tag-based approach
        count = 0
        try:
            # Get all keys with this pattern tag
            tag_key = f"pattern:{pattern}"
            keys = self.cache_backend.get(tag_key, [])
            
            for key in keys:
                if self.invalidate_key(key):
                    count += 1
                    
            self.cache_backend.delete(tag_key)
            logger.info(f"Invalidated {count} keys matching pattern: {pattern}")
            return count
        except Exception as e:
            logger.error(f"Failed to invalidate pattern {pattern}: {e}")
            return 0
            
    def invalidate_tag(self, tag: str) -> int:
        """
        Invalidate all keys with a specific tag.
        
        Args:
            tag: Tag name
            
        Returns:
            Number of keys invalidated
        """
        count = 0
        try:
            tag_key = f"tag:{tag}"
            keys = self.cache_backend.get(tag_key, [])
            
            for key in keys:
                if self.invalidate_key(key):
                    count += 1
                    
            self.cache_backend.delete(tag_key)
            logger.info(f"Invalidated {count} keys with tag: {tag}")
            return count
        except Exception as e:
            logger.error(f"Failed to invalidate tag {tag}: {e}")
            return 0
            
    def register_pattern(self, pattern: str, keys: List[str]) -> None:
        """
        Register keys for a pattern.
        
        Args:
            pattern: Pattern string
            keys: List of keys matching pattern
        """
        tag_key = f"pattern:{pattern}"
        existing_keys = self.cache_backend.get(tag_key, [])
        all_keys = list(set(existing_keys + keys))
        self.cache_backend.set(tag_key, all_keys, 86400)  # 24 hours
        
    def register_tag(self, tag: str, key: str) -> None:
        """
        Register a key with a tag.
        
        Args:
            tag: Tag name
            key: Cache key
        """
        tag_key = f"tag:{tag}"
        existing_keys = self.cache_backend.get(tag_key, [])
        if key not in existing_keys:
            existing_keys.append(key)
            self.cache_backend.set(tag_key, existing_keys, 86400)  # 24 hours


class TieredCache:
    """
    Multi-tier caching system.
    
    Implements L1 (memory), L2 (Redis), L3 (database) caching.
    """
    
    def __init__(self, l1_cache: BaseCache = None, l2_cache: BaseCache = None):
        self.l1_cache = l1_cache  # In-memory cache (e.g., local dict)
        self.l2_cache = l2_cache or cache  # Redis cache
        self.l1_storage: Dict[str, CacheEntry] = {}
        self.l1_max_size = 1000
        self.l1_max_bytes = 10 * 1024 * 1024  # 10MB
        self._l1_current_bytes = 0
        
    def get(self, key: str, tier: CacheTier = None) -> Optional[Any]:
        """
        Get value from cache, checking tiers in order.
        
        Args:
            key: Cache key
            tier: Specific tier to check (None = check all)
            
        Returns:
            Cached value or None
        """
        # Check L1 first
        if tier is None or tier == CacheTier.L1:
            l1_value = self._get_l1(key)
            if l1_value is not None:
                logger.debug(f"Cache hit L1: {key}")
                return l1_value
                
        # Check L2
        if tier is None or tier == CacheTier.L2:
            l2_value = self.l2_cache.get(key)
            if l2_value is not None:
                logger.debug(f"Cache hit L2: {key}")
                # Promote to L1
                self._set_l1(key, l2_value, 300)
                return l2_value
                
        logger.debug(f"Cache miss: {key}")
        return None
        
    def set(self, key: str, value: Any, ttl: int = 300, 
            tiers: List[CacheTier] = None) -> None:
        """
        Set value in cache tiers.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds
            tiers: List of tiers to set (None = all tiers)
        """
        if tiers is None:
            tiers = [CacheTier.L1, CacheTier.L2]
            
        if CacheTier.L1 in tiers:
            self._set_l1(key, value, ttl)
            
        if CacheTier.L2 in tiers:
            self.l2_cache.set(key, value, ttl)
            
    def delete(self, key: str) -> None:
        """Delete key from all tiers."""
        self._delete_l1(key)
        self.l2_cache.delete(key)
        
    def clear(self, tier: CacheTier = None) -> None:
        """Clear cache tier(s)."""
        if tier is None or tier == CacheTier.L1:
            self.l1_storage.clear()
            self._l1_current_bytes = 0
            
        if tier is None or tier == CacheTier.L2:
            # Clear L2 (requires Redis-specific implementation)
            pass
            
    def _get_l1(self, key: str) -> Optional[Any]:
        """Get from L1 cache."""
        entry = self.l1_storage.get(key)
        if entry and not entry.is_expired:
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            return entry.value
        elif entry:
            # Remove expired entry
            self._delete_l1(key)
        return None
        
    def _set_l1(self, key: str, value: Any, ttl: int) -> None:
        """Set in L1 cache with eviction."""
        # Calculate size
        size = len(json.dumps(value, default=str).encode()) if value else 0
        
        # Evict if necessary
        self._evict_l1(size)
        
        entry = CacheEntry(
            key=key,
            value=value,
            ttl=ttl,
            size_bytes=size,
        )
        
        self.l1_storage[key] = entry
        self._l1_current_bytes += size
        
    def _delete_l1(self, key: str) -> None:
        """Delete from L1 cache."""
        entry = self.l1_storage.pop(key, None)
        if entry:
            self._l1_current_bytes -= entry.size_bytes
            
    def _evict_l1(self, required_bytes: int) -> None:
        """Evict entries from L1 cache using LRU."""
        while (len(self.l1_storage) >= self.l1_max_size or 
               self._l1_current_bytes + required_bytes > self.l1_max_bytes):
            if not self.l1_storage:
                break
                
            # Find LRU entry
            lru_key = min(self.l1_storage.keys(), 
                         key=lambda k: self.l1_storage[k].last_accessed)
            self._delete_l1(lru_key)
            
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "l1": {
                "entries": len(self.l1_storage),
                "bytes": self._l1_current_bytes,
                "max_entries": self.l1_max_size,
                "max_bytes": self.l1_max_bytes,
            },
        }


class DistributedCacheInterface:
    """
    Interface for distributed cache operations.
    
    Provides distributed cache coordination and consistency.
    """
    
    def __init__(self, cache_backend: BaseCache = None):
        self.cache_backend = cache_backend or cache
        self._locks: Dict[str, Any] = {}
        
    def get_distributed(self, key: str) -> Optional[Any]:
        """
        Get value from distributed cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        return self.cache_backend.get(key)
        
    def set_distributed(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set value in distributed cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds
            
        Returns:
            True if successful
        """
        try:
            self.cache_backend.set(key, value, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to set distributed cache: {e}")
            return False
            
    def delete_distributed(self, key: str) -> bool:
        """
        Delete from distributed cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        try:
            self.cache_backend.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete from distributed cache: {e}")
            return False
            
    def acquire_lock(self, key: str, timeout: int = 10) -> bool:
        """
        Acquire distributed lock.
        
        Args:
            key: Lock key
            timeout: Lock timeout in seconds
            
        Returns:
            True if lock acquired
        """
        lock_key = f"lock:{key}"
        # Use Redis SETNX if available, otherwise use cache.add
        try:
            acquired = self.cache_backend.add(lock_key, "1", timeout)
            if acquired:
                self._locks[key] = lock_key
            return acquired
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            return False
            
    def release_lock(self, key: str) -> bool:
        """
        Release distributed lock.
        
        Args:
            key: Lock key
            
        Returns:
            True if lock released
        """
        lock_key = f"lock:{key}"
        try:
            self.cache_backend.delete(lock_key)
            self._locks.pop(key, None)
            return True
        except Exception as e:
            logger.error(f"Failed to release lock: {e}")
            return False
            
    def get_or_set(self, key: str, value_func: Callable, 
                   ttl: int = 300, lock_timeout: int = 10) -> Any:
        """
        Get value from cache or set using value_func.
        
        Uses distributed lock to prevent cache stampede.
        
        Args:
            key: Cache key
            value_func: Function to generate value
            ttl: TTL in seconds
            lock_timeout: Lock timeout in seconds
            
        Returns:
            Cached or generated value
        """
        value = self.get_distributed(key)
        if value is not None:
            return value
            
        # Acquire lock
        if self.acquire_lock(key, lock_timeout):
            try:
                # Double-check after acquiring lock
                value = self.get_distributed(key)
                if value is not None:
                    return value
                    
                # Generate value
                value = value_func()
                self.set_distributed(key, value, ttl)
                return value
            finally:
                self.release_lock(key)
        else:
            # Wait and retry
            time.sleep(0.1)
            return self.get_distributed(key) or value_func()


class CacheOptimizer:
    """
    Cache optimization utilities.
    
    Optimizes cache performance for specific use cases.
    """
    
    @staticmethod
    def generate_cache_key(prefix: str, *args, **kwargs) -> str:
        """
        Generate a consistent cache key.
        
        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        key_parts = [prefix]
        
        if args:
            key_parts.extend(str(arg) for arg in args)
            
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend(f"{k}={v}" for k, v in sorted_kwargs)
            
        key_string = ":".join(key_parts)
        
        # Hash if too long
        if len(key_string) > 200:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:{key_hash}"
            
        return key_string
        
    @staticmethod
    def optimize_search_cache_key(query: str, filters: Dict = None, 
                                  page: int = 1, page_size: int = 20) -> str:
        """
        Generate optimized cache key for search queries.
        
        Args:
            query: Search query
            filters: Filter dictionary
            page: Page number
            page_size: Page size
            
        Returns:
            Optimized cache key
        """
        key_parts = ["search", query.lower().strip()]
        
        if filters:
            sorted_filters = sorted(filters.items())
            key_parts.extend(f"{k}:{v}" for k, v in sorted_filters)
            
        key_parts.extend([str(page), str(page_size)])
        
        return ":".join(key_parts)
        
    @staticmethod
    def optimize_recommendation_cache_key(user_id: int, 
                                         strategy: str = "default",
                                         limit: int = 10) -> str:
        """
        Generate optimized cache key for recommendations.
        
        Args:
            user_id: User ID
            strategy: Recommendation strategy
            limit: Result limit
            
        Returns:
            Optimized cache key
        """
        return f"recommend:{user_id}:{strategy}:{limit}"


class QueryCacheOptimizer:
    """
    Cache optimization for search queries.
    
    Specialized caching strategies for query performance.
    """
    
    def __init__(self, cache_backend=None):
        self.cache_backend = cache_backend or cache
        self.optimizer = CacheOptimizer()
        
    def cache_query_result(self, query: str, filters: Dict, results: List,
                          ttl: int = 300) -> None:
        """
        Cache query results with optimized key.
        
        Args:
            query: Search query
            filters: Filter dictionary
            results: Query results
            ttl: Time to live in seconds
        """
        key = self.optimizer.optimize_search_cache_key(query, filters)
        self.cache_backend.set(key, results, ttl)
        
    def get_cached_query(self, query: str, filters: Dict) -> Optional[List]:
        """
        Get cached query results.
        
        Args:
            query: Search query
            filters: Filter dictionary
            
        Returns:
            Cached results or None
        """
        key = self.optimizer.optimize_search_cache_key(query, filters)
        return self.cache_backend.get(key)
        
    def invalidate_query(self, query: str = None, filters: Dict = None) -> None:
        """
        Invalidate cached queries.
        
        Args:
            query: Query to invalidate (None = all)
            filters: Filters to match (None = all)
        """
        # This would require pattern-based invalidation
        # For now, we'll use a simpler approach
        pass


class RecommendationCacheOptimizer:
    """
    Cache optimization for recommendations.
    
    Specialized caching strategies for recommendation performance.
    """
    
    def __init__(self, cache_backend=None):
        self.cache_backend = cache_backend or cache
        self.optimizer = CacheOptimizer()
        
    def cache_recommendations(self, user_id: int, strategy: str,
                             recommendations: List, ttl: int = 600) -> None:
        """
        Cache recommendations for a user.
        
        Args:
            user_id: User ID
            strategy: Recommendation strategy
            recommendations: Recommendation results
            ttl: Time to live in seconds
        """
        key = self.optimizer.optimize_recommendation_cache_key(user_id, strategy)
        self.cache_backend.set(key, recommendations, ttl)
        
    def get_cached_recommendations(self, user_id: int,
                                   strategy: str = "default") -> Optional[List]:
        """
        Get cached recommendations.
        
        Args:
            user_id: User ID
            strategy: Recommendation strategy
            
        Returns:
            Cached recommendations or None
        """
        key = self.optimizer.optimize_recommendation_cache_key(user_id, strategy)
        return self.cache_backend.get(key)
        
    def invalidate_user_recommendations(self, user_id: int) -> None:
        """
        Invalidate all recommendations for a user.
        
        Args:
            user_id: User ID
        """
        # Invalidate all strategies for this user
        strategies = ["default", "content_based", "similarity", "hybrid"]
        for strategy in strategies:
            key = self.optimizer.optimize_recommendation_cache_key(user_id, strategy)
            self.cache_backend.delete(key)


class RankingCacheOptimizer:
    """
    Cache optimization for ranking operations.
    
    Specialized caching strategies for ranking performance.
    """
    
    def __init__(self, cache_backend=None):
        self.cache_backend = cache_backend or cache
        self.optimizer = CacheOptimizer()
        
    def cache_ranking_signals(self, entity_id: int, entity_type: str,
                             signals: Dict, ttl: int = 1800) -> None:
        """
        Cache ranking signals for an entity.
        
        Args:
            entity_id: Entity ID
            entity_type: Entity type (candidate, job, etc.)
            signals: Ranking signals
            ttl: Time to live in seconds
        """
        key = f"ranking:signals:{entity_type}:{entity_id}"
        self.cache_backend.set(key, signals, ttl)
        
    def get_cached_signals(self, entity_id: int,
                          entity_type: str) -> Optional[Dict]:
        """
        Get cached ranking signals.
        
        Args:
            entity_id: Entity ID
            entity_type: Entity type
            
        Returns:
            Cached signals or None
        """
        key = f"ranking:signals:{entity_type}:{entity_id}"
        return self.cache_backend.get(key)
        
    def cache_ranked_results(self, query_hash: str, ranked_results: List,
                            ttl: int = 300) -> None:
        """
        Cache ranked results for a query.
        
        Args:
            query_hash: Hash of the query
            ranked_results: Ranked results
            ttl: Time to live in seconds
        """
        key = f"ranking:results:{query_hash}"
        self.cache_backend.set(key, ranked_results, ttl)
        
    def get_cached_ranked_results(self, query_hash: str) -> Optional[List]:
        """
        Get cached ranked results.
        
        Args:
            query_hash: Hash of the query
            
        Returns:
            Cached ranked results or None
        """
        key = f"ranking:results:{query_hash}"
        return self.cache_backend.get(key)
        
    def invalidate_entity_signals(self, entity_id: int, entity_type: str) -> None:
        """
        Invalidate signals for an entity.
        
        Args:
            entity_id: Entity ID
            entity_type: Entity type
        """
        key = f"ranking:signals:{entity_type}:{entity_id}"
        self.cache_backend.delete(key)


class CacheWarmerManager:
    """
    Manager for cache warming operations.
    
    Coordinates warming of different cache types.
    """
    
    def __init__(self):
        self.cache_warmer = CacheWarmer()
        self.query_optimizer = QueryCacheOptimizer()
        self.rec_optimizer = RecommendationCacheOptimizer()
        self.ranking_optimizer = RankingCacheOptimizer()
        
    def warmup_popular_queries(self, queries: List[Dict[str, Any]]) -> int:
        """
        Warm up cache with popular queries.
        
        Args:
            queries: List of query dictionaries with 'query' and 'filters'
            
        Returns:
            Number of queries warmed
        """
        count = 0
        for q in queries:
            # This would execute the query and cache the result
            # For now, just increment count
            count += 1
        return count
        
    def warmup_user_recommendations(self, user_ids: List[int]) -> int:
        """
        Warm up cache with user recommendations.
        
        Args:
            user_ids: List of user IDs
            
        Returns:
            Number of users warmed
        """
        count = 0
        for user_id in user_ids:
            # This would generate and cache recommendations
            # For now, just increment count
            count += 1
        return count


# Global instances
adaptive_ttl = AdaptiveTTLStrategy()
cache_warmer = CacheWarmer()
cache_invalidator = CacheInvalidator()
tiered_cache = TieredCache()
distributed_cache = DistributedCacheInterface()
cache_optimizer = CacheOptimizer()
query_cache_optimizer = QueryCacheOptimizer()
recommendation_cache_optimizer = RecommendationCacheOptimizer()
ranking_cache_optimizer = RankingCacheOptimizer()
cache_warming_manager = CacheWarmerManager()
