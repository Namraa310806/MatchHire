# Query Engine Examples

## Table of Contents

- [Basic Search](#basic-search)
- [Advanced Query DSL](#advanced-query-dsl)
- [Filtering](#filtering)
- [Faceted Search](#faceted-search)
- [Aggregations](#aggregations)
- [Highlighting](#highlighting)
- [Autocomplete](#autocomplete)
- [Unified Search](#unified-search)
- [Sorting and Ranking](#sorting-and-ranking)
- [Performance Optimization](#performance-optimization)

## Basic Search

### Simple Text Search

```python
from apps.search.query_engine import QueryEngine, SearchExecutionContext
from apps.search.registry import get_registry

# Get the query engine
registry = get_registry()
engine = QueryEngine(registry)

# Create search context
context = SearchExecutionContext(
    entity_type="job",
    query="software engineer",
    pagination={"page": 1, "page_size": 20},
)

# Execute search
result = engine.search(context)

# Access results
for item in result.results:
    print(f"{item['title']} - {item['company_name']}")
```

### Search with Filters

```python
from apps.search.query_engine.filters import FilterBuilder, JobFilters

# Build filters
builder = FilterBuilder()
filters = (
    builder
    .eq(field="status", value="active")
    .range(field="salary", gte=50000, lte=100000)
    .build()
)

# Create search context with filters
context = SearchExecutionContext(
    entity_type="job",
    query="software engineer",
    filters=filters,
    pagination={"page": 1, "page_size": 20},
)

result = engine.search(context)
```

### Search with Sorting

```python
from apps.search.query_engine.sorting import SortBuilder, SortDirection

# Build sort conditions
builder = SortBuilder()
sort_conditions = builder.by_relevance(direction=SortDirection.DESC).build_sort()

# Convert to dictionary format
sort_dicts = [s.to_dict() for s in sort_conditions]

# Create search context with sorting
context = SearchExecutionContext(
    entity_type="job",
    query="software engineer",
    sort_conditions=sort_dicts,
    pagination={"page": 1, "page_size": 20},
)

result = engine.search(context)
```

## Advanced Query DSL

### Boolean Query

```python
from apps.search.query_engine.dsl import BoolQuery, MatchQuery, RangeQuery

# Build a boolean query
query = BoolQuery(
    must=[
        MatchQuery(field="title", query="software"),
    ],
    should=[
        MatchQuery(field="description", query="engineer"),
        MatchQuery(field="requirements", query="python"),
    ],
    must_not=[
        MatchQuery(field="status", query="closed"),
    ],
    filter=[
        RangeQuery(field="salary", gte=50000),
    ],
    minimum_should_match=1,
)
```

### Multi-Match Query

```python
from apps.search.query_engine.dsl import MultiMatchQuery, MatchType

# Search across multiple fields
query = MultiMatchQuery(
    query="software engineer",
    fields=["title", "description", "requirements"],
    type=MatchType.BEST_FIELDS,
    tie_breaker=0.3,
)
```

### Function Score Query

```python
from apps.search.query_engine.dsl import (
    FunctionScoreQuery, MatchQuery,
    FieldValueFactorFunction, WeightFunction
)

# Base query
base_query = MatchQuery(field="title", query="software")

# Add scoring functions
query = FunctionScoreQuery(
    query=base_query,
    functions=[
        {
            "field_value_factor": {
                "field": "popularity",
                "factor": 1.5,
                "modifier": "log1p"
            }
        },
        {
            "weight": 2.0,
            "filter": {"term": {"is_featured": True}}
        }
    ],
    score_mode="multiply",
)
```

### Using the DSL Builder

```python
from apps.search.query_engine.dsl import DSLQueryBuilder

# Build a complex query
builder = DSLQueryBuilder()
query = (
    builder
    .bool()
    .must(MatchQuery(field="title", query="software"))
    .should([
        MatchQuery(field="description", query="engineer"),
        MatchQuery(field="requirements", query="python"),
    ])
    .filter(RangeQuery(field="salary", gte=50000))
    .build()
)
```

## Filtering

### Using Predefined Filters

```python
from apps.search.query_engine.filters import JobFilters

# Filter by status
status_filter = JobFilters.by_status("active")

# Filter by salary range
salary_filter = JobFilters.by_salary_range(min_salary=50000, max_salary=100000)

# Filter by location
location_filter = JobFilters.by_location("San Francisco")

# Combine filters
filters = [status_filter, salary_filter, location_filter]
```

### Building Custom Filters

```python
from apps.search.query_engine.filters import FilterBuilder, FilterOperator

builder = FilterBuilder()
filters = (
    builder
    .eq(field="status", value="active")
    .range(field="salary", gte=50000, lte=100000)
    .in_(field="industry", values=["Technology", "Finance"])
    .contains(field="title", value="software")
    .build()
)
```

### Boolean Filters

```python
from apps.search.query_engine.filters import BooleanFilter, FilterFilterOperator

# AND filter
and_filter = BooleanFilter(
    operator="AND",
    filters=[
        Filter(field="status", operator=FilterOperator.EQ, value="active"),
        Filter(field="type", operator=FilterOperator.EQ, value="full-time"),
    ]
)

# OR filter
or_filter = BooleanFilter(
    operator="OR",
    filters=[
        Filter(field="status", operator=FilterOperator.EQ, value="active"),
        Filter(field="status", operator=FilterOperator.EQ, value="pending"),
    ]
)
```

### Nested Filters

```python
from apps.search.query_engine.filters import Filter, FilterOperator

# Filter on nested field
skill_filter = Filter(
    field="name",
    operator=FilterOperator.EQ,
    value="python",
    nested_path="skills",
)
```

## Faceted Search

### Basic Facets

```python
from apps.search.query_engine.facets import FacetBuilder

builder = FacetBuilder()
facets = (
    builder
    .add_facet(field="location", name="Location", size=20)
    .add_facet(field="industry", name="Industry", size=15)
    .build()
)

context = SearchExecutionContext(
    entity_type="job",
    query="software engineer",
    facets=facets,
)

result = engine.search(context)

# Access facet results
for facet in result.facets:
    print(f"{facet.name}:")
    for value in facet.values:
        print(f"  {value.value}: {value.count}")
```

### Using Predefined Facets

```python
from apps.search.query_engine.facets import PredefinedFacets

# Get job search facets
facets = PredefinedFacets.job_search_facets()

context = SearchExecutionContext(
    entity_type="job",
    query="software engineer",
    facets=facets,
)

result = engine.search(context)
```

### Facet State Management

```python
from apps.search.query_engine.facets import FacetState

# Create facet state
state = FacetState()

# Add selections
state.add_selection("location", "San Francisco")
state.add_selection("industry", "Technology")

# Use in search context
context = SearchExecutionContext(
    entity_type="job",
    query="software engineer",
    facet_state=state,
)

result = engine.search(context)
```

## Aggregations

### Basic Aggregations

```python
from apps.search.query_engine.aggregations import AggregationBuilder

builder = AggregationBuilder()
aggregations = (
    builder
    .count(name="doc_count")
    .terms(name="by_status", field="status", size=10)
    .stats(name="salary_stats", field="salary")
    .build()
)

context = SearchExecutionContext(
    entity_type="job",
    query="software engineer",
    aggregations=aggregations,
)

result = engine.search(context)

# Access aggregation results
for agg_name, agg_result in result.aggregations.items():
    print(f"{agg_name}: {agg_result}")
```

### Using Predefined Aggregations

```python
from apps.search.query_engine.aggregations import PredefinedAggregations

# Get job salary stats
aggregations = PredefinedAggregations.job_salary_stats()

context = SearchExecutionContext(
    entity_type="job",
    query="software engineer",
    aggregations=aggregations,
)

result = engine.search(context)
```

### Range Aggregation

```python
from apps.search.query_engine.aggregations import RangeAggregation, RangeBucket

ranges = [
    RangeBucket(key="entry", from_value=0, to_value=50000),
    RangeBucket(key="mid", from_value=50000, to_value=100000),
    RangeBucket(key="senior", from_value=100000, to_value=None),
]

agg = RangeAggregation(
    name="salary_ranges",
    field="salary",
    ranges=ranges,
)
```

### Date Histogram Aggregation

```python
from apps.search.query_engine.aggregations import DateHistogramAggregation, HistogramInterval

agg = DateHistogramAggregation(
    name="posted_over_time",
    field="posted_date",
    interval=HistogramInterval.MONTH,
)
```

## Highlighting

### Basic Highlighting

```python
from apps.search.query_engine.highlighting import HighlightBuilder

builder = HighlightBuilder()
highlights = (
    builder
    .title(field="title")
    .description(field="description")
    .build()
)

context = SearchExecutionContext(
    entity_type="job",
    query="software engineer",
    highlights=highlights,
)

result = engine.search(context)

# Access highlights
for doc_id, highlight in result.highlights.items():
    print(f"Document {doc_id}:")
    for field, field_highlight in highlight.highlights.items():
        print(f"  {field}: {field_highlight.get_best_fragment().text}")
```

### Custom Highlighting

```python
from apps.search.query_engine.highlighting import HighlightBuilder

builder = HighlightBuilder()
builder.set_global_tags(["<strong>"], ["</strong>"])

highlights = (
    builder
    .add_field(
        field="title",
        fragment_size=100,
        number_of_fragments=1,
    )
    .add_field(
        field="description",
        fragment_size=200,
        number_of_fragments=3,
    )
    .build()
)
```

### Using Predefined Highlights

```python
from apps.search.query_engine.highlighting import PredefinedHighlights

# Get job search highlights
highlights = PredefinedHighlights.job_search()

context = SearchExecutionContext(
    entity_type="job",
    query="software engineer",
    highlights=highlights,
)

result = engine.search(context)
```

## Autocomplete

### Basic Autocomplete

```python
from apps.search.query_engine.autocomplete import AutocompleteRequest

request = AutocompleteRequest(
    prefix="soft",
    field="title",
    entity_type="job",
    limit=10,
)

response = engine.autocomplete(request)

for suggestion in response.suggestions:
    print(f"{suggestion.value} (score: {suggestion.score})")
```

### Autocomplete with Context

```python
from apps.search.query_engine.autocomplete import AutocompleteRequest, AutocompleteContext

context = AutocompleteContext(
    user_id="123",
    entity_type="job",
    location="San Francisco",
    recent_queries=["software engineer", "data scientist"],
)

request = AutocompleteRequest(
    prefix="soft",
    field="title",
    entity_type="job",
    context=context,
    limit=10,
    fuzzy=True,
)

response = engine.autocomplete(request)
```

### Managing Popular Queries

```python
autocomplete_engine = engine.get_autocomplete_engine()

# Add popular query
autocomplete_engine.add_popular_query("software engineer", weight=1.0)

# Decay popularity over time
autocomplete_engine.decay_popular_queries(factor=0.95)
```

## Unified Search

### Basic Unified Search

```python
from apps.search.query_engine.unified_search import UnifiedSearchRequest, EntityType

request = UnifiedSearchRequest(
    query="software engineer",
    entity_types=[EntityType.JOB, EntityType.CANDIDATE],
    per_entity_limit=10,
    total_limit=20,
)

response = engine.unified_search(request)

# Access results by entity type
jobs = response.get_entity_results(EntityType.JOB)
candidates = response.get_entity_results(EntityType.CANDIDATE)

print(f"Jobs: {jobs.total}")
print(f"Candidates: {candidates.total}")
```

### Unified Search with Filters

```python
request = UnifiedSearchRequest(
    query="software engineer",
    entity_types=[EntityType.JOB, EntityType.CANDIDATE],
    filters={"location": "San Francisco"},
    per_entity_limit=10,
)

response = engine.unified_search(request)
```

### Convenience Methods

```python
# Search jobs and candidates
response = engine.unified_search_engine.search_jobs_and_candidates(
    query="software engineer",
    filters={"location": "San Francisco"}
)

# Search all entities
response = engine.unified_search_engine.search_all_entities(
    query="software engineer"
)
```

## Sorting and Ranking

### Custom Sorting

```python
from apps.search.query_engine.sorting import SortBuilder, SortDirection

builder = SortBuilder()
sort_conditions = (
    builder
    .by_relevance(direction=SortDirection.DESC)
    .by_date(field="posted_date", direction=SortDirection.DESC)
    .by_salary(direction=SortDirection.DESC)
    .build_sort()
)

sort_dicts = [s.to_dict() for s in sort_conditions]

context = SearchExecutionContext(
    entity_type="job",
    query="software engineer",
    sort_conditions=sort_dicts,
)
```

### Field Boosting

```python
from apps.search.query_engine.sorting import SortBuilder

builder = SortBuilder()
boosts = (
    builder
    .boost_title(boost=2.0)
    .boost_description(boost=1.5)
    .boost_skills(boost=2.0)
    .build_boosts()
)
```

### Freshness Boosting

```python
from apps.search.query_engine.sorting import SortBuilder

builder = SortBuilder()
boosts = (
    builder
    .boost_freshness(field="posted_date", scale="30d")
    .build_boosts()
)
```

### Ranking Hooks

```python
# Add pre-ranking hook
def pre_rank_hook(context):
    print(f"Pre-ranking: {context['query']}")

engine.add_ranking_hook("pre_rank", pre_rank_hook)

# Add post-ranking hook
def post_rank_hook(results, context):
    print(f"Post-ranking: {len(results)} results")

engine.add_ranking_hook("post_rank", post_rank_hook)

# Add score modifier
def score_modifier(results, context):
    for result in results:
        if result.get("is_featured"):
            result["_score"] *= 2.0

engine.add_ranking_hook("score_modifier", score_modifier)
```

## Performance Optimization

### Using Query Cache

```python
from apps.search.query_engine.performance import PerformanceConfig

config = PerformanceConfig(
    cache_enabled=True,
    cache_ttl_seconds=300,  # 5 minutes
    cache_max_size=1000,
)

engine = QueryEngine(registry, config=config)

# Search with caching
result = engine.search(context, use_cache=True)

# Get cache stats
stats = engine.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
```

### Cache Invalidation

```python
# Invalidate all cache
engine.clear_cache()

# Invalidate specific entity type
engine.invalidate_cache(entity_type="job")
```

### Query Optimization

```python
from apps.search.query_engine.performance import QueryOptimizer, PerformanceConfig

config = PerformanceConfig()
optimizer = QueryOptimizer(config)

# Optimize query
optimized = optimizer.optimize_query(
    query="  software   engineer  ",
    filters={"status": "active"}
)

# Check query complexity
complexity = optimizer.check_query_complexity(query_dict)
if complexity["is_complex"]:
    print("Query is complex, consider simplifying")
```

## Complete Example

```python
from apps.search.query_engine import QueryEngine, SearchExecutionContext
from apps.search.query_engine.dsl import DSLQueryBuilder, MatchQuery, RangeQuery
from apps.search.query_engine.filters import FilterBuilder, JobFilters
from apps.search.query_engine.facets import FacetBuilder
from apps.search.query_engine.aggregations import AggregationBuilder
from apps.search.query_engine.highlighting import HighlightBuilder
from apps.search.query_engine.sorting import SortBuilder, SortDirection
from apps.search.query_engine.performance import PerformanceConfig
from apps.search.registry import get_registry

# Configure performance
config = PerformanceConfig(
    cache_enabled=True,
    cache_ttl_seconds=300,
)

# Get engine
registry = get_registry()
engine = QueryEngine(registry, config=config)

# Build query
query_builder = DSLQueryBuilder()
query = query_builder.match(field="title", query="software engineer").build()

# Build filters
filter_builder = FilterBuilder()
filters = (
    filter_builder
    .eq(field="status", value="active")
    .range(field="salary", gte=50000, lte=100000)
    .build()
)

# Build facets
facet_builder = FacetBuilder()
facets = (
    facet_builder
    .location_facet(size=20)
    .company_facet(size=15)
    .skills_facet(size=30)
    .build()
)

# Build aggregations
agg_builder = AggregationBuilder()
aggregations = (
    agg_builder
    .count(name="doc_count")
    .terms(name="by_status", field="status", size=10)
    .stats(name="salary_stats", field="salary")
    .build()
)

# Build highlights
highlight_builder = HighlightBuilder()
highlights = (
    highlight_builder
    .title(field="title")
    .description(field="description")
    .build()
)

# Build sort
sort_builder = SortBuilder()
sort_conditions = (
    sort_builder
    .by_relevance(direction=SortDirection.DESC)
    .by_date(field="posted_date", direction=SortDirection.DESC)
    .build_sort()
)
sort_dicts = [s.to_dict() for s in sort_conditions]

# Create search context
context = SearchExecutionContext(
    entity_type="job",
    query="software engineer",
    filters=filters,
    sort_conditions=sort_dicts,
    pagination={"page": 1, "page_size": 20},
    facets=facets,
    aggregations=aggregations,
    highlights=highlights,
)

# Execute search
result = engine.search(context, use_cache=True)

# Display results
print(f"Found {result.total} results in {result.took_ms}ms")
print()

for item in result.results:
    print(f"{item['title']} - {item['company_name']}")
    print(f"  Salary: ${item['salary']}")
    print()

# Display facets
print("Facets:")
for facet in result.facets:
    print(f"  {facet.name}:")
    for value in facet.values[:5]:
        print(f"    {value.value}: {value.count}")

# Display aggregations
print("Aggregations:")
for agg_name, agg_result in result.aggregations.items():
    print(f"  {agg_name}: {agg_result}")

# Display cache stats
stats = engine.get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']:.2%}")
```
