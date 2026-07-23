# Integration Guide

This guide explains how to integrate the observability platform with the existing MatchHire search, ranking, and recommendation systems.

## Integration Principles

The observability platform is designed to be **orthogonal** to business logic. This means:

1. **No changes to core business logic**: Existing code continues to work without modification
2. **Decorator-based instrumentation**: Use decorators to add observability
3. **Middleware for web requests**: Automatic instrumentation of HTTP requests
4. **Hook-based quality metrics**: Non-intrusive quality tracking
5. **Provider independence**: Works with any search provider

## Search Integration

### Instrumenting QueryEngine

The `QueryEngine` can be instrumented using decorators:

```python
from apps.search.observability.instrumentation import instrument_search
from apps.search.query_engine.engine import QueryEngine

class InstrumentedQueryEngine(QueryEngine):
    @instrument_search
    def search(self, request):
        return super().search(request)
    
    @instrument_search
    def autocomplete(self, request):
        return super().autocomplete(request)
```

### Alternative: Wrapper Pattern

If you prefer not to modify the existing class, use a wrapper:

```python
from apps.search.observability.instrumentation import instrument_search
from apps.search.query_engine.engine import QueryEngine

class ObservableQueryEngine:
    def __init__(self, engine: QueryEngine):
        self._engine = engine
    
    @instrument_search
    def search(self, request):
        return self._engine.search(request)
    
    @instrument_search
    def autocomplete(self, request):
        return self._engine.autocomplete(request)
```

## Ranking Integration

### Instrumenting RankingPipeline

```python
from apps.search.observability.instrumentation import instrument_ranking
from apps.search.ranking.pipeline import RankingPipeline

class InstrumentedRankingPipeline(RankingPipeline):
    @instrument_ranking
    def rank(self, results, context):
        return super().rank(results, context)
```

### Signal-Level Instrumentation

Instrument individual ranking signals:

```python
from apps.search.observability.instrumentation import observe_operation
from apps.search.observability.core import ObservabilityComponent

class MySignal:
    def compute(self, result, context):
        with observe_operation(
            operation_name="signal_compute",
            component=ObservabilityComponent.SIGNAL,
        ) as span:
            span.set_attribute("signal_name", "my_signal")
            # Signal computation logic
            return score
```

## Recommendation Integration

### Instrumenting RecommendationEngine

```python
from apps.search.observability.instrumentation import instrument_recommendation
from apps.search.recommendations.core import RecommendationEngine

class InstrumentedRecommendationEngine(RecommendationEngine):
    @instrument_recommendation
    def recommend(self, request):
        return super().recommend(request)
```

### Pipeline Stage Instrumentation

```python
from apps.search.observability.instrumentation import PipelineInstrumentation

# Instrument each pipeline stage
pipeline = RecommendationPipeline()

pipeline.candidate_generation = PipelineInstrumentation.instrument_pipeline_stage(
    "candidate_generation",
    pipeline.candidate_generation,
)

pipeline.filtering = PipelineInstrumentation.instrument_pipeline_stage(
    "filtering",
    pipeline.filtering,
)

pipeline.ranking = PipelineInstrumentation.instrument_pipeline_stage(
    "ranking",
    pipeline.ranking,
)
```

## Provider Integration

### Instrumenting SearchProvider

```python
from apps.search.observability.instrumentation import instrument_provider
from apps.search.providers.base import SearchProvider

class InstrumentedPostgreSQLProvider(SearchProvider):
    @instrument_provider
    def search(self, query, filters, pagination):
        return super().search(query, filters, pagination)
    
    @instrument_provider
    def autocomplete(self, query, limit):
        return super().autocomplete(query, limit)
```

## Cache Integration

### Instrumenting Cache Operations

```python
from apps.search.observability.instrumentation import CacheInstrumentation

# Instrument cache instance
cache = get_cache()
instrumented_cache = CacheInstrumentation.instrument_cache_get(cache)
instrumented_cache = CacheInstrumentation.instrument_cache_set(instrumented_cache)
```

## Django Integration

### Middleware Setup

Add the observability middleware to Django settings:

```python
# settings.py
MIDDLEWARE = [
    'apps.search.observability.instrumentation.ObservabilityMiddleware',
    # ... other middleware
]
```

### Configuration in Django Settings

```python
# settings.py
OBSERVABILITY = {
    'enabled': True,
    'sampling_rate': 1.0,
    'environment': 'production',
    'metrics_enabled': True,
    'tracing_enabled': True,
    'logging_enabled': True,
    'log_level': 'INFO',
    'prometheus_enabled': True,
    'prometheus_port': 9090,
    'opentelemetry_enabled': True,
    'trace_exporter': 'otlp',
    'otlp_endpoint': 'http://localhost:4317',
}
```

### Initialization in Django App

Create an initialization function in your Django app:

```python
# apps/search/__init__.py
from django.conf import settings

def initialize_observability():
    from apps.search.observability import get_manager, ObservabilityConfig
    
    config = ObservabilityConfig(**getattr(settings, 'OBSERVABILITY', {}))
    manager = get_manager(config)
    
    return manager

# Call this during app initialization
default_app_config = 'apps.search.apps.SearchConfig'
```

## Quality Metrics Integration

### Recording User Interactions

```python
from apps.search.observability.quality_metrics import QualityMetricsCollector

# Get the collector
from apps.search.observability import get_manager
manager = get_manager()
collector = manager._quality_collector

# Record click events
def on_result_click(user_id, result_id, position, session_id):
    collector.record_click(user_id, result_id, position, session_id)

# Record recommendation acceptance
def on_recommendation_acceptance(user_id, recommendation_id, entity_type, entity_id):
    collector.record_recommendation_acceptance(
        user_id, recommendation_id, entity_type, entity_id
    )
```

### Integrating with Views

```python
from django.views import View
from apps.search.observability import get_manager

class SearchView(View):
    def get(self, request):
        manager = get_manager()
        
        # Set context
        from apps.search.observability.core import ObservabilityContext
        context = ObservabilityContext()
        if request.user.is_authenticated:
            context.user_id = str(request.user.id)
        manager.set_context(context)
        
        # Perform search
        results = perform_search(request.GET.get('q'))
        
        # Record quality metrics
        if results:
            manager._quality_collector.record_search_success(
                user_id=str(request.user.id) if request.user.is_authenticated else None,
                query=request.GET.get('q'),
                result_count=len(results),
            )
        else:
            manager._quality_collector.record_zero_results(
                user_id=str(request.user.id) if request.user.is_authenticated else None,
                query=request.GET.get('q'),
            )
        
        return render(request, 'search.html', {'results': results})
```

## Testing Integration

### Unit Tests with Observability

```python
from django.test import TestCase
from apps.search.observability import get_manager, ObservabilityConfig

class SearchTestCase(TestCase):
    def setUp(self):
        # Initialize observability for testing
        config = ObservabilityConfig(enabled=True)
        self.manager = get_manager(config)
    
    def test_search(self):
        # Your test logic
        response = self.client.get('/search/?q=python')
        
        # Check metrics
        metrics = self.manager.metrics.get_summary()
        self.assertGreater(metrics['search_requests_total']['value'], 0)
```

### Disabling Observability in Tests

```python
# settings/test.py
OBSERVABILITY = {
    'enabled': False,
}
```

## Migration Strategy

### Phase 1: Core Components

1. Initialize observability manager
2. Add middleware
3. Instrument QueryEngine
4. Instrument RankingPipeline
5. Instrument RecommendationEngine

### Phase 2: Providers and Cache

1. Instrument SearchProvider implementations
2. Instrument cache operations
3. Add provider health checks

### Phase 3: Quality Metrics

1. Add quality metric hooks
2. Integrate with user interaction tracking
3. Set up quality dashboards

### Phase 4: Advanced Features

1. Enable OpenTelemetry export
2. Set up Prometheus scraping
3. Configure Grafana dashboards
4. Set up alerting

## Rollback Strategy

If issues arise, observability can be disabled without affecting core functionality:

```python
# settings.py
OBSERVABILITY = {
    'enabled': False,
}
```

Or remove the middleware:

```python
# settings.py
MIDDLEWARE = [
    # 'apps.search.observability.instrumentation.ObservabilityMiddleware',
    # ... other middleware
]
```

## Performance Impact

### Expected Overhead

- **Metrics**: <1% overhead
- **Tracing**: <2% overhead (with sampling)
- **Logging**: <1% overhead
- **Diagnostics**: <0.5% overhead

### Mitigation Strategies

1. Use sampling for tracing: `sampling_rate=0.1`
2. Disable expensive profiling in production
3. Adjust metrics export interval
4. Filter unnecessary metrics

## Monitoring the Observability System

### Observability Self-Monitoring

The observability system monitors itself:

```python
from apps.search.observability import get_manager

manager = get_manager()

# Check observability health
health = manager.get_health_status()

# Check telemetry queue size
telemetry = manager.get_telemetry()
queue_size = telemetry['queue_size']
```

### Alerting on Observability Issues

Set up alerts for:

- High telemetry queue size
- Observability component failures
- High memory usage by observability
- Slow observability operations
