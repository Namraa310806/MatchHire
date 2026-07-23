"""
Tests for the Unified Search system.
"""

import unittest
from apps.search.query_engine.unified_search import (
    UnifiedSearchEngine,
    UnifiedSearchRequest,
    UnifiedSearchResponse,
    EntitySearchResult,
    EntityType,
)


class TestEntityType(unittest.TestCase):
    """Test cases for EntityType enum."""
    
    def test_entity_type_values(self):
        """Test entity type enum values."""
        self.assertEqual(EntityType.JOB.value, "job")
        self.assertEqual(EntityType.CANDIDATE.value, "candidate")
        self.assertEqual(EntityType.COMPANY.value, "company")


class TestUnifiedSearchRequest(unittest.TestCase):
    """Test cases for UnifiedSearchRequest."""
    
    def test_basic_request(self):
        """Test basic unified search request."""
        request = UnifiedSearchRequest(
            query="software engineer",
            entity_types=[EntityType.JOB, EntityType.CANDIDATE]
        )
        self.assertEqual(request.query, "software engineer")
        self.assertEqual(len(request.entity_types), 2)
    
    def test_request_validation_empty_query(self):
        """Test request validation with empty query."""
        with self.assertRaises(ValueError):
            UnifiedSearchRequest(
                query="",
                entity_types=[EntityType.JOB]
            )
    
    def test_request_validation_empty_entity_types(self):
        """Test request validation with empty entity types."""
        with self.assertRaises(ValueError):
            UnifiedSearchRequest(
                query="software engineer",
                entity_types=[]
            )
    
    def test_request_validation_limits(self):
        """Test request validation with invalid limits."""
        with self.assertRaises(ValueError):
            UnifiedSearchRequest(
                query="software engineer",
                entity_types=[EntityType.JOB],
                per_entity_limit=0
            )
        
        with self.assertRaises(ValueError):
            UnifiedSearchRequest(
                query="software engineer",
                entity_types=[EntityType.JOB],
                total_limit=0
            )
    
    def test_request_default_pagination(self):
        """Test request default pagination."""
        request = UnifiedSearchRequest(
            query="software engineer",
            entity_types=[EntityType.JOB]
        )
        self.assertIsNotNone(request.pagination)
        self.assertEqual(request.pagination["page"], 1)
    
    def test_request_to_dict(self):
        """Test request serialization."""
        request = UnifiedSearchRequest(
            query="software engineer",
            entity_types=[EntityType.JOB]
        )
        request_dict = request.to_dict()
        self.assertEqual(request_dict["query"], "software engineer")
        self.assertEqual(request_dict["entity_types"], ["job"])


class TestEntitySearchResult(unittest.TestCase):
    """Test cases for EntitySearchResult."""
    
    def test_basic_result(self):
        """Test basic entity search result."""
        result = EntitySearchResult(
            entity_type=EntityType.JOB,
            results=[{"id": 1, "title": "Software Engineer"}],
            total=1,
            took_ms=10
        )
        self.assertEqual(result.entity_type, EntityType.JOB)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.total, 1)
    
    def test_result_to_dict(self):
        """Test result serialization."""
        result = EntitySearchResult(
            entity_type=EntityType.JOB,
            results=[{"id": 1}],
            total=1,
            took_ms=10
        )
        result_dict = result.to_dict()
        self.assertEqual(result_dict["entity_type"], "job")
        self.assertEqual(result_dict["total"], 1)


class TestUnifiedSearchResponse(unittest.TestCase):
    """Test cases for UnifiedSearchResponse."""
    
    def test_basic_response(self):
        """Test basic unified search response."""
        entity_results = {
            EntityType.JOB: EntitySearchResult(
                entity_type=EntityType.JOB,
                results=[{"id": 1}],
                total=1,
                took_ms=5
            )
        }
        response = UnifiedSearchResponse(
            query="software engineer",
            entity_results=entity_results,
            total_results=1,
            took_ms=10
        )
        self.assertEqual(response.query, "software engineer")
        self.assertEqual(response.total_results, 1)
    
    def test_response_to_dict(self):
        """Test response serialization."""
        entity_results = {
            EntityType.JOB: EntitySearchResult(
                entity_type=EntityType.JOB,
                results=[{"id": 1}],
                total=1,
                took_ms=5
            )
        }
        response = UnifiedSearchResponse(
            query="software engineer",
            entity_results=entity_results,
            total_results=1,
            took_ms=10
        )
        response_dict = response.to_dict()
        self.assertEqual(response_dict["query"], "software engineer")
        self.assertIn("job", response_dict["entity_results"])
    
    def test_get_entity_results(self):
        """Test getting results for specific entity type."""
        entity_results = {
            EntityType.JOB: EntitySearchResult(
                entity_type=EntityType.JOB,
                results=[{"id": 1}],
                total=1,
                took_ms=5
            )
        }
        response = UnifiedSearchResponse(
            query="software engineer",
            entity_results=entity_results,
            total_results=1,
            took_ms=10
        )
        job_result = response.get_entity_results(EntityType.JOB)
        self.assertIsNotNone(job_result)
        self.assertEqual(job_result.total, 1)
    
    def test_get_all_results(self):
        """Test getting all results."""
        entity_results = {
            EntityType.JOB: EntitySearchResult(
                entity_type=EntityType.JOB,
                results=[{"id": 1}, {"id": 2}],
                total=2,
                took_ms=5
            ),
            EntityType.CANDIDATE: EntitySearchResult(
                entity_type=EntityType.CANDIDATE,
                results=[{"id": 3}],
                total=1,
                took_ms=3
            )
        }
        response = UnifiedSearchResponse(
            query="software engineer",
            entity_results=entity_results,
            total_results=3,
            took_ms=10
        )
        all_results = response.get_all_results()
        self.assertEqual(len(all_results), 3)
    
    def test_get_entity_count(self):
        """Test getting entity count."""
        entity_results = {
            EntityType.JOB: EntitySearchResult(
                entity_type=EntityType.JOB,
                results=[{"id": 1}],
                total=10,
                took_ms=5
            )
        }
        response = UnifiedSearchResponse(
            query="software engineer",
            entity_results=entity_results,
            total_results=10,
            took_ms=10
        )
        self.assertEqual(response.get_entity_count(EntityType.JOB), 10)
    
    def test_get_searched_entity_types(self):
        """Test getting searched entity types."""
        entity_results = {
            EntityType.JOB: EntitySearchResult(
                entity_type=EntityType.JOB,
                results=[{"id": 1}],
                total=1,
                took_ms=5
            ),
            EntityType.CANDIDATE: EntitySearchResult(
                entity_type=EntityType.CANDIDATE,
                results=[{"id": 2}],
                total=1,
                took_ms=3
            )
        }
        response = UnifiedSearchResponse(
            query="software engineer",
            entity_results=entity_results,
            total_results=2,
            took_ms=10
        )
        types = response.get_searched_entity_types()
        self.assertEqual(len(types), 2)
        self.assertIn(EntityType.JOB, types)
        self.assertIn(EntityType.CANDIDATE, types)


class TestUnifiedSearchEngine(unittest.TestCase):
    """Test cases for UnifiedSearchEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock provider registry
        class MockProvider:
            def search(self, entity_type, query, filters, sort, pagination, fields):
                return {
                    "results": [{"id": 1, "title": f"{entity_type} result"}],
                    "total": 1,
                    "took_ms": 5,
                    "metadata": {}
                }
        
        class MockRegistry:
            def get_current_provider(self):
                return "mock"
            
            def get_provider(self, name):
                return MockProvider()
        
        self.registry = MockRegistry()
        self.engine = UnifiedSearchEngine(self.registry)
    
    def test_search_single_entity(self):
        """Test searching single entity type."""
        request = UnifiedSearchRequest(
            query="software engineer",
            entity_types=[EntityType.JOB]
        )
        response = self.engine.search(request)
        self.assertIsInstance(response, UnifiedSearchResponse)
        self.assertEqual(len(response.entity_results), 1)
    
    def test_search_multiple_entities(self):
        """Test searching multiple entity types."""
        request = UnifiedSearchRequest(
            query="software engineer",
            entity_types=[EntityType.JOB, EntityType.CANDIDATE]
        )
        response = self.engine.search(request)
        self.assertIsInstance(response, UnifiedSearchResponse)
        self.assertEqual(len(response.entity_results), 2)
    
    def test_search_jobs_and_candidates(self):
        """Test convenience method for jobs and candidates."""
        response = self.engine.search_jobs_and_candidates("software engineer")
        self.assertIsInstance(response, UnifiedSearchResponse)
        self.assertEqual(len(response.entity_results), 2)
    
    def test_search_all_entities(self):
        """Test convenience method for all entities."""
        response = self.engine.search_all_entities("software engineer")
        self.assertIsInstance(response, UnifiedSearchResponse)
        self.assertGreater(len(response.entity_results), 0)
    
    def test_total_limit(self):
        """Test total limit enforcement."""
        request = UnifiedSearchRequest(
            query="software engineer",
            entity_types=[EntityType.JOB, EntityType.CANDIDATE],
            per_entity_limit=10,
            total_limit=5
        )
        response = self.engine.search(request)
        total_results = sum(len(r.results) for r in response.entity_results.values())
        self.assertLessEqual(total_results, 5)


if __name__ == "__main__":
    unittest.main()
