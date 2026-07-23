"""
Performance optimizations for the query engine.

This module provides query cache hooks, timeouts, cancellation,
maximum depth, maximum clauses, pagination optimization,
and large-result protection.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
import hashlib
import json


class CacheStrategy(Enum):
    """Cache strategy options."""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    NONE = "none"


@dataclass
class PerformanceConfig:
    """
    Configuration for performance optimizations.
    """
    
    query_timeout_ms: int = 30000  # 30 seconds
    max_query_depth: int = 10
    max_clauses: int = 1000
    max_result_window: int = 10000
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    cache_max_size: int = 1000
    cache_strategy: CacheStrategy = CacheStrategy.LRU
    enable_query_cancellation: bool = True
    enable_pagination_optimization: bool = True
    enable_large_result_protection: bool = True
    large_result_threshold: int = 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query_timeout_ms": self.query_timeout_ms,
            "max_query_depth": self.max_query_depth,
            "max_clauses": self.max_clauses,
            "max_result_window": self.max_result_window,
            "cache_enabled": self.cache_enabled,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "cache_max_size": self.cache_max_size,
            "cache_strategy": self.cache_strategy.value,
            "enable_query_cancellation": self.enable_query_cancellation,
            "enable_pagination_optimization": self.enable_pagination_optimization,
            "enable_large_result_protection": self.enable_large_result_protection,
            "large_result_threshold": self.large_result_threshold,
        }


@dataclass
class CacheEntry:
    """
    A single cache entry.
    """
    
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    
    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if the entry is expired."""
        return (datetime.now() - self.created_at).total_seconds() > ttl_seconds
    
    def touch(self) -> None:
        """Update access information."""
        self.access_count += 1
        self.last_accessed = datetime.now()


class QueryCache:
    """
    Cache for search query results.
    
    Implements LRU (Least Recently Used) caching strategy with TTL support.
    """
    
    def __init__(self, config: PerformanceConfig):
        """
        Initialize the query cache.
        
        Args:
            config: Performance configuration
        """
        self._config = config
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def _generate_key(
        self,
        entity_type: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
        pagination: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a cache key from query parameters.
        
        Args:
            entity_type: Entity type
            query: Search query
            filters: Query filters
            sort: Sort specifications
            pagination: Pagination parameters
            
        Returns:
            Cache key
        """
        key_data = {
            "entity_type": entity_type,
            "query": query,
            "filters": filters or {},
            "sort": sort or [],
            "pagination": pagination or {},
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(
        self,
        entity_type: str,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
        pagination: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        Get a cached result.
        
        Args:
            entity_type: Entity type
            query: Search query
            filters: Query filters
            sort: Sort specifications
            pagination: Pagination parameters
            
        Returns:
            Cached value or None
        """
        if not self._config.cache_enabled:
            return None
        
        key = self._generate_key(entity_type, query, filters, sort, pagination)
        
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                
                # Check if expired
                if entry.is_expired(self._config.cache_ttl_seconds):
                    del self._cache[key]
                    self._misses += 1
                    return None
                
                # Update access information
                entry.touch()
                self._hits += 1
                
                # Enforce max size (LRU eviction)
                self._evict_if_needed()
                
                return entry.value
            
            self._misses += 1
            return None
    
    def set(
        self,
        entity_type: str,
        query: str,
        value: Any,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
        pagination: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Cache a result.
        
        Args:
            entity_type: Entity type
            query: Search query
            value: Value to cache
            filters: Query filters
            sort: Sort specifications
            pagination: Pagination parameters
        """
        if not self._config.cache_enabled:
            return
        
        key = self._generate_key(entity_type, query, filters, sort, pagination)
        
        with self._lock:
            entry = CacheEntry(key=key, value=value)
            self._cache[key] = entry
            
            # Enforce max size
            self._evict_if_needed()
    
    def invalidate(
        self,
        entity_type: Optional[str] = None,
    ) -> None:
        """
        Invalidate cache entries.
        
        Args:
            entity_type: Entity type to invalidate (None for all)
        """
        with self._lock:
            if entity_type is None:
                self._cache.clear()
            else:
                keys_to_delete = [
                    key for key in self._cache.keys()
                    if key.startswith(entity_type)
                ]
                for key in keys_to_delete:
                    del self._cache[key]
    
    def _evict_if_needed(self) -> None:
        """Evict entries if cache is too large (LRU strategy)."""
        if len(self._cache) <= self._config.cache_max_size:
            return
        
        # Sort by last accessed time (LRU)
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        # Evict oldest entries
        entries_to_remove = len(self._cache) - self._config.cache_max_size
        for key, _ in sorted_entries[:entries_to_remove]:
            del self._cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "size": len(self._cache),
                "max_size": self._config.cache_max_size,
            }
    
    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0


class QueryOptimizer:
    """
    Optimizer for search queries.
    
    Performs query validation, optimization, and safety checks.
    """
    
    def __init__(self, config: PerformanceConfig):
        """
        Initialize the query optimizer.
        
        Args:
            config: Performance configuration
        """
        self._config = config
    
    def optimize_query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Optimize a search query.
        
        Args:
            query: Search query string
            filters: Query filters
            
        Returns:
            Optimized query parameters
        """
        optimized = {
            "query": self._optimize_querystring(query),
            "filters": self._optimize_filters(filters or {}),
        }
        
        return optimized
    
    def _optimize_querystring(self, query: str) -> str:
        """
        Optimize the query string.
        
        Args:
            query: Query string
            
        Returns:
            Optimized query string
        """
        # Trim whitespace
        query = query.strip()
        
        # Remove excessive whitespace
        query = " ".join(query.split())
        
        # Limit query length
        if len(query) > 1000:
            query = query[:1000]
        
        return query
    
    def _optimize_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize query filters.
        
        Args:
            filters: Query filters
            
        Returns:
            Optimized filters
        """
        optimized = {}
        
        for key, value in filters.items():
            # Skip None values
            if value is None:
                continue
            
            # Optimize list filters
            if isinstance(value, list):
                # Remove duplicates
                value = list(set(value))
                # Limit list size
                if len(value) > 100:
                    value = value[:100]
            
            optimized[key] = value
        
        return optimized
    
    def validate_query_depth(
        self,
        query_dict: Dict[str, Any],
        current_depth: int = 0,
    ) -> bool:
        """
        Validate query depth to prevent deep recursion.
        
        Args:
            query_dict: Query dictionary
            current_depth: Current recursion depth
            
        Returns:
            True if valid, False otherwise
        """
        if current_depth > self._config.max_query_depth:
            return False
        
        for key, value in query_dict.items():
            if isinstance(value, dict):
                if not self.validate_query_depth(value, current_depth + 1):
                    return False
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        if not self.validate_query_depth(item, current_depth + 1):
                            return False
        
        return True
    
    def validate_clause_count(
        self,
        query_dict: Dict[str, Any],
    ) -> bool:
        """
        Validate clause count to prevent excessive clauses.
        
        Args:
            query_dict: Query dictionary
            
        Returns:
            True if valid, False otherwise
        """
        clause_count = self._count_clauses(query_dict)
        return clause_count <= self._config.max_clauses
    
    def _count_clauses(self, query_dict: Dict[str, Any]) -> int:
        """
        Count clauses in a query.
        
        Args:
            query_dict: Query dictionary
            
        Returns:
            Number of clauses
        """
        count = 0
        
        for key, value in query_dict.items():
            if key in ["must", "should", "must_not", "filter", "clauses"]:
                if isinstance(value, list):
                    count += len(value)
                    for item in value:
                        if isinstance(item, dict):
                            count += self._count_clauses(item)
            elif isinstance(value, dict):
                count += self._count_clauses(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        count += self._count_clauses(item)
        
        return count
    
    def optimize_pagination(
        self,
        pagination: Dict[str, Any],
        total_results: int,
    ) -> Dict[str, Any]:
        """
        Optimize pagination parameters.
        
        Args:
            pagination: Pagination parameters
            total_results: Total number of results
            
        Returns:
            Optimized pagination
        """
        if not self._config.enable_pagination_optimization:
            return pagination
        
        optimized = pagination.copy()
        
        # Enforce max result window
        if "offset" in optimized:
            if optimized["offset"] > self._config.max_result_window:
                optimized["offset"] = self._config.max_result_window
        
        if "limit" in optimized:
            if optimized["limit"] > self._config.max_result_window:
                optimized["limit"] = self._config.max_result_window
        
        # Adjust for large result sets
        if self._config.enable_large_result_protection:
            if total_results > self._config.large_result_threshold:
                # Force smaller page size for large result sets
                if "limit" in optimized:
                    optimized["limit"] = min(optimized["limit"], 100)
        
        return optimized
    
    def check_query_complexity(
        self,
        query_dict: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Check query complexity and return metrics.
        
        Args:
            query_dict: Query dictionary
            
        Returns:
            Complexity metrics
        """
        depth = self._calculate_query_depth(query_dict)
        clauses = self._count_clauses(query_dict)
        
        return {
            "depth": depth,
            "clauses": clauses,
            "max_depth": self._config.max_query_depth,
            "max_clauses": self._config.max_clauses,
            "is_complex": depth > self._config.max_query_depth // 2 or clauses > self._config.max_clauses // 2,
        }
    
    def _calculate_query_depth(
        self,
        query_dict: Dict[str, Any],
        current_depth: int = 0,
    ) -> int:
        """
        Calculate query depth.
        
        Args:
            query_dict: Query dictionary
            current_depth: Current depth
            
        Returns:
            Maximum depth
        """
        max_depth = current_depth
        
        for value in query_dict.values():
            if isinstance(value, dict):
                depth = self._calculate_query_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        depth = self._calculate_query_depth(item, current_depth + 1)
                        max_depth = max(max_depth, depth)
        
        return max_depth
