"""
Tests for score explanation system.
"""

import unittest
from datetime import datetime
from apps.search.ranking.explanation import (
    ScoreExplanation,
    SignalContribution,
    BoostExplanation,
    BusinessRuleExplanation,
    RankingBreakdown,
    ExplanationBuilder,
)


class TestSignalContribution(unittest.TestCase):
    """Test cases for SignalContribution."""
    
    def test_contribution_creation(self):
        """Test creating a signal contribution."""
        contribution = SignalContribution(
            signal_name="lexical",
            signal_type="lexical",
            raw_score=1.0,
            normalized_score=0.5,
            weight=1.0,
            contribution=0.5,
        )
        
        self.assertEqual(contribution.signal_name, "lexical")
        self.assertEqual(contribution.contribution, 0.5)
    
    def test_contribution_to_dict(self):
        """Test converting contribution to dictionary."""
        contribution = SignalContribution(
            signal_name="lexical",
            signal_type="lexical",
            raw_score=1.0,
            normalized_score=0.5,
            weight=1.0,
            contribution=0.5,
        )
        
        contribution_dict = contribution.to_dict()
        self.assertEqual(contribution_dict["signal_name"], "lexical")
        self.assertEqual(contribution_dict["contribution"], 0.5)


class TestBoostExplanation(unittest.TestCase):
    """Test cases for BoostExplanation."""
    
    def test_boost_creation(self):
        """Test creating a boost explanation."""
        boost = BoostExplanation(
            boost_type="pinned",
            boost_amount=10.0,
            reason="Pinned result",
            source="business_rules",
        )
        
        self.assertEqual(boost.boost_type, "pinned")
        self.assertEqual(boost.boost_amount, 10.0)
    
    def test_boost_to_dict(self):
        """Test converting boost to dictionary."""
        boost = BoostExplanation(
            boost_type="pinned",
            boost_amount=10.0,
            reason="Pinned result",
            source="business_rules",
        )
        
        boost_dict = boost.to_dict()
        self.assertEqual(boost_dict["boost_type"], "pinned")
        self.assertEqual(boost_dict["boost_amount"], 10.0)


class TestBusinessRuleExplanation(unittest.TestCase):
    """Test cases for BusinessRuleExplanation."""
    
    def test_rule_explanation_creation(self):
        """Test creating a business rule explanation."""
        explanation = BusinessRuleExplanation(
            rule_name="pin_rule",
            rule_type="pinned_result",
            action="pin",
            priority=0,
            effect=10.0,
            reason="Pinned by business rule",
        )
        
        self.assertEqual(explanation.rule_name, "pin_rule")
        self.assertEqual(explanation.effect, 10.0)
    
    def test_rule_explanation_to_dict(self):
        """Test converting rule explanation to dictionary."""
        explanation = BusinessRuleExplanation(
            rule_name="pin_rule",
            rule_type="pinned_result",
            action="pin",
            priority=0,
            effect=10.0,
            reason="Pinned by business rule",
        )
        
        explanation_dict = explanation.to_dict()
        self.assertEqual(explanation_dict["rule_name"], "pin_rule")
        self.assertEqual(explanation_dict["effect"], 10.0)


class TestRankingBreakdown(unittest.TestCase):
    """Test cases for RankingBreakdown."""
    
    def test_breakdown_creation(self):
        """Test creating a ranking breakdown."""
        breakdown = RankingBreakdown(
            document_id="doc1",
            final_score=1.5,
            original_score=1.0,
        )
        
        self.assertEqual(breakdown.document_id, "doc1")
        self.assertEqual(breakdown.final_score, 1.5)
        self.assertEqual(breakdown.original_score, 1.0)
    
    def test_breakdown_to_dict(self):
        """Test converting breakdown to dictionary."""
        breakdown = RankingBreakdown(
            document_id="doc1",
            final_score=1.5,
            original_score=1.0,
        )
        
        breakdown_dict = breakdown.to_dict()
        self.assertEqual(breakdown_dict["document_id"], "doc1")
        self.assertEqual(breakdown_dict["final_score"], 1.5)
    
    def test_get_total_signal_contribution(self):
        """Test getting total signal contribution."""
        breakdown = RankingBreakdown(
            document_id="doc1",
            final_score=1.5,
            original_score=1.0,
        )
        
        breakdown.signal_contributions = [
            SignalContribution("s1", "t1", 1.0, 0.5, 1.0, 0.5),
            SignalContribution("s2", "t2", 1.0, 0.3, 1.0, 0.3),
        ]
        
        total = breakdown.get_total_signal_contribution()
        self.assertAlmostEqual(total, 0.8)
    
    def test_get_total_boost(self):
        """Test getting total boost."""
        breakdown = RankingBreakdown(
            document_id="doc1",
            final_score=1.5,
            original_score=1.0,
        )
        
        breakdown.boosts = [
            BoostExplanation("b1", 5.0, "reason1", "source1"),
            BoostExplanation("b2", 3.0, "reason2", "source2"),
        ]
        
        total = breakdown.get_total_boost()
        self.assertEqual(total, 8.0)
    
    def test_get_top_signals(self):
        """Test getting top signals."""
        breakdown = RankingBreakdown(
            document_id="doc1",
            final_score=1.5,
            original_score=1.0,
        )
        
        breakdown.signal_contributions = [
            SignalContribution("s1", "t1", 1.0, 0.5, 1.0, 0.5),
            SignalContribution("s2", "t2", 1.0, 0.3, 1.0, 0.3),
            SignalContribution("s3", "t3", 1.0, 0.7, 1.0, 0.7),
        ]
        
        top_signals = breakdown.get_top_signals(2)
        self.assertEqual(len(top_signals), 2)
        self.assertEqual(top_signals[0].signal_name, "s3")


class TestScoreExplanation(unittest.TestCase):
    """Test cases for ScoreExplanation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.explanation = ScoreExplanation()
    
    def test_explanation_creation(self):
        """Test creating a score explanation."""
        self.assertIsNotNone(self.explanation)
        self.assertTrue(self.explanation.is_enabled())
    
    def test_enable_disable(self):
        """Test enabling and disabling explanation."""
        self.explanation.disable()
        self.assertFalse(self.explanation.is_enabled())
        
        self.explanation.enable()
        self.assertTrue(self.explanation.is_enabled())
    
    def test_create_breakdown(self):
        """Test creating a breakdown."""
        document = {
            "id": "doc1",
            "_ranking_score": 1.5,
            "_score": 1.0,
            "_ranking_signals": {"lexical": 0.5, "metadata": 0.3},
        }
        context = {"query": "test"}
        
        breakdown = self.explanation.create_breakdown(document, context)
        
        self.assertEqual(breakdown.document_id, "doc1")
        self.assertEqual(breakdown.final_score, 1.5)
        self.assertEqual(len(breakdown.signal_contributions), 2)
    
    def test_create_breakdown_disabled(self):
        """Test creating breakdown when disabled."""
        self.explanation.disable()
        
        document = {"id": "doc1", "_ranking_score": 1.5}
        context = {"query": "test"}
        
        breakdown = self.explanation.create_breakdown(document, context)
        
        self.assertEqual(breakdown.document_id, "doc1")
        self.assertEqual(len(breakdown.signal_contributions), 0)
    
    def test_get_breakdown(self):
        """Test getting a breakdown."""
        document = {"id": "doc1", "_ranking_score": 1.5}
        context = {"query": "test"}
        
        self.explanation.create_breakdown(document, context)
        breakdown = self.explanation.get_breakdown("doc1")
        
        self.assertIsNotNone(breakdown)
        self.assertEqual(breakdown.document_id, "doc1")
    
    def test_explain_results(self):
        """Test explaining multiple results."""
        results = [
            {"id": "doc1", "_ranking_score": 1.5, "_ranking_signals": {"lexical": 0.5}},
            {"id": "doc2", "_ranking_score": 1.0, "_ranking_signals": {"lexical": 0.3}},
        ]
        context = {"query": "test"}
        
        breakdowns = self.explanation.explain_results(results, context)
        
        self.assertEqual(len(breakdowns), 2)
        self.assertIn("doc1", breakdowns)
        self.assertIn("doc2", breakdowns)
    
    def test_clear_breakdowns(self):
        """Test clearing breakdowns."""
        document = {"id": "doc1", "_ranking_score": 1.5}
        context = {"query": "test"}
        
        self.explanation.create_breakdown(document, context)
        self.explanation.clear_breakdowns()
        
        self.assertEqual(len(self.explanation._breakdowns), 0)


class TestExplanationBuilder(unittest.TestCase):
    """Test cases for ExplanationBuilder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.builder = ExplanationBuilder()
    
    def test_builder_creation(self):
        """Test creating an explanation builder."""
        self.assertIsNotNone(self.builder)
        self.assertIsNotNone(self.builder._explanation)
    
    def test_build_for_document(self):
        """Test building explanation for a single document."""
        document = {"id": "doc1", "_ranking_score": 1.5}
        context = {"query": "test"}
        
        breakdown = self.builder.build_for_document(document, context)
        
        self.assertEqual(breakdown.document_id, "doc1")
    
    def test_build_for_results(self):
        """Test building explanations for multiple results."""
        results = [
            {"id": "doc1", "_ranking_score": 1.5},
            {"id": "doc2", "_ranking_score": 1.0},
        ]
        context = {"query": "test"}
        
        breakdowns = self.builder.build_for_results(results, context)
        
        self.assertEqual(len(breakdowns), 2)
    
    def test_format_for_api(self):
        """Test formatting for API response."""
        breakdown = RankingBreakdown(
            document_id="doc1",
            final_score=1.5,
            original_score=1.0,
        )
        
        api_format = self.builder.format_for_api(breakdown)
        
        self.assertIn("document_id", api_format)
        self.assertIn("score", api_format)
        self.assertIn("signals", api_format)
    
    def test_format_for_ui(self):
        """Test formatting for UI display."""
        breakdown = RankingBreakdown(
            document_id="doc1",
            final_score=1.5,
            original_score=1.0,
        )
        
        ui_format = self.builder.format_for_ui(breakdown)
        
        self.assertIn("document_id", ui_format)
        self.assertIn("score", ui_format)
        self.assertIn("top_factors", ui_format)
    
    def test_format_for_logs(self):
        """Test formatting for logging."""
        breakdown = RankingBreakdown(
            document_id="doc1",
            final_score=1.5,
            original_score=1.0,
        )
        
        log_format = self.builder.format_for_logs(breakdown)
        
        self.assertIsInstance(log_format, str)
        self.assertIn("doc1", log_format)
    
    def test_get_summary_statistics(self):
        """Test getting summary statistics."""
        breakdowns = {
            "doc1": RankingBreakdown(
                document_id="doc1",
                final_score=1.5,
                original_score=1.0,
            ),
            "doc2": RankingBreakdown(
                document_id="doc2",
                final_score=1.0,
                original_score=0.5,
            ),
        }
        
        stats = self.builder.get_summary_statistics(breakdowns)
        
        self.assertIn("total_documents", stats)
        self.assertEqual(stats["total_documents"], 2)


if __name__ == "__main__":
    unittest.main()
