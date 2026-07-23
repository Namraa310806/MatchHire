# Performance Optimization

## Overview

The recommendation engine includes several performance optimization features to ensure low-latency recommendations and high throughput.

## Optimization Features

### 1. Recommendation Cache

**Description**: LRU cache with TTL support for recommendation results.

**Configuration**:
```python
from apps.search.recommendations.cache import RecommendationCache

cache = RecommendationCache(
    config={
        "max_size": 1000,
        "default_ttl": 300,  # 5 minutes
    }
)
```

**Features**:
- LRU eviction policy
- TTL-based expiration
- Thread-safe operations
- Cache statistics tracking
- Selective invalidation (by entity, by user)

**Usage**:
```python
# Get cached result
cached = cache.get(request, context)

# Set cached result
cache.set(request, context, response, ttl=600)

# Invalidate by entity
cache.invalidate_by_entity("job_123")

# Invalidate by user
cache.invalidate_by_user("user_456")

# Get statistics
stats = cache.get_stats()
print(f"Hit rate: {stats.hit_rate}")
```

### 2. Candidate Pool Cache

**Description**: Cache for pre-computed candidate pools.

**Configuration**:
```python
from apps.search.recommendations.cache import CandidatePoolCache

pool_cache = CandidatePoolCache(
    config={
        "max_size": 500,
        "default_ttl": 600,  # 10 minutes
    }
)
```

**Features**:
- Pre-compute candidate pools for common queries
- Faster recommendation generation for cached pools
- Configurable TTL
- Automatic cleanup

**Usage**:
```python
# Cache candidate pool
pool_key = "job_123_skills_python_django"
pool_cache.set(pool_key, candidates, ttl=600)

# Get cached pool
cached_pool = pool_cache.get(pool_key)
```

### 3. Parallel Candidate Generation

**Description**: Generate candidates in parallel from multiple sources.

**Configuration**:
```python
from apps.search.recommendations.pipeline import PipelineConfig

config = PipelineConfig(
    enable_parallel_generation=True,
    max_parallel_workers=4,
)
```

**Features**:
- Parallel execution of independent candidate generation tasks
- Configurable worker count
- Automatic load balancing

**Usage**:
```python
import multiprocessing

workers = min(4, multiprocessing.cpu_count())
config = PipelineConfig(
    max_parallel_workers=workers,
)
```

### 4. Incremental Recommendation

**Description**: Lazy recommendation generation for large result sets.

**Configuration**:
```python
from apps.search.recommendations.pipeline import PipelineConfig

config = PipelineConfig(
    enable_lazy_ranking=True,
)
```

**Features**:
- Rank only top N candidates
- Lazy loading of remaining candidates
- Reduced memory usage
- Faster initial response

### 5. Benchmark Utilities

**Description**: Utilities for performance benchmarking and profiling.

**Usage**:
```python
import time
from apps.search.recommendations import RecommendationEngine

# Benchmark recommendation generation
start = time.time()
response = engine.recommend(request)
end = time.time()

latency_ms = (end - start) * 1000
print(f"Latency: {latency_ms}ms")
```

## Performance Targets

### Latency Targets

- **Cached recommendations**: < 100ms (P95)
- **Uncached recommendations**: < 500ms (P95)
- **Candidate generation**: < 200ms
- **Ranking**: < 300ms
- **Diversification**: < 50ms

### Throughput Targets

- **Recommendations per second**: 1000+
- **Cache hit rate**: > 80%
- **Parallel efficiency**: > 70%

### Resource Targets

- **Memory per instance**: < 2GB
- **CPU utilization**: < 70%
- **Cache size**: < 1GB

## Performance Monitoring

### Track Latency

```python
monitor.record_recommendation(
    recommendation_type="candidate",
    count=10,
    latency_ms=50.0,
)

metrics = monitor.get_recommendation_metrics()
print(f"Avg latency: {metrics.total_latency_ms / metrics.total_recommendations}ms")
```

### Track Cache Performance

```python
stats = cache.get_stats()
print(f"Hit rate: {stats.hit_rate}")
print(f"Misses: {stats.misses}")
print(f"Evictions: {stats.evictions}")
```

### Track Pipeline Performance

```python
pipeline_metrics = monitor.get_pipeline_metrics()
print(f"Avg stage times: {pipeline_metrics.avg_stage_times_ms}")
print(f"Failure rate: {pipeline_metrics.failure_rate}")
```

## Optimization Strategies

### 1. Cache Frequently Accessed Recommendations

```python
# Enable caching for high-traffic endpoints
config = RecommendationConfig(
    enable_caching=True,
)
```

### 2. Use Parallel Processing

```python
# Enable parallel generation for CPU-bound tasks
config = PipelineConfig(
    enable_parallel_generation=True,
    max_parallel_workers=4,
)
```

### 3. Limit Candidate Pool Size

```python
# Reduce candidate pool size for faster ranking
config = PipelineConfig(
    max_candidates=500,  # Instead of 1000
)
```

### 4. Enable Early Termination

```python
# Stop ranking once quality threshold is met
config = PipelineConfig(
    enable_early_termination=True,
    early_termination_threshold=0.95,
)
```

### 5. Use Lazy Ranking

```python
# Rank only top N candidates
config = PipelineConfig(
    enable_lazy_ranking=True,
)
```

## Performance Profiling

### Profile Pipeline Stages

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

response = engine.recommend(request)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Profile Signal Execution

```python
# Enable diagnostics to get signal timing
config = PipelineConfig(
    enable_diagnostics=True,
)

diagnostics = pipeline.get_diagnostics()
print(f"Stage times: {diagnostics.stage_times_ms}")
```

## Common Performance Issues

### Issue: High Latency

**Solutions**:
1. Enable caching
2. Reduce candidate pool size
3. Enable parallel processing
4. Use lazy ranking
5. Optimize signal weights

### Issue: Low Cache Hit Rate

**Solutions**:
1. Increase cache TTL
2. Increase cache size
3. Reduce cache key granularity
4. Pre-warm cache with common queries

### Issue: High Memory Usage

**Solutions**:
1. Reduce cache size
2. Reduce candidate pool size
3. Enable lazy ranking
4. Use memory-efficient data structures

### Issue: CPU Saturation

**Solutions**:
1. Reduce parallel workers
2. Optimize expensive signals
3. Enable early termination
4. Use caching more aggressively

## Scaling Strategies

### Horizontal Scaling

- Partition cache across instances
- Use distributed cache (Redis, Memcached)
- Load balance recommendation requests
- Stateless recommendation generation

### Vertical Scaling

- Increase CPU cores for parallel processing
- Increase memory for larger caches
- Use faster storage for candidate pools
- Optimize database queries

### Database Optimization

- Add indexes for frequently queried fields
- Use read replicas for query engine
- Optimize search provider configuration
- Use connection pooling

## Performance Testing

### Load Testing

```python
import concurrent.futures

def generate_recommendation():
    return engine.recommend(request)

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(generate_recommendation) for _ in range(100)]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]
```

### Stress Testing

```python
# Gradually increase load
for workers in [1, 2, 4, 8, 16]:
    test_with_workers(workers)
```

### Benchmarking

```python
# Compare different configurations
configs = [
    get_low_performance_config(),
    get_standard_config(),
    get_high_performance_config(),
]

for config in configs:
    benchmark_config(config)
```

## Best Practices

### 1. Monitor Performance Continuously

Track key metrics and set up alerts:
- Latency P50, P95, P99
- Cache hit rate
- Throughput
- Resource utilization

### 2. Optimize Hot Paths

Identify and optimize frequently executed code paths:
- Profile to find bottlenecks
- Optimize signal calculations
- Cache expensive computations

### 3. Use Appropriate Caching

Cache at the right level:
- Cache recommendation results
- Cache candidate pools
- Cache signal calculations
- Cache user preferences

### 4. Tune Parallelism

Find the optimal parallel worker count:
- Too few: Underutilized CPU
- Too many: Context switching overhead
- Benchmark to find sweet spot

### 5. Test Under Load

Test performance under realistic load:
- Simulate production traffic patterns
- Test with concurrent users
- Monitor resource utilization

## Future Enhancements

The performance framework is ready for:

- **Distributed Caching**: Redis, Memcached integration
- **GPU Acceleration**: GPU-based signal computation
- **Async Processing**: AsyncIO for I/O-bound operations
- **Predictive Caching**: Pre-cache based on usage patterns
- **Auto-scaling**: Dynamic resource allocation
