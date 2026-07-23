"""
Tests for Structured Logging.
"""

import unittest
from datetime import datetime
from apps.search.observability.core import ObservabilityConfig, ObservabilityContext, ObservabilityComponent, EventType
from apps.search.observability.logging import (
    LogLevel,
    LogEntry,
    StructuredLogger,
    LoggingManager,
)


class TestLogEntry(unittest.TestCase):
    """Tests for LogEntry."""
    
    def test_log_entry_creation(self):
        """Test log entry creation."""
        entry = LogEntry(
            level=LogLevel.INFO,
            message="Test message",
        )
        
        self.assertEqual(entry.level, LogLevel.INFO)
        self.assertEqual(entry.message, "Test message")
        self.assertIsNotNone(entry.timestamp)
    
    def test_log_entry_with_context(self):
        """Test log entry with context."""
        context = ObservabilityContext()
        entry = LogEntry(
            level=LogLevel.INFO,
            message="Test message",
            context=context,
        )
        
        self.assertEqual(entry.context, context)
    
    def test_log_entry_to_dict(self):
        """Test log entry serialization."""
        entry = LogEntry(
            level=LogLevel.ERROR,
            message="Test error",
            component="test_component",
        )
        entry_dict = entry.to_dict()
        
        self.assertEqual(entry_dict["level"], "ERROR")
        self.assertEqual(entry_dict["message"], "Test error")
        self.assertEqual(entry_dict["component"], "test_component")
    
    def test_log_entry_to_json(self):
        """Test log entry JSON serialization."""
        entry = LogEntry(
            level=LogLevel.INFO,
            message="Test message",
        )
        json_str = entry.to_json()
        
        self.assertIn("INFO", json_str)
        self.assertIn("Test message", json_str)


class TestStructuredLogger(unittest.TestCase):
    """Tests for StructuredLogger."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ObservabilityConfig(enabled=True, logging_enabled=True)
        self.log_manager = LoggingManager(self.config)
        self.logger = self.log_manager.get_logger("test_logger")
    
    def tearDown(self):
        """Clean up after tests."""
        self.log_manager.shutdown()
    
    def test_logger_creation(self):
        """Test logger creation."""
        self.assertIsNotNone(self.logger)
        self.assertEqual(self.logger._name, "test_logger")
    
    def test_logger_debug(self):
        """Test debug logging."""
        self.logger.debug("Debug message")
        
        # Should not raise an exception
        self.assertTrue(True)
    
    def test_logger_info(self):
        """Test info logging."""
        self.logger.info("Info message")
        
        # Should not raise an exception
        self.assertTrue(True)
    
    def test_logger_warning(self):
        """Test warning logging."""
        self.logger.warning("Warning message")
        
        # Should not raise an exception
        self.assertTrue(True)
    
    def test_logger_error(self):
        """Test error logging."""
        self.logger.error("Error message")
        
        # Should not raise an exception
        self.assertTrue(True)
    
    def test_logger_critical(self):
        """Test critical logging."""
        self.logger.critical("Critical message")
        
        # Should not raise an exception
        self.assertTrue(True)
    
    def test_logger_with_context(self):
        """Test logging with context."""
        context = ObservabilityContext()
        context.with_tag("test", "value")
        
        self.logger.info("Test message", context=context)
        
        # Should not raise an exception
        self.assertTrue(True)
    
    def test_logger_exception(self):
        """Test exception logging."""
        try:
            raise ValueError("Test exception")
        except Exception:
            self.logger.exception("Exception occurred")
        
        # Should not raise an exception
        self.assertTrue(True)


class TestLoggingManager(unittest.TestCase):
    """Tests for LoggingManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ObservabilityConfig(enabled=True, logging_enabled=True)
        self.manager = LoggingManager(self.config)
    
    def tearDown(self):
        """Clean up after tests."""
        self.manager.shutdown()
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        self.assertIsNotNone(self.manager)
        self.assertIsNotNone(self.manager._config)
    
    def test_get_logger(self):
        """Test getting a logger."""
        logger = self.manager.get_logger("test_logger")
        
        self.assertIsNotNone(logger)
        self.assertEqual(logger._name, "test_logger")
    
    def test_get_logger_same_instance(self):
        """Test that getting same logger returns same instance."""
        logger1 = self.manager.get_logger("test_logger")
        logger2 = self.manager.get_logger("test_logger")
        
        self.assertIs(logger1, logger2)
    
    def test_add_entry(self):
        """Test adding a log entry."""
        entry = LogEntry(
            level=LogLevel.INFO,
            message="Test message",
        )
        self.manager.add_entry(entry)
        
        entries = self.manager.get_entries(limit=10)
        self.assertGreater(len(entries), 0)
    
    def test_get_entries_with_level_filter(self):
        """Test getting entries with level filter."""
        self.manager.add_entry(LogEntry(level=LogLevel.INFO, message="Info"))
        self.manager.add_entry(LogEntry(level=LogLevel.ERROR, message="Error"))
        
        error_entries = self.manager.get_entries(level=LogLevel.ERROR)
        self.assertEqual(len(error_entries), 1)
        self.assertEqual(error_entries[0].level, LogLevel.ERROR)
    
    def test_get_entries_by_trace(self):
        """Test getting entries by trace ID."""
        context = ObservabilityContext()
        entry = LogEntry(
            level=LogLevel.INFO,
            message="Test message",
            context=context,
        )
        self.manager.add_entry(entry)
        
        trace_entries = self.manager.get_entries_by_trace(context.trace_id)
        self.assertGreater(len(trace_entries), 0)
    
    def test_get_error_entries(self):
        """Test getting error entries."""
        self.manager.add_entry(LogEntry(level=LogLevel.INFO, message="Info"))
        self.manager.add_entry(LogEntry(level=LogLevel.ERROR, message="Error"))
        
        error_entries = self.manager.get_error_entries()
        self.assertEqual(len(error_entries), 1)
    
    def test_log_from_event(self):
        """Test logging from observability event."""
        from apps.search.observability.core import ObservabilityEvent, EventType
        
        event = ObservabilityEvent(
            event_type=EventType.LOG,
            level="INFO",
            message="Test message",
            component=ObservabilityComponent.SEARCH,
        )
        self.manager.log(event)
        
        # Should not raise an exception
        self.assertTrue(True)
    
    def test_get_log_summary(self):
        """Test getting log summary."""
        self.manager.add_entry(LogEntry(level=LogLevel.INFO, message="Info"))
        self.manager.add_entry(LogEntry(level=LogLevel.ERROR, message="Error"))
        
        summary = self.manager.get_log_summary()
        
        self.assertIsNotNone(summary)
        self.assertIn("total_entries", summary)
        self.assertIn("level_counts", summary)


if __name__ == "__main__":
    unittest.main()
