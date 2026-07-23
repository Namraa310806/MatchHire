"""
Tests for business rules engine.
"""

import unittest
from apps.search.ranking.business_rules import (
    BusinessRulesEngine,
    PinnedResultRule,
    HiddenResultRule,
    PromotedJobRule,
    BlockedCandidateRule,
    PriorityCompanyRule,
    SponsoredRule,
    ManualBoostRule,
    RuleBuilder,
    RuleType,
    RulePriority,
)


class TestPinnedResultRule(unittest.TestCase):
    """Test cases for PinnedResultRule."""
    
    def test_rule_creation(self):
        """Test creating a pinned result rule."""
        rule = PinnedResultRule(
            name="test_pin",
            document_ids=["doc1", "doc2"],
            position=0,
        )
        
        self.assertEqual(rule.name, "test_pin")
        self.assertEqual(rule.document_ids, ["doc1", "doc2"])
        self.assertEqual(rule.position, 0)
        self.assertEqual(rule.rule_type, RuleType.PINNED_RESULT)
    
    def test_rule_matches(self):
        """Test rule matching."""
        rule = PinnedResultRule(
            name="test_pin",
            document_ids=["doc1"],
        )
        
        document = {"id": "doc1"}
        self.assertTrue(rule.matches(document, {}))
        
        document = {"id": "doc2"}
        self.assertFalse(rule.matches(document, {}))
    
    def test_rule_apply(self):
        """Test rule application."""
        rule = PinnedResultRule(
            name="test_pin",
            document_ids=["doc1"],
        )
        
        document = {"id": "doc1"}
        result = rule.apply(document, {})
        
        self.assertTrue(result.get("_pinned"))
        self.assertEqual(result.get("_pin_position"), 0)
        self.assertGreater(result.get("_ranking_boost", 0), 0)


class TestHiddenResultRule(unittest.TestCase):
    """Test cases for HiddenResultRule."""
    
    def test_rule_creation(self):
        """Test creating a hidden result rule."""
        rule = HiddenResultRule(
            name="test_hide",
            document_ids=["doc1"],
            reason="Test reason",
        )
        
        self.assertEqual(rule.name, "test_hide")
        self.assertEqual(rule.reason, "Test reason")
        self.assertEqual(rule.rule_type, RuleType.HIDDEN_RESULT)
    
    def test_rule_apply(self):
        """Test rule application."""
        rule = HiddenResultRule(
            name="test_hide",
            document_ids=["doc1"],
        )
        
        document = {"id": "doc1"}
        result = rule.apply(document, {})
        
        self.assertTrue(result.get("_hidden"))
        self.assertEqual(result.get("_hidden_reason"), "Hidden by business rule")
        self.assertLess(result.get("_ranking_boost", 0), 0)


class TestPromotedJobRule(unittest.TestCase):
    """Test cases for PromotedJobRule."""
    
    def test_rule_creation(self):
        """Test creating a promoted job rule."""
        rule = PromotedJobRule(
            name="test_promote",
            job_ids=["job1"],
            boost_amount=5.0,
        )
        
        self.assertEqual(rule.name, "test_promote")
        self.assertEqual(rule.boost_amount, 5.0)
        self.assertEqual(rule.rule_type, RuleType.PROMOTED_JOB)
    
    def test_rule_apply(self):
        """Test rule application."""
        rule = PromotedJobRule(
            name="test_promote",
            job_ids=["job1"],
        )
        
        document = {"id": "job1"}
        result = rule.apply(document, {})
        
        self.assertTrue(result.get("_promoted"))
        self.assertGreater(result.get("_ranking_boost", 0), 0)


class TestPriorityCompanyRule(unittest.TestCase):
    """Test cases for PriorityCompanyRule."""
    
    def test_rule_creation(self):
        """Test creating a priority company rule."""
        rule = PriorityCompanyRule(
            name="test_priority",
            company_names=["Company A", "Company B"],
            boost_amount=3.0,
        )
        
        self.assertEqual(rule.name, "test_priority")
        self.assertEqual(rule.company_names, ["Company A", "Company B"])
        self.assertEqual(rule.rule_type, RuleType.PRIORITY_COMPANY)
    
    def test_rule_matches(self):
        """Test rule matching."""
        rule = PriorityCompanyRule(
            name="test_priority",
            company_names=["Company A"],
        )
        
        document = {"company_name": "Company A"}
        self.assertTrue(rule.matches(document, {}))
        
        document = {"company_name": "Company B"}
        self.assertFalse(rule.matches(document, {}))


class TestManualBoostRule(unittest.TestCase):
    """Test cases for ManualBoostRule."""
    
    def test_rule_creation(self):
        """Test creating a manual boost rule."""
        rule = ManualBoostRule(
            name="test_boost",
            field="title",
            value_pattern="Senior.*",
            boost_amount=2.0,
        )
        
        self.assertEqual(rule.name, "test_boost")
        self.assertEqual(rule.field, "title")
        self.assertEqual(rule.value_pattern, "Senior.*")
    
    def test_rule_matches_regex(self):
        """Test rule matching with regex."""
        rule = ManualBoostRule(
            name="test_boost",
            field="title",
            value_pattern="Senior.*",
        )
        
        document = {"title": "Senior Engineer"}
        self.assertTrue(rule.matches(document, {}))
        
        document = {"title": "Junior Engineer"}
        self.assertFalse(rule.matches(document, {}))


class TestBusinessRulesEngine(unittest.TestCase):
    """Test cases for BusinessRulesEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = BusinessRulesEngine()
    
    def test_engine_creation(self):
        """Test creating a business rules engine."""
        self.assertIsNotNone(self.engine)
        self.assertEqual(len(self.engine._rules), 0)
    
    def test_add_rule(self):
        """Test adding a rule."""
        rule = PinnedResultRule(
            name="test_pin",
            document_ids=["doc1"],
        )
        
        self.engine.add_rule(rule)
        self.assertEqual(len(self.engine._rules), 1)
    
    def test_remove_rule(self):
        """Test removing a rule."""
        rule = PinnedResultRule(
            name="test_pin",
            document_ids=["doc1"],
        )
        
        self.engine.add_rule(rule)
        self.engine.remove_rule("test_pin")
        
        self.assertEqual(len(self.engine._rules), 0)
    
    def test_get_rule(self):
        """Test getting a rule."""
        rule = PinnedResultRule(
            name="test_pin",
            document_ids=["doc1"],
        )
        
        self.engine.add_rule(rule)
        retrieved = self.engine.get_rule("test_pin")
        
        self.assertEqual(retrieved, rule)
    
    def test_enable_disable_rule(self):
        """Test enabling and disabling a rule."""
        rule = PinnedResultRule(
            name="test_pin",
            document_ids=["doc1"],
        )
        
        self.engine.add_rule(rule)
        
        self.assertTrue(self.engine.disable_rule("test_pin"))
        self.assertFalse(rule.enabled)
        
        self.assertTrue(self.engine.enable_rule("test_pin"))
        self.assertTrue(rule.enabled)
    
    def test_apply_rules(self):
        """Test applying rules to results."""
        rule = PinnedResultRule(
            name="test_pin",
            document_ids=["doc1"],
        )
        
        self.engine.add_rule(rule)
        
        results = [
            {"id": "doc1", "title": "Job 1"},
            {"id": "doc2", "title": "Job 2"},
        ]
        context = {}
        
        modified_results, applied_rules = self.engine.apply_rules(results, context)
        
        self.assertEqual(len(modified_results), 2)
        self.assertTrue(modified_results[0].get("_pinned"))
        self.assertGreater(len(applied_rules), 0)
    
    def test_apply_hidden_rule(self):
        """Test applying hidden rule filters results."""
        rule = HiddenResultRule(
            name="test_hide",
            document_ids=["doc1"],
        )
        
        self.engine.add_rule(rule)
        
        results = [
            {"id": "doc1", "title": "Job 1"},
            {"id": "doc2", "title": "Job 2"},
        ]
        context = {}
        
        modified_results, _ = self.engine.apply_rules(results, context)
        
        # Hidden results should be filtered out
        self.assertEqual(len(modified_results), 1)
        self.assertEqual(modified_results[0]["id"], "doc2")
    
    def test_clear_rules(self):
        """Test clearing all rules."""
        rule = PinnedResultRule(
            name="test_pin",
            document_ids=["doc1"],
        )
        
        self.engine.add_rule(rule)
        self.engine.clear_rules()
        
        self.assertEqual(len(self.engine._rules), 0)
    
    def test_validate_rules(self):
        """Test rule validation."""
        # Add rule with no description
        rule = PinnedResultRule(
            name="test_pin",
            document_ids=["doc1"],
            description="",
        )
        
        self.engine.add_rule(rule)
        issues = self.engine.validate_rules()
        
        self.assertGreater(len(issues), 0)


class TestRuleBuilder(unittest.TestCase):
    """Test cases for RuleBuilder."""
    
    def test_build_pinned_rule(self):
        """Test building a pinned rule."""
        rule = RuleBuilder.pinned("test_pin", ["doc1"], position=0)
        
        self.assertEqual(rule.name, "test_pin")
        self.assertEqual(rule.document_ids, ["doc1"])
        self.assertEqual(rule.position, 0)
    
    def test_build_hidden_rule(self):
        """Test building a hidden rule."""
        rule = RuleBuilder.hidden("test_hide", ["doc1"], reason="Test")
        
        self.assertEqual(rule.name, "test_hide")
        self.assertEqual(rule.reason, "Test")
    
    def test_build_promoted_rule(self):
        """Test building a promoted rule."""
        rule = RuleBuilder.promoted("test_promote", ["job1"], boost=5.0)
        
        self.assertEqual(rule.name, "test_promote")
        self.assertEqual(rule.boost_amount, 5.0)
    
    def test_build_blocked_rule(self):
        """Test building a blocked rule."""
        rule = RuleBuilder.blocked("test_block", ["cand1"], reason="Test")
        
        self.assertEqual(rule.name, "test_block")
        self.assertEqual(rule.block_reason, "Test")
    
    def test_build_priority_company_rule(self):
        """Test building a priority company rule."""
        rule = RuleBuilder.priority_company("test_priority", ["Company A"], boost=3.0)
        
        self.assertEqual(rule.name, "test_priority")
        self.assertEqual(rule.company_names, ["Company A"])
    
    def test_build_sponsored_rule(self):
        """Test building a sponsored rule."""
        rule = RuleBuilder.sponsored("test_sponsored", ["job1"], boost=2.0)
        
        self.assertEqual(rule.name, "test_sponsored")
        self.assertEqual(rule.boost_amount, 2.0)
    
    def test_build_manual_boost_rule(self):
        """Test building a manual boost rule."""
        rule = RuleBuilder.manual_boost("test_boost", "title", "Senior.*", boost=2.0)
        
        self.assertEqual(rule.name, "test_boost")
        self.assertEqual(rule.field, "title")
        self.assertEqual(rule.value_pattern, "Senior.*")


if __name__ == "__main__":
    unittest.main()
