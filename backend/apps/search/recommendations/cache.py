"""
Recommendation Cache.

This module provides caching for recommendation results to improve
performance and reduce load on the search infrastructure.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json
import threading
from collections import OrderedDict


@dataclass
class CacheKey:
    """
    Cache key for recommendations.
    
    Represents a unique key for caching recommendation results.
    """
    
    recommendation_type: str
    entity_id: str
    user_id: Optional[str] = None
    recruiter_id: Optional[str] = None
    filters_hash: Optional[str] = None
    context_hash: Optional[str] = None
    
    def to_string(self) -> str:
        """Convert cache key to string."""
        key_data = {
            "recommendation_type": self.recommendation_type,
            "entity_id": self.entity_id,
            "user_id": self.user_id,
            "recruiter_id": self.recruiter_id,
            "filters_hash": self.filters_hash,
            "context_hash": self.context_hash,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    @classmethod
    def from_request(cls, request, context) -> "CacheKey":
        """
        Create cache key from request and context.
        
        Args:
            request: Recommendation request
            context: Recommendation context
            
        Returns:
            Cache key
        """
        # Hash filters
        filters_str = json.dumps(request.filters, sort_keys=True)
        filters_hash = hashlib.md5(filters_str.encode()).hexdigest()
        
        # Hash context
        context_dict = context.to_dict()
        context_str = json.dumps(context_dict, sort_keys=True)
        context_hash = hashlib.md5(context_str.encode()).hexdigest()
        
        return cls(
            recommendation_type=request.recommendation_type.value,
            entity_id=request.entity_id,
            user_id=request.user_id,
            recruiter_id=request.recruiter_id,
            filters_hash=filters_hash,
            context_hash=context_hash,
        )


@dataclass
class CacheEntry:
    """
    Cache entry for recommendation results.
    
    Contains the cached result along with metadata.
    """
    
    key: CacheKey
    value: Any
    created_at: datetime
    ttl_seconds: int
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if the cache entry is expired."""
        if self.ttl_seconds <= 0:
            return False
        
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now() > expiry_time
    
    def touch(self) -> None:
        """Update last accessed time and increment access count."""
        self.last_accessed = datetime.now()
        self.access_count += 1


@dataclass
class CacheStats:
    """Statistics for the recommendation cache."""
    
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 1000
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "size": self.size,
            "max_size": self.max_size,
            "hit_rate": self.hit_rate,
        }


class RecommendationCache:
    """
    Cache for recommendation results.
    
    Provides LRU caching with TTL support for recommendation results.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the recommendation cache.
        
        Args:
            config: Cache configuration
        """
        self._config = config or {}
        self._max_size = self._config.get("max_size", 1000)
        self._default_ttl = self._config.get("default_ttl", 300)  # 5 minutes
        
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats(max_size=self._max_size)
    
    def get(
        self,
        request,
        context,
    ) -> Optional[Any]:
        """
        Get cached recommendation result.
        
        Args:
            request: Recommendation request
            context: Recommendation context
            
        Returns:
            Cached result or None
        """
        key = CacheKey.from_request(request, context)
        key_str = key.to_string()
        
        with self._lock:
            if key_str not in self._cache:
                self._stats.misses += 1
                return None
            
            entry = self._cache[key_str]
            
            # Check if expired
            if entry.is_expired():
                del self._cache[key_str]
                self._stats.size -= 1
                self._stats.misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key_str)
            entry.touch()
            
            self._stats.hits += 1
            return entry.value
    
    def set(
        self,
        request,
        context,
        value,
        ttl: Optional[int] = None,
    ) -> None:
        """
        Cache a recommendation result.
        
        Args:
            request: Recommendation request
            context: Recommendation context
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
        """
        key = CacheKey.from_request(request, context)
        key_str = key.to_string()
        ttl = ttl or self._default_ttl
        
        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self._max_size and key_str not in self._cache:
                self._evict_lru()
            
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                ttl_seconds=ttl,
            )
            
            self._cache[key_str] = entry
            self._cache.move_to_end(key_str)
            self._stats.size = len(self._cache)
    
    def delete(
        self,
        request,
        context,
    ) -> bool:
        """
        Delete a cached recommendation result.
        
        Args:
            request: Recommendation request
            context: Recommendation context
            
        Returns:
            True if deleted, False if not found
        """
        key = CacheKey.from_request(request, context)
        key_str = key.to_string()
        
        with self._lock:
            if key_str in self._cache:
                del self._cache[key_str]
                self._stats.size = len(self._cache)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            self._stats.size = 0
    
    def invalidate_by_entity(self, entity_id: str) -> int:
        """
        Invalidate all cache entries for a specific entity.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_delete = [
                key_str for key_str, entry in self._cache.items()
                if entry.key.entity_id == entity_id
            ]
            
            for key_str in keys_to_delete:
                del self._cache[key_str]
            
            self._stats.size = len(self._cache)
            return len(keys_to_delete)
    
    def invalidate_by_user(self, user_id: str) -> int:
        """
        Invalidate all cache entries for a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_delete = [
                key_str for key_str, entry in self._cache.items()
                if entry.key.user_id == user_id
            ]
            
            for key_str in keys_to_delete:
                del self._cache[key_str]
            
            self._stats.size = len(self._cache)
            return len(keys_to_delete)
    
    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if self._cache:
            key_str, _ = self._cache.popitem(last=False)
            self._stats.evictions += 1
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key_str for key_str, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key_str in expired_keys:
                del self._cache[key_str]
            
            self._stats.size = len(self._cache)
            return len(expired_keys)
    
    def get_stats(self) -> CacheStats:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        with self._lock:
            return self._stats
    
    def get_size(self) -> int:
        """
        Get current cache size.
        
        Returns:
            Number of entries in cache
        """
        with self._lock:
            return len(self._cache)


class CandidatePoolCache:
    """
    Cache for candidate pools.
    
    Caches pre-computed candidate pools for faster recommendation generation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the candidate pool cache.
        
        Args:
            config: Cache configuration
        """
        self._config = config or {}
        self._max_size = self._config.get("max_size", 500)
        self._default_ttl = self._config.get("default_ttl", 600)  # 10 minutes
        
        self._cache: Dict[str, tuple] = {}
        self._lock = threading.RLock()
    
    def get(
        self,
        pool_key: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached candidate pool.
        
        Args:
            pool_key: Key for the candidate pool
            
        Returns:
            Cached candidate pool or None
        """
        with self._lock:
            if pool_key not in self._cache:
                return None
            
            candidates, timestamp, ttl = self._cache[pool_key]
            
            # Check if expired
            if datetime.now().timestamp() - timestamp > ttl:
                del self._cache[pool_key]
                return None
            
            return candidates
    
    def set(
        self,
        pool_key: str,
        candidates: List[Dict[str, Any]],
        ttl: Optional[int] = None,
    ) -> None:
        """
        Cache a candidate pool.
        
        Args:
            pool_key: Key for the candidate pool
            candidates: Candidate pool to cache
            ttl: Time to live in seconds
        """
        ttl = ttl or self._default_ttl
        
        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self._max_size and pool_key not in self._cache:
                # Remove oldest entry
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            
            self._cache[pool_key] = (
                candidates,
                datetime.now().timestamp(),
                ttl,
            )
    
    def clear(self) -> None:
        """Clear all cached candidate pools."""
        with self._lock:
            self._cache.clear()
    
    def get_size(self) -> int:
        """
        Get current cache size.
        
        Returns:
            Number of entries in cache
        """
        with self._lock:
            return len(self._cache)
