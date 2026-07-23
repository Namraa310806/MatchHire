"""
Tests for the Query Engine.
"""

import unittest
from unittest.mock import Mock, MagicMock
from apps.search.query_engine.engine import (
    QueryEngine,
    SearchExecutionContext,
    EngineResult,
)
from apps.search.query_engine.performance import PerformanceConfig


class TestSearchExecutionContext(unittest.TestCase):
    """Test cases for SearchExecutionContext."""
    
    def test_basic_context(self):
        """Test basic search execution context."""
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer"
        )
        self.assertEqual(context.entity_type, "job")
        self.assertEqual(context.query, "software engineer")
    
    def test_context_with_filters(self):
        """Test context with filters."""
        from apps.search.query_engine.filters import Filter, FilterOperator
        
        filter_obj = Filter(field="status", operator=FilterOperator.EQ, value="active")
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer",
            filters=[filter_obj]
        )
        self.assertEqual(len(context.filters), 1)
    
    def test_context_with_sort(self):
        """Test context with sort conditions."""
        sort_conditions = [{"field": "salary", "direction": "desc"}]
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer",
            sort_conditions=sort_conditions
        )
        self.assertEqual(len(context.sort_conditions), 1)
    
    def test_context_with_pagination(self):
        """Test context with pagination."""
        pagination = {"offset": 0, "limit": 20}
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer",
            pagination=pagination
        )
        self.assertEqual(context.pagination, pagination)
    
    def test_context_with_facets(self):
        """Test context with facets."""
        from apps.search.query_engine.facets import FacetConfig
        
        facet = FacetConfig(field="location", name="Location")
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer",
            facets=[facet]
        )
        self.assertEqual(len(context.facets), 1)
    
    def test_context_with_aggregations(self):
        """Test context with aggregations."""
        from apps.search.query_engine.aggregations import TermsAggregation
        
        agg = TermsAggregation(name="location_agg", field="location")
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer",
            aggregations=[agg]
        )
        self.assertEqual(len(context.aggregations), 1)
    
    def test_context_with_highlights(self):
        """Test context with highlights."""
        from apps.search.query_engine.highlighting import HighlightConfig
        
        highlight = HighlightConfig(field="title")
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer",
            highlights=[highlight]
        )
        self.assertEqual(len(context.highlights), 1)
    
    def test_context_with_user_id(self):
        """Test context with user ID."""
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer",
            user_id="user123"
        )
        self.assertEqual(context.user_id, "user123")
    
    def test_context_to_dict(self):
        """Test context serialization."""
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer"
        )
        context_dict = context.to_dict()
        self.assertEqual(context_dict["entity_type"], "job")
        self.assertEqual(context_dict["query"], "software engineer")


class TestEngineResult(unittest.TestCase):
    """Test cases for EngineResult."""
    
    def test_basic_result(self):
        """Test basic engine result."""
        result = EngineResult(
            results=[{"id": 1, "title": "Software Engineer"}],
            total=1,
            took_ms=10
        )
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.total, 1)
        self.assertEqual(result.took_ms, 10)
    
    def test_result_with_facets(self):
        """Test result with facets."""
        from apps.search.query_engine.facets import FacetResponse, FacetValue
        
        facet = FacetResponse(
            field="location",
            name="Location",
            values=[FacetValue(value="SF", count=10)],
            total=10
        )
        result = EngineResult(
            results=[],
            total=0,
            took_ms=10,
            facets=[facet]
        )
        self.assertEqual(len(result.facets), 1)
    
    def test_result_with_aggregations(self):
        """Test result with aggregations."""
        aggregations = {"location_count": 10}
        result = EngineResult(
            results=[],
            total=0,
            took_ms=10,
            aggregations=aggregations
        )
        self.assertEqual(result.aggregations["location_count"], 10)
    
    def test_result_with_highlights(self):
        """Test result with highlights."""
        from apps.search.query_engine.highlighting import HighlightResult, FieldHighlight
        
        highlights = {
            "doc1": HighlightResult(
                document_id="doc1",
                fields=[FieldHighlight(field="title", fragments=["Software"])]
            )
        }
        result = EngineResult(
            results=[],
            total=0,
            took_ms=10,
            highlights=highlights
        )
        self.assertEqual(len(result.highlights), 1)
    
    def test_result_with_metadata(self):
        """Test result with metadata."""
        metadata = {"provider": "elasticsearch", "cached": False}
        result = EngineResult(
            results=[],
            total=0,
            took_ms=10,
            metadata=metadata
        )
        self.assertEqual(result.metadata["provider"], "elasticsearch")
    
    def test_result_to_dict(self):
        """Test result serialization."""
        result = EngineResult(
            results=[{"id": 1}],
            total=1,
            took_ms=10
        )
        result_dict = result.to_dict()
        self.assertEqual(result_dict["total"], 1)
        self.assertEqual(result_dict["took_ms"], 10)


class TestQueryEngine(unittest.TestCase):
    """Test cases for QueryEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock provider registry
        self.mock_provider = Mock()
        self.mock_provider.search.return_value = {
            "results": [{"id": 1, "title": "Software Engineer"}],
            "total": 1,
            "took_ms": 5,
            "metadata": {}
        }
        
        self.mock_registry = Mock()
        self.mock_registry.get_current_provider.return_value = "mock"
        self.mock_registry.get_provider.return_value = self.mock_provider
        
        self.config = PerformanceConfig(cache_enabled=False)
        self.engine = QueryEngine(self.mock_registry, self.config)
    
    def test_search_basic(self):
        """Test basic search."""
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer"
        )
        result = self.engine.search(context, use_cache=False)
        
        self.assertIsInstance(result, EngineResult)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.total, 1)
    
    def test_search_with_filters(self):
        """Test search with filters."""
        from apps.search.query_engine.filters import Filter, FilterOperator
        
        filter_obj = Filter(field="status", operator=FilterOperator.EQ, value="active")
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer",
            filters=[filter_obj]
        )
        result = self.engine.search(context, use_cache=False)
        
        self.assertIsInstance(result, EngineResult)
        self.mock_provider.search.assert_called_once()
    
    def test_search_with_sort(self):
        """Test search with sort."""
        sort_conditions = [{"field": "salary", "direction": "desc"}]
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer",
            sort_conditions=sort_conditions
        )
        result = self.engine.search(context, use_cache=False)
        
        self.assertIsInstance(result, EngineResult)
    
    def test_search_with_pagination(self):
        """Test search with pagination."""
        pagination = {"offset": 0, "limit": 20}
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer",
            pagination=pagination
        )
        result = self.engine.search(context, use_cache=False)
        
        self.assertIsInstance(result, EngineResult)
    
    def test_search_cache_hit(self):
        """Test search with cache hit."""
        config = PerformanceConfig(cache_enabled=True)
        engine = QueryEngine(self.mock_registry, config)
        
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer"
        )
        
        # First call - cache miss
        result1 = engine.search(context, use_cache=True)
        
        # Second call - cache hit
        result2 = engine.search(context, use_cache=True)
        
        self.assertEqual(result1.total, result2.total)
    
    def test_search_cache_disabled(self):
        """Test search with cache disabled."""
        config = PerformanceConfig(cache_enabled=False)
        engine = QueryEngine(self.mock_registry, config)
        
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer"
        )
        
        result = engine.search(context, use_cache=True)
        
        self.assertIsInstance(result, EngineResult)
    
    def test_autocomplete(self):
        """Test autocomplete."""
        from apps.search.query_engine.autocomplete import AutocompleteRequest
        
        request = AutocompleteRequest(
            prefix="soft",
            field="title",
            entity_type="job"
        )
        response = self.engine.autocomplete(request)
        
        self.assertIsNotNone(response)
        self.assertEqual(response.prefix, "soft")
    
    def test_unified_search(self):
        """Test unified search."""
        from apps.search.query_engine.unified_search import UnifiedSearchRequest, EntityType
        
        request = UnifiedSearchRequest(
            query="software engineer",
            entity_types=[EntityType.JOB]
        )
        response = self.engine.unified_search(request)
        
        self.assertIsNotNone(response)
    
    def test_add_ranking_hook(self):
        """Test adding ranking hook."""
        def hook(context):
            pass
        
        self.engine.add_ranking_hook("pre_rank", hook)
        
        hooks = self.engine.get_ranking_hooks()
        self.assertEqual(len(hooks._pre_rank_hooks), 1)
    
    def test_add_post_rank_hook(self):
        """Test adding post-rank hook."""
        def hook(results, context):
            pass
        
        self.engine.add_ranking_hook("post_rank", hook)
        
        hooks = self.engine.get_ranking_hooks()
        self.assertEqual(len(hooks._post_rank_hooks), 1)
    
    def test_add_score_modifier(self):
        """Test adding score modifier."""
        def modifier(results, context):
            pass
        
        self.engine.add_ranking_hook("score_modifier", modifier)
        
        hooks = self.engine.get_ranking_hooks()
        self.assertEqual(len(hooks._score_modifiers), 1)
    
    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        config = PerformanceConfig(cache_enabled=True)
        engine = QueryEngine(self.mock_registry, config)
        
        stats = engine.get_cache_stats()
        self.assertIn("hits", stats)
        self.assertIn("misses", stats)
        self.assertIn("size", stats)
    
    def test_clear_cache(self):
        """Test clearing cache."""
        config = PerformanceConfig(cache_enabled=True)
        engine = QueryEngine(self.mock_registry, config)
        
        engine.clear_cache()
        
        stats = engine.get_cache_stats()
        self.assertEqual(stats["size"], 0)
    
    def test_invalidate_cache(self):
        """Test invalidating cache."""
        config = PerformanceConfig(cache_enabled=True)
        engine = QueryEngine(self.mock_registry, config)
        
        engine.invalidate_cache(entity_type="job")
        
        stats = engine.get_cache_stats()
        self.assertEqual(stats["size"], 0)
    
    def test_get_suggestion_engine(self):
        """Test getting suggestion engine."""
        suggestion_engine = self.engine.get_suggestion_engine()
        self.assertIsNotNone(suggestion_engine)
    
    def test_get_autocomplete_engine(self):
        """Test getting autocomplete engine."""
        autocomplete_engine = self.engine.get_autocomplete_engine()
        self.assertIsNotNone(autocomplete_engine)
    
    def test_get_ranking_hooks(self):
        """Test getting ranking hooks."""
        hooks = self.engine.get_ranking_hooks()
        self.assertIsNotNone(hooks)
    
    def test_search_with_provider_error(self):
        """Test search with provider error."""
        self.mock_provider.search.side_effect = Exception("Provider error")
        
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer"
        )
        
        with self.assertRaises(Exception):
            self.engine.search(context, use_cache=False)
    
    def test_search_no_provider_configured(self):
        """Test search with no provider configured."""
        self.mock_registry.get_current_provider.return_value = None
        
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer"
        )
        
        with self.assertRaises(ValueError):
            self.engine.search(context, use_cache=False)
    
    def test_apply_pre_rank_hooks(self):
        """Test applying pre-rank hooks."""
        executed = []
        
        def hook(context):
            executed.append("pre_rank")
        
        self.engine.add_ranking_hook("pre_rank", hook)
        
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer"
        )
        self.engine.search(context, use_cache=False)
        
        self.assertIn("pre_rank", executed)
    
    def test_apply_post_rank_hooks(self):
        """Test applying post-rank hooks."""
        executed = []
        
        def hook(results, context):
            executed.append("post_rank")
        
        self.engine.add_ranking_hook("post_rank", hook)
        
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer"
        )
        self.engine.search(context, use_cache=False)
        
        self.assertIn("post_rank", executed)
    
    def test_apply_score_modifiers(self):
        """Test applying score modifiers."""
        executed = []
        
        def modifier(results, context):
            executed.append("score_modifier")
        
        self.engine.add_ranking_hook("score_modifier", modifier)
        
        context = SearchExecutionContext(
            entity_type="job",
            query="software engineer"
        )
        self.engine.search(context, use_cache=False)
        
        self.assertIn("score_modifier", executed)


if __name__ == "__main__":
    unittest.main()
