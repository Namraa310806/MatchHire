"""
Tests for indexing metrics module.
"""

from django.test import TestCase

from apps.search.indexing.metrics import get_metrics, reset_metrics


class TestIndexingMetricsSingleton(TestCase):
    """Validate process-shared metrics behavior."""

    def tearDown(self):
        reset_metrics()

    def test_get_metrics_returns_singleton(self):
        first = get_metrics()
        second = get_metrics()

        self.assertIs(first, second)

    def test_reset_metrics_clears_collector(self):
        metrics = get_metrics()
        metrics.record_document_synced("candidate", success=False)

        before = metrics.get_summary()
        self.assertEqual(before["total_documents_synced"], 1)
        self.assertEqual(before["total_sync_failures"], 1)

        reset_metrics()

        after = get_metrics().get_summary()
        self.assertEqual(after["total_documents_synced"], 0)
        self.assertEqual(after["total_sync_failures"], 0)
