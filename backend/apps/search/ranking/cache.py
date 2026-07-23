"""
Ranking Cache.

This module provides caching for ranking operations to improve performance.
The cache stores computed scores, pipeline results, and fused search results.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json
import threading
from collections import OrderedDict


@dataclass
class CacheKey:
    """
    Key for cache entries.
    """
    
    entity_type: str
    query: str
    profile_name: str
    filters_hash: str
    sort_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "entity_type": self.entity_type,
            "query": self.query,
            "profile_name": self.profile_name,
            "filters_hash": self.filters_hash,
            "sort_hash": self.sort_hash,
        }
    
    def __hash__(self) -> int:
        """Generate hash for cache key."""
        key_str = json.dumps(self.to_dict(), sort_keys=True)
        return int(hashlib.md5(key_str.encode()).hexdigest(), 16)
    
    def __eq__(self, other) -> bool:
        """Check equality of cache keys."""
        if not isinstance(other, CacheKey):
            return False
        return self.to_dict() == other.to_dict()


@dataclass
class CacheEntry:
    """
    A single cache entry.
    """
    
    key: CacheKey
    value: Any
    created_at: datetime
    ttl_seconds: int
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl_seconds <= 0:
            return False
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now() > expiry_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "key": self.key.to_dict(),
            "value": self.value,
            "created_at": self.created_at.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "metadata": self.metadata,
        }


@dataclass
class CacheStats:
    """
    Statistics for cache performance.
    """
    
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 1000
    
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total
    
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 1.0 - self.hit_rate()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "size": self.size,
            "max_size": self.max_size,
            "hit_rate": self.hit_rate(),
            "miss_rate": self.miss_rate(),
        }


class RankingCache:
    """
    Cache for ranking operations.
    
    Implements an LRU cache with TTL support for storing
    ranking results, signal scores, and pipeline outputs.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize the ranking cache.
        
        Args:
            max_size: Maximum number of entries in cache
            default_ttl: Default TTL in seconds
        """
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache: OrderedDict[CacheKey, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats(max_size=max_size)
    
    def get(
        self,
        entity_type: str,
        query: str,
        profile_name: str,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            entity_type: Entity type
            query: Search query
            profile_name: Ranking profile name
            filters: Search filters
            sort: Sort conditions
            
        Returns:
            Cached value or None if not found/expired
        """
        key = self._create_key(entity_type, query, profile_name, filters, sort)
        
        with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self._cache[key]
                self._stats.misses += 1
                self._stats.size -= 1
                return None
            
            # Update access info
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            
            self._stats.hits += 1
            return entry.value
    
    def set(
        self,
        entity_type: str,
        query: str,
        profile_name: str,
        value: Any,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """
        Set a value in cache.
        
        Args:
            entity_type: Entity type
            query: Search query
            profile_name: Ranking profile name
            value: Value to cache
            filters: Search filters
            sort: Sort conditions
            ttl: TTL in seconds (uses default if None)
        """
        key = self._create_key(entity_type, query, profile_name, filters, sort)
        ttl = ttl if ttl is not None else self._default_ttl
        
        with self._lock:
            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                ttl_seconds=ttl,
                last_accessed=datetime.now(),
            )
            
            # Evict if necessary
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_lru()
            
            # Set entry
            self._cache[key] = entry
            self._cache.move_to_end(key)
            self._stats.size = len(self._cache)
    
    def delete(
        self,
        entity_type: str,
        query: str,
        profile_name: str,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        Delete a value from cache.
        
        Args:
            entity_type: Entity type
            query: Search query
            profile_name: Ranking profile name
            filters: Search filters
            sort: Sort conditions
            
        Returns:
            True if entry was deleted, False if not found
        """
        key = self._create_key(entity_type, query, profile_name, filters, sort)
        
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.size = len(self._cache)
                return True
            return False
    
    def invalidate_entity_type(self, entity_type: str) -> int:
        """
        Invalidate all cache entries for an entity type.
        
        Args:
            entity_type: Entity type to invalidate
            
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_delete = [
                key for key in self._cache.keys()
                if key.entity_type == entity_type
            ]
            
            for key in keys_to_delete:
                del self._cache[key]
            
            self._stats.size = len(self._cache)
            return len(keys_to_delete)
    
    def invalidate_profile(self, profile_name: str) -> int:
        """
        Invalidate all cache entries for a profile.
        
        Args:
            profile_name: Profile name to invalidate
            
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_delete = [
                key for key in self._cache.keys()
                if key.profile_name == profile_name
            ]
            
            for key in keys_to_delete:
                del self._cache[key]
            
            self._stats.size = len(self._cache)
            return len(keys_to_delete)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._stats.size = 0
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            keys_to_delete = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in keys_to_delete:
                del self._cache[key]
            
            self._stats.size = len(self._cache)
            return len(keys_to_delete)
    
    def get_stats(self) -> CacheStats:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                size=self._stats.size,
                max_size=self._stats.max_size,
            )
    
    def _create_key(
        self,
        entity_type: str,
        query: str,
        profile_name: str,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
    ) -> CacheKey:
        """
        Create a cache key.
        
        Args:
            entity_type: Entity type
            query: Search query
            profile_name: Ranking profile name
            filters: Search filters
            sort: Sort conditions
            
        Returns:
            Cache key
        """
        filters_hash = self._hash_dict(filters or {})
        sort_hash = self._hash_dict(sort or [])
        
        return CacheKey(
            entity_type=entity_type,
            query=query,
            profile_name=profile_name,
            filters_hash=filters_hash,
            sort_hash=sort_hash,
        )
    
    def _hash_dict(self, data: Any) -> str:
        """
        Hash a dictionary or list.
        
        Args:
            data: Data to hash
            
        Returns:
            Hash string
        """
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if self._cache:
            self._cache.popitem(last=False)
            self._stats.evictions += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cache state to dictionary representation."""
        with self._lock:
            return {
                "stats": self._stats.to_dict(),
                "size": len(self._cache),
                "max_size": self._max_size,
                "default_ttl": self._default_ttl,
            }
