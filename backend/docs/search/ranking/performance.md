# Performance Optimization

## Overview

The ranking system is designed for production-grade performance with built-in caching, parallel execution, lazy evaluation, and monitoring. This guide covers performance optimization strategies and best practices.

## Performance Features

### Caching

The ranking system uses multi-level caching to avoid redundant computations:

**Signal Score Caching**
- Caches individual signal scores
- Cache key includes signal name, document IDs, and query
- TTL-based expiration
- LRU eviction for memory management

**Pipeline Result Caching**
- Caches complete pipeline results
- Cache key includes entity type, query, filters, and profile
- Configurable TTL
- Entity-type specific invalidation

**Configuration**
```python
from apps.search.ranking.pipeline import PipelineConfig

config = PipelineConfig(
    cache_enabled=True,
    cache_ttl_seconds=300,  # 5 minutes
)
```

**Cache Statistics**
```python
from apps.search.ranking.cache import RankingCache

cache = RankingCache(max_size=1000, default_ttl=300)
stats = cache.get_stats()

print(f"Hit rate: {stats.hit_rate():.2%}")
print(f"Miss rate: {stats.miss_rate():.2%}")
print(f"Size: {stats.size}/{stats.max_size}")
```

---

### Parallel Scoring

Signals within a stage can be executed in parallel to reduce latency:

**Configuration**
```python
config = PipelineConfig(
    enable_parallel_scoring=True,
    max_parallel_workers=4,
)
```

**When to Use Parallel Scoring**
- CPU-bound signal calculations
- Multiple independent signals in a stage
- Signals with similar execution times
- When CPU cores are available

**When NOT to Use Parallel Scoring**
- I/O-bound signals (database queries, API calls)
- Few signals in a stage
- When memory is constrained
- When signals have very different execution times

**Monitoring Parallel Execution**
```python
diagnostics = pipeline.get_diagnostics()
print(f"Parallel workers used: {diagnostics.parallel_workers_used}")
print(f"Stage times: {diagnostics.stage_times_ms}")
```

---

### Early Termination

Stop scoring when top results are stable to reduce latency:

**Configuration**
```python
config = PipelineConfig(
    enable_early_termination=True,
    early_termination_threshold=0.95,
)
```

**Termination Conditions**
- Top N results have stable scores
- Score confidence exceeds threshold
- Remaining results unlikely to change top positions

**Monitoring**
```python
diagnostics = pipeline.get_diagnostics()
print(f"Early termination triggered: {diagnostics.early_termination_triggered}")
```

---

### Lazy Scoring

Score only top results initially, score remaining on demand:

**Configuration**
```python
config = PipelineConfig(
    enable_lazy_scoring=True,
    max_scoring_depth=100,
)
```

**Benefits**
- Reduces initial ranking latency
- Scores remaining results only when needed
- Better for large result sets
- Improves first-page load time

**Use Cases**
- Pagination (score only current page)
- Infinite scroll (score as user scrolls)
- Large result sets (>1000 documents)

---

### Maximum Scoring Depth

Limit the number of documents scored to improve performance:

**Configuration**
```python
config = PipelineConfig(
    max_scoring_depth=1000,
)
```

**Benefits**
- Reduces memory usage
- Limits computation time
- Improves cache hit rate
- Predictable performance

**Trade-offs**
- May miss relevant documents beyond depth
- Reduced result diversity
- Potential for incomplete ranking

## Monitoring

### Signal Performance

Track individual signal execution times:

```python
from apps.search.ranking.monitoring import RankingMonitor

monitor = RankingMonitor()

# Record signal execution
monitor.record_signal_execution(
    signal_name="skill_overlap",
    duration_ms=15.5,
    cached=False,
)

# Get signal metrics
metrics = monitor.get_signal_metrics("skill_overlap")
print(f"Average time: {metrics.avg_time_ms}ms")
print(f"Total calls: {metrics.total_calls}")
print(f"Cache hit rate: {metrics.cache_hit_rate():.2%}")
```

### Pipeline Performance

Track pipeline execution metrics:

```python
# Record pipeline execution
monitor.record_pipeline_execution(
    duration_ms=45.2,
    stage_times={
        "lexical_relevance": 10.5,
        "skill_matching": 25.0,
        "business_rules": 9.7,
    },
    parallel=True,
)

# Get pipeline metrics
metrics = monitor.get_pipeline_metrics()
print(f"Average time: {metrics.avg_time_ms}ms")
print(f"Stage times: {metrics.stage_avg_times_ms}")
print(f"Parallel executions: {metrics.parallel_executions}")
```

### Cache Performance

Track cache effectiveness:

```python
# Update cache metrics
cache_stats = cache.get_stats()
monitor.update_cache_metrics(cache_stats.to_dict())

# Get cache metrics
metrics = monitor.get_cache_metrics()
print(f"Hit rate: {metrics.hit_rate():.2%}")
print(f"Size: {metrics.size}/{metrics.max_size}")
```

### Overall Ranking Performance

Track overall ranking metrics:

```python
# Record ranking operation
monitor.record_ranking(duration_ms=50.0, document_count=100)

# Get ranking metrics
metrics = monitor.get_ranking_metrics()
print(f"P50 latency: {metrics.ranking_latency_p50_ms}ms")
print(f"P95 latency: {metrics.ranking_latency_p95_ms}ms")
print(f"P99 latency: {metrics.ranking_latency_p99_ms}ms")
```

### Summary Statistics

Get comprehensive performance summary:

```python
summary = monitor.get_summary()

print(f"Uptime: {summary['uptime_seconds']}s")
print(f"Top signals by calls: {summary['top_signals_by_calls']}")
print(f"Slowest signals: {summary['slowest_signals']}")
print(f"Highest error signals: {summary['highest_error_signals']}")
```

## Optimization Strategies

### Signal Optimization

**Profile Slow Signals**
```python
# Identify slow signals
summary = monitor.get_summary()
for signal in summary['slowest_signals']:
    print(f"{signal['signal_name']}: {signal['avg_time_ms']}ms")
```

**Optimize Signal Logic**
- Use efficient data structures
- Avoid complex regex in hot paths
- Pre-compute when possible
- Cache expensive calculations

**Signal Caching**
```python
# Enable signal caching
config = PipelineConfig(cache_enabled=True)
```

### Pipeline Optimization

**Reduce Stage Count**
- Combine related signals into single stage
- Remove unused stages
- Use conditional stages for entity-specific signals

**Optimize Stage Order**
- Place fast signals in early stages
- Place expensive signals in later stages
- Use early termination to skip later stages

**Parallel Execution**
```python
# Enable parallel scoring
config = PipelineConfig(
    enable_parallel_scoring=True,
    max_parallel_workers=4,
)
```

### Cache Optimization

**Increase Cache Size**
```python
cache = RankingCache(max_size=2000)  # Increase from 1000
```

**Adjust TTL**
```python
# Longer TTL for stable data
cache = RankingCache(default_ttl=600)  # 10 minutes

# Shorter TTL for dynamic data
cache = RankingCache(default_ttl=60)  # 1 minute
```

**Cache Warming**
```python
# Warm cache with common queries
common_queries = ["engineer", "developer", "manager"]
for query in common_queries:
    results = execute_search(query)
    pipeline.execute(results, context)
```

### Query Optimization

**Reduce Result Set Size**
```python
# Limit results before ranking
config = PipelineConfig(max_scoring_depth=500)
```

**Use Lazy Scoring**
```python
# Score only top results
config = PipelineConfig(
    enable_lazy_scoring=True,
    max_scoring_depth=100,
)
```

**Filter Early**
- Apply filters before ranking
- Use provider-level filtering
- Reduce documents entering pipeline

## Performance Benchmarks

### Expected Performance

**Small Result Sets (< 100 documents)**
- Pipeline execution: < 10ms
- Signal scoring: < 5ms per signal
- Total ranking: < 20ms

**Medium Result Sets (100-1000 documents)**
- Pipeline execution: < 50ms
- Signal scoring: < 10ms per signal
- Total ranking: < 100ms

**Large Result Sets (> 1000 documents)**
- Pipeline execution: < 200ms
- Signal scoring: < 20ms per signal
- Total ranking: < 500ms

### Cache Performance

**Hit Rate Targets**
- Production: > 80%
- Staging: > 60%
- Development: > 40%

**Latency with Cache**
- Cache hit: < 5ms
- Cache miss: Full pipeline time
- Mixed: Depends on hit rate

## Performance Tuning

### Step 1: Baseline Measurement

```python
# Measure baseline performance
monitor = RankingMonitor()

# Execute searches
for query in test_queries:
    results = execute_search(query)
    ranked, _ = pipeline.execute(results, context)
    monitor.record_ranking(duration_ms=..., document_count=len(results))

# Get baseline metrics
baseline = monitor.get_summary()
```

### Step 2: Identify Bottlenecks

```python
# Identify slow signals
slow_signals = baseline['slowest_signals']

# Identify low cache hit rate
if baseline['cache_metrics']['hit_rate'] < 0.5:
    print("Cache hit rate is low")

# Identify high error rates
for signal in baseline['highest_error_signals']:
    if signal['error_count'] > 10:
        print(f"High error rate: {signal['signal_name']}")
```

### Step 3: Apply Optimizations

```python
# Apply optimizations based on bottlenecks
config = PipelineConfig(
    cache_enabled=True,
    enable_parallel_scoring=True,
    max_parallel_workers=4,
    max_scoring_depth=1000,
)
```

### Step 4: Measure Improvement

```python
# Measure after optimization
monitor.reset()

for query in test_queries:
    results = execute_search(query)
    ranked, _ = pipeline.execute(results, context)
    monitor.record_ranking(duration_ms=..., document_count=len(results))

optimized = monitor.get_summary()

# Compare
improvement = baseline['ranking_metrics']['avg_time_ms'] - optimized['ranking_metrics']['avg_time_ms']
print(f"Improvement: {improvement}ms")
```

## Troubleshooting Performance Issues

### High Latency

**Symptoms**: Slow ranking (> 500ms)

**Solutions**:
- Enable parallel scoring
- Increase cache size
- Reduce max_scoring_depth
- Enable lazy scoring
- Profile slow signals
- Optimize signal logic

### Low Cache Hit Rate

**Symptoms**: Cache hit rate < 50%

**Solutions**:
- Increase cache TTL
- Increase cache size
- Review cache key generation
- Check for cache invalidation
- Warm cache with common queries

### High Memory Usage

**Symptoms**: High memory consumption

**Solutions**:
- Reduce max_scoring_depth
- Reduce max_parallel_workers
- Reduce cache size
- Enable lazy scoring
- Clear cache periodically

### Signal Errors

**Symptoms**: High error rate in signals

**Solutions**:
- Review signal error handling
- Check input data validation
- Monitor error logs
- Fix signal bugs
- Add fallback logic

## Performance Checklist

### Before Deployment

- [ ] Enable caching in production
- [ ] Set appropriate cache TTL
- [ ] Configure cache size
- [ ] Enable parallel scoring
- [ ] Set appropriate worker count
- [ ] Configure max_scoring_depth
- [ ] Enable monitoring
- [ ] Set up alerts for latency
- [ ] Benchmark with production data
- [ ] Test cache invalidation

### Ongoing Monitoring

- [ ] Monitor cache hit rate
- [ ] Monitor ranking latency
- [ ] Monitor signal execution times
- [ ] Monitor error rates
- [ ] Review slow signals
- [ ] Review cache size
- [ ] Review parallel execution efficiency
- [ ] Review early termination rate

### Regular Optimization

- [ ] Review signal performance monthly
- [ ] Optimize slow signals
- [ ] Adjust cache configuration
- [ ] Review and update profiles
- [ ] Benchmark after changes
- [ ] Monitor impact of optimizations
