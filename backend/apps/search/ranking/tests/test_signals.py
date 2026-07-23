"""
Tests for ranking signals.
"""

import unittest
from datetime import datetime, timedelta
from apps.search.ranking.signals import (
    LexicalSignal,
    MetadataSignal,
    BusinessRuleSignal,
    FreshnessSignal,
    PopularitySignal,
    QualitySignal,
    SkillOverlapSignal,
    ExperienceOverlapSignal,
    EducationOverlapSignal,
    LocationProximitySignal,
    SalaryCompatibilitySignal,
    SignalConfig,
)


class TestLexicalSignal(unittest.TestCase):
    """Test cases for LexicalSignal."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.signal = LexicalSignal()
    
    def test_signal_type(self):
        """Test signal type."""
        self.assertEqual(self.signal.signal_type.value, "lexical")
    
    def test_score_with_provider_score(self):
        """Test scoring with provider score."""
        document = {"id": "1", "_score": 5.0}
        context = {"query": "engineer"}
        
        score = self.signal.score(document, context)
        self.assertEqual(score, 5.0)
    
    def test_score_with_field_matching(self):
        """Test scoring with field matching."""
        document = {
            "id": "1",
            "title": "Software Engineer",
            "description": "Python developer",
        }
        context = {"query": "engineer"}
        
        score = self.signal.score(document, context)
        self.assertGreater(score, 0)
    
    def test_score_no_match(self):
        """Test scoring with no match."""
        document = {"id": "1", "title": "Accountant"}
        context = {"query": "engineer"}
        
        score = self.signal.score(document, context)
        self.assertEqual(score, 0.0)


class TestMetadataSignal(unittest.TestCase):
    """Test cases for MetadataSignal."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.signal = MetadataSignal()
    
    def test_signal_type(self):
        """Test signal type."""
        self.assertEqual(self.signal.signal_type.value, "metadata")
    
    def test_score_with_filter_match(self):
        """Test scoring with filter match."""
        document = {"id": "1", "category": "Technology"}
        context = {"filters": {"category": "Technology"}}
        
        score = self.signal.score(document, context)
        self.assertGreater(score, 0)
    
    def test_score_no_match(self):
        """Test scoring with no filter match."""
        document = {"id": "1", "category": "Technology"}
        context = {"filters": {"category": "Finance"}}
        
        score = self.signal.score(document, context)
        self.assertEqual(score, 0.0)


class TestFreshnessSignal(unittest.TestCase):
    """Test cases for FreshnessSignal."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.signal = FreshnessSignal()
    
    def test_signal_type(self):
        """Test signal type."""
        self.assertEqual(self.signal.signal_type.value, "freshness")
    
    def test_score_recent_document(self):
        """Test scoring recent document."""
        now = datetime.now()
        document = {"id": "1", "created_at": now.isoformat()}
        context = {}
        
        score = self.signal.score(document, context)
        self.assertGreater(score, 0.5)
    
    def test_score_old_document(self):
        """Test scoring old document."""
        old_date = datetime.now() - timedelta(days=100)
        document = {"id": "1", "created_at": old_date.isoformat()}
        context = {}
        
        score = self.signal.score(document, context)
        self.assertLess(score, 0.5)
    
    def test_score_no_date(self):
        """Test scoring document without date."""
        document = {"id": "1"}
        context = {}
        
        score = self.signal.score(document, context)
        self.assertEqual(score, 0.0)


class TestPopularitySignal(unittest.TestCase):
    """Test cases for PopularitySignal."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.signal = PopularitySignal()
    
    def test_signal_type(self):
        """Test signal type."""
        self.assertEqual(self.signal.signal_type.value, "popularity")
    
    def test_score_popular_document(self):
        """Test scoring popular document."""
        document = {
            "id": "1",
            "view_count": 1000,
            "application_count": 50,
            "save_count": 20,
        }
        context = {}
        
        score = self.signal.score(document, context)
        self.assertGreater(score, 0)
    
    def test_score_unpopular_document(self):
        """Test scoring unpopular document."""
        document = {
            "id": "1",
            "view_count": 0,
            "application_count": 0,
            "save_count": 0,
        }
        context = {}
        
        score = self.signal.score(document, context)
        self.assertEqual(score, 0.0)


class TestQualitySignal(unittest.TestCase):
    """Test cases for QualitySignal."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.signal = QualitySignal()
    
    def test_signal_type(self):
        """Test signal type."""
        self.assertEqual(self.signal.signal_type.value, "quality")
    
    def test_score_high_quality(self):
        """Test scoring high quality document."""
        document = {
            "id": "1",
            "is_verified": True,
            "is_featured": True,
            "is_premium": True,
            "completeness": 100,
        }
        context = {}
        
        score = self.signal.score(document, context)
        self.assertGreater(score, 0)
    
    def test_score_low_quality(self):
        """Test scoring low quality document."""
        document = {
            "id": "1",
            "is_verified": False,
            "is_featured": False,
            "is_premium": False,
            "completeness": 10,
        }
        context = {}
        
        score = self.signal.score(document, context)
        self.assertGreaterEqual(score, 0)


class TestSkillOverlapSignal(unittest.TestCase):
    """Test cases for SkillOverlapSignal."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.signal = SkillOverlapSignal()
    
    def test_signal_type(self):
        """Test signal type."""
        self.assertEqual(self.signal.signal_type.value, "skill_overlap")
    
    def test_score_perfect_match(self):
        """Test scoring perfect skill match."""
        document = {"id": "1", "skills": ["Python", "JavaScript", "SQL"]}
        context = {"required_skills": ["Python", "JavaScript", "SQL"]}
        
        score = self.signal.score(document, context)
        self.assertGreater(score, 0.9)
    
    def test_score_partial_match(self):
        """Test scoring partial skill match."""
        document = {"id": "1", "skills": ["Python", "JavaScript"]}
        context = {"required_skills": ["Python", "JavaScript", "SQL"]}
        
        score = self.signal.score(document, context)
        self.assertGreater(score, 0)
        self.assertLess(score, 1.0)
    
    def test_score_no_match(self):
        """Test scoring no skill match."""
        document = {"id": "1", "skills": ["Java", "C++"]}
        context = {"required_skills": ["Python", "JavaScript"]}
        
        score = self.signal.score(document, context)
        self.assertEqual(score, 0.0)


class TestExperienceOverlapSignal(unittest.TestCase):
    """Test cases for ExperienceOverlapSignal."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.signal = ExperienceOverlapSignal()
    
    def test_signal_type(self):
        """Test signal type."""
        self.assertEqual(self.signal.signal_type.value, "experience_overlap")
    
    def test_score_exact_match(self):
        """Test scoring exact experience match."""
        document = {"id": "1", "experience_years": 5}
        context = {"required_experience": 5}
        
        score = self.signal.score(document, context)
        self.assertGreater(score, 0)
    
    def test_score_overqualified(self):
        """Test scoring overqualified candidate."""
        document = {"id": "1", "experience_years": 10}
        context = {"required_experience": 5}
        
        score = self.signal.score(document, context)
        self.assertGreater(score, 0)
    
    def test_score_underqualified(self):
        """Test scoring underqualified candidate."""
        document = {"id": "1", "experience_years": 2}
        context = {"required_experience": 5}
        
        score = self.signal.score(document, context)
        self.assertGreaterEqual(score, 0)


class TestLocationProximitySignal(unittest.TestCase):
    """Test cases for LocationProximitySignal."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.signal = LocationProximitySignal()
    
    def test_signal_type(self):
        """Test signal type."""
        self.assertEqual(self.signal.signal_type.value, "location_proximity")
    
    def test_score_exact_match(self):
        """Test scoring exact location match."""
        document = {"id": "1", "location": "San Francisco, CA"}
        context = {"required_location": "San Francisco, CA"}
        
        score = self.signal.score(document, context)
        self.assertEqual(score, 1.0)
    
    def test_score_partial_match(self):
        """Test scoring partial location match."""
        document = {"id": "1", "location": "San Francisco, CA"}
        context = {"required_location": "San Francisco"}
        
        score = self.signal.score(document, context)
        self.assertGreater(score, 0)
    
    def test_score_no_match(self):
        """Test scoring no location match."""
        document = {"id": "1", "location": "New York, NY"}
        context = {"required_location": "San Francisco, CA"}
        
        score = self.signal.score(document, context)
        self.assertEqual(score, 0.0)


class TestSalaryCompatibilitySignal(unittest.TestCase):
    """Test cases for SalaryCompatibilitySignal."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.signal = SalaryCompatibilitySignal()
    
    def test_signal_type(self):
        """Test signal type."""
        self.assertEqual(self.signal.signal_type.value, "salary_compatibility")
    
    def test_score_in_range(self):
        """Test scoring salary in range."""
        document = {"id": "1", "salary": 80000}
        context = {"min_salary": 70000, "max_salary": 90000}
        
        score = self.signal.score(document, context)
        self.assertEqual(score, 1.0)
    
    def test_score_below_range(self):
        """Test scoring salary below range."""
        document = {"id": "1", "salary": 50000}
        context = {"min_salary": 70000, "max_salary": 90000}
        
        score = self.signal.score(document, context)
        self.assertGreaterEqual(score, 0)
        self.assertLess(score, 1.0)
    
    def test_score_above_range(self):
        """Test scoring salary above range."""
        document = {"id": "1", "salary": 100000}
        context = {"min_salary": 70000, "max_salary": 90000}
        
        score = self.signal.score(document, context)
        self.assertGreaterEqual(score, 0)
        self.assertLess(score, 1.0)


class TestSignalConfig(unittest.TestCase):
    """Test cases for SignalConfig."""
    
    def test_default_config(self):
        """Test default signal configuration."""
        config = SignalConfig()
        
        self.assertTrue(config.enabled)
        self.assertEqual(config.weight, 1.0)
        self.assertEqual(config.normalization, "min_max")
    
    def test_custom_config(self):
        """Test custom signal configuration."""
        config = SignalConfig(
            enabled=False,
            weight=2.0,
            normalization="z_score",
            params={"param1": "value1"},
        )
        
        self.assertFalse(config.enabled)
        self.assertEqual(config.weight, 2.0)
        self.assertEqual(config.normalization, "z_score")
    
    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = SignalConfig(weight=1.5)
        config_dict = config.to_dict()
        
        self.assertEqual(config_dict["weight"], 1.5)
        self.assertIn("enabled", config_dict)
        self.assertIn("normalization", config_dict)


if __name__ == "__main__":
    unittest.main()
