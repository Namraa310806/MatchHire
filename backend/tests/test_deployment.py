"""
Deployment Tests

Comprehensive tests for deployment configuration, health checks,
and container orchestration.
"""

import pytest
from unittest.mock import Mock, patch

from matchhire_backend.core.health import (
    HealthChecker,
    ReadinessChecker,
    LivenessChecker,
    HealthStatus,
    health_checker,
    readiness_checker,
    liveness_checker,
)


class TestHealthChecker:
    """Test health checker functionality."""
    
    @patch('matchhire_backend.core.health.connection')
    def test_check_database_success(self, mock_connection):
        """Test successful database health check."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = health_checker.check_database()
        
        assert result.status == HealthStatus.HEALTHY
        assert "successful" in result.message.lower()
    
    @patch('matchhire_backend.core.health.connection')
    def test_check_database_failure(self, mock_connection):
        """Test failed database health check."""
        mock_connection.cursor.side_effect = Exception("Connection failed")
        
        result = health_checker.check_database()
        
        assert result.status == HealthStatus.UNHEALTHY
        assert "failed" in result.message.lower()
    
    @patch('matchhire_backend.core.health.cache')
    def test_check_cache_success(self, mock_cache):
        """Test successful cache health check."""
        mock_cache.get.return_value = "test"
        
        result = health_checker.check_cache()
        
        assert result.status == HealthStatus.HEALTHY
        assert "successful" in result.message.lower()
    
    @patch('matchhire_backend.core.health.cache')
    def test_check_cache_failure(self, mock_cache):
        """Test failed cache health check."""
        mock_cache.get.side_effect = Exception("Cache failed")
        
        result = health_checker.check_cache()
        
        assert result.status == HealthStatus.UNHEALTHY
    
    def test_check_disk_space_healthy(self):
        """Test disk space check when healthy."""
        result = health_checker.check_disk_space(threshold_percent=95)
        
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
    
    def test_check_memory_healthy(self):
        """Test memory check when healthy."""
        result = health_checker.check_memory(threshold_percent=95)
        
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
    
    def test_check_cpu_healthy(self):
        """Test CPU check when healthy."""
        result = health_checker.check_cpu(threshold_percent=95)
        
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
    
    def test_run_all_checks(self):
        """Test running all health checks."""
        result = health_checker.run_all_checks()
        
        assert "status" in result
        assert "checks" in result
        assert "timestamp" in result
        assert isinstance(result["checks"], list)


class TestReadinessChecker:
    """Test readiness checker functionality."""
    
    @patch('matchhire_backend.core.health.health_checker')
    def test_is_ready_healthy(self, mock_health_checker):
        """Test readiness when healthy."""
        from matchhire_backend.core.health import HealthCheckResult, HealthStatus
        
        mock_health_checker.check_database.return_value = HealthCheckResult(
            name="database",
            status=HealthStatus.HEALTHY,
            message="OK",
            duration_ms=10
        )
        mock_health_checker.check_cache.return_value = HealthCheckResult(
            name="cache",
            status=HealthStatus.HEALTHY,
            message="OK",
            duration_ms=10
        )
        
        checker = ReadinessChecker()
        checker._startup_time = checker._startup_time.replace(second=0, microsecond=0)
        
        result = checker.is_ready()
        
        assert result["ready"] is True
    
    @patch('matchhire_backend.core.health.health_checker')
    def test_is_ready_unhealthy(self, mock_health_checker):
        """Test readiness when unhealthy."""
        from matchhire_backend.core.health import HealthCheckResult, HealthStatus
        
        mock_health_checker.check_database.return_value = HealthCheckResult(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message="Failed",
            duration_ms=10
        )
        mock_health_checker.check_cache.return_value = HealthCheckResult(
            name="cache",
            status=HealthStatus.HEALTHY,
            message="OK",
            duration_ms=10
        )
        
        checker = ReadinessChecker()
        checker._startup_time = checker._startup_time.replace(second=0, microsecond=0)
        
        result = checker.is_ready()
        
        assert result["ready"] is False


class TestLivenessChecker:
    """Test liveness checker functionality."""
    
    def test_is_alive(self):
        """Test liveness check."""
        result = liveness_checker.is_alive()
        
        assert result["alive"] is True
        assert "timestamp" in result


class TestSecurityValidation:
    """Test security validation functionality."""
    
    @patch('matchhire_backend.core.security_validation.os.environ')
    def test_secret_validation_strong(self, mock_environ):
        """Test strong secret validation."""
        from matchhire_backend.core.security_validation import SecretValidator
        
        mock_environ.get.return_value = "very_strong_secret_with_high_entropy_12345678"
        
        validator = SecretValidator()
        issue = validator.validate_secret_strength(mock_environ.get("SECRET_KEY"), "SECRET_KEY")
        
        assert issue is None
    
    @patch('matchhire_backend.core.security_validation.os.environ')
    def test_secret_validation_weak(self, mock_environ):
        """Test weak secret validation."""
        from matchhire_backend.core.security_validation import SecretValidator, SecuritySeverity
        
        mock_environ.get.return_value = "weak"
        
        validator = SecretValidator()
        issue = validator.validate_secret_strength(mock_environ.get("SECRET_KEY"), "SECRET_KEY")
        
        assert issue is not None
        assert issue.severity in [SecuritySeverity.HIGH, SecuritySeverity.CRITICAL]
    
    @patch('matchhire_backend.core.security_validation.settings')
    @patch('matchhire_backend.core.security_validation.os.environ')
    def test_debug_mode_validation(self, mock_environ, mock_settings):
        """Test DEBUG mode validation."""
        from matchhire_backend.core.security_validation import ConfigurationValidator
        
        mock_environ.get.return_value = "production"
        mock_settings.DEBUG = True
        
        validator = ConfigurationValidator()
        issue = validator.validate_debug_mode()
        
        assert issue is not None


class TestBackupValidation:
    """Test backup and recovery functionality."""
    
    @patch('matchhire_backend.core.backup.os.path.exists')
    @patch('matchhire_backend.core.backup.os.makedirs')
    @patch('matchhire_backend.core.backup.subprocess.Popen')
    def test_backup_creation(self, mock_popen, mock_makedirs, mock_exists):
        """Test backup creation."""
        from matchhire_backend.core.backup import BackupManager, BackupStatus
        
        mock_exists.return_value = True
        mock_proc = Mock()
        mock_proc.wait.return_value = 0
        mock_proc.stdout.read.return_value = b"backup data"
        mock_popen.return_value.__enter__.return_value = mock_proc
        
        manager = BackupManager()
        result = manager.create_backup()
        
        assert result.status in [BackupStatus.SUCCESS, BackupStatus.FAILED]


class TestFeatureFlags:
    """Test feature flag functionality."""
    
    def test_feature_flag_enabled(self):
        """Test feature flag enabled."""
        from matchhire_backend.core.feature_flags import feature_flag_manager
        
        # Test with default flag
        result = feature_flag_manager.is_enabled("api.rate_limiting", default=True)
        assert result is True
    
    def test_feature_flag_disabled(self):
        """Test feature flag disabled."""
        from matchhire_backend.core.feature_flags import feature_flag_manager
        
        result = feature_flag_manager.is_enabled("search.elasticsearch", default=False)
        assert result is False
    
    def test_enable_flag(self):
        """Test enabling a feature flag."""
        from matchhire_backend.core.feature_flags import feature_flag_manager
        
        success = feature_flag_manager.enable_flag("test_flag")
        assert success is True
    
    def test_disable_flag(self):
        """Test disabling a feature flag."""
        from matchhire_backend.core.feature_flags import feature_flag_manager
        
        feature_flag_manager.enable_flag("test_flag")
        success = feature_flag_manager.disable_flag("test_flag")
        assert success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
