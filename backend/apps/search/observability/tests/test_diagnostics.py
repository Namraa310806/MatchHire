"""
Tests for Diagnostics Manager.
"""

import unittest
from datetime import datetime, timedelta
from apps.search.observability.core import ObservabilityConfig, ObservabilityComponent, ObservabilityContext, EventType
from apps.search.observability.diagnostics import (
    DiagnosticType,
    Severity,
    DiagnosticRecord,
    DiagnosticReport,
    DiagnosticsManager,
)


class TestDiagnosticRecord(unittest.TestCase):
    """Tests for DiagnosticRecord."""
    
    def test_diagnostic_creation(self):
        """Test diagnostic record creation."""
        record = DiagnosticRecord(
            diagnostic_type=DiagnosticType.SLOW_QUERY,
            severity=Severity.WARNING,
            message="Test diagnostic",
        )
        
        self.assertEqual(record.diagnostic_type, DiagnosticType.SLOW_QUERY)
        self.assertEqual(record.severity, Severity.WARNING)
        self.assertEqual(record.message, "Test diagnostic")
    
    def test_diagnostic_to_dict(self):
        """Test diagnostic serialization."""
        record = DiagnosticRecord(
            diagnostic_type=DiagnosticType.PROVIDER_FAILURE,
            severity=Severity.ERROR,
            message="Provider failed",
            component=ObservabilityComponent.PROVIDER,
        )
        record_dict = record.to_dict()
        
        self.assertEqual(record_dict["diagnostic_type"], "provider_failure")
        self.assertEqual(record_dict["severity"], "error")
        self.assertEqual(record_dict["message"], "Provider failed")
    
    def test_diagnostic_with_suggestions(self):
        """Test diagnostic with suggestions."""
        record = DiagnosticRecord(
            diagnostic_type=DiagnosticType.SLOW_QUERY,
            severity=Severity.WARNING,
            message="Slow query",
            suggestions=["Add index", "Optimize query"],
        )
        
        self.assertEqual(len(record.suggestions), 2)


class TestDiagnosticsManager(unittest.TestCase):
    """Tests for DiagnosticsManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ObservabilityConfig(enabled=True, diagnostics_enabled=True)
        self.manager = DiagnosticsManager(self.config)
    
    def test_manager_initialization(self):
        """Test manager initialization."""
        self.assertIsNotNone(self.manager)
        self.assertIsNotNone(self.manager._config)
    
    def test_record_diagnostic(self):
        """Test recording a diagnostic."""
        record = self.manager.record_diagnostic(
            diagnostic_type=DiagnosticType.SLOW_QUERY,
            severity=Severity.WARNING,
            message="Test diagnostic",
        )
        
        self.assertIsNotNone(record)
        self.assertEqual(record.message, "Test diagnostic")
    
    def test_check_slow_query(self):
        """Test slow query check."""
        record = self.manager.check_slow_query(
            latency_ms=1500.0,
            query="test query",
            component=ObservabilityComponent.SEARCH,
        )
        
        self.assertIsNotNone(record)
        self.assertEqual(record.diagnostic_type, DiagnosticType.SLOW_QUERY)
    
    def test_check_slow_query_not_slow(self):
        """Test slow query check with fast query."""
        record = self.manager.check_slow_query(
            latency_ms=100.0,
            query="test query",
            component=ObservabilityComponent.SEARCH,
        )
        
        self.assertIsNone(record)
    
    def test_check_slow_ranking(self):
        """Test slow ranking check."""
        record = self.manager.check_slow_ranking(
            latency_ms=600.0,
            component=ObservabilityComponent.RANKING,
        )
        
        self.assertIsNotNone(record)
        self.assertEqual(record.diagnostic_type, DiagnosticType.SLOW_RANKING)
    
    def test_check_slow_recommendation(self):
        """Test slow recommendation check."""
        record = self.manager.check_slow_recommendation(
            latency_ms=2500.0,
            component=ObservabilityComponent.RECOMMENDATION,
        )
        
        self.assertIsNotNone(record)
        self.assertEqual(record.diagnostic_type, DiagnosticType.SLOW_RECOMMENDATION)
    
    def test_check_provider_failure(self):
        """Test provider failure check."""
        record = self.manager.check_provider_failure(
            provider="elasticsearch",
            error="Connection timeout",
            component=ObservabilityComponent.PROVIDER,
        )
        
        self.assertIsNotNone(record)
        self.assertEqual(record.diagnostic_type, DiagnosticType.PROVIDER_FAILURE)
    
    def test_check_high_error_rate(self):
        """Test high error rate check."""
        record = self.manager.check_high_error_rate(
            component=ObservabilityComponent.SEARCH,
            error_rate=0.10,
        )
        
        self.assertIsNotNone(record)
        self.assertEqual(record.diagnostic_type, DiagnosticType.HIGH_ERROR_RATE)
    
    def test_get_diagnostics(self):
        """Test getting diagnostics with filters."""
        self.manager.record_diagnostic(
            diagnostic_type=DiagnosticType.SLOW_QUERY,
            severity=Severity.WARNING,
            message="Test 1",
        )
        self.manager.record_diagnostic(
            diagnostic_type=DiagnosticType.PROVIDER_FAILURE,
            severity=Severity.ERROR,
            message="Test 2",
        )
        
        slow_queries = self.manager.get_diagnostics(
            diagnostic_type=DiagnosticType.SLOW_QUERY,
        )
        
        self.assertEqual(len(slow_queries), 1)
        self.assertEqual(slow_queries[0].diagnostic_type, DiagnosticType.SLOW_QUERY)
    
    def test_get_unresolved_diagnostics(self):
        """Test getting unresolved diagnostics."""
        record = self.manager.record_diagnostic(
            diagnostic_type=DiagnosticType.SLOW_QUERY,
            severity=Severity.WARNING,
            message="Test",
        )
        
        unresolved = self.manager.get_unresolved_diagnostics()
        
        self.assertGreater(len(unresolved), 0)
    
    def test_get_critical_diagnostics(self):
        """Test getting critical diagnostics."""
        self.manager.record_diagnostic(
            diagnostic_type=DiagnosticType.PROVIDER_FAILURE,
            severity=Severity.CRITICAL,
            message="Critical issue",
        )
        
        critical = self.manager.get_critical_diagnostics()
        
        self.assertGreater(len(critical), 0)
    
    def test_resolve_diagnostic(self):
        """Test resolving a diagnostic."""
        record = self.manager.record_diagnostic(
            diagnostic_type=DiagnosticType.SLOW_QUERY,
            severity=Severity.WARNING,
            message="Test",
        )
        
        resolved = self.manager.resolve_diagnostic(record.request_id)
        self.assertTrue(resolved)
    
    def test_get_report(self):
        """Test getting diagnostic report."""
        self.manager.record_diagnostic(
            diagnostic_type=DiagnosticType.SLOW_QUERY,
            severity=Severity.WARNING,
            message="Test",
        )
        
        report = self.manager.get_report()
        
        self.assertIsNotNone(report)
        self.assertIn("summary", report)
        self.assertIn("diagnostics", report)
    
    def test_clear_old_diagnostics(self):
        """Test clearing old diagnostics."""
        self.manager.record_diagnostic(
            diagnostic_type=DiagnosticType.SLOW_QUERY,
            severity=Severity.WARNING,
            message="Test",
        )
        
        self.manager.clear_old_diagnostics(retention_days=0)
        
        diagnostics = self.manager.get_diagnostics()
        # Should only keep unresolved
        self.assertEqual(len(diagnostics), 0)


if __name__ == "__main__":
    unittest.main()
