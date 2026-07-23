"""
Tests for Health Monitoring.
"""

import unittest
from apps.search.observability.core import ObservabilityConfig, ObservabilityComponent
from apps.search.observability.health import (
    HealthStatus,
    HealthCheck,
    HealthCheckResult,
    ComponentHealth,
    HealthMonitor,
)


class TestHealthCheck(unittest.TestCase):
    """Tests for HealthCheck."""
    
    def test_health_check_creation(self):
        """Test health check creation."""
        check = HealthCheck(
            name="test_check",
            component=ObservabilityComponent.SEARCH,
            check_function=lambda: {"status": "healthy"},
        )
        
        self.assertEqual(check.name, "test_check")
        self.assertEqual(check.component, ObservabilityComponent.SEARCH)
        self.assertTrue(check.enabled)
    
    def test_health_check_to_dict(self):
        """Test health check serialization."""
        check = HealthCheck(
            name="test_check",
            component=ObservabilityComponent.SEARCH,
            check_function=lambda: {"status": "healthy"},
        )
        check_dict = check.to_dict()
        
        self.assertEqual(check_dict["name"], "test_check")
        self.assertEqual(check_dict["component"], "search")


class TestHealthCheckResult(unittest.TestCase):
    """Tests for HealthCheckResult."""
    
    def test_result_creation(self):
        """Test health check result creation."""
        result = HealthCheckResult(
            name="test_check",
            component=ObservabilityComponent.SEARCH,
            status=HealthStatus.HEALTHY,
        )
        
        self.assertEqual(result.name, "test_check")
        self.assertEqual(result.status, HealthStatus.HEALTHY)
    
    def test_result_to_dict(self):
        """Test health check result serialization."""
        result = HealthCheckResult(
            name="test_check",
            component=ObservabilityComponent.SEARCH,
            status=HealthStatus.UNHEALTHY,
            message="Check failed",
        )
        result_dict = result.to_dict()
        
        self.assertEqual(result_dict["name"], "test_check")
        self.assertEqual(result_dict["status"], "unhealthy")
        self.assertEqual(result_dict["message"], "Check failed")


class TestComponentHealth(unittest.TestCase):
    """Tests for ComponentHealth."""
    
    def test_component_health_creation(self):
        """Test component health creation."""
        health = ComponentHealth(component=ObservabilityComponent.SEARCH)
        
        self.assertEqual(health.component, ObservabilityComponent.SEARCH)
        self.assertEqual(health.status, HealthStatus.UNKNOWN)
    
    def test_component_health_to_dict(self):
        """Test component health serialization."""
        health = ComponentHealth(
            component=ObservabilityComponent.SEARCH,
            status=HealthStatus.HEALTHY,
        )
        health_dict = health.to_dict()
        
        self.assertEqual(health_dict["component"], "search")
        self.assertEqual(health_dict["status"], "healthy")


class TestHealthMonitor(unittest.TestCase):
    """Tests for HealthMonitor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ObservabilityConfig(enabled=True)
        self.monitor = HealthMonitor(self.config)
    
    def tearDown(self):
        """Clean up after tests."""
        self.monitor.shutdown()
    
    def test_monitor_initialization(self):
        """Test monitor initialization."""
        self.assertIsNotNone(self.monitor)
        self.assertIsNotNone(self.monitor._config)
    
    def test_register_health_check(self):
        """Test registering a health check."""
        check = HealthCheck(
            name="test_check",
            component=ObservabilityComponent.SEARCH,
            check_function=lambda: {"status": "healthy"},
        )
        self.monitor.register_health_check(check)
        
        self.assertIsNotNone(self.monitor.get_health_check("test_check"))
    
    def test_unregister_health_check(self):
        """Test unregistering a health check."""
        check = HealthCheck(
            name="test_check",
            component=ObservabilityComponent.SEARCH,
            check_function=lambda: {"status": "healthy"},
        )
        self.monitor.register_health_check(check)
        self.monitor.unregister_health_check("test_check")
        
        self.assertIsNone(self.monitor.get_health_check("test_check"))
    
    def test_run_health_check(self):
        """Test running a single health check."""
        check = HealthCheck(
            name="test_check",
            component=ObservabilityComponent.SEARCH,
            check_function=lambda: {"status": "healthy"},
        )
        result = self.monitor.run_health_check(check)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "test_check")
    
    def test_run_all_health_checks(self):
        """Test running all health checks."""
        results = self.monitor.run_all_health_checks()
        
        self.assertIsNotNone(results)
        self.assertGreater(len(results), 0)
    
    def test_get_component_health(self):
        """Test getting component health."""
        health = self.monitor.get_component_health(ObservabilityComponent.SEARCH)
        
        self.assertIsNotNone(health)
        self.assertEqual(health.component, ObservabilityComponent.SEARCH)
    
    def test_get_status(self):
        """Test getting overall health status."""
        status = self.monitor.get_status()
        
        self.assertIsNotNone(status)
        self.assertIn("overall_status", status)
        self.assertIn("components", status)
    
    def test_is_healthy(self):
        """Test checking if system is healthy."""
        is_healthy = self.monitor.is_healthy()
        
        self.assertIsInstance(is_healthy, bool)


if __name__ == "__main__":
    unittest.main()
