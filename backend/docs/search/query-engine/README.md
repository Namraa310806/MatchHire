# Advanced Query Engine Documentation

## Overview

The MatchHire Advanced Query Engine is a provider-independent search abstraction layer that powers all search experiences in the platform. It transforms SearchRequest objects into optimized queries, supports advanced filtering, faceting, aggregations, highlighting, autocomplete, and unified multi-entity search.

## Architecture

### Core Principles

1. **Provider Independence**: The Query Engine uses a provider-independent DSL that can be translated to PostgreSQL or Elasticsearch without application code changes.
2. **Single Abstraction**: The Query Engine is the single abstraction responsible for every search request in MatchHire.
3. **Business Logic Separation**: The engine does not contain business logic - it only handles query construction and execution.
4. **Registry-Based**: Uses the SearchRegistry to manage provider selection and configuration.

### Components

```
query_engine/
├── __init__.py              # Main exports
├── dsl.py                   # Query DSL (Match, MultiMatch, Bool, etc.)
├── filters.py               # Advanced filters (JobFilters, CandidateFilters, etc.)
├── facets.py                # Faceted search (FacetBuilder, FacetState)
├── aggregations.py          # Aggregations (Terms, Range, Histogram, Stats)
├── highlighting.py          # Highlighting (HighlightConfig, HighlightBuilder)
├── autocomplete.py          # Autocomplete (AutocompleteEngine, Suggestions)
├── unified_search.py       # Unified multi-entity search
├── sorting.py              # Sorting & ranking hooks
├── suggestions.py          # Search suggestions (Related queries, Did-you-mean)
├── performance.py          # Performance optimizations (Cache, Optimizer)
├── engine.py               # Main QueryEngine orchestration
└── translators/
    ├── __init__.py
    ├── postgresql.py       # PostgreSQL DSL translator
    └── elasticsearch.py    # Elasticsearch DSL translator
```

### Data Flow

```
SearchRequest → QueryEngine → Query DSL → Translator → Provider → Results
                    ↓
                Filters
                Facets
                Aggregations
                Highlighting
```

## Quick Start

### Basic Search

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
    pagination={"page": 1, "page_size": 20}
)

# Execute search
result = engine.search(context)
```

### Using the Query DSL

```python
from apps.search.query_engine.dsl import DSLQueryBuilder, MatchQuery

# Build a query
builder = DSLQueryBuilder()
query = builder.match(field="title", query="software engineer").build()
```

### Using Filters

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

# Or use predefined filters
status_filter = JobFilters.by_status("active")
salary_filter = JobFilters.by_salary_range(min_salary=50000, max_salary=100000)
```

### Using Facets

```python
from apps.search.query_engine.facets import FacetBuilder

builder = FacetBuilder()
facets = (
    builder
    .location_facet(size=20)
    .company_facet(size=15)
    .skills_facet(size=30)
    .build()
)
```

## Provider Configuration

### PostgreSQL

```python
# settings.py
SEARCH_PROVIDER = "postgresql"
SEARCH_CONFIG = {
    "postgresql": {
        "connection": "default",
    }
}
```

### Elasticsearch

```python
# settings.py
SEARCH_PROVIDER = "elasticsearch"
SEARCH_CONFIG = {
    "elasticsearch": {
        "hosts": ["http://localhost:9200"],
        "index_prefix": "matchhire",
    }
}
```

## Performance

The Query Engine includes several performance optimizations:

- **Query Caching**: LRU cache with TTL support
- **Query Optimization**: Automatic query simplification and validation
- **Pagination Optimization**: Enforced result windows and page size limits
- **Large Result Protection**: Automatic result set size limits

## Testing

Run tests with:

```bash
python manage.py test apps.search.query_engine.tests
```

## Next Steps

- [Query DSL Reference](./dsl-reference.md)
- [Filter Guide](./filter-guide.md)
- [Aggregation Guide](./aggregation-guide.md)
- [Faceted Search](./faceted-search.md)
- [Autocomplete](./autocomplete.md)
- [Unified Search](./unified-search.md)
- [Examples](./examples.md)
- [Performance](./performance.md)
- [Extension Guide](./extension-guide.md)
