"""
Tests for the Autocomplete system.
"""

import unittest
from apps.search.query_engine.autocomplete import (
    AutocompleteEngine,
    AutocompleteRequest,
    AutocompleteResponse,
    AutocompleteSuggestion,
    AutocompleteContext,
    AutocompleteType,
    SuggestionSource,
)


class TestAutocompleteContext(unittest.TestCase):
    """Test cases for AutocompleteContext."""
    
    def test_basic_context(self):
        """Test basic autocomplete context."""
        context = AutocompleteContext(user_id="user123")
        self.assertEqual(context.user_id, "user123")
        self.assertEqual(context.entity_type, None)
    
    def test_context_with_entity_type(self):
        """Test context with entity type."""
        context = AutocompleteContext(entity_type="job")
        self.assertEqual(context.entity_type, "job")
    
    def test_context_to_dict(self):
        """Test context serialization."""
        context = AutocompleteContext(user_id="user123", entity_type="job")
        context_dict = context.to_dict()
        self.assertEqual(context_dict["user_id"], "user123")
        self.assertEqual(context_dict["entity_type"], "job")


class TestAutocompleteSuggestion(unittest.TestCase):
    """Test cases for AutocompleteSuggestion."""
    
    def test_basic_suggestion(self):
        """Test basic suggestion."""
        suggestion = AutocompleteSuggestion(value="software engineer")
        self.assertEqual(suggestion.value, "software engineer")
        self.assertEqual(suggestion.score, 0.0)
        self.assertEqual(suggestion.type, AutocompleteType.PREFIX)
    
    def test_suggestion_with_score(self):
        """Test suggestion with score."""
        suggestion = AutocompleteSuggestion(value="software engineer", score=1.5)
        self.assertEqual(suggestion.score, 1.5)
    
    def test_suggestion_to_dict(self):
        """Test suggestion serialization."""
        suggestion = AutocompleteSuggestion(
            value="software engineer",
            score=1.5,
            type=AutocompleteType.POPULAR
        )
        suggestion_dict = suggestion.to_dict()
        self.assertEqual(suggestion_dict["value"], "software engineer")
        self.assertEqual(suggestion_dict["score"], 1.5)
        self.assertEqual(suggestion_dict["type"], "popular")
    
    def test_suggestion_comparison(self):
        """Test suggestion comparison."""
        suggestion1 = AutocompleteSuggestion(value="a", score=1.0)
        suggestion2 = AutocompleteSuggestion(value="b", score=2.0)
        self.assertTrue(suggestion2 < suggestion1)  # Higher score first


class TestAutocompleteRequest(unittest.TestCase):
    """Test cases for AutocompleteRequest."""
    
    def test_basic_request(self):
        """Test basic autocomplete request."""
        request = AutocompleteRequest(
            prefix="soft",
            field="title",
            entity_type="job"
        )
        self.assertEqual(request.prefix, "soft")
        self.assertEqual(request.field, "title")
        self.assertEqual(request.entity_type, "job")
    
    def test_request_validation_empty_prefix(self):
        """Test request validation with empty prefix."""
        with self.assertRaises(ValueError):
            AutocompleteRequest(prefix="", field="title", entity_type="job")
    
    def test_request_validation_empty_field(self):
        """Test request validation with empty field."""
        with self.assertRaises(ValueError):
            AutocompleteRequest(prefix="soft", field="", entity_type="job")
    
    def test_request_validation_limit(self):
        """Test request validation with invalid limit."""
        with self.assertRaises(ValueError):
            AutocompleteRequest(prefix="soft", field="title", entity_type="job", limit=0)
        
        with self.assertRaises(ValueError):
            AutocompleteRequest(prefix="soft", field="title", entity_type="job", limit=100)


class TestAutocompleteResponse(unittest.TestCase):
    """Test cases for AutocompleteResponse."""
    
    def test_basic_response(self):
        """Test basic autocomplete response."""
        suggestions = [
            AutocompleteSuggestion(value="software engineer"),
            AutocompleteSuggestion(value="software developer"),
        ]
        response = AutocompleteResponse(
            suggestions=suggestions,
            took_ms=10,
            prefix="soft",
            field="title",
            entity_type="job"
        )
        self.assertEqual(len(response.suggestions), 2)
        self.assertEqual(response.took_ms, 10)
    
    def test_response_deduplicate(self):
        """Test response deduplication."""
        suggestions = [
            AutocompleteSuggestion(value="software engineer"),
            AutocompleteSuggestion(value="software engineer"),
            AutocompleteSuggestion(value="software developer"),
        ]
        response = AutocompleteResponse(
            suggestions=suggestions,
            took_ms=10,
            prefix="soft",
            field="title",
            entity_type="job"
        )
        response.deduplicate()
        self.assertEqual(len(response.suggestions), 2)
    
    def test_response_sort_by_score(self):
        """Test response sorting by score."""
        suggestions = [
            AutocompleteSuggestion(value="a", score=1.0),
            AutocompleteSuggestion(value="b", score=3.0),
            AutocompleteSuggestion(value="c", score=2.0),
        ]
        response = AutocompleteResponse(
            suggestions=suggestions,
            took_ms=10,
            prefix="soft",
            field="title",
            entity_type="job"
        )
        response.sort_by_score()
        self.assertEqual(response.suggestions[0].value, "b")
        self.assertEqual(response.suggestions[1].value, "c")
        self.assertEqual(response.suggestions[2].value, "a")
    
    def test_response_limit_to(self):
        """Test response limiting."""
        suggestions = [
            AutocompleteSuggestion(value=f"item{i}", score=float(i))
            for i in range(10)
        ]
        response = AutocompleteResponse(
            suggestions=suggestions,
            took_ms=10,
            prefix="soft",
            field="title",
            entity_type="job"
        )
        response.limit_to(5)
        self.assertEqual(len(response.suggestions), 5)
    
    def test_response_filter_by_score(self):
        """Test response filtering by score."""
        suggestions = [
            AutocompleteSuggestion(value="a", score=0.5),
            AutocompleteSuggestion(value="b", score=1.5),
            AutocompleteSuggestion(value="c", score=2.5),
        ]
        response = AutocompleteResponse(
            suggestions=suggestions,
            took_ms=10,
            prefix="soft",
            field="title",
            entity_type="job"
        )
        response.filter_by_score(1.0)
        self.assertEqual(len(response.suggestions), 2)


class TestAutocompleteEngine(unittest.TestCase):
    """Test cases for AutocompleteEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = AutocompleteEngine()
    
    def test_add_popular_query(self):
        """Test adding popular query."""
        self.engine.add_popular_query("software engineer", weight=1.0)
        self.assertIn("software engineer", self.engine._popular_queries)
        self.assertEqual(self.engine._popular_queries["software engineer"], 1.0)
    
    def test_add_popular_query_increment(self):
        """Test incrementing popular query weight."""
        self.engine.add_popular_query("software engineer", weight=1.0)
        self.engine.add_popular_query("software engineer", weight=0.5)
        self.assertEqual(self.engine._popular_queries["software engineer"], 1.5)
    
    def test_add_recent_search(self):
        """Test adding recent search."""
        self.engine.add_recent_search("user123", "python developer")
        self.assertIn("user123", self.engine._recent_searches)
        self.assertEqual(len(self.engine._recent_searches["user123"]), 1)
    
    def test_add_recent_search_limit(self):
        """Test recent search limit."""
        for i in range(60):
            self.engine.add_recent_search("user123", f"query{i}")
        self.assertEqual(len(self.engine._recent_searches["user123"]), 50)
    
    def test_add_entity_suggestions(self):
        """Test adding entity suggestions."""
        self.engine.add_entity_suggestions("job", ["software engineer", "data scientist"])
        self.assertIn("job", self.engine._entity_suggestions)
        self.assertEqual(len(self.engine._entity_suggestions["job"]), 2)
    
    def test_get_popular_suggestions(self):
        """Test getting popular suggestions."""
        self.engine.add_popular_query("software engineer", weight=2.0)
        self.engine.add_popular_query("python developer", weight=1.0)
        self.engine.add_popular_query("java developer", weight=1.5)
        
        suggestions = self.engine.get_popular_suggestions("software", limit=5)
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0].value, "software engineer")
    
    def test_get_entity_suggestions(self):
        """Test getting entity suggestions."""
        self.engine.add_entity_suggestions("job", ["software engineer", "data scientist"])
        
        suggestions = self.engine.get_entity_suggestions("soft", "job", limit=10)
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0].value, "software engineer")
    
    def test_generate_suggestions(self):
        """Test generating suggestions."""
        self.engine.add_entity_suggestions("job", ["software engineer", "data scientist"])
        
        request = AutocompleteRequest(
            prefix="soft",
            field="title",
            entity_type="job",
            limit=10
        )
        response = self.engine.generate_suggestions(request)
        self.assertIsInstance(response, AutocompleteResponse)
        self.assertEqual(response.prefix, "soft")
    
    def test_cleanup_old_searches(self):
        """Test cleaning up old searches."""
        self.engine.add_recent_search("user123", "python developer")
        self.engine.cleanup_old_searches(days=0)
        self.assertEqual(len(self.engine._recent_searches.get("user123", [])), 0)
    
    def test_decay_popular_queries(self):
        """Test decaying popular queries."""
        self.engine.add_popular_query("software engineer", weight=10.0)
        self.engine.decay_popular_queries(factor=0.5)
        self.assertEqual(self.engine._popular_queries["software engineer"], 5.0)
    
    def test_decay_popular_queries_remove_low(self):
        """Test removing low-score popular queries."""
        self.engine.add_popular_query("software engineer", weight=0.005)
        self.engine.decay_popular_queries(factor=0.5)
        self.assertNotIn("software engineer", self.engine._popular_queries)


if __name__ == "__main__":
    unittest.main()
