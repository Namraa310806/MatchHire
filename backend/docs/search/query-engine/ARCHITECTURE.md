# Query Engine Architecture

## Overview

The MatchHire Query Engine is a provider-independent search abstraction layer that powers all search experiences across the platform. It transforms high-level search requests into optimized queries for different backend providers (PostgreSQL, Elasticsearch) while maintaining a unified API.

## Core Principles

1. **Provider Independence**: The Query Engine abstracts away provider-specific details, allowing seamless switching between PostgreSQL and Elasticsearch without application code changes.

2. **Single Abstraction**: All search operations flow through the Query Engine, ensuring consistent behavior and centralized optimization.

3. **No Business Logic**: The Query Engine focuses solely on search operations and does not contain business logic.

4. **Registry Integration**: The Query Engine integrates with the SearchProvider Registry for provider management.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  (Views, Services, API Endpoints)                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Query Engine                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              QueryEngine (Main Entry)                │  │
│  │  - search()                                          │  │
│  │  - autocomplete()                                    │  │
│  │  - unified_search()                                  │  │
│  │  - Ranking Hooks                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│  ┌─────────────────────────┼────────────────────────────┐  │
│  │                         │                            │  │
│  ▼                         ▼                            ▼  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Query DSL  │  │   Filters    │  │    Facets    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Aggregations  │  │ Highlighting │  │ Autocomplete │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Sorting    │  │ Suggestions  │  │ Performance  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Provider Translators                            │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │  PostgreSQL Translator│  │ Elasticsearch Translator│     │
│  └──────────────────────┘  └──────────────────────┘        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Search Provider Registry                         │
│  - get_current_provider()                                     │
│  - get_provider(name)                                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Search Providers                                 │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │   PostgreSQL Provider│  │  Elasticsearch Provider│       │
│  └──────────────────────┘  └──────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Query Engine (`engine.py`)

The central orchestrator that coordinates all search operations.

**Key Classes:**
- `QueryEngine`: Main entry point for all search operations
- `SearchExecutionContext`: Context object containing all search parameters
- `EngineResult`: Unified result object with search results, facets, aggregations

**Responsibilities:**
- Transform search requests into execution contexts
- Apply query optimization
- Execute ranking hooks (pre-rank, post-rank, score modifiers)
- Coordinate with provider translators
- Manage query caching
- Compute facets and aggregations
- Apply highlighting

### 2. Query DSL (`dsl.py`)

Provider-independent query language for expressing search queries.

**Key Classes:**
- `Query`: Base class for all query types
- `MatchQuery`, `MultiMatchQuery`, `PhraseQuery`: Text search queries
- `RangeQuery`, `TermQuery`, `TermsQuery`: Structural queries
- `BoolQuery`, `DisMaxQuery`: Boolean combination queries
- `FunctionScoreQuery`: Custom scoring queries
- `DSLQueryBuilder`: Fluent builder for constructing queries

**Responsibilities:**
- Define query types and their parameters
- Provide query validation
- Support query composition (AND, OR, NOT)
- Serialize queries to provider-agnostic format

### 3. Filters (`filters.py`)

Reusable filter definitions for common search patterns.

**Key Classes:**
- `Filter`: Base filter class with field, operator, value
- `RangeFilter`: Range-based filtering
- `BooleanFilter`: Boolean combination of filters
- `FilterBuilder`: Fluent builder for constructing filters
- `JobFilters`, `CandidateFilters`, etc.: Pre-configured entity filters

**Responsibilities:**
- Define filter operators and their semantics
- Provide reusable filter patterns
- Support filter composition
- Validate filter parameters

### 4. Facets (`facets.py`)

Dynamic faceted search support.

**Key Classes:**
- `FacetConfig`: Configuration for a facet
- `FacetResponse`: Response containing facet values and counts
- `FacetState`: State management for selected facets
- `FacetBuilder`: Builder for constructing facet configurations
- `PredefinedFacets`: Common facet configurations

**Responsibilities:**
- Define facet configurations
- Manage facet selection state
- Provide facet sorting and pagination
- Support nested facets

### 5. Aggregations (`aggregations.py`)

Provider-independent aggregation framework.

**Key Classes:**
- `Aggregation`: Base aggregation class
- `CountAggregation`, `TermsAggregation`: Bucket aggregations
- `StatsAggregation`, `AverageAggregation`: Metric aggregations
- `RangeAggregation`, `HistogramAggregation`: Range-based aggregations
- `AggregationBuilder`: Builder for constructing aggregations

**Responsibilities:**
- Define aggregation types
- Support nested aggregations
- Provide aggregation result structures
- Validate aggregation parameters

### 6. Highlighting (`highlighting.py`)

Search result highlighting support.

**Key Classes:**
- `HighlightConfig`: Configuration for field highlighting
- `HighlightResult`: Result containing highlighted fragments
- `HighlightBuilder`: Builder for constructing highlight configurations
- `PredefinedHighlights`: Common highlight configurations

**Responsibilities:**
- Define highlight configurations
- Support multiple highlighter types
- Manage fragment selection and ordering
- Provide customizable tags and formatting

### 7. Autocomplete (`autocomplete.py`)

Intelligent autocomplete suggestions.

**Key Classes:**
- `AutocompleteEngine`: Main autocomplete engine
- `AutocompleteRequest`: Request for autocomplete suggestions
- `AutocompleteResponse`: Response with suggestions
- `AutocompleteSuggestion`: Individual suggestion with metadata

**Responsibilities:**
- Generate prefix-based suggestions
- Support fuzzy matching
- Track popular and recent queries
- Provide entity-aware suggestions
- Deduplicate and rank suggestions

### 8. Unified Search (`unified_search.py`)

Multi-entity search across different entity types.

**Key Classes:**
- `UnifiedSearchEngine`: Engine for multi-entity searches
- `UnifiedSearchRequest`: Request for unified search
- `UnifiedSearchResponse`: Response with grouped results
- `EntitySearchResult`: Results for a single entity type

**Responsibilities:**
- Coordinate searches across multiple entities
- Aggregate results from different sources
- Provide unified response format
- Support cross-entity pagination

### 9. Sorting (`sorting.py`)

Sorting and ranking hooks.

**Key Classes:**
- `SortBuilder`: Builder for constructing sort specifications
- `SortCondition`: Individual sort condition
- `FieldBoost`, `FreshnessBoost`, `PopularityBoost`: Boost configurations
- `RankingHooks`: Hooks for custom ranking logic
- `PredefinedSorts`: Common sort configurations

**Responsibilities:**
- Define sort conditions and parameters
- Support multi-field sorting
- Provide score boosting mechanisms
- Enable custom ranking hooks
- Support business-rule-based boosting

### 10. Suggestions (`suggestions.py`)

Search suggestion system.

**Key Classes:**
- `SearchSuggestionEngine`: Main suggestion engine
- `RelatedQuery`, `SpellingCorrection`, `DidYouMean`: Suggestion types
- `RecentSearch`, `SavedSearch`, `TrendingSearch`: Search history
- `SearchTemplate`: Reusable search templates

**Responsibilities:**
- Generate related query suggestions
- Track recent and saved searches
- Compute trending searches
- Provide search templates
- Support spelling correction hooks

### 11. Performance (`performance.py`)

Performance optimization features.

**Key Classes:**
- `QueryCache`: LRU cache for query results
- `QueryOptimizer`: Query validation and optimization
- `PerformanceConfig`: Configuration for performance features
- `CacheEntry`: Individual cache entry

**Responsibilities:**
- Cache query results with TTL
- Optimize query strings and filters
- Validate query complexity
- Enforce query limits (depth, clauses)
- Provide cache statistics

### 12. Provider Translators (`translators/`)

Translation layer for provider-specific query languages.

**Key Classes:**
- `ElasticsearchQueryTranslator`: Translates DSL to Elasticsearch queries
- `PostgreSQLQueryTranslator`: Translates DSL to PostgreSQL/Django queries

**Responsibilities:**
- Translate Query DSL to provider-specific format
- Translate filters to provider format
- Translate aggregations to provider format
- Translate highlighting to provider format
- Handle provider-specific optimizations

## Data Flow

### Search Request Flow

1. **Request Reception**: Application layer creates a `SearchRequest` or `SearchExecutionContext`
2. **Context Creation**: Query Engine converts request to `SearchExecutionContext`
3. **Cache Check**: Query Engine checks cache for existing results
4. **Query Optimization**: `QueryOptimizer` optimizes query and filters
5. **Pre-Rank Hooks**: Ranking hooks are applied before search
6. **Provider Selection**: Current provider is selected from registry
7. **Query Translation**: Provider translator converts DSL to provider format
8. **Provider Execution**: Provider executes the search
9. **Post-Rank Hooks**: Ranking hooks are applied to results
10. **Score Modification**: Score modifiers adjust result scores
11. **Facet Computation**: Facets are computed if requested
12. **Aggregation Computation**: Aggregations are computed if requested
13. **Highlighting**: Highlights are applied if requested
14. **Result Construction**: `EngineResult` is constructed
15. **Cache Storage**: Result is cached if enabled
16. **Response Return**: Result is returned to application layer

### Autocomplete Flow

1. **Request**: Application creates `AutocompleteRequest`
2. **Prefix Matching**: Engine generates prefix-based suggestions
3. **Fuzzy Matching**: Engine generates fuzzy suggestions (if enabled)
4. **Popular Queries**: Engine retrieves popular query suggestions
5. **Recent Searches**: Engine retrieves recent search suggestions
6. **Entity Suggestions**: Engine retrieves entity-specific suggestions
7. **Deduplication**: Duplicate suggestions are removed
8. **Ranking**: Suggestions are ranked by score
9. **Limiting**: Results are limited to requested count
10. **Response**: `AutocompleteResponse` is returned

### Unified Search Flow

1. **Request**: Application creates `UnifiedSearchRequest`
2. **Entity Iteration**: Engine iterates over requested entity types
3. **Filter Conversion**: Generic filters are converted to entity-specific
4. **Parallel Search**: Searches are executed for each entity type
5. **Result Aggregation**: Results are aggregated by entity type
6. **Total Limit**: Results are limited to total limit
7. **Facet Computation**: Cross-entity facets are computed (if enabled)
8. **Response**: `UnifiedSearchResponse` is returned

## Configuration

### Performance Configuration

```python
from apps.search.query_engine.performance import PerformanceConfig

config = PerformanceConfig(
    query_timeout_ms=30000,
    max_query_depth=10,
    max_clauses=1000,
    max_result_window=10000,
    cache_enabled=True,
    cache_ttl_seconds=300,
    cache_max_size=1000,
    enable_query_cancellation=True,
    enable_pagination_optimization=True,
    enable_large_result_protection=True,
    large_result_threshold=1000,
)
```

### Query Engine Initialization

```python
from apps.search.query_engine.engine import QueryEngine
from apps.search.query_engine.performance import PerformanceConfig
from apps.search.providers import SearchProviderRegistry

registry = SearchProviderRegistry()
config = PerformanceConfig()
engine = QueryEngine(registry, config)
```

## Extension Points

### Custom Ranking Hooks

Add custom ranking logic by registering hooks:

```python
def custom_pre_rank_hook(context):
    # Modify context before ranking
    pass

def custom_post_rank_hook(results, context):
    # Modify results after ranking
    pass

def custom_score_modifier(results, context):
    # Modify scores
    pass

engine.add_ranking_hook("pre_rank", custom_pre_rank_hook)
engine.add_ranking_hook("post_rank", custom_post_rank_hook)
engine.add_ranking_hook("score_modifier", custom_score_modifier)
```

### Custom Filters

Extend filter system by creating entity-specific filters:

```python
from apps.search.query_engine.filters import Filter, FilterOperator

class CustomFilters:
    @staticmethod
    def by_custom_field(value):
        return Filter(
            field="custom_field",
            operator=FilterOperator.EQ,
            value=value
        )
```

### Custom Aggregations

Create custom aggregation types by extending the base class:

```python
from apps.search.query_engine.aggregations import Aggregation

class CustomAggregation(Aggregation):
    def __init__(self, name: str, field: str):
        super().__init__(name, "custom")
        self.field = field
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": "custom",
            "field": self.field,
        }
```

## Best Practices

1. **Use Builders**: Always use builder classes (`DSLQueryBuilder`, `FilterBuilder`, etc.) for constructing complex queries
2. **Validate Early**: Validate requests before executing searches to fail fast
3. **Cache Appropriately**: Enable caching for frequently-executed queries
4. **Monitor Complexity**: Use `QueryOptimizer` to check query complexity
5. **Use Predefined Configurations**: Leverage `PredefinedFacets`, `PredefinedSorts`, etc. for common patterns
6. **Handle Errors Gracefully**: Always handle provider errors and provide fallback behavior
7. **Profile Performance**: Use cache statistics and query timing to identify bottlenecks

## Performance Considerations

1. **Query Caching**: Cache results for identical queries to reduce provider load
2. **Query Optimization**: Let the optimizer clean up queries before execution
3. **Pagination**: Use pagination to avoid large result sets
4. **Facet Limits**: Limit facet sizes to prevent excessive computation
5. **Aggregation Limits**: Limit aggregation buckets to prevent memory issues
6. **Depth Limits**: Enforce query depth limits to prevent deep recursion
7. **Clause Limits**: Enforce clause limits to prevent overly complex queries

## Security Considerations

1. **Input Validation**: Always validate user input before constructing queries
2. **Injection Prevention**: Use parameterized queries to prevent injection attacks
3. **Access Control**: Ensure users can only search entities they have access to
4. **Rate Limiting**: Implement rate limiting for search endpoints
5. **Query Limits**: Enforce maximum query complexity to prevent DoS attacks
