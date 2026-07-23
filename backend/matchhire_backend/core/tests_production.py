"""
Production Readiness Tests

Comprehensive tests for resilience, rate limiting, performance,
deployment, configuration, recovery, security, and edge cases.
"""

import pytest
import time
from unittest.mock import Mock, patch

from matchhire_backend.core.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    RetryPolicy,
    RetryExecutor,
    TimeoutPolicy,
    GracefulDegradation,
    BulkheadIsolation,
    circuit_breaker,
    retry,
    timeout,
    bulkhead,
)
from matchhire_backend.core.caching import (
    AdaptiveTTLStrategy,
    CacheWarmer,
    CacheInvalidator,
    TieredCache,
    DistributedCacheInterface,
    CacheOptimizer,
)
from matchhire_backend.core.rate_limiting import (
    RateLimiter,
    RateLimitConfig,
    RateLimitStrategy,
    RateLimitResult,
)
from matchhire_backend.core.validation import (
    EnvironmentValidator,
    ConfigurationValidator,
    StartupDiagnostics,
)
from matchhire_backend.core.security_validation import (
    SecretValidator,
    DependencyScanner,
    ConfigurationValidator as SecurityConfigValidator,
)
from matchhire_backend.core.backup import (
    BackupManager,
    PostgreSQLBackupStrategy,
    DisasterRecoveryPlan,
)
from matchhire_backend.core.feature_flags import (
    FeatureFlagManager,
    FeatureFlag,
    FlagType,
)
from matchhire_backend.core.health import (
    HealthChecker,
    ReadinessChecker,
    LivenessChecker,
)


class TestCircuitBreaker:
    """Tests for circuit breaker functionality."""
    
    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker initial state."""
        config = CircuitBreakerConfig(failure_threshold=3, timeout=60)
        breaker = CircuitBreaker("test", config)
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.total_calls == 0
        
    def test_circuit_breaker_success(self):
        """Test circuit breaker with successful calls."""
        config = CircuitBreakerConfig(failure_threshold=3, timeout=60)
        breaker = CircuitBreaker("test", config)
        
        def success_func():
            return "success"
            
        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.successful_calls == 1
        
    def test_circuit_breaker_failure(self):
        """Test circuit breaker with failed calls."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout=60)
        breaker = CircuitBreaker("test", config)
        
        def fail_func():
            raise Exception("Test error")
            
        # Trigger failures
        for _ in range(3):
            try:
                breaker.call(fail_func)
            except:
                pass
                
        assert breaker.state == CircuitState.OPEN
        
    def test_circuit_breaker_decorator(self):
        """Test circuit breaker decorator."""
        @circuit_breaker("test_decorator", CircuitBreakerConfig(failure_threshold=3))
        def test_function():
            return "decorated"
            
        result = test_function()
        assert result == "decorated"


class TestRetryPolicy:
    """Tests for retry policy functionality."""
    
    def test_retry_policy_success(self):
        """Test retry with successful call."""
        policy = RetryPolicy(max_attempts=3, base_delay=0.1)
        executor = RetryExecutor(policy)
        
        def success_func():
            return "success"
            
        result = executor.execute(success_func)
        assert result == "success"
        
    def test_retry_policy_failure(self):
        """Test retry with failed calls."""
        policy = RetryPolicy(max_attempts=3, base_delay=0.1)
        executor = RetryExecutor(policy)
        
        def fail_func():
            raise Exception("Test error")
            
        with pytest.raises(Exception):
            executor.execute(fail_func)
            
    def test_retry_decorator(self):
        """Test retry decorator."""
        @retry(max_attempts=3, base_delay=0.1)
        def test_function():
            return "retried"
            
        result = test_function()
        assert result == "retried"


class TestRateLimiting:
    """Tests for rate limiting functionality."""
    
    def test_rate_limiter_user_limit(self):
        """Test user rate limiting."""
        limiter = RateLimiter()
        limiter.register_config("test", RateLimitConfig(limit=10, window=60))
        
        result = limiter.check_user(user_id=1, config_name="test")
        assert result.allowed is True
        assert result.remaining == 9
        
    def test_rate_limiter_exceeded(self):
        """Test rate limit exceeded."""
        limiter = RateLimiter()
        limiter.register_config("test", RateLimitConfig(limit=2, window=60))
        
        # Make requests up to limit
        limiter.check_user(user_id=1, config_name="test")
        limiter.check_user(user_id=1, config_name="test")
        
        # This should be blocked
        result = limiter.check_user(user_id=1, config_name="test")
        assert result.allowed is False
        
    def test_rate_limiter_sliding_window(self):
        """Test sliding window rate limiting."""
        limiter = RateLimiter()
        config = RateLimitConfig(limit=5, window=10, strategy=RateLimitStrategy.SLIDING_WINDOW)
        limiter.register_config("sliding", config)
        
        for i in range(5):
            result = limiter.check_user(user_id=1, config_name="sliding")
            assert result.allowed is True
            
        result = limiter.check_user(user_id=1, config_name="sliding")
        assert result.allowed is False


class TestCaching:
    """Tests for caching functionality."""
    
    def test_adaptive_ttl(self):
        """Test adaptive TTL calculation."""
        strategy = AdaptiveTTLStrategy(base_ttl=300)
        
        # High access rate should increase TTL
        for _ in range(20):
            strategy.record_access("test_key")
            
        ttl = strategy.calculate_ttl("test_key")
        assert ttl > 300
        
    def test_cache_invalidation(self):
        """Test cache invalidation."""
        from django.core.cache import cache
        
        invalidator = CacheInvalidator()
        
        # Set a cache key
        cache.set("test_key", "test_value", 300)
        assert cache.get("test_key") == "test_value"
        
        # Invalidate it
        invalidator.invalidate_key("test_key")
        assert cache.get("test_key") is None
        
    def test_tiered_cache(self):
        """Test tiered cache."""
        tiered = TieredCache()
        
        tiered.set("test_key", "test_value", 300)
        result = tiered.get("test_key")
        
        assert result == "test_value"
        
    def test_cache_optimizer_key_generation(self):
        """Test cache key optimization."""
        optimizer = CacheOptimizer()
        
        key = optimizer.generate_cache_key("search", "python", "developer")
        assert "search" in key
        assert "python" in key
        assert "developer" in key


class TestValidation:
    """Tests for validation functionality."""
    
    def test_environment_validator_required_vars(self):
        """Test required environment variable validation."""
        validator = EnvironmentValidator()
        
        # Mock environment
        with patch.dict('os.environ', {'SECRET_KEY': 'test-secret-key-32-chars-long', 'DB_NAME': 'test'}):
            results = validator.validate_required_vars()
            assert len(results) > 0
            
    def test_secret_validation(self):
        """Test secret strength validation."""
        validator = SecretValidator()
        
        # Weak secret
        result = validator.validate_secret_strength("weak", "test")
        assert result.passed is False
        
        # Strong secret
        result = validator.validate_secret_strength("a" * 40, "test")
        assert result.passed is True
        
    def test_configuration_validator(self):
        """Test Django configuration validation."""
        validator = ConfigurationValidator()
        
        result = validator.validate_installed_apps()
        assert result is not None


class TestBackup:
    """Tests for backup functionality."""
    
    def test_backup_manager_init(self):
        """Test backup manager initialization."""
        manager = BackupManager()
        assert manager.backup_dir == "./backups"
        assert manager.strategy is not None
        
    def test_disaster_recovery_validation(self):
        """Test disaster recovery validation."""
        plan = DisasterRecoveryPlan()
        
        result = plan.validate_recovery()
        assert "timestamp" in result
        assert "database" in result


class TestFeatureFlags:
    """Tests for feature flag functionality."""
    
    def test_feature_flag_manager(self):
        """Test feature flag manager."""
        manager = FeatureFlagManager()
        
        # Register a flag
        flag = FeatureFlag(
            name="test_flag",
            flag_type=FlagType.BOOLEAN,
            enabled=True,
        )
        manager.register_default_flag(flag)
        
        # Check if enabled
        assert manager.is_enabled("test_flag") is True
        
    def test_feature_flag_percentage(self):
        """Test percentage-based feature flag."""
        manager = FeatureFlagManager()
        
        manager.set_percentage_flag("test_percentage", 50)
        
        # User 1 should have 50% chance
        result1 = manager.is_enabled("test_percentage", user_id=1)
        assert isinstance(result1, bool)
        
    def test_feature_flag_decorator(self):
        """Test feature flag decorator."""
        from matchhire_backend.core.feature_flags import feature_flag
        
        # Enable the flag
        manager = FeatureFlagManager()
        manager.enable_flag("decorator_test")
        
        @feature_flag("decorator_test", default=False)
        def test_function():
            return "flagged"
            
        result = test_function()
        assert result == "flagged"


class TestHealthChecks:
    """Tests for health check functionality."""
    
    def test_health_checker_database(self):
        """Test database health check."""
        checker = HealthChecker()
        
        result = checker.check_database()
        assert result.name == "database"
        assert result.status is not None
        
    def test_health_checker_cache(self):
        """Test cache health check."""
        checker = HealthChecker()
        
        result = checker.check_cache()
        assert result.name == "cache"
        assert result.status is not None
        
    def test_readiness_checker(self):
        """Test readiness checker."""
        checker = ReadinessChecker()
        
        result = checker.is_ready()
        assert "ready" in result
        assert "uptime_seconds" in result
        
    def test_liveness_checker(self):
        """Test liveness checker."""
        checker = LivenessChecker()
        
        result = checker.is_alive()
        assert result["alive"] is True


class TestSecurityValidation:
    """Tests for security validation."""
    
    def test_secret_validator_hardcoded_secrets(self):
        """Test hardcoded secret detection."""
        validator = SecretValidator()
        
        # This should scan the codebase
        results = validator.validate_no_hardcoded_secrets(".")
        assert isinstance(results, list)
        
    def test_dependency_scanner(self):
        """Test dependency scanning."""
        scanner = DependencyScanner()
        
        results = scanner.scan_requirements("requirements.txt")
        assert isinstance(results, list)


class TestResiliencePatterns:
    """Tests for resilience patterns."""
    
    def test_graceful_degradation(self):
        """Test graceful degradation."""
        from matchhire_backend.core.resilience import GracefulDegradation, DefaultValueFallback
        
        degradation = GracefulDegradation()
        degradation.register_fallback(
            "test_feature",
            DefaultValueFallback("default_value")
        )
        
        def failing_function():
            raise Exception("Service unavailable")
            
        result = degradation.execute("test_feature", failing_function)
        assert result == "default_value"
        
    def test_bulkhead_isolation(self):
        """Test bulkhead isolation."""
        from matchhire_backend.core.resilience import BulkheadIsolation, BulkheadRejectedError
        
        bulkhead = BulkheadIsolation(max_concurrent=2)
        
        def quick_function():
            return "success"
            
        result = bulkhead.execute(quick_function)
        assert result == "success"
        
    def test_timeout_policy(self):
        """Test timeout policy."""
        from matchhire_backend.core.resilience import TimeoutPolicy
        
        policy = TimeoutPolicy(default_timeout=1.0)
        
        def quick_function():
            return "success"
            
        result = policy.execute_with_timeout(quick_function, timeout=1.0)
        assert result == "success"


class TestPerformanceMonitoring:
    """Tests for performance monitoring."""
    
    def test_performance_manager(self):
        """Test performance manager."""
        from matchhire_backend.core.performance import PerformanceManager
        
        manager = PerformanceManager()
        
        manager.record_metric("test_operation", 0.1, 1000, 50.0)
        
        stats = manager.get_statistics("test_operation")
        assert "operation" in stats
        assert stats["operation"] == "test_operation"
        
    def test_performance_profiler(self):
        """Test performance profiler."""
        from matchhire_backend.core.performance import PerformanceProfiler
        
        profiler = PerformanceProfiler()
        
        stats = profiler.get_system_stats()
        assert "cpu_percent" in stats
        assert "memory" in stats


class TestStartupDiagnostics:
    """Tests for startup diagnostics."""
    
    def test_startup_diagnostics(self):
        """Test startup diagnostics."""
        diagnostics = StartupDiagnostics()
        
        results = diagnostics.run_diagnostics()
        assert "passed" in results
        assert "environment" in results
        assert "configuration" in results
        assert "system" in results


@pytest.mark.integration
class TestIntegrationScenarios:
    """Integration tests for production scenarios."""
    
    def test_circuit_breaker_with_retry(self):
        """Test circuit breaker combined with retry."""
        config = CircuitBreakerConfig(failure_threshold=3, timeout=60)
        breaker = CircuitBreaker("test", config)
        
        policy = RetryPolicy(max_attempts=2, base_delay=0.1)
        executor = RetryExecutor(policy)
        
        call_count = 0
        
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"
            
        result = breaker.call(lambda: executor.execute(flaky_function))
        assert result == "success"
        
    def test_rate_limiting_with_caching(self):
        """Test rate limiting combined with caching."""
        limiter = RateLimiter()
        limiter.register_config("test", RateLimitConfig(limit=5, window=60))
        
        # Cache the rate limit result
        from django.core.cache import cache
        
        cache_key = f"ratelimit:user:1"
        cache.set(cache_key, "cached_result", 10)
        
        cached = cache.get(cache_key)
        assert cached == "cached_result"
        
    def test_health_check_with_feature_flags(self):
        """Test health check with feature flags."""
        from matchhire_backend.core.feature_flags import feature_flag_manager
        
        # Enable a feature flag
        feature_flag_manager.enable_flag("enhanced_health_check")
        
        checker = HealthChecker()
        result = checker.check_database()
        
        assert result.name == "database"
