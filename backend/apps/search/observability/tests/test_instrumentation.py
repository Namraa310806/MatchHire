"""
Tests for Instrumentation Layer.
"""

import unittest
from apps.search.observability.core import ObservabilityConfig, ObservabilityComponent
from apps.search.observability.instrumentation import (
    instrument_search,
    instrument_ranking,
    instrument_recommendation,
    instrument_provider,
    observe_operation,
    ObservabilityMiddleware,
    CacheInstrumentation,
    PipelineInstrumentation,
)


class TestInstrumentationDecorators(unittest.TestCase):
    """Tests for instrumentation decorators."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ObservabilityConfig(enabled=True)
    
    def test_instrument_search(self):
        """Test search instrumentation decorator."""
        @instrument_search
        def test_search(query):
            return {"results": [], "total": 0}
        
        result = test_search("test query")
        
        self.assertIsNotNone(result)
        self.assertIn("results", result)
    
    def test_instrument_search_with_error(self):
        """Test search instrumentation with error."""
        @instrument_search
        def failing_search(query):
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            failing_search("test query")
    
    def test_instrument_ranking(self):
        """Test ranking instrumentation decorator."""
        @instrument_ranking
        def test_ranking(results):
            return results
        
        result = test_ranking([{"id": 1}])
        
        self.assertIsNotNone(result)
    
    def test_instrument_recommendation(self):
        """Test recommendation instrumentation decorator."""
        @instrument_recommendation
        def test_recommendate(request):
            return {"recommendations": []}
        
        result = test_recommendate({"entity_id": "test"})
        
        self.assertIsNotNone(result)
    
    def test_instrument_provider(self):
        """Test provider instrumentation decorator."""
        class TestProvider:
            @instrument_provider
            def search(self, query):
                return {"results": []}
        
        provider = TestProvider()
        result = provider.search("test query")
        
        self.assertIsNotNone(result)


class TestObserveOperation(unittest.TestCase):
    """Tests for observe_operation context manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ObservabilityConfig(enabled=True)
    
    def test_observe_operation(self):
        """Test observe_operation context manager."""
        with observe_operation(
            operation_name="test_operation",
            component=ObservabilityComponent.SEARCH,
        ) as span:
            self.assertIsNotNone(span)
            self.assertEqual(span.name, "test_operation")
    
    def test_observe_operation_with_error(self):
        """Test observe_operation with error."""
        try:
            with observe_operation(
                operation_name="test_operation",
                component=ObservabilityComponent.SEARCH,
            ):
                raise ValueError("Test error")
        except ValueError:
            pass  # Expected


class TestObservabilityMiddleware(unittest.TestCase):
    """Tests for ObservabilityMiddleware."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ObservabilityConfig(enabled=True)
    
    def test_middleware_creation(self):
        """Test middleware creation."""
        def get_response(request):
            return type('Response', (), {'status_code': 200})()
        
        middleware = ObservabilityMiddleware(get_response)
        
        self.assertIsNotNone(middleware)
    
    def test_middleware_call(self):
        """Test middleware call."""
        def get_response(request):
            return type('Response', (), {'status_code': 200})()
        
        middleware = ObservabilityMiddleware(get_response)
        
        request = type('Request', (), {
            'path': '/test',
            'method': 'GET',
            'user': type('User', (), {'is_authenticated': False})(),
        })()
        
        response = middleware(request)
        
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)


class TestCacheInstrumentation(unittest.TestCase):
    """Tests for CacheInstrumentation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ObservabilityConfig(enabled=True)
    
    def test_instrument_cache_get(self):
        """Test cache get instrumentation."""
        class MockCache:
            def __init__(self):
                self._cache = {"key": "value"}
            
            def get(self, key, default=None):
                return self._cache.get(key, default)
        
        cache = MockCache()
        instrumented = CacheInstrumentation.instrument_cache_get(cache)
        
        result = instrumented.get("key")
        
        self.assertEqual(result, "value")
    
    def test_instrument_cache_set(self):
        """Test cache set instrumentation."""
        class MockCache:
            def __init__(self):
                self._cache = {}
            
            def set(self, key, value):
                self._cache[key] = value
        
        cache = MockCache()
        instrumented = CacheInstrumentation.instrument_cache_set(cache)
        
        instrumented.set("key", "value")
        
        self.assertEqual(cache._cache["key"], "value")


class TestPipelineInstrumentation(unittest.TestCase):
    """Tests for PipelineInstrumentation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = ObservabilityConfig(enabled=True)
    
    def test_instrument_pipeline_stage(self):
        """Test pipeline stage instrumentation."""
        def test_stage(data):
            return data
        
        instrumented = PipelineInstrumentation.instrument_pipeline_stage(
            "test_stage",
            test_stage,
        )
        
        result = instrumented({"test": "data"})
        
        self.assertIsNotNone(result)
        self.assertEqual(result["test"], "data")


if __name__ == "__main__":
    unittest.main()
