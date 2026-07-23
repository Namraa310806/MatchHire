"""
Advanced Rate Limiting Module

Implements user/IP/API key rate limiting, burst limits,
sliding windows, and distributed counters.
"""

import hashlib
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from django.core.cache import cache

logger = logging.getLogger(__name__)


class RateLimitType(Enum):
    """Rate limit types."""
    USER = "user"
    IP = "ip"
    API_KEY = "api_key"
    ENDPOINT = "endpoint"


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    limit: int
    window: int  # seconds
    burst: int = 0
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    
    @property
    def burst_limit(self) -> int:
        """Get burst limit (or regular limit if burst not set)."""
        return self.burst if self.burst > 0 else self.limit


@dataclass
class RateLimitResult:
    """Rate limit check result."""
    allowed: bool
    remaining: int
    reset_time: datetime
    limit: int
    window: int
    retry_after: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SlidingWindowCounter:
    """
    Sliding window rate limiter.
    
    Provides accurate rate limiting with sliding time windows.
    """
    
    def __init__(self, cache_backend=None):
        self.cache_backend = cache_backend or cache
        
    def check(self, key: str, limit: int, window: int) -> RateLimitResult:
        """
        Check rate limit using sliding window.
        
        Args:
            key: Rate limit key
            limit: Request limit
            window: Time window in seconds
            
        Returns:
            RateLimitResult
        """
        now = time.time()
        window_start = now - window
        
        # Get existing requests
        cache_key = f"ratelimit:sliding:{key}"
        requests = self.cache_backend.get(cache_key, [])
        
        # Filter out old requests
        requests = [req_time for req_time in requests if req_time > window_start]
        
        # Check if limit exceeded
        allowed = len(requests) < limit
        
        if allowed:
            # Add current request
            requests.append(now)
            self.cache_backend.set(cache_key, requests, window + 1)
            
        # Calculate reset time
        if requests:
            reset_time = datetime.utcfromtimestamp(requests[0] + window)
        else:
            reset_time = datetime.utcfromtimestamp(now + window)
            
        # Calculate retry after
        retry_after = None
        if not allowed and requests:
            oldest_request = requests[0]
            retry_after = max(0, oldest_request + window - now)
            
        return RateLimitResult(
            allowed=allowed,
            remaining=max(0, limit - len(requests)),
            reset_time=reset_time,
            limit=limit,
            window=window,
            retry_after=retry_after,
        )


class TokenBucket:
    """
    Token bucket rate limiter.
    
    Allows burst traffic while maintaining average rate.
    """
    
    def __init__(self, cache_backend=None):
        self.cache_backend = cache_backend or cache
        
    def check(self, key: str, rate: float, capacity: int) -> RateLimitResult:
        """
        Check rate limit using token bucket.
        
        Args:
            key: Rate limit key
            rate: Token refill rate (tokens per second)
            capacity: Bucket capacity (burst limit)
            
        Returns:
            RateLimitResult
        """
        now = time.time()
        cache_key = f"ratelimit:token:{key}"
        
        # Get current bucket state
        state = self.cache_backend.get(cache_key, {
            "tokens": capacity,
            "last_update": now,
        })
        
        # Calculate tokens to add
        time_passed = now - state["last_update"]
        tokens_to_add = time_passed * rate
        
        # Update tokens (don't exceed capacity)
        state["tokens"] = min(capacity, state["tokens"] + tokens_to_add)
        state["last_update"] = now
        
        # Check if we have tokens
        allowed = state["tokens"] >= 1
        
        if allowed:
            state["tokens"] -= 1
            
        # Save state
        self.cache_backend.set(cache_key, state, 3600)
        
        # Calculate retry after
        retry_after = None
        if not allowed:
            retry_after = (1 - state["tokens"]) / rate
            
        return RateLimitResult(
            allowed=allowed,
            remaining=int(state["tokens"]),
            reset_time=datetime.utcfromtimestamp(now + retry_after) if retry_after else datetime.utcfromtimestamp(now + 1),
            limit=int(capacity),
            window=int(capacity / rate),
            retry_after=retry_after,
        )


class LeakyBucket:
    """
    Leaky bucket rate limiter.
    
    Smooths out traffic by processing at constant rate.
    """
    
    def __init__(self, cache_backend=None):
        self.cache_backend = cache_backend or cache
        
    def check(self, key: str, rate: float, capacity: int) -> RateLimitResult:
        """
        Check rate limit using leaky bucket.
        
        Args:
            key: Rate limit key
            rate: Leak rate (requests per second)
            capacity: Bucket capacity
            
        Returns:
            RateLimitResult
        """
        now = time.time()
        cache_key = f"ratelimit:leaky:{key}"
        
        # Get current bucket state
        state = self.cache_backend.get(cache_key, {
            "queue": [],
            "last_leak": now,
        })
        
        # Leak requests
        time_passed = now - state["last_leak"]
        requests_to_leak = int(time_passed * rate)
        
        if requests_to_leak > 0:
            state["queue"] = state["queue"][requests_to_leak:]
            state["last_leak"] = now
            
        # Check if bucket has capacity
        allowed = len(state["queue"]) < capacity
        
        if allowed:
            state["queue"].append(now)
            
        # Save state
        self.cache_backend.set(cache_key, state, 3600)
        
        # Calculate retry after
        retry_after = None
        if not allowed and state["queue"]:
            retry_after = (len(state["queue"]) - capacity + 1) / rate
            
        return RateLimitResult(
            allowed=allowed,
            remaining=max(0, capacity - len(state["queue"])),
            reset_time=datetime.utcfromtimestamp(now + retry_after) if retry_after else datetime.utcfromtimestamp(now + 1),
            limit=int(capacity),
            window=int(capacity / rate),
            retry_after=retry_after,
        )


class DistributedCounter:
    """
    Distributed counter for rate limiting.
    
    Uses Redis for distributed rate limiting across multiple instances.
    """
    
    def __init__(self, cache_backend=None):
        self.cache_backend = cache_backend or cache
        
    def increment(self, key: str, window: int) -> int:
        """
        Increment counter and return new value.
        
        Args:
            key: Counter key
            window: Time window in seconds
            
        Returns:
            Current count
        """
        cache_key = f"ratelimit:counter:{key}"
        
        # Try to increment existing counter
        try:
            # This requires Redis INCR command
            # For Django cache, we'll use a simpler approach
            current = self.cache_backend.get(cache_key, 0)
            current += 1
            self.cache_backend.set(cache_key, current, window)
            return current
        except Exception:
            return 0
            
    def reset(self, key: str) -> None:
        """Reset counter."""
        cache_key = f"ratelimit:counter:{key}"
        self.cache_backend.delete(cache_key)
        
    def get(self, key: str) -> int:
        """Get current counter value."""
        cache_key = f"ratelimit:counter:{key}"
        return self.cache_backend.get(cache_key, 0)


class RateLimiter:
    """
    Main rate limiter with multiple strategies.
    
    Supports user, IP, and API key rate limiting.
    """
    
    def __init__(self, cache_backend=None):
        self.cache_backend = cache_backend or cache
        self.sliding_window = SlidingWindowCounter(cache_backend)
        self.token_bucket = TokenBucket(cache_backend)
        self.leaky_bucket = LeakyBucket(cache_backend)
        self.distributed_counter = DistributedCounter(cache_backend)
        self._configs: Dict[str, RateLimitConfig] = {}
        
    def register_config(self, name: str, config: RateLimitConfig) -> None:
        """
        Register a rate limit configuration.
        
        Args:
            name: Configuration name
            config: Rate limit configuration
        """
        self._configs[name] = config
        
    def check_user(self, user_id: int, config_name: str = "default") -> RateLimitResult:
        """
        Check rate limit for a user.
        
        Args:
            user_id: User ID
            config_name: Configuration name
            
        Returns:
            RateLimitResult
        """
        config = self._configs.get(config_name, RateLimitConfig(limit=1000, window=3600))
        key = f"user:{user_id}"
        return self._check(key, config)
        
    def check_ip(self, ip_address: str, config_name: str = "default") -> RateLimitResult:
        """
        Check rate limit for an IP address.
        
        Args:
            ip_address: IP address
            config_name: Configuration name
            
        Returns:
            RateLimitResult
        """
        config = self._configs.get(config_name, RateLimitConfig(limit=100, window=60))
        key = f"ip:{self._hash_ip(ip_address)}"
        return self._check(key, config)
        
    def check_api_key(self, api_key: str, config_name: str = "default") -> RateLimitResult:
        """
        Check rate limit for an API key.
        
        Args:
            api_key: API key
            config_name: Configuration name
            
        Returns:
            RateLimitResult
        """
        config = self._configs.get(config_name, RateLimitConfig(limit=10000, window=3600))
        key = f"apikey:{self._hash_key(api_key)}"
        return self._check(key, config)
        
    def check_endpoint(self, endpoint: str, config_name: str = "default") -> RateLimitResult:
        """
        Check rate limit for an endpoint.
        
        Args:
            endpoint: Endpoint path
            config_name: Configuration name
            
        Returns:
            RateLimitResult
        """
        config = self._configs.get(config_name, RateLimitConfig(limit=500, window=60))
        key = f"endpoint:{endpoint}"
        return self._check(key, config)
        
    def check_combined(self, user_id: int = None, ip_address: str = None,
                     api_key: str = None, endpoint: str = None,
                     config_name: str = "default") -> RateLimitResult:
        """
        Check rate limits for multiple dimensions.
        
        Args:
            user_id: User ID
            ip_address: IP address
            api_key: API key
            endpoint: Endpoint path
            config_name: Configuration name
            
        Returns:
            RateLimitResult (most restrictive limit)
        """
        results = []
        
        if user_id:
            results.append(self.check_user(user_id, config_name))
            
        if ip_address:
            results.append(self.check_ip(ip_address, config_name))
            
        if api_key:
            results.append(self.check_api_key(api_key, config_name))
            
        if endpoint:
            results.append(self.check_endpoint(endpoint, config_name))
            
        if not results:
            return RateLimitResult(
                allowed=True,
                remaining=1000,
                reset_time=datetime.utcnow() + timedelta(hours=1),
                limit=1000,
                window=3600,
            )
            
        # Return most restrictive result
        return min(results, key=lambda r: r.remaining)
        
    def _check(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        """Check rate limit based on strategy."""
        if config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return self.sliding_window.check(key, config.limit, config.window)
        elif config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            rate = config.limit / config.window
            return self.token_bucket.check(key, rate, config.burst_limit)
        elif config.strategy == RateLimitStrategy.LEAKY_BUCKET:
            rate = config.limit / config.window
            return self.leaky_bucket.check(key, rate, config.burst_limit)
        else:  # FIXED_WINDOW
            return self._check_fixed_window(key, config)
            
    def _check_fixed_window(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        """Check rate limit using fixed window."""
        now = time.time()
        window_start = int(now // config.window) * config.window
        cache_key = f"ratelimit:fixed:{key}:{window_start}"
        
        count = self.distributed_counter.increment(cache_key, config.window)
        allowed = count <= config.limit
        
        reset_time = datetime.utcfromtimestamp(window_start + config.window)
        retry_after = reset_time.timestamp() - now if not allowed else None
        
        return RateLimitResult(
            allowed=allowed,
            remaining=max(0, config.limit - count),
            reset_time=reset_time,
            limit=config.limit,
            window=config.window,
            retry_after=retry_after,
        )
        
    def _hash_ip(self, ip_address: str) -> str:
        """Hash IP address for privacy."""
        return hashlib.sha256(ip_address.encode()).hexdigest()[:16]
        
    def _hash_key(self, key: str) -> str:
        """Hash API key for storage."""
        return hashlib.sha256(key.encode()).hexdigest()[:16]
        
    def reset_user(self, user_id: int) -> None:
        """Reset rate limit for a user."""
        key = f"user:{user_id}"
        self._reset_all_strategies(key)
        
    def reset_ip(self, ip_address: str) -> None:
        """Reset rate limit for an IP."""
        key = f"ip:{self._hash_ip(ip_address)}"
        self._reset_all_strategies(key)
        
    def reset_api_key(self, api_key: str) -> None:
        """Reset rate limit for an API key."""
        key = f"apikey:{self._hash_key(api_key)}"
        self._reset_all_strategies(key)
        
    def _reset_all_strategies(self, key: str) -> None:
        """Reset all strategies for a key."""
        patterns = [
            f"ratelimit:sliding:{key}",
            f"ratelimit:token:{key}",
            f"ratelimit:leaky:{key}",
            f"ratelimit:counter:{key}",
            f"ratelimit:fixed:{key}:*",
        ]
        
        for pattern in patterns:
            if "*" in pattern:
                # This would require Redis SCAN
                pass
            else:
                self.cache_backend.delete(pattern)


class RateLimitMiddleware:
    """
    Django middleware for rate limiting.
    
    Automatically rate limits requests based on configuration.
    """
    
    def __init__(self, get_response, rate_limiter: RateLimiter = None):
        self.get_response = get_response
        self.rate_limiter = rate_limiter or RateLimiter()
        
        # Register default configurations
        self.rate_limiter.register_config("default", RateLimitConfig(limit=1000, window=3600))
        self.rate_limiter.register_config("strict", RateLimitConfig(limit=100, window=60))
        self.rate_limiter.register_config("api", RateLimitConfig(limit=10000, window=3600))
        
    def __call__(self, request):
        """Process request with rate limiting."""
        # Get identifiers
        user_id = getattr(request.user, "id", None) if hasattr(request, "user") else None
        ip_address = self._get_client_ip(request)
        api_key = request.META.get("HTTP_X_API_KEY")
        endpoint = request.path
        
        # Check rate limits
        result = self.rate_limiter.check_combined(
            user_id=user_id,
            ip_address=ip_address,
            api_key=api_key,
            endpoint=endpoint,
            config_name="default",
        )
        
        if not result.allowed:
            response = self.get_response(request)
            response.status_code = 429
            response["X-RateLimit-Limit"] = str(result.limit)
            response["X-RateLimit-Remaining"] = str(result.remaining)
            response["X-RateLimit-Reset"] = result.reset_time.isoformat()
            if result.retry_after:
                response["Retry-After"] = str(int(result.retry_after))
            return response
            
        response = self.get_response(request)
        
        # Add rate limit headers
        response["X-RateLimit-Limit"] = str(result.limit)
        response["X-RateLimit-Remaining"] = str(result.remaining)
        response["X-RateLimit-Reset"] = result.reset_time.isoformat()
        
        return response
        
    def _get_client_ip(self, request) -> str:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
        return ip


# Global rate limiter instance
rate_limiter = RateLimiter()

# Register default configurations
rate_limiter.register_config("default", RateLimitConfig(limit=1000, window=3600))
rate_limiter.register_config("strict", RateLimitConfig(limit=100, window=60))
rate_limiter.register_config("api", RateLimitConfig(limit=10000, window=3600))
rate_limiter.register_config("search", RateLimitConfig(limit=500, window=60, burst=50))
rate_limiter.register_config("matching", RateLimitConfig(limit=200, window=60))
rate_limiter.register_config("upload", RateLimitConfig(limit=30, window=3600))
