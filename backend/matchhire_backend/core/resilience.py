"""
Resilience Patterns Module

Implements circuit breakers, retry policies, timeout policies,
fallback strategies, graceful degradation, bulkhead isolation,
and request cancellation.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from threading import Lock, Semaphore
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: int = 60  # seconds
    expected_exception: Exception = Exception


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_transitions: List[Dict[str, Any]] = field(default_factory=list)


class CircuitBreaker:
    """
    Circuit breaker implementation.
    
    Prevents cascading failures by failing fast when a service is down.
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._lock = Lock()
        self._stats = CircuitBreakerStats()
        
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state
        
    @property
    def stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        return self._stats
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to(CircuitState.HALF_OPEN)
                    logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
                else:
                    self._stats.total_calls += 1
                    self._stats.failed_calls += 1
                    raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")
                    
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise
            
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset."""
        if self._last_failure_time is None:
            return True
            
        elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
        return elapsed >= self.config.timeout
        
    def _on_success(self) -> None:
        """Handle successful call."""
        with self._lock:
            self._stats.total_calls += 1
            self._stats.successful_calls += 1
            self._stats.last_success_time = datetime.utcnow()
            
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
                    self._success_count = 0
                    self._failure_count = 0
                    logger.info(f"Circuit breaker {self.name} transitioning to CLOSED")
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0
                
    def _on_failure(self, exception: Exception) -> None:
        """Handle failed call."""
        with self._lock:
            self._stats.total_calls += 1
            self._stats.failed_calls += 1
            self._stats.last_failure_time = datetime.utcnow()
            
            if isinstance(exception, self.config.expected_exception):
                self._failure_count += 1
                
                if self._state == CircuitState.HALF_OPEN:
                    self._transition_to(CircuitState.OPEN)
                    self._success_count = 0
                    logger.warning(f"Circuit breaker {self.name} transitioning to OPEN")
                elif self._failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
                    logger.warning(f"Circuit breaker {self.name} transitioning to OPEN")
                    
    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state."""
        old_state = self._state
        self._state = new_state
        self._stats.state_transitions.append({
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            logger.info(f"Circuit breaker {self.name} reset to CLOSED")


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


class RetryPolicy:
    """
    Retry policy with configurable backoff strategy.
    """
    
    def __init__(self, max_attempts: int = 3, 
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_factor: float = 2.0,
                 jitter: bool = True):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        
    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given attempt.
        
        Args:
            attempt: Attempt number (1-indexed)
            
        Returns:
            Delay in seconds
        """
        delay = self.base_delay * (self.backoff_factor ** (attempt - 1))
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)
            
        return delay
        
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if operation should be retried.
        
        Args:
            exception: Exception that occurred
            attempt: Current attempt number
            
        Returns:
            True if should retry
        """
        return attempt < self.max_attempts


class RetryExecutor:
    """
    Executes operations with retry logic.
    """
    
    def __init__(self, policy: RetryPolicy = None):
        self.policy = policy or RetryPolicy()
        
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        last_exception = None
        
        for attempt in range(1, self.policy.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if not self.policy.should_retry(e, attempt):
                    logger.error(f"Retry exhausted after {attempt} attempts")
                    raise
                    
                delay = self.policy.get_delay(attempt)
                logger.warning(f"Retry attempt {attempt}/{self.policy.max_attempts} "
                             f"after {delay:.2f}s delay: {e}")
                time.sleep(delay)
                
        raise last_exception


class TimeoutPolicy:
    """
    Timeout policy for operations.
    """
    
    def __init__(self, default_timeout: float = 30.0):
        self.default_timeout = default_timeout
        self._timeouts: Dict[str, float] = {}
        
    def set_timeout(self, operation: str, timeout: float) -> None:
        """
        Set timeout for a specific operation.
        
        Args:
            operation: Operation name
            timeout: Timeout in seconds
        """
        self._timeouts[operation] = timeout
        
    def get_timeout(self, operation: str) -> float:
        """
        Get timeout for an operation.
        
        Args:
            operation: Operation name
            
        Returns:
            Timeout in seconds
        """
        return self._timeouts.get(operation, self.default_timeout)
        
    def execute_with_timeout(self, func: Callable, operation: str = None,
                            timeout: float = None, *args, **kwargs) -> Any:
        """
        Execute function with timeout.
        
        Args:
            func: Function to execute
            operation: Operation name for timeout lookup
            timeout: Override timeout
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        if timeout is None:
            timeout = self.get_timeout(operation or "default")
            
        # Use signal-based timeout for Unix, thread-based for cross-platform
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                future.cancel()
                raise TimeoutError(f"Operation {operation or 'default'} timed out after {timeout}s")


class FallbackStrategy(ABC):
    """Abstract base class for fallback strategies."""
    
    @abstractmethod
    def execute(self, original_func: Callable, *args, **kwargs) -> Any:
        """
        Execute fallback strategy.
        
        Args:
            original_func: Original function that failed
            *args: Original arguments
            **kwargs: Original keyword arguments
            
        Returns:
            Fallback result
        """
        pass


class DefaultValueFallback(FallbackStrategy):
    """Fallback that returns a default value."""
    
    def __init__(self, default_value: Any):
        self.default_value = default_value
        
    def execute(self, original_func: Callable, *args, **kwargs) -> Any:
        return self.default_value


class CachedFallback(FallbackStrategy):
    """Fallback that returns cached value."""
    
    def __init__(self, cache_key: str, cache_backend=None):
        self.cache_key = cache_key
        self.cache_backend = cache_backend
        
    def execute(self, original_func: Callable, *args, **kwargs) -> Any:
        if self.cache_backend:
            return self.cache_backend.get(self.cache_key)
        return None


class AlternativeProviderFallback(FallbackStrategy):
    """Fallback that uses an alternative provider."""
    
    def __init__(self, alternative_func: Callable):
        self.alternative_func = alternative_func
        
    def execute(self, original_func: Callable, *args, **kwargs) -> Any:
        return self.alternative_func(*args, **kwargs)


class GracefulDegradation:
    """
    Graceful degradation manager.
    
    Degrades functionality gracefully when services fail.
    """
    
    def __init__(self):
        self._fallbacks: Dict[str, FallbackStrategy] = {}
        self._degraded_features: set = set()
        
    def register_fallback(self, feature: str, strategy: FallbackStrategy) -> None:
        """
        Register fallback for a feature.
        
        Args:
            feature: Feature name
            strategy: Fallback strategy
        """
        self._fallbacks[feature] = strategy
        
    def execute(self, feature: str, func: Callable, 
                *args, **kwargs) -> Any:
        """
        Execute function with graceful degradation.
        
        Args:
            feature: Feature name
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or fallback result
        """
        try:
            result = func(*args, **kwargs)
            if feature in self._degraded_features:
                self._degraded_features.remove(feature)
                logger.info(f"Feature {feature} recovered")
            return result
        except Exception as e:
            logger.warning(f"Feature {feature} failed, using fallback: {e}")
            self._degraded_features.add(feature)
            
            fallback = self._fallbacks.get(feature)
            if fallback:
                return fallback.execute(func, *args, **kwargs)
            else:
                raise
                
    def is_degraded(self, feature: str) -> bool:
        """Check if feature is currently degraded."""
        return feature in self._degraded_features
        
    def get_degraded_features(self) -> set:
        """Get set of degraded features."""
        return self._degraded_features.copy()


class BulkheadIsolation:
    """
    Bulkhead pattern implementation.
    
    Isolates resources to prevent cascading failures.
    """
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._semaphore = Semaphore(max_concurrent)
        self._active_count = 0
        self._rejected_count = 0
        self._lock = Lock()
        
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with bulkhead isolation.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            BulkheadRejectedError: If bulkhead is full
        """
        if not self._semaphore.acquire(blocking=False):
            with self._lock:
                self._rejected_count += 1
            raise BulkheadRejectedError(
                f"Bulkhead rejected: max concurrent {self.max_concurrent} exceeded"
            )
            
        try:
            with self._lock:
                self._active_count += 1
                
            return func(*args, **kwargs)
        finally:
            with self._lock:
                self._active_count -= 1
            self._semaphore.release()
            
    def get_stats(self) -> Dict[str, Any]:
        """Get bulkhead statistics."""
        with self._lock:
            return {
                "max_concurrent": self.max_concurrent,
                "active_count": self._active_count,
                "rejected_count": self._rejected_count,
                "available_slots": self.max_concurrent - self._active_count,
            }


class BulkheadRejectedError(Exception):
    """Raised when bulkhead rejects request."""
    pass


class RequestCancellation:
    """
    Request cancellation support.
    
    Allows cancellation of long-running operations.
    """
    
    def __init__(self):
        self._cancellations: Dict[str, bool] = {}
        self._lock = Lock()
        
    def register_request(self, request_id: str) -> None:
        """
        Register a request for cancellation tracking.
        
        Args:
            request_id: Unique request identifier
        """
        with self._lock:
            self._cancellations[request_id] = False
            
    def cancel_request(self, request_id: str) -> None:
        """
        Cancel a request.
        
        Args:
            request_id: Request identifier to cancel
        """
        with self._lock:
            if request_id in self._cancellations:
                self._cancellations[request_id] = True
                logger.info(f"Request {request_id} cancelled")
                
    def is_cancelled(self, request_id: str) -> bool:
        """
        Check if request is cancelled.
        
        Args:
            request_id: Request identifier
            
        Returns:
            True if cancelled
        """
        with self._lock:
            return self._cancellations.get(request_id, False)
            
    def unregister_request(self, request_id: str) -> None:
        """
        Unregister a request.
        
        Args:
            request_id: Request identifier
        """
        with self._lock:
            self._cancellations.pop(request_id, None)
            
    def execute_cancellable(self, request_id: str, func: Callable,
                           *args, **kwargs) -> Any:
        """
        Execute function with cancellation support.
        
        Args:
            request_id: Request identifier
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CancelledError: If request was cancelled
        """
        self.register_request(request_id)
        
        try:
            # Check if already cancelled
            if self.is_cancelled(request_id):
                raise CancelledError(f"Request {request_id} was cancelled")
                
            return func(*args, **kwargs)
        finally:
            self.unregister_request(request_id)


class CancelledError(Exception):
    """Raised when request is cancelled."""
    pass


# Decorators for easy use
def circuit_breaker(name: str, config: CircuitBreakerConfig = None):
    """
    Decorator for circuit breaker protection.
    
    Args:
        name: Circuit breaker name
        config: Circuit breaker configuration
    """
    breaker = CircuitBreaker(name, config)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


def retry(max_attempts: int = 3, base_delay: float = 1.0, 
          backoff_factor: float = 2.0):
    """
    Decorator for retry logic.
    
    Args:
        max_attempts: Maximum retry attempts
        base_delay: Base delay in seconds
        backoff_factor: Backoff multiplier
    """
    policy = RetryPolicy(max_attempts, base_delay, backoff_factor=backoff_factor)
    executor = RetryExecutor(policy)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return executor.execute(func, *args, **kwargs)
        return wrapper
    return decorator


def timeout(seconds: float):
    """
    Decorator for timeout protection.
    
    Args:
        seconds: Timeout in seconds
    """
    policy = TimeoutPolicy(default_timeout=seconds)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return policy.execute_with_timeout(func, timeout=seconds, *args, **kwargs)
        return wrapper
    return decorator


def bulkhead(max_concurrent: int = 10):
    """
    Decorator for bulkhead isolation.
    
    Args:
        max_concurrent: Maximum concurrent executions
    """
    isolation = BulkheadIsolation(max_concurrent)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return isolation.execute(func, *args, **kwargs)
        return wrapper
    return decorator


# Global instances
circuit_breakers: Dict[str, CircuitBreaker] = {}
graceful_degradation = GracefulDegradation()
request_cancellation = RequestCancellation()


def get_circuit_breaker(name: str, 
                        config: CircuitBreakerConfig = None) -> CircuitBreaker:
    """
    Get or create circuit breaker by name.
    
    Args:
        name: Circuit breaker name
        config: Configuration (only used on creation)
        
    Returns:
        CircuitBreaker instance
    """
    if name not in circuit_breakers:
        circuit_breakers[name] = CircuitBreaker(name, config)
    return circuit_breakers[name]
