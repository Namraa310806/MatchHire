# Performance Guide

## Overview

The Query Engine includes several performance optimizations including query caching, query optimization, pagination optimization, and large result protection.

## Performance Configuration

```python
from apps.search.query_engine.performance import PerformanceConfig, CacheStrategy

config = PerformanceConfig(
    query_timeout_ms=30000,           # 30 seconds
    max_query_depth=10,               # Maximum nested query depth
    max_clauses=1000,                # Maximum boolean clauses
    max_result_window=10000,         # Maximum results for pagination
    cache_enabled=True,               # Enable query cache
    cache_ttl_seconds=300,           # 5 minutes cache TTL
    cache_max_size=1000,              # Maximum cache entries
    cache_strategy=CacheStrategy.LRU, # LRU, LFU, TTL, or NONE
    enable_query_cancellation=True,   # Enable query cancellation
    enable_pagination_optimization=True,
    enable_large_result_protection=True,
    large_result_threshold=1000,      # Threshold for large result protection
)
```

## Query Cache

### Basic Usage

```python
from apps.search.query_engine import QueryEngine
from apps.search.query_engine.performance import PerformanceConfig

config = PerformanceConfig(cache_enabled=True)
engine = QueryEngine(registry, config=config)

# Search with caching
result = engine.search(context, use_cache=True)

# Get cache stats
stats = engine.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
print(f"Cache size: {stats['size']}")
```

### Cache Invalidation

```python
# Invalidate all cache
engine.clear_cache()

# Invalidate specific entity type
engine.invalidate_cache(entity_type="job")

# Invalidate by entity type
engine.invalidate_cache(entity_type="candidate")
```

### Cache Statistics

```python
stats = engine.get_cache_stats()
# Returns:
# {
#     "hits": 100,
#     "misses": 50,
#     "hit_rate": 0.6667,
#     "size": 100,
#     "max_size": 1000,
# }
```

## Query Optimization

### Automatic Optimization

The QueryOptimizer automatically optimizes queries:

```python
from apps.search.query_engine.performance import QueryOptimizer, PerformanceConfig

config = PerformanceConfig()
optimizer = QueryOptimizer(config)

# Optimize query string
optimized = optimizer.optimize_query(
    query="  software   engineer  ",  # Extra whitespace
    filters={"status": "active"}
)
# Returns: {"query": "software engineer", "filters": {...}}
```

### Query Depth Validation

```python
# Validate query depth to prevent deep recursion
is_valid = optimizer.validate_query_depth(query_dict, current_depth=0)
```

### Clause Count Validation

```python
# Validate clause count to prevent excessive clauses
is_valid = optimizer.validate_clause_count(query_dict)
```

### Query Complexity Check

```python
# Check query complexity
complexity = optimizer.check_query_complexity(query_dict)
# Returns:
# {
#     "depth": 3,
#     "clauses": 15,
#     "max_depth": 10,
#     "max_clauses": 1000,
#     "is_complex": False,
# }
```

## Pagination Optimization

### Automatic Pagination Optimization

```python
# Pagination is automatically optimized
pagination = optimizer.optimize_pagination(
    pagination={"offset": 0, "limit": 100},
    total_results=50000,
)
# Returns optimized pagination with enforced limits
```

### Result Window Enforcement

```python
# The max_result_window is enforced automatically
# Prevents deep pagination issues
config = PerformanceConfig(max_result_window=10000)
```

## Large Result Protection

### Automatic Protection

```python
# Large result sets are automatically protected
config = PerformanceConfig(
    enable_large_result_protection=True,
    large_result_threshold=1000,
)

# For result sets > 1000, page size is limited to 100
```

## Query Timeout

### Timeout Configuration

```python
config = PerformanceConfig(query_timeout_ms=30000)  # 30 seconds
```

### Timeout Handling

Queries that exceed the timeout are automatically cancelled:

```python
# The provider should respect the timeout
# If timeout is exceeded, the query is cancelled
```

## Query Cancellation

### Enable Cancellation

```python
config = PerformanceConfig(enable_query_cancellation=True)
```

### Cancellation Handling

Queries can be cancelled mid-execution:

```python
# This is handled by the provider
# PostgreSQL: Uses statement_timeout
# Elasticsearch: Uses timeout parameter
```

## Performance Best Practices

### 1. Use Query Caching

```python
# Enable caching for repeated queries
config = PerformanceConfig(
    cache_enabled=True,
    cache_ttl_seconds=300,  # 5 minutes
)
```

### 2. Set Appropriate Limits

```python
# Set reasonable limits to prevent resource exhaustion
config = PerformanceConfig(
    max_query_depth=10,
    max_clauses=1000,
    max_result_window=10000,
)
```

### 3. Use Pagination

```python
# Always use pagination for large result sets
context = SearchExecutionContext(
    entity_type="job",
    query="software engineer",
    pagination={"page": 1, "page_size": 20},
)
```

### 4. Limit Fields Returned

```python
# Only request the fields you need
context = SearchExecutionContext(
    entity_type="job",
    query="software engineer",
    fields=["title", "company_name", "salary"],
)
```

### 5. Use Specific Filters

```python
# Use specific filters to reduce result sets
filters = [
    JobFilters.by_status("active"),
    JobFilters.by_location("San Francisco"),
]
```

### 6. Avoid Deep Queries

```python
# Keep query depth reasonable
# Deep queries are harder to optimize and slower
```

### 7. Monitor Cache Performance

```python
# Regularly check cache statistics
stats = engine.get_cache_stats()
if stats["hit_rate"] < 0.5:
    # Consider adjusting cache TTL or size
    pass
```

### 8. Use Facets Wisely

```python
# Facets add overhead
# Only request facets you need
facets = builder.location_facet(size=10).build()
```

## Performance Monitoring

### Query Execution Time

```python
result = engine.search(context)
print(f"Query took {result.took_ms}ms")
```

### Cache Performance

```python
stats = engine.get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']:.2%}")
print(f"Cache size: {stats['size']}/{stats['max_size']}")
```

### Query Complexity

```python
complexity = optimizer.check_query_complexity(query_dict)
if complexity["is_complex"]:
    # Consider simplifying the query
    pass
```

## Tuning Guidelines

### Cache Size

- **Small applications**: 100-500 entries
- **Medium applications**: 500-1000 entries
- **Large applications**: 1000-5000 entries

### Cache TTL

- **Frequently changing data**: 60-300 seconds
- **Moderately changing data**: 300-1800 seconds
- **Slowly changing data**: 1800-3600 seconds

### Query Timeout

- **Simple queries**: 5-10 seconds
- **Complex queries**: 10-30 seconds
- **Very complex queries**: 30-60 seconds

### Result Window

- **Standard**: 10000 results
- **High-performance**: 5000 results
- **Memory-constrained**: 2000 results

## Troubleshooting

### Slow Queries

1. Check query complexity
2. Verify cache is enabled
3. Review pagination settings
4. Check provider performance
5. Consider adding indexes

### Low Cache Hit Rate

1. Increase cache TTL
2. Increase cache size
3. Review query patterns
4. Check cache key generation

### Memory Issues

1. Reduce cache size
2. Reduce max_result_window
3. Enable large result protection
4. Limit page size

## Provider-Specific Considerations

### PostgreSQL

- Use GIN indexes for full-text search
- Use pg_trgm for autocomplete
- Set appropriate statement_timeout
- Use connection pooling

### Elasticsearch

- Use appropriate shard count
- Configure refresh interval
- Use index aliases
- Enable query caching
