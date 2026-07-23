"""
Resilience Tests

Comprehensive tests for resilience patterns including circuit breakers,
retry policies, graceful degradation, and bulkhead isolation.
"""

import pytest
import time
from unittest.mock import Mock, patch

from matchhire_backend.core.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    RetryPolicy,
    RetryExecutor,
    TimeoutPolicy,
    GracefulDegradation,
    DefaultValueFallback,
    BulkheadIsolation,
    BulkheadRejectedError,
    get_circuit_breaker,
)


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        config = CircuitBreakerConfig(failure_threshold=3, timeout=60)
        breaker = CircuitBreaker("test", config)
        
        def success_func():
            return "success"
        
        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state.name == "closed"
    
    def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after threshold failures."""
        config = CircuitBreakerConfig(failure_threshold=3, timeout=60)
        breaker = CircuitBreaker("test", config)
        
        def failing_func():
            raise Exception("Test failure")
        
        # Trigger failures
        for _ in range(3):
            with pytest.raises(Exception):
                breaker.call(failing_func)
        
        # Circuit should be open
        assert breaker.state.name == "open"
        
        # Calls should fail fast
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(failing_func)
    
    def test_circuit_breaker_half_open_state(self):
        """Test circuit breaker transitions to half-open after timeout."""
        config = CircuitBreakerConfig(failure_threshold=3, timeout=1)
        breaker = CircuitBreaker("test", config)
        
        def failing_func():
            raise Exception("Test failure")
        
        # Trigger failures to open circuit
        for _ in range(3):
            with pytest.raises(Exception):
                breaker.call(failing_func)
        
        assert breaker.state.name == "open"
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Next call should attempt reset
        def success_func():
            return "success"
        
        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state.name == "closed"
    
    def test_circuit_breaker_reset(self):
        """Test circuit breaker reset."""
        breaker = get_circuit_breaker("test_reset")
        breaker.reset()
        assert breaker.state.name == "closed"
        assert breaker._failure_count == 0


class TestRetryPolicy:
    """Test retry policy functionality."""
    
    def test_retry_policy_success(self):
        """Test retry succeeds on first attempt."""
        policy = RetryPolicy(max_attempts=3, base_delay=0.1)
        executor = RetryExecutor(policy)
        
        def success_func():
           return "success"
        
        result = executor.execute(success_func)
        assert result == "success"
    
    def test_retry_policy_with_backoff(self):
        """Test retry with exponential backoff."""
        policy = RetryPolicy(max_attempts=3, base_delay=0.1, backoff_factor=2)
        executor = RetryExecutor(policy)
        
        call_count = 0
        
        def eventually_success_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Not yet")
            return "success"
        
        result = executor.execute(eventually_success_func)
        assert result == "success"
        assert call_count == 3
    
    def test_retry_policy_exhausted(self):
        """Test retry exhausts all attempts."""
        policy = RetryPolicy(max_attempts=3, base_delay=0.1)
        executor = RetryExecutor(policy)
        
        def always_fail_func():
            raise Exception("Always fails")
        
        with pytest.raises(Exception):
            executor.execute(always_fail_func)
    
    def test_retry_delay_calculation(self):
        """Test retry delay calculation."""
        policy = RetryPolicy(max_attempts=5, base_delay=1.0, backoff_factor=2, jitter=False)
        
        delay1 = policy.get_delay(1)
        delay2 = policy.get_delay(2)
        delay3 = policy.get_delay(3)
        
        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0


class TestTimeoutPolicy:
    """Test timeout policy functionality."""
    
    def test_timeout_success(self):
        """Test timeout with fast function."""
        policy = TimeoutPolicy(default_timeout=5.0)
        
        def fast_func():
            return "success"
        
        result = policy.execute_with_timeout(fast_func, timeout=1.0)
        assert result == "success"
    
    def test_timeout_exceeded(self):
        """Test timeout exceeded."""
        policy = TimeoutPolicy(default_timeout=0.1)
        
        def slow_func():
            time.sleep(1.0)
            return "success"
        
        with pytest.raises(TimeoutError):
            policy.execute_with_timeout(slow_func, timeout=0.1)


class TestGracefulDegradation:
    """Test graceful degradation functionality."""
    
    def test_graceful_degradation_success(self):
        """Test graceful degradation with successful function."""
        degradation = GracefulDegradation()
        degradation.register_fallback("test", DefaultValueFallback("fallback"))
        
        def success_func():
            return "success"
        
        result = degradation.execute("test", success_func)
        assert result == "success"
        assert not degradation.is_degraded("test")
    
    def test_graceful_degradation_fallback(self):
        """Test graceful degradation uses fallback."""
        degradation = GracefulDegradation()
        degradation.register_fallback("test", DefaultValueFallback("fallback"))
        
        def failing_func():
            raise Exception("Test failure")
        
        result = degradation.execute("test", failing_func)
        assert result == "fallback"
        assert degradation.is_degraded("test")
    
    def test_graceful_degradation_recovery(self):
        """Test graceful degradation recovery."""
        degradation = GracefulDegradation()
        degradation.register_fallback("test", DefaultValueFallback("fallback"))
        
        call_count = 0
        
        def eventually_success_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First failure")
            return "success"
        
        # First call fails, uses fallback
        result1 = degradation.execute("test", eventually_success_func)
        assert result1 == "fallback"
        
        # Second call succeeds, recovers
        result2 = degradation.execute("test", eventually_success_func)
        assert result2 == "success"
        assert not degradation.is_degraded("test")


class TestBulkheadIsolation:
    """Test bulkhead isolation functionality."""
    
    def test_bulkhead_within_limit(self):
        """Test bulkhead within concurrency limit."""
        bulkhead = BulkheadIsolation(max_concurrent=2)
        
        def fast_func():
            return "success"
        
        result = bulkhead.execute(fast_func)
        assert result == "success"
    
    def test_bulkhead_exceeded(self):
        """Test bulkhead rejects when limit exceeded."""
        bulkhead = BulkheadIsolation(max_concurrent=2)
        
        def slow_func():
            time.sleep(1.0)
            return "success"
        
        # Start 2 slow operations
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(bulkhead.execute, slow_func) for _ in range(2)]
            
            # Third call should be rejected
            with pytest.raises(BulkheadRejectedError):
                bulkhead.execute(slow_func)
    
    def test_bulkhead_stats(self):
        """Test bulkhead statistics."""
        bulkhead = BulkheadIsolation(max_concurrent=5)
        
        def fast_func():
            return "success"
        
        bulkhead.execute(fast_func)
        
        stats = bulkhead.get_stats()
        assert stats["max_concurrent"] == 5
        assert stats["active_count"] == 0
        assert stats["available_slots"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
