"""
Tests for Observability Core Components.
"""

import unittest
from datetime import datetime
from apps.search.observability.core import (
    ObservabilityConfig,
    ObservabilityContext,
    ObservabilityEvent,
    ObservabilityComponent,
    EventType,
    ObservabilityManager,
    get_manager,
)


class TestObservabilityConfig(unittest.TestCase):
    """Tests for ObservabilityConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ObservabilityConfig()
        
        self.assertTrue(config.enabled)
        self.assertEqual(config.sampling_rate, 1.0)
        self.assertEqual(config.environment, "production")
        self.assertTrue(config.metrics_enabled)
        self.assertTrue(config.tracing_enabled)
        self.assertTrue(config.logging_enabled)
        self.assertTrue(config.audit_enabled)
        self.assertTrue(config.diagnostics_enabled)
    
    def test_config_to_dict(self):
        """Test configuration serialization."""
        config = ObservabilityConfig()
        config_dict = config.to_dict()
        
        self.assertIn("enabled", config_dict)
        self.assertIn("sampling_rate", config_dict)
        self.assertIn("environment", config_dict)
        self.assertEqual(config_dict["enabled"], True)


class TestObservabilityContext(unittest.TestCase):
    """Tests for ObservabilityContext."""
    
    def test_context_creation(self):
        """Test context creation with defaults."""
        context = ObservabilityContext()
        
        self.assertIsNotNone(context.request_id)
        self.assertIsNotNone(context.trace_id)
        self.assertIsNone(context.user_id)
        self.assertIsNone(context.span_id)
    
    def test_context_with_tags(self):
        """Test context with tags."""
        context = ObservabilityContext()
        context.with_tag("key1", "value1")
        
        self.assertEqual(context.tags["key1"], "value1")
    
    def test_context_with_metadata(self):
        """Test context with metadata."""
        context = ObservabilityContext()
        context.with_metadata("key1", "value1")
        
        self.assertEqual(context.metadata["key1"], "value1")
    
    def test_context_to_dict(self):
        """Test context serialization."""
        context = ObservabilityContext()
        context_dict = context.to_dict()
        
        self.assertIn("request_id", context_dict)
        self.assertIn("trace_id", context_dict)
        self.assertIn("tags", context_dict)
        self.assertIn("metadata", context_dict)
    
    def test_context_create_child(self):
        """Test creating child context."""
        parent = ObservabilityContext()
        parent.with_tag("parent_tag", "parent_value")
        
        child = parent.create_child()
        
        self.assertEqual(child.trace_id, parent.trace_id)
        self.assertEqual(child.parent_span_id, parent.span_id)
        self.assertEqual(child.tags["parent_tag"], "parent_value")


class TestObservabilityEvent(unittest.TestCase):
    """Tests for ObservabilityEvent."""
    
    def test_event_creation(self):
        """Test event creation."""
        event = ObservabilityEvent(
            event_type=EventType.METRIC,
            level="INFO",
            message="Test event",
        )
        
        self.assertEqual(event.event_type, EventType.METRIC)
        self.assertEqual(event.level, "INFO")
        self.assertEqual(event.message, "Test event")
    
    def test_event_to_dict(self):
        """Test event serialization."""
        event = ObservabilityEvent(
            event_type=EventType.LOG,
            level="ERROR",
            message="Test error",
        )
        event_dict = event.to_dict()
        
        self.assertEqual(event_dict["event_type"], "log")
        self.assertEqual(event_dict["level"], "ERROR")
        self.assertEqual(event_dict["message"], "Test error")
    
    def test_event_with_context(self):
        """Test event with context."""
        context = ObservabilityContext()
        event = ObservabilityEvent(
            event_type=EventType.TRACE,
            context=context,
        )
        
        self.assertEqual(event.context, context)


class TestObservabilityManager(unittest.TestCase):
    """Tests for ObservabilityManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Reset global manager
        import apps.search.observability.core as core_module
        core_module._global_manager = None
        
        self.config = ObservabilityConfig(enabled=True)
        self.manager = ObservabilityManager(self.config)
    
    def tearDown(self):
        """Clean up after tests."""
        self.manager.shutdown()
        
        # Reset global manager
        import apps.search.observability.core as core_module
        core_module._global_manager = None
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        self.assertIsNotNone(self.manager)
        self.assertIsNotNone(self.manager.config)
        self.assertIsNotNone(self.manager.telemetry)
        self.assertIsNotNone(self.manager.metrics)
        self.assertIsNotNone(self.manager.tracing)
        self.assertIsNotNone(self.manager.logging)
        self.assertIsNotNone(self.manager.audit)
        self.assertIsNotNone(self.manager.diagnostics)
        self.assertIsNotNone(self.manager.health)
    
    def test_get_context(self):
        """Test getting context."""
        context = self.manager.get_context()
        
        self.assertIsNotNone(context)
        self.assertIsNotNone(context.request_id)
        self.assertIsNotNone(context.trace_id)
    
    def test_set_context(self):
        """Test setting context."""
        context = ObservabilityContext()
        self.manager.set_context(context)
        
        retrieved = self.manager.get_context()
        self.assertEqual(retrieved.request_id, context.request_id)
    
    def test_clear_context(self):
        """Test clearing context."""
        self.manager.set_context(ObservabilityContext())
        self.manager.clear_context()
        
        new_context = self.manager.get_context()
        # Should create a new context
        self.assertIsNotNone(new_context)
    
    def test_context_scope(self):
        """Test context scope manager."""
        outer_context = ObservabilityContext()
        outer_context.with_tag("outer", "value")
        
        with self.manager.context_scope(outer_context):
            retrieved = self.manager.get_context()
            self.assertEqual(retrieved.tags["outer"], "value")
    
    def test_record_metric(self):
        """Test recording a metric."""
        self.manager.record_metric(
            name="test_metric",
            value=42.0,
            metric_type="gauge",
        )
        
        # Should not raise an exception
        self.assertTrue(True)
    
    def test_log(self):
        """Test logging."""
        self.manager.log(
            level="INFO",
            message="Test log message",
        )
        
        # Should not raise an exception
        self.assertTrue(True)
    
    def test_audit(self):
        """Test audit recording."""
        self.manager.audit(
            action="test_action",
            entity_type="test_entity",
            entity_id="test_id",
        )
        
        # Should not raise an exception
        self.assertTrue(True)
    
    def test_get_telemetry(self):
        """Test getting telemetry data."""
        telemetry = self.manager.get_telemetry()
        
        self.assertIsNotNone(telemetry)
        self.assertIn("data", telemetry)
    
    def test_get_metrics_summary(self):
        """Test getting metrics summary."""
        summary = self.manager.get_metrics_summary()
        
        self.assertIsNotNone(summary)
    
    def test_get_diagnostics_report(self):
        """Test getting diagnostics report."""
        report = self.manager.get_diagnostics_report()
        
        self.assertIsNotNone(report)
    
    def test_get_health_status(self):
        """Test getting health status."""
        status = self.manager.get_health_status()
        
        self.assertIsNotNone(status)
    
    def test_singleton_pattern(self):
        """Test singleton pattern."""
        manager1 = get_manager(self.config)
        manager2 = get_manager()
        
        self.assertIs(manager1, manager2)


if __name__ == "__main__":
    unittest.main()
