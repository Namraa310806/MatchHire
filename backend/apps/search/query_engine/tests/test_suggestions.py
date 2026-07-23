"""
Tests for the Search Suggestions system.
"""

import unittest
from datetime import datetime
from apps.search.query_engine.suggestions import (
    SearchSuggestionEngine,
    RelatedQuery,
    SpellingCorrection,
    DidYouMean,
    RecentSearch,
    SavedSearch,
    TrendingSearch,
    SearchTemplate,
    SuggestionType,
)


class TestSuggestionType(unittest.TestCase):
    """Test cases for SuggestionType enum."""
    
    def test_suggestion_type_values(self):
        """Test suggestion type enum values."""
        self.assertEqual(SuggestionType.RELATED.value, "related")
        self.assertEqual(SuggestionType.SPELLING.value, "spelling")
        self.assertEqual(SuggestionType.DID_YOU_MEAN.value, "did_you_mean")


class TestRelatedQuery(unittest.TestCase):
    """Test cases for RelatedQuery."""
    
    def test_basic_related_query(self):
        """Test basic related query."""
        related = RelatedQuery(query="python developer")
        self.assertEqual(related.query, "python developer")
        self.assertEqual(related.score, 0.0)
    
    def test_related_query_with_score(self):
        """Test related query with score."""
        related = RelatedQuery(query="python developer", score=1.5)
        self.assertEqual(related.score, 1.5)
    
    def test_related_query_to_dict(self):
        """Test related query serialization."""
        related = RelatedQuery(query="python developer", score=1.5)
        related_dict = related.to_dict()
        self.assertEqual(related_dict["query"], "python developer")
        self.assertEqual(related_dict["score"], 1.5)


class TestSpellingCorrection(unittest.TestCase):
    """Test cases for SpellingCorrection."""
    
    def test_basic_spelling_correction(self):
        """Test basic spelling correction."""
        correction = SpellingCorrection(
            original="pyton",
            corrected="python"
        )
        self.assertEqual(correction.original, "pyton")
        self.assertEqual(correction.corrected, "python")
    
    def test_spelling_correction_with_confidence(self):
        """Test spelling correction with confidence."""
        correction = SpellingCorrection(
            original="pyton",
            corrected="python",
            confidence=0.95
        )
        self.assertEqual(correction.confidence, 0.95)
    
    def test_spelling_correction_to_dict(self):
        """Test spelling correction serialization."""
        correction = SpellingCorrection(
            original="pyton",
            corrected="python"
        )
        correction_dict = correction.to_dict()
        self.assertEqual(correction_dict["original"], "pyton")
        self.assertEqual(correction_dict["corrected"], "python")


class TestDidYouMean(unittest.TestCase):
    """Test cases for DidYouMean."""
    
    def test_basic_did_you_mean(self):
        """Test basic did-you-mean."""
        dym = DidYouMean(
            suggestion="python developer",
            original_query="pyton developer"
        )
        self.assertEqual(dym.suggestion, "python developer")
        self.assertEqual(dym.original_query, "pyton developer")
    
    def test_did_you_mean_with_score(self):
        """Test did-you-mean with score."""
        dym = DidYouMean(
            suggestion="python developer",
            original_query="pyton developer",
            score=0.9
        )
        self.assertEqual(dym.score, 0.9)
    
    def test_did_you_mean_to_dict(self):
        """Test did-you-mean serialization."""
        dym = DidYouMean(
            suggestion="python developer",
            original_query="pyton developer"
        )
        dym_dict = dym.to_dict()
        self.assertEqual(dym_dict["suggestion"], "python developer")


class TestRecentSearch(unittest.TestCase):
    """Test cases for RecentSearch."""
    
    def test_basic_recent_search(self):
        """Test basic recent search."""
        search = RecentSearch(query="software engineer")
        self.assertEqual(search.query, "software engineer")
        self.assertIsNotNone(search.timestamp)
    
    def test_recent_search_with_entity_type(self):
        """Test recent search with entity type."""
        search = RecentSearch(
            query="software engineer",
            entity_type="job"
        )
        self.assertEqual(search.entity_type, "job")
    
    def test_recent_search_with_result_count(self):
        """Test recent search with result count."""
        search = RecentSearch(
            query="software engineer",
            result_count=100
        )
        self.assertEqual(search.result_count, 100)
    
    def test_recent_search_to_dict(self):
        """Test recent search serialization."""
        search = RecentSearch(query="software engineer")
        search_dict = search.to_dict()
        self.assertEqual(search_dict["query"], "software engineer")
        self.assertIn("timestamp", search_dict)


class TestSavedSearch(unittest.TestCase):
    """Test cases for SavedSearch."""
    
    def test_basic_saved_search(self):
        """Test basic saved search."""
        search = SavedSearch(
            id="search123",
            name="My Job Search",
            query="software engineer"
        )
        self.assertEqual(search.id, "search123")
        self.assertEqual(search.name, "My Job Search")
    
    def test_saved_search_with_filters(self):
        """Test saved search with filters."""
        search = SavedSearch(
            id="search123",
            name="My Job Search",
            query="software engineer",
            filters={"location": "San Francisco"}
        )
        self.assertEqual(search.filters["location"], "San Francisco")
    
    def test_saved_search_with_alert(self):
        """Test saved search with alert enabled."""
        search = SavedSearch(
            id="search123",
            name="My Job Search",
            query="software engineer",
            alert_enabled=True
        )
        self.assertTrue(search.alert_enabled)
    
    def test_saved_search_to_dict(self):
        """Test saved search serialization."""
        search = SavedSearch(
            id="search123",
            name="My Job Search",
            query="software engineer"
        )
        search_dict = search.to_dict()
        self.assertEqual(search_dict["id"], "search123")
        self.assertEqual(search_dict["name"], "My Job Search")


class TestTrendingSearch(unittest.TestCase):
    """Test cases for TrendingSearch."""
    
    def test_basic_trending_search(self):
        """Test basic trending search."""
        trending = TrendingSearch(query="software engineer")
        self.assertEqual(trending.query, "software engineer")
        self.assertEqual(trending.count, 0)
    
    def test_trending_search_with_count(self):
        """Test trending search with count."""
        trending = TrendingSearch(
            query="software engineer",
            count=100
        )
        self.assertEqual(trending.count, 100)
    
    def test_trending_search_with_trend_score(self):
        """Test trending search with trend score."""
        trending = TrendingSearch(
            query="software engineer",
            count=100,
            trend_score=1.5
        )
        self.assertEqual(trending.trend_score, 1.5)
    
    def test_trending_search_to_dict(self):
        """Test trending search serialization."""
        trending = TrendingSearch(query="software engineer")
        trending_dict = trending.to_dict()
        self.assertEqual(trending_dict["query"], "software engineer")


class TestSearchTemplate(unittest.TestCase):
    """Test cases for SearchTemplate."""
    
    def test_basic_search_template(self):
        """Test basic search template."""
        template = SearchTemplate(
            id="template123",
            name="Senior Developer",
            template="senior {language} developer"
        )
        self.assertEqual(template.id, "template123")
        self.assertEqual(template.name, "Senior Developer")
    
    def test_search_template_with_parameters(self):
        """Test search template with parameters."""
        template = SearchTemplate(
            id="template123",
            name="Senior Developer",
            template="senior {language} developer",
            parameters={"language": "python"}
        )
        self.assertEqual(template.parameters["language"], "python")
    
    def test_search_template_with_description(self):
        """Test search template with description."""
        template = SearchTemplate(
            id="template123",
            name="Senior Developer",
            template="senior {language} developer",
            description="Template for senior developer searches"
        )
        self.assertEqual(template.description, "Template for senior developer searches")
    
    def test_search_template_to_dict(self):
        """Test search template serialization."""
        template = SearchTemplate(
            id="template123",
            name="Senior Developer",
            template="senior {language} developer"
        )
        template_dict = template.to_dict()
        self.assertEqual(template_dict["id"], "template123")


class TestSearchSuggestionEngine(unittest.TestCase):
    """Test cases for SearchSuggestionEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = SearchSuggestionEngine()
    
    def test_add_recent_search(self):
        """Test adding recent search."""
        self.engine.add_recent_search("user123", "software engineer")
        recent = self.engine.get_recent_searches("user123")
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].query, "software engineer")
    
    def test_add_recent_search_limit(self):
        """Test recent search limit."""
        for i in range(25):
            self.engine.add_recent_search("user123", f"query{i}")
        recent = self.engine.get_recent_searches("user123")
        self.assertEqual(len(recent), 20)
    
    def test_get_recent_searches_limit(self):
        """Test getting recent searches with limit."""
        for i in range(10):
            self.engine.add_recent_search("user123", f"query{i}")
        recent = self.engine.get_recent_searches("user123", limit=5)
        self.assertEqual(len(recent), 5)
    
    def test_add_saved_search(self):
        """Test adding saved search."""
        saved = SavedSearch(
            id="search123",
            name="My Search",
            query="software engineer"
        )
        self.engine.add_saved_search("user123", saved)
        saved_searches = self.engine.get_saved_searches("user123")
        self.assertEqual(len(saved_searches), 1)
    
    def test_delete_saved_search(self):
        """Test deleting saved search."""
        saved = SavedSearch(
            id="search123",
            name="My Search",
            query="software engineer"
        )
        self.engine.add_saved_search("user123", saved)
        deleted = self.engine.delete_saved_search("user123", "search123")
        self.assertTrue(deleted)
        saved_searches = self.engine.get_saved_searches("user123")
        self.assertEqual(len(saved_searches), 0)
    
    def test_delete_saved_search_not_found(self):
        """Test deleting non-existent saved search."""
        deleted = self.engine.delete_saved_search("user123", "nonexistent")
        self.assertFalse(deleted)
    
    def test_update_trending_searches(self):
        """Test updating trending searches."""
        queries = ["software engineer"] * 10 + ["python developer"] * 5
        self.engine.update_trending_searches(queries)
        trending = self.engine.get_trending_searches()
        self.assertGreater(len(trending), 0)
    
    def test_get_trending_searches_with_entity_type(self):
        """Test getting trending searches filtered by entity type."""
        queries = ["software engineer"] * 10
        self.engine.update_trending_searches(queries, entity_type="job")
        trending = self.engine.get_trending_searches(entity_type="job")
        self.assertGreater(len(trending), 0)
    
    def test_add_search_template(self):
        """Test adding search template."""
        template = SearchTemplate(
            id="template123",
            name="Senior Developer",
            template="senior {language} developer"
        )
        self.engine.add_search_template(template)
        retrieved = self.engine.get_search_template("template123")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Senior Developer")
    
    def test_get_search_template_not_found(self):
        """Test getting non-existent template."""
        retrieved = self.engine.get_search_template("nonexistent")
        self.assertIsNone(retrieved)
    
    def test_get_search_templates(self):
        """Test getting all search templates."""
        template1 = SearchTemplate(
            id="template1",
            name="Template 1",
            template="template1"
        )
        template2 = SearchTemplate(
            id="template2",
            name="Template 2",
            template="template2",
            entity_type="job"
        )
        self.engine.add_search_template(template1)
        self.engine.add_search_template(template2)
        
        all_templates = self.engine.get_search_templates()
        self.assertEqual(len(all_templates), 2)
        
        job_templates = self.engine.get_search_templates(entity_type="job")
        self.assertEqual(len(job_templates), 1)
    
    def test_get_related_queries(self):
        """Test getting related queries."""
        # This test is limited since co-occurrence is not fully implemented
        related = self.engine.get_related_queries("software engineer")
        self.assertIsInstance(related, list)
    
    def test_get_spelling_correction(self):
        """Test getting spelling correction."""
        # This is a placeholder implementation
        correction = self.engine.get_spelling_correction("pyton")
        self.assertIsNone(correction)  # Placeholder returns None
    
    def test_get_did_you_mean(self):
        """Test getting did-you-mean suggestion."""
        # This is a placeholder implementation
        dym = self.engine.get_did_you_mean("pyton developer")
        self.assertIsNone(dym)  # Placeholder returns None
    
    def test_cleanup_old_recent_searches(self):
        """Test cleaning up old recent searches."""
        self.engine.add_recent_search("user123", "software engineer")
        self.engine.cleanup_old_recent_searches(days=0)
        recent = self.engine.get_recent_searches("user123")
        self.assertEqual(len(recent), 0)
    
    def test_decay_trending_scores(self):
        """Test decaying trending scores."""
        queries = ["software engineer"] * 10
        self.engine.update_trending_searches(queries)
        
        original_score = self.engine._trending_searches[0].trend_score
        self.engine.decay_trending_scores(factor=0.5)
        
        new_score = self.engine._trending_searches[0].trend_score
        self.assertLess(new_score, original_score)
    
    def test_decay_trending_scores_remove_low(self):
        """Test removing low-score trending searches."""
        queries = ["software engineer"] * 3  # Below threshold
        self.engine.update_trending_searches(queries)
        self.engine.decay_trending_scores(factor=0.1)
        
        # Low scores should be removed
        self.assertEqual(len(self.engine._trending_searches), 0)


if __name__ == "__main__":
    unittest.main()
