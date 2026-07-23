"""
Rate Limiting Tests

Comprehensive tests for rate limiting including user, IP, API key limiting,
sliding windows, token buckets, and distributed counters.
"""

import pytest
import time
from unittest.mock import Mock, patch

from matchhire_backend.core.rate_limiting import (
    RateLimiter,
    RateLimitConfig,
    RateLimitStrategy,
    RateLimitResult,
    SlidingWindowCounter,
    TokenBucket,
    LeakyBucket,
    DistributedCounter,
    rate_limiter,
)


class TestSlidingWindowCounter:
    """Test sliding window rate limiting."""
    
    def test_sliding_window_within_limit(self):
        """Test requests within limit are allowed."""
        counter = SlidingWindowCounter()
        result = counter.check("test_key", limit=10, window=60)
        
        assert result.allowed is True
        assert result.remaining == 9
    
    def test_sliding_window_exceeded(self):
        """Test requests exceeding limit are denied."""
        counter = SlidingWindowCounter()
        
        # Make 10 requests
        for _ in range(10):
            counter.check("test_key", limit=10, window=60)
        
        # 11th request should be denied
        result = counter.check("test_key", limit=10, window=60)
        assert result.allowed is False
        assert result.remaining == 0
    
    def test_sliding_window_reset(self):
        """Test sliding window resets after time passes."""
        counter = SlidingWindowCounter()
        
        # Make 10 requests
        for _ in range(10):
            counter.check("test_key", limit=10, window=1)
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be allowed again
        result = counter.check("test_key", limit=10, window=1)
        assert result.allowed is True


class TestTokenBucket:
    """Test token bucket rate limiting."""
    
    def test_token_bucket_within_capacity(self):
        """Test requests within bucket capacity are allowed."""
        bucket = TokenBucket()
        result = bucket.check("test_key", rate=10, capacity=10)
        
        assert result.allowed is True
        assert result.remaining >= 9
    
    def test_token_bucket_refill(self):
        """Test tokens refill over time."""
        bucket = TokenBucket()
        
        # Consume all tokens
        for _ in range(10):
            bucket.check("test_key", rate=10, capacity=10)
        
        # Should be denied
        result = bucket.check("test_key", rate=10, capacity=10)
        assert result.allowed is False
        
        # Wait for refill
        time.sleep(0.2)
        
        # Should be allowed again
        result = bucket.check("test_key", rate=10, capacity=10)
        assert result.allowed is True


class TestLeakyBucket:
    """Test leaky bucket rate limiting."""
    
    def test_leaky_bucket_within_capacity(self):
        """Test requests within bucket capacity are allowed."""
        bucket = LeakyBucket()
        result = bucket.check("test_key", rate=10, capacity=10)
        
        assert result.allowed is True
    
    def test_leaky_bucket_leak(self):
        """Test bucket leaks over time."""
        bucket = LeakyBucket()
        
        # Fill bucket
        for _ in range(10):
            bucket.check("test_key", rate=1, capacity=10)
        
        # Wait for leak
        time.sleep(1.0)
        
        # Should have capacity again
        result = bucket.check("test_key", rate=1, capacity=10)
        assert result.allowed is True


class TestRateLimiter:
    """Test main rate limiter functionality."""
    
    def test_user_rate_limiting(self):
        """Test user-based rate limiting."""
        limiter = RateLimiter()
        limiter.register_config("test", RateLimitConfig(limit=5, window=60))
        
        # Make 5 requests
        for _ in range(5):
            result = limiter.check_user(1, "test")
            assert result.allowed is True
        
        # 6th request should be denied
        result = limiter.check_user(1, "test")
        assert result.allowed is False
    
    def test_ip_rate_limiting(self):
        """Test IP-based rate limiting."""
        limiter = RateLimiter()
        limiter.register_config("test", RateLimitConfig(limit=5, window=60))
        
        # Make 5 requests
        for _ in range(5):
            result = limiter.check_ip("192.168.1.1", "test")
            assert result.allowed is True
        
        # 6th request should be denied
        result = limiter.check_ip("192.168.1.1", "test")
        assert result.allowed is False
    
    def test_api_key_rate_limiting(self):
        """Test API key-based rate limiting."""
        limiter = RateLimiter()
        limiter.register_config("test", RateLimitConfig(limit=100, window=60))
        
        # Make 100 requests
        for _ in range(100):
            result = limiter.check_api_key("test_key", "test")
            assert result.allowed is True
        
        # 101st request should be denied
        result = limiter.check_api_key("test_key", "test")
        assert result.allowed is False
    
    def test_combined_rate_limiting(self):
        """Test combined rate limiting across dimensions."""
        limiter = RateLimiter()
        limiter.register_config("test", RateLimitConfig(limit=5, window=60))
        
        # Should respect most restrictive limit
        result = limiter.check_combined(user_id=1, ip_address="192.168.1.1", config_name="test")
        assert result.allowed is True
    
    def test_rate_limit_reset(self):
        """Test rate limit reset."""
        limiter = RateLimiter()
        limiter.register_config("test", RateLimitConfig(limit=5, window=60))
        
        # Make requests
        for _ in range(5):
            limiter.check_user(1, "test")
        
        # Reset
        limiter.reset_user(1)
        
        # Should be allowed again
        result = limiter.check_user(1, "test")
        assert result.allowed is True


class TestDistributedCounter:
    """Test distributed counter functionality."""
    
    def test_distributed_counter_increment(self):
        """Test distributed counter increment."""
        counter = DistributedCounter()
        
        count = counter.increment("test_key", window=60)
        assert count == 1
        
        count = counter.increment("test_key", window=60)
        assert count == 2
    
    def test_distributed_counter_reset(self):
        """Test distributed counter reset."""
        counter = DistributedCounter()
        
        counter.increment("test_key", window=60)
        counter.reset("test_key")
        
        count = counter.get("test_key")
        assert count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
