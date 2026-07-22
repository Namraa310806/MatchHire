"""
Cache utilities for MatchHire backend.

Provides safe caching with TTL and invalidation strategies.
"""
from django.core.cache import cache
from django.conf import settings
from typing import Optional, Any, Callable
import hashlib
import json


class CacheService:
    """
    Service for safe caching with TTL and invalidation.
    
    Features:
    - Configurable TTL per cache key
    - Automatic key generation with hash
    - Safe fallback on cache miss
    - Invalidation helpers
    """
    
    # Cache TTL configurations (in seconds)
    TTL_CONFIG = {
        'dashboard_metrics': 300,  # 5 minutes
        'job_recommendations': 3600,  # 1 hour
        'public_job_list': 60,  # 1 minute
        'candidate_profile': 600,  # 10 minutes
        'job_detail': 300,  # 5 minutes
    }
    
    @classmethod
    def get_key(cls, prefix: str, *args, **kwargs) -> str:
        """
        Generate a cache key from prefix and arguments.
        
        Args:
            prefix: Cache key prefix
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key
            
        Returns:
            Cache key string
        """
        # Create a hash of the arguments
        key_parts = [prefix]
        if args:
            key_parts.extend(str(arg) for arg in args)
        if kwargs:
            # Sort kwargs for consistent key generation
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend(f"{k}={v}" for k, v in sorted_kwargs)
        
        key_string = ":".join(key_parts)
        
        # Hash if key is too long (Redis limit is 250MB but shorter is better)
        if len(key_string) > 200:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:{key_hash}"
        
        return key_string
    
    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        return cache.get(key)
    
    @classmethod
    def set(cls, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if ttl is None:
            ttl = 300  # Default 5 minutes
        
        return cache.set(key, value, ttl)
    
    @classmethod
    def get_or_set(
        cls,
        key: str,
        fallback: Callable,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get value from cache or compute and set it.
        
        Args:
            key: Cache key
            fallback: Function to compute value on cache miss
            ttl: Time to live in seconds (optional)
            
        Returns:
            Cached or computed value
        """
        value = cls.get(key)
        if value is not None:
            return value
        
        # Compute value
        value = fallback()
        if value is not None:
            cls.set(key, value, ttl)
        
        return value
    
    @classmethod
    def delete(cls, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        return cache.delete(key)
    
    @classmethod
    def delete_pattern(cls, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Note: This requires Redis backend. With other backends,
        it may not work efficiently.
        
        Args:
            pattern: Cache key pattern (e.g., "dashboard:*")
            
        Returns:
            Number of keys deleted
        """
        if settings.CACHES['default']['BACKEND'] == 'django.core.cache.backends.redis.RedisCache':
            from django.core.cache import cache
            # Use Redis pattern deletion
            client = cache.client.get_client()
            keys = client.keys(pattern)
            if keys:
                return client.delete(*keys)
        return 0
    
    @classmethod
    def invalidate_dashboard(cls, user_id: str, role: str) -> bool:
        """
        Invalidate dashboard cache for a user.
        
        Args:
            user_id: User ID
            role: User role (candidate/recruiter)
            
        Returns:
            True if successful
        """
        key = cls.get_key('dashboard', user_id, role)
        return cls.delete(key)
    
    @classmethod
    def invalidate_recommendations(cls, candidate_id: str) -> bool:
        """
        Invalidate job recommendations cache for a candidate.
        
        Args:
            candidate_id: Candidate user ID
            
        Returns:
            True if successful
        """
        key = cls.get_key('job_recommendations', candidate_id)
        return cls.delete(key)
    
    @classmethod
    def invalidate_public_jobs(cls) -> int:
        """
        Invalidate public job list cache.
        
        Returns:
            Number of keys deleted
        """
        return cls.delete_pattern('public_jobs:*')
    
    @classmethod
    def invalidate_job_detail(cls, job_id: str) -> bool:
        """
        Invalidate job detail cache.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if successful
        """
        key = cls.get_key('job_detail', job_id)
        return cls.delete(key)
    
    @classmethod
    def invalidate_candidate_profile(cls, candidate_id: str) -> bool:
        """
        Invalidate candidate profile cache.
        
        Args:
            candidate_id: Candidate user ID
            
        Returns:
            True if successful
        """
        key = cls.get_key('candidate_profile', candidate_id)
        return cls.delete(key)
