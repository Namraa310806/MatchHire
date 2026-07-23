"""
Tests for Distributed Tracing.
"""

import unittest
import time
from apps.search.observability.core import ObservabilityConfig, ObservabilityComponent, ObservabilityContext
from apps.search.observability.tracing import (
    SpanKind,
    SpanContext,
    Span,
    TracingManager,
)


class TestSpanContext(unittest.TestCase):
    """Tests for SpanContext."""
    
    def test_span_context_creation(self):
        """Test span context creation."""
        context = SpanContext(
            trace_id="test_trace_id",
            span_id="test_span_id",
        )
        
        self.assertEqual(context.trace_id, "test_trace_id")
        self.assertEqual(context.span_id, "test_span_id")
    
    def test_span_context_to_dict(self):
        """Test span context serialization."""
        context = SpanContext(
            trace_id="test_trace_id",
            span_id="test_span_id",
            baggage={"key": "value"},
        )
        context_dict = context.to_dict()
        
        self.assertEqual(context_dict["trace_id"], "test_trace_id")
        self.assertEqual(context_dict["span_id"], "test_span_id")
        self.assertEqual(context_dict["baggage"]["key"], "value")
    
    def test_span_context_from_dict(self):
        """Test span context deserialization."""
        data = {
            "trace_id": "test_trace_id",
            "span_id": "test_span_id",
            "parent_span_id": "parent_id",
            "baggage": {"key": "value"},
        }
        context = SpanContext.from_dict(data)
        
        self.assertEqual(context.trace_id, "test_trace_id")
        self.assertEqual(context.span_id, "test_span_id")
        self.assertEqual(context.parent_span_id, "parent_id")


class TestSpan(unittest.TestCase):
    """Tests for Span."""
    
    def test_span_creation(self):
        """Test span creation."""
        span = Span(
            name="test_span",
            kind=SpanKind.INTERNAL,
        )
        
        self.assertEqual(span.name, "test_span")
        self.assertEqual(span.kind, SpanKind.INTERNAL)
        self.assertIsNotNone(span.span_id)
        self.assertIsNotNone(span.trace_id)
    
    def test_span_end(self):
        """Test span end."""
        span = Span(name="test_span")
        time.sleep(0.01)
        span.end()
        
        self.assertIsNotNone(span.end_time)
        self.assertIsNotNone(span.duration_ms)
        self.assertGreater(span.duration_ms, 0)
    
    def test_span_set_attribute(self):
        """Test setting span attribute."""
        span = Span(name="test_span")
        span.set_attribute("key", "value")
        
        self.assertEqual(span.attributes["key"], "value")
    
    def test_span_set_attributes(self):
        """Test setting multiple span attributes."""
        span = Span(name="test_span")
        span.set_attributes({"key1": "value1", "key2": "value2"})
        
        self.assertEqual(span.attributes["key1"], "value1")
        self.assertEqual(span.attributes["key2"], "value2")
    
    def test_span_add_event(self):
        """Test adding event to span."""
        span = Span(name="test_span")
        span.add_event("test_event", {"attr": "value"})
        
        self.assertEqual(len(span.events), 1)
        self.assertEqual(span.events[0]["name"], "test_event")
    
    def test_span_set_status(self):
        """Test setting span status."""
        span = Span(name="test_span")
        span.set_status("error", "Test error")
        
        self.assertEqual(span.status, "error")
        self.assertEqual(span.status_message, "Test error")
    
    def test_span_record_exception(self):
        """Test recording exception on span."""
        span = Span(name="test_span")
        try:
            raise ValueError("Test exception")
        except Exception as e:
            span.record_exception(e)
        
        self.assertEqual(span.status, "error")
        self.assertEqual(len(span.events), 1)
    
    def test_span_to_dict(self):
        """Test span serialization."""
        span = Span(
            name="test_span",
            kind=SpanKind.SERVER,
        )
        span.set_attribute("key", "value")
        span_dict = span.to_dict()
        
        self.assertEqual(span_dict["name"], "test_span")
        self.assertEqual(span_dict["kind"], "server")
        self.assertEqual(span_dict["attributes"]["key"], "value")


class TestTracingManager(unittest.TestCase):
    """Tests for TracingManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ObservabilityConfig(enabled=True, tracing_enabled=True)
        self.manager = TracingManager(self.config)
    
    def tearDown(self):
        """Clean up after tests."""
        self.manager.shutdown()
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        self.assertIsNotNone(self.manager)
        self.assertIsNotNone(self.manager._config)
    
    def test_start_span(self):
        """Test starting a span."""
        context = ObservabilityContext()
        span = self.manager.start_span(
            name="test_span",
            component=ObservabilityComponent.SEARCH,
            context=context,
        )
        
        self.assertIsNotNone(span)
        self.assertEqual(span.name, "test_span")
        self.assertEqual(span.component, ObservabilityComponent.SEARCH)
    
    def test_end_span(self):
        """Test ending a span."""
        span = self.manager.start_span(
            name="test_span",
            component=ObservabilityComponent.SEARCH,
        )
        time.sleep(0.01)
        self.manager.end_span(span)
        
        self.assertIsNotNone(span.end_time)
        self.assertIsNotNone(span.duration_ms)
    
    def test_span_context_manager(self):
        """Test span context manager."""
        with self.manager.span_context(
            name="test_span",
            component=ObservabilityComponent.SEARCH,
        ) as span:
            self.assertIsNotNone(span)
            self.assertEqual(span.name, "test_span")
        
        self.assertIsNotNone(span.end_time)
    
    def test_get_active_span(self):
        """Test getting active span."""
        span = self.manager.start_span(
            name="test_span",
            component=ObservabilityComponent.SEARCH,
        )
        
        active = self.manager.get_active_span(span.span_id)
        self.assertEqual(active, span)
        
        self.manager.end_span(span)
    
    def test_get_span(self):
        """Test getting a span."""
        span = self.manager.start_span(
            name="test_span",
            component=ObservabilityComponent.SEARCH,
        )
        self.manager.end_span(span)
        
        retrieved = self.manager.get_span(span.span_id)
        self.assertEqual(retrieved, span)
    
    def test_get_trace(self):
        """Test getting all spans in a trace."""
        span1 = self.manager.start_span(
            name="span1",
            component=ObservabilityComponent.SEARCH,
        )
        span2 = self.manager.start_span(
            name="span2",
            component=ObservabilityComponent.RANKING,
        )
        span2.parent_span_id = span1.span_id
        span2.trace_id = span1.trace_id
        
        self.manager.end_span(span1)
        self.manager.end_span(span2)
        
        trace = self.manager.get_trace(span1.trace_id)
        self.assertEqual(len(trace), 2)
    
    def test_export_spans(self):
        """Test exporting spans."""
        span = self.manager.start_span(
            name="test_span",
            component=ObservabilityComponent.SEARCH,
        )
        self.manager.end_span(span)
        
        exported = self.manager.export_spans()
        self.assertGreater(len(exported), 0)
    
    def test_get_trace_summary(self):
        """Test getting trace summary."""
        span = self.manager.start_span(
            name="test_span",
            component=ObservabilityComponent.SEARCH,
        )
        time.sleep(0.01)
        self.manager.end_span(span)
        
        summary = self.manager.get_trace_summary(span.trace_id)
        self.assertIsNotNone(summary)
        self.assertEqual(summary["trace_id"], span.trace_id)
        self.assertEqual(summary["span_count"], 1)


if __name__ == "__main__":
    unittest.main()
