"""
Tests for Metrics Registry and Collection.
"""

import unittest
from apps.search.observability.core import ObservabilityConfig, ObservabilityComponent
from apps.search.observability.metrics import (
    MetricType,
    Counter,
    Gauge,
    Histogram,
    Summary,
    MetricsRegistry,
)


class TestCounter(unittest.TestCase):
    """Tests for Counter metric."""
    
    def test_counter_creation(self):
        """Test counter creation."""
        counter = Counter(
            name="test_counter",
            metric_type=MetricType.COUNTER,
        )
        
        self.assertEqual(counter.name, "test_counter")
        self.assertEqual(counter.value, 0.0)
    
    def test_counter_increment(self):
        """Test counter increment."""
        counter = Counter(
            name="test_counter",
            metric_type=MetricType.COUNTER,
        )
        counter.inc()
        
        self.assertEqual(counter.value, 1.0)
    
    def test_counter_increment_by_amount(self):
        """Test counter increment by amount."""
        counter = Counter(
            name="test_counter",
            metric_type=MetricType.COUNTER,
        )
        counter.inc(5.0)
        
        self.assertEqual(counter.value, 5.0)
    
    def test_counter_negative_increment_raises(self):
        """Test that negative increment raises error."""
        counter = Counter(
            name="test_counter",
            metric_type=MetricType.COUNTER,
        )
        
        with self.assertRaises(ValueError):
            counter.inc(-1.0)
    
    def test_counter_reset(self):
        """Test counter reset."""
        counter = Counter(
            name="test_counter",
            metric_type=MetricType.COUNTER,
        )
        counter.inc(10.0)
        counter.reset()
        
        self.assertEqual(counter.value, 0.0)


class TestGauge(unittest.TestCase):
    """Tests for Gauge metric."""
    
    def test_gauge_creation(self):
        """Test gauge creation."""
        gauge = Gauge(
            name="test_gauge",
            metric_type=MetricType.GAUGE,
        )
        
        self.assertEqual(gauge.name, "test_gauge")
        self.assertEqual(gauge.value, 0.0)
    
    def test_gauge_set(self):
        """Test gauge set."""
        gauge = Gauge(
            name="test_gauge",
            metric_type=MetricType.GAUGE,
        )
        gauge.set(42.0)
        
        self.assertEqual(gauge.value, 42.0)
    
    def test_gauge_increment(self):
        """Test gauge increment."""
        gauge = Gauge(
            name="test_gauge",
            metric_type=MetricType.GAUGE,
        )
        gauge.set(10.0)
        gauge.inc(5.0)
        
        self.assertEqual(gauge.value, 15.0)
    
    def test_gauge_decrement(self):
        """Test gauge decrement."""
        gauge = Gauge(
            name="test_gauge",
            metric_type=MetricType.GAUGE,
        )
        gauge.set(10.0)
        gauge.dec(5.0)
        
        self.assertEqual(gauge.value, 5.0)


class TestHistogram(unittest.TestCase):
    """Tests for Histogram metric."""
    
    def test_histogram_creation(self):
        """Test histogram creation."""
        histogram = Histogram(
            name="test_histogram",
            metric_type=MetricType.HISTOGRAM,
        )
        
        self.assertEqual(histogram.name, "test_histogram")
        self.assertEqual(histogram.count, 0)
        self.assertEqual(histogram.sum, 0.0)
    
    def test_histogram_observe(self):
        """Test histogram observe."""
        histogram = Histogram(
            name="test_histogram",
            metric_type=MetricType.HISTOGRAM,
        )
        histogram.observe(1.5)
        histogram.observe(2.5)
        
        self.assertEqual(histogram.count, 2)
        self.assertEqual(histogram.sum, 4.0)
    
    def test_histogram_buckets(self):
        """Test histogram buckets."""
        histogram = Histogram(
            name="test_histogram",
            metric_type=MetricType.HISTOGRAM,
        )
        histogram.observe(0.01)
        histogram.observe(0.1)
        histogram.observe(1.0)
        
        # Check that values are in appropriate buckets
        self.assertGreater(histogram.get_bucket(0.1), 0)
    
    def test_histogram_summary(self):
        """Test histogram summary."""
        histogram = Histogram(
            name="test_histogram",
            metric_type=MetricType.HISTOGRAM,
        )
        histogram.observe(1.0)
        histogram.observe(2.0)
        histogram.observe(3.0)
        
        summary = histogram.get_summary()
        
        self.assertEqual(summary["count"], 3)
        self.assertEqual(summary["sum"], 6.0)
        self.assertEqual(summary["avg"], 2.0)


class TestSummary(unittest.TestCase):
    """Tests for Summary metric."""
    
    def test_summary_creation(self):
        """Test summary creation."""
        summary = Summary(
            name="test_summary",
            metric_type=MetricType.SUMMARY,
        )
        
        self.assertEqual(summary.name, "test_summary")
        self.assertEqual(len(summary.values), 0)
    
    def test_summary_observe(self):
        """Test summary observe."""
        summary = Summary(
            name="test_summary",
            metric_type=MetricType.SUMMARY,
        )
        summary.observe(1.0)
        summary.observe(2.0)
        
        self.assertEqual(len(summary.values), 2)
    
    def test_summary_quantile(self):
        """Test summary quantile calculation."""
        summary = Summary(
            name="test_summary",
            metric_type=MetricType.SUMMARY,
        )
        summary.observe(1.0)
        summary.observe(2.0)
        summary.observe(3.0)
        summary.observe(4.0)
        summary.observe(5.0)
        
        p50 = summary.get_quantile(0.5)
        p95 = summary.get_quantile(0.95)
        
        self.assertEqual(p50, 3.0)
        self.assertEqual(p95, 5.0)
    
    def test_summary_summary(self):
        """Test summary summary."""
        summary = Summary(
            name="test_summary",
            metric_type=MetricType.SUMMARY,
        )
        summary.observe(1.0)
        summary.observe(2.0)
        summary.observe(3.0)
        
        summary_data = summary.get_summary()
        
        self.assertEqual(summary_data["count"], 3)
        self.assertEqual(summary_data["sum"], 6.0)


class TestMetricsRegistry(unittest.TestCase):
    """Tests for MetricsRegistry."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ObservabilityConfig(enabled=True)
        self.registry = MetricsRegistry(self.config)
    
    def test_registry_initialization(self):
        """Test registry initialization."""
        self.assertIsNotNone(self.registry)
        self.assertGreater(len(self.registry.get_all_metrics()), 0)
    
    def test_register_counter(self):
        """Test registering a counter."""
        counter = self.registry.register_counter(
            name="test_counter",
            description="Test counter",
        )
        
        self.assertIsNotNone(counter)
        self.assertEqual(counter.name, "test_counter")
    
    def test_register_gauge(self):
        """Test registering a gauge."""
        gauge = self.registry.register_gauge(
            name="test_gauge",
            description="Test gauge",
        )
        
        self.assertIsNotNone(gauge)
        self.assertEqual(gauge.name, "test_gauge")
    
    def test_register_histogram(self):
        """Test registering a histogram."""
        histogram = self.registry.register_histogram(
            name="test_histogram",
            description="Test histogram",
        )
        
        self.assertIsNotNone(histogram)
        self.assertEqual(histogram.name, "test_histogram")
    
    def test_register_summary(self):
        """Test registering a summary."""
        summary = self.registry.register_summary(
            name="test_summary",
            description="Test summary",
        )
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary.name, "test_summary")
    
    def test_get_metric(self):
        """Test getting a metric."""
        self.registry.register_counter(name="test_counter")
        metric = self.registry.get_metric("test_counter")
        
        self.assertIsNotNone(metric)
    
    def test_increment_counter(self):
        """Test incrementing a counter."""
        self.registry.register_counter(name="test_counter")
        self.registry.increment_counter("test_counter", 5.0)
        
        metric = self.registry.get_metric("test_counter")
        self.assertEqual(metric.get(), 5.0)
    
    def test_set_gauge(self):
        """Test setting a gauge."""
        self.registry.register_gauge(name="test_gauge")
        self.registry.set_gauge("test_gauge", 42.0)
        
        metric = self.registry.get_metric("test_gauge")
        self.assertEqual(metric.get(), 42.0)
    
    def test_observe_histogram(self):
        """Test observing a histogram."""
        self.registry.register_histogram(name="test_histogram")
        self.registry.observe_histogram("test_histogram", 1.5)
        
        metric = self.registry.get_metric("test_histogram")
        self.assertEqual(metric.count, 1)
    
    def test_get_summary(self):
        """Test getting metrics summary."""
        summary = self.registry.get_summary()
        
        self.assertIsNotNone(summary)
        self.assertIsInstance(summary, dict)
    
    def test_export_prometheus(self):
        """Test Prometheus export."""
        prometheus_export = self.registry.export_prometheus()
        
        self.assertIsNotNone(prometheus_export)
        self.assertIn("# HELP", prometheus_export)
        self.assertIn("# TYPE", prometheus_export)
    
    def test_reset_metric(self):
        """Test resetting a metric."""
        self.registry.register_counter(name="test_counter")
        self.registry.increment_counter("test_counter", 10.0)
        self.registry.reset_metric("test_counter")
        
        metric = self.registry.get_metric("test_counter")
        self.assertEqual(metric.get(), 0.0)
    
    def test_reset_all(self):
        """Test resetting all metrics."""
        self.registry.register_counter(name="test_counter")
        self.registry.increment_counter("test_counter", 10.0)
        self.registry.reset_all()
        
        metric = self.registry.get_metric("test_counter")
        self.assertEqual(metric.get(), 0.0)


if __name__ == "__main__":
    unittest.main()
