# Search Infrastructure Documentation

## Phase 5.1 - Search Infrastructure Implementation

**Date:** 2026-07-23
**Status:** Complete

---

## Overview

This document describes the search infrastructure implemented for the MatchHire platform. The infrastructure provides a provider-agnostic search framework that supports multiple search backends (PostgreSQL, Elasticsearch, OpenSearch, Vector Search, Hybrid Search) while maintaining a consistent API and service layer.

---

## Architecture

### Layer Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer                                │
│  (Future: Search Views, Autocomplete Views, Recommendation Views)│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                               │
│  JobSearchService, CandidateSearchService, ResumeSearchService, │
│  CompanySearchService, RecruiterSearchService, SkillSearchService│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Provider Layer                               │
│  PostgreSQLProvider (Current)                                   │
│  ElasticsearchProvider (Future - Phase 5.2)                     │
│  OpenSearchProvider (Future)                                     │
│  VectorSearchProvider (Future)                                   │
│  HybridProvider (Future)                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                               │
│  PostgreSQL Database (Current)                                   │
│  Elasticsearch Cluster (Future)                                  │
│  Vector Database (Future)                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module Structure

```
apps/search/
├── __init__.py
├── apps.py                          # Django app configuration
├── config.py                        # Search configuration manager
├── exceptions.py                    # Search-specific exceptions
├── registry.py                      # Provider registry
├── signals.py                       # Django signals for indexing
├── providers/
│   ├── __init__.py
│   ├── base.py                      # Base provider interface
│   └── postgresql.py               # PostgreSQL provider implementation
├── schemas/
│   ├── __init__.py
│   ├── requests.py                  # Request models (SearchRequest, etc.)
│   └── responses.py                 # Response models (SearchResponse, etc.)
├── services/
│   ├── __init__.py
│   ├── base.py                      # Base search service
│   ├── entity_services.py           # Entity-specific services
│   └── factory.py                   # Service factory
├── query_builder/
│   ├── __init__.py
│   └── builder.py                   # Query builder implementation
├── utils/
│   ├── __init__.py
│   └── helpers.py                   # Utility functions
└── tests/
    ├── __init__.py
    ├── test_exceptions.py
    ├── test_registry.py
    ├── test_schemas.py
    ├── test_query_builder.py
    ├── test_config.py
    └── test_utils.py
```

---

## Components

### 1. Provider Interface (`providers/base.py`)

The `SearchProvider` abstract base class defines the interface that all search providers must implement:

**Methods:**
- `search()` - Execute a search query
- `autocomplete()` - Get autocomplete suggestions
- `index()` - Index a single document
- `bulk_index()` - Index multiple documents
- `delete()` - Delete a single document
- `bulk_delete()` - Delete multiple documents
- `health()` - Check provider health
- `statistics()` - Get statistics about indexed documents

**Data Classes:**
- `IndexResult` - Result of single document indexing
- `BulkIndexResult` - Result of bulk document indexing
- `DeleteResult` - Result of document deletion
- `BulkDeleteResult` - Result of bulk document deletion
- `HealthResult` - Result of health check
- `StatisticsResult` - Result of statistics query

### 2. PostgreSQL Provider (`providers/postgresql.py`)

The `PostgreSQLProvider` implements the search provider interface using Django ORM and PostgreSQL-specific features:

**Features:**
- Full-text search using PostgreSQL `tsvector`
- Trigram matching for autocomplete
- GIN indexes for performance
- ORM-based filtering and sorting
- Pagination support

**Entity Types Supported:**
- `job` - Jobs
- `candidate` - Candidates (Users)
- `resume` - Resumes
- `company` - Companies (RecruiterProfile)
- `recruiter` - Recruiters (Users)
- `skill` - Skills

### 3. Search Registry (`registry.py`)

The `SearchRegistry` manages provider registration and retrieval:

**Features:**
- Singleton pattern for global access
- Provider registration/unregistration
- Current provider selection
- Provider instance caching
- Built-in PostgreSQL provider registration

**Usage:**
```python
from apps.search.registry import get_registry

registry = get_registry()
registry.set_current_provider("postgresql")
provider = registry.get_provider(config={"connection": "default"})
```

### 4. Request Models (`schemas/requests.py`)

Standardized request models for search operations:

**Models:**
- `SearchRequest` - Complete search request with query, filters, sort, pagination
- `SearchFilter` - Individual filter specification
- `SearchSort` - Sort specification
- `PaginationRequest` - Pagination parameters
- `AutocompleteRequest` - Autocomplete request

**Usage:**
```python
from apps.search.schemas.requests import SearchRequest, SearchFilter, SortDirection

request = (
    SearchRequest(entity_type="job", query="engineer")
    .add_filter("status", "active")
    .add_sort("created_at", SortDirection.DESC)
    .with_pagination(page=1, page_size=20)
)
```

### 5. Response Models (`schemas/responses.py`)

Standardized response models for search operations:

**Models:**
- `SearchResponse` - Complete search response with results, pagination, facets
- `SearchResultItem` - Individual search result
- `PaginationMetadata` - Pagination metadata
- `FacetResponse` - Facet/aggregation response
- `AutocompleteResponse` - Autocomplete response
- `SuggestionResponse` - Individual suggestion
- `ErrorResponse` - Error response

### 6. Query Builder (`query_builder/builder.py`)

Provider-agnostic query builder for constructing complex queries:

**Features:**
- Boolean filters (AND, OR, NOT)
- Nested filters
- Multiple sort conditions
- Field selection
- Field boosts for relevance scoring
- Pagination (page/page_size or offset/limit)

**Usage:**
```python
from apps.search.query_builder.builder import QueryBuilder, ComparisonOperator

query = (
    QueryBuilder.for_entity("job")
    .set_query("software engineer")
    .add_filter("status", ComparisonOperator.EXACT, "active")
    .add_filter("salary", ComparisonOperator.GTE, 50000)
    .add_sort("created_at", "desc")
    .set_pagination(page=1, page_size=20)
)
```

### 7. Search Services (`services/`)

**Base Service (`services/base.py`):**
- `BaseSearchService` - Abstract base class for entity-specific services
- Provides common functionality for all search services

**Entity Services (`services/entity_services.py`):**
- `JobSearchService` - Job search
- `CandidateSearchService` - Candidate search
- `ResumeSearchService` - Resume search
- `CompanySearchService` - Company search
- `RecruiterSearchService` - Recruiter search
- `SkillSearchService` - Skill search

**Service Factory (`services/factory.py`):**
- `SearchServiceFactory` - Factory for creating entity-specific services

**Usage:**
```python
from apps.search.services.factory import SearchServiceFactory
from apps.search.registry import get_registry

registry = get_registry()
provider = registry.get_provider("postgresql", config={"connection": "default"})
service = SearchServiceFactory.create_job_service(provider)

results = service.search(request)
```

### 8. Configuration (`config.py`)

The `SearchConfig` class provides access to search-related configuration:

**Configuration Options:**
- `SEARCH_PROVIDER` - Default provider name
- `SEARCH_CONFIG` - Provider-specific configuration
- `SEARCH_PAGE_SIZE` - Default page size
- `SEARCH_MAX_PAGE_SIZE` - Maximum page size
- `SEARCH_AUTOCOMPLETE_LIMIT` - Default autocomplete limit
- `SEARCH_MAX_AUTOCOMPLETE_LIMIT` - Maximum autocomplete limit
- `SEARCH_TIMEOUT` - Search timeout in seconds
- `SEARCH_CACHE_CONFIG` - Cache configuration
- `SEARCH_FEATURE_FLAGS` - Feature flags
- `SEARCH_RANKING_CONFIG` - Ranking configuration
- `SEARCH_VECTOR_CONFIG` - Vector search configuration

### 9. Exceptions (`exceptions.py`)

Search-specific exceptions:

- `SearchError` - Base exception
- `ProviderUnavailable` - Provider not available
- `InvalidQuery` - Invalid query
- `InvalidFilter` - Invalid filter
- `SearchTimeout` - Search timeout
- `ConfigurationError` - Configuration error
- `ProviderNotRegistered` - Provider not registered
- `IndexingError` - Indexing failed
- `BulkIndexingError` - Bulk indexing failed

### 10. Utilities (`utils/helpers.py`)

Helper functions for common search operations:

- `sanitize_query()` - Sanitize query strings
- `normalize_filters()` - Normalize filter values
- `extract_field_boosts()` - Extract field boosts from query
- `calculate_score_normalization()` - Normalize scores
- `merge_results()` - Merge multiple result sets
- `format_highlight()` - Apply highlight tags
- `truncate_text()` - Truncate text
- `parse_date_range()` - Parse date range strings
- `validate_pagination()` - Validate pagination parameters

---

## Configuration

### Django Settings

The search infrastructure is configured in `matchhire_backend/settings/base.py`:

```python
# Search configuration
SEARCH_PROVIDER = "postgresql"

SEARCH_CONFIG = {
    "postgresql": {
        "connection": "default",
    },
    "elasticsearch": {
        "hosts": ["http://localhost:9200"],
        "index_prefix": "matchhire",
        "timeout": 30,
    },
}

SEARCH_PAGE_SIZE = 20
SEARCH_MAX_PAGE_SIZE = 100
SEARCH_AUTOCOMPLETE_LIMIT = 10
SEARCH_MAX_AUTOCOMPLETE_LIMIT = 50
SEARCH_TIMEOUT = 30

SEARCH_FEATURE_FLAGS = {
    "full_text_search": True,
    "autocomplete": True,
    "faceting": False,
    "vector_search": False,
    "hybrid_search": False,
}
```

### Environment Variables

Configure via environment variables:

- `SEARCH_PROVIDER` - Default search provider
- `ELASTICSEARCH_HOSTS` - Elasticsearch hosts (comma-separated)
- `OPENSEARCH_HOSTS` - OpenSearch hosts (comma-separated)
- `SEARCH_TIMEOUT` - Search timeout in seconds
- `SEARCH_CACHE_ENABLED` - Enable/disable caching

---

## Usage Examples

### Basic Search

```python
from apps.search.schemas.requests import SearchRequest
from apps.search.services.factory import SearchServiceFactory
from apps.search.registry import get_registry

# Get provider
registry = get_registry()
provider = registry.get_provider("postgresql", config={"connection": "default"})

# Create service
service = SearchServiceFactory.create_job_service(provider)

# Create request
request = SearchRequest(entity_type="job", query="software engineer")

# Execute search
response = service.search(request)
print(f"Found {response.total} results")
```

### Search with Filters and Sorting

```python
from apps.search.schemas.requests import SearchRequest, SortDirection

request = (
    SearchRequest(entity_type="job", query="engineer")
    .add_filter("status", "active")
    .add_filter("salary", 50000, operator="gte")
    .add_sort("created_at", SortDirection.DESC)
    .with_pagination(page=1, page_size=20)
)

response = service.search(request)
```

### Autocomplete

```python
from apps.search.schemas.requests import AutocompleteRequest

request = AutocompleteRequest(
    entity_type="job",
    field="title",
    prefix="soft",
    limit=10
)

response = service.autocomplete(request)
for suggestion in response.suggestions:
    print(suggestion.value)
```

### Using Query Builder

```python
from apps.search.query_builder.builder import QueryBuilder, ComparisonOperator

query = (
    QueryBuilder.for_entity("job")
    .set_query("software engineer")
    .add_filter("status", ComparisonOperator.EXACT, "active")
    .add_filter("salary", ComparisonOperator.GTE, 50000)
    .add_sort("created_at", "desc")
    .set_pagination(page=1, page_size=20)
)

query_dict = query.build()
```

---

## Testing

### Running Tests

```bash
# Run all search tests
python manage.py test apps.search

# Run specific test file
python manage.py test apps.search.tests.test_registry

# Run with coverage
coverage run --source='apps.search' manage.py test apps.search
coverage report
```

### Test Coverage

The test suite includes:

- `test_exceptions.py` - Exception hierarchy and behavior
- `test_registry.py` - Provider registration and retrieval
- `test_schemas.py` - Request and response models
- `test_query_builder.py` - Query builder functionality
- `test_config.py` - Configuration management
- `test_utils.py` - Utility functions

---

## Extension Guide

### Adding a New Provider

To add a new search provider (e.g., Elasticsearch):

1. Create provider class in `providers/elasticsearch.py`:

```python
from apps.search.providers.base import SearchProvider

class ElasticsearchProvider(SearchProvider):
    def _initialize(self):
        # Initialize Elasticsearch client
        pass

    def search(self, entity_type, query, filters=None, sort=None, pagination=None, fields=None):
        # Implement search using Elasticsearch
        pass

    # Implement other required methods...
```

2. Register the provider:

```python
from apps.search.registry import get_registry
from apps.search.providers.elasticsearch import ElasticsearchProvider

registry = get_registry()
registry.register_provider("elasticsearch", ElasticsearchProvider)
```

3. Add configuration to settings:

```python
SEARCH_CONFIG = {
    "elasticsearch": {
        "hosts": ["http://localhost:9200"],
        "index_prefix": "matchhire",
        "timeout": 30,
    },
}
```

4. Set as current provider:

```python
registry.set_current_provider("elasticsearch")
```

### Adding a New Entity Type

To add a new searchable entity type:

1. Add entity type to `PostgreSQLProvider.ENTITY_MODELS`
2. Add searchable fields to `PostgreSQLProvider.SEARCHABLE_FIELDS`
3. Add autocomplete fields to `PostgreSQLProvider.AUTOCOMPLETE_FIELDS`
4. Create entity service in `services/entity_services.py`
5. Add factory method in `services/factory.py`
6. Add query builder factory method in `query_builder/builder.py`

---

## Migration Path

### Phase 5.1 (Current)
- PostgreSQL provider implementation
- Basic full-text search
- Autocomplete
- Provider abstraction

### Phase 5.2 (Next)
- Elasticsearch provider implementation
- Advanced full-text search with BM25
- Faceted search
- Better autocomplete with completion suggester
- Index synchronization

### Phase 5.3 (Future)
- Vector search provider
- Semantic search
- Hybrid search (keyword + vector)
- LLM-based ranking

---

## Technical Decisions

### 1. Provider Interface Design
- **Decision:** Abstract base class with interface methods
- **Rationale:** Ensures all providers implement the same interface, making it easy to switch between providers

### 2. PostgreSQL as Default Provider
- **Decision:** Use PostgreSQL ORM as the default provider
- **Rationale:** No additional infrastructure required, leverages existing database, provides immediate value

### 3. Registry Pattern
- **Decision:** Singleton registry for provider management
- **Rationale:** Centralized provider management, easy to switch providers globally

### 4. Request/Response Models
- **Decision:** Separate request and response models from provider logic
- **Rationale:** Provider-agnostic API, consistent format across providers

### 5. Query Builder
- **Decision:** Separate	query builder for constructing queries
- **Rationale:** Reusable query construction, supports complex queries, provider-agnostic

### 6. Service Layer
- **Decision:** Entity-specific services extending base service
- **Rationale:** Encapsulates entity-specific logic, provides consistent interface

### 7. Configuration via Django Settings
- **Decision:** Use Django settings for configuration
- **Rationale:** Familiar pattern for Django developers, easy to override per environment

---

## Performance Considerations

### PostgreSQL Provider
- Uses GIN indexes for full-text search
- Supports partial indexes for common queries
- Implements efficient pagination with offset/limit
- Uses `only()` for field selection to reduce query overhead

### Caching
- Cache configuration is ready but disabled by default
- Will be enabled in Phase 5.2 with Redis backend
- Separate TTL for different result types

### Indexing
- PostgreSQL provider uses database as source of truth (no explicit indexing)
- Future providers will implement async indexing via Celery
- Signals are ready for automatic indexing

---

## Security Considerations

### Input Validation
- All request models validate input parameters
- Query sanitization removes dangerous characters
- Pagination parameters are clamped to maximum values

### Access Control
- Provider layer does not implement access control
- Access control should be implemented at the API layer
- Services can be wrapped with permission checks

### SQL Injection Prevention
- PostgreSQL provider uses Django ORM with parameterized queries
- No raw SQL queries are used

---

## Monitoring and Observability

### Metrics
- Query execution time (`took_ms`)
- Result counts
- Provider health status
- Document statistics

### Logging
- Provider errors are logged
- Search failures are logged
- Configuration errors are logged

### Health Checks
- Provider health check endpoint
- Database connection verification

---

## Known Limitations

### PostgreSQL Provider
- Full-text search is basic compared to Elasticsearch
- No faceted search support
- Autocomplete uses simple prefix matching
- No relevance scoring beyond basic ranking

### Current Implementation
- No API views implemented (future phase)
- No caching enabled (future phase)
- No vector search (future phase)
- No hybrid search (future phase)

---

## Future Enhancements

### Phase 5.2
- Elasticsearch provider implementation
- Faceted search
- Advanced autocomplete
- Index synchronization
- Caching layer

### Phase 5.3
- Vector search provider
- Semantic search
- Hybrid search
- LLM-based ranking
- Learning-to-rank

### Phase 5.4
- Multi-region deployment
- Cross-cluster replication
- Advanced analytics
- A/B testing framework

---

## Troubleshooting

### Provider Not Available
```python
from apps.search.exceptions import ProviderUnavailable

try:
    response = service.search(request)
except ProviderUnavailable as e:
    print(f"Provider unavailable: {e}")
```

### Invalid Query
```python
from apps.search.exceptions import InvalidQuery

try:
    response = service.search(request)
except InvalidQuery as e:
    print(f"Invalid query: {e}")
```

### Configuration Error
```python
from apps.search.exceptions import ConfigurationError

try:
    provider = registry.get_provider("postgresql")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

---

## References

- [Search Architecture Design](../search_architecture/SEARCH_ARCHITECTURE.md)
- [Search Domain Model](../search_architecture/SEARCH_DOMAIN_MODEL.md)
- [Search Requirements](../search_architecture/SEARCH_REQUIREMENTS.md)
- [Index Strategy](../search_architecture/INDEX_STRATEGY.md)
- [Ranking Strategy](../search_architecture/RANKING_STRATEGY.md)

---

## Summary

The search infrastructure implemented in Phase 5.1 provides:

- **Provider-agnostic architecture** - Easy to switch between search providers
- **PostgreSQL provider** - Immediate value with no additional infrastructure
- **Extensible design** - Ready for Elasticsearch, vector search, and hybrid search
- **Comprehensive testing** - High test coverage for all components
- **Well-documented** - Complete documentation for developers
- **Configuration-driven** - Easy to configure via Django settings
- **Production-ready** - Error handling, validation, and monitoring hooks

The infrastructure is ready for Phase 5.2 where Elasticsearch will be implemented as an additional provider, enabling advanced search features while maintaining backward compatibility with the PostgreSQL provider.
