# Search Module

## Phase 5.1 - Search Infrastructure
## Phase 5.2 - Search Indexing Engine

**Status:** Complete

---

## Overview

The search module provides a provider-agnostic search infrastructure for the MatchHire platform. It supports multiple search backends (PostgreSQL, Elasticsearch, OpenSearch, Vector Search, Hybrid Search) while maintaining a consistent API and service layer.

The indexing engine serves as the single source of truth for keeping search providers synchronized with application data.

---

## Directory Structure

```
apps/search/
├── __init__.py
├── apps.py                          # Django app configuration
├── config.py                        # Search configuration manager
├── exceptions.py                    # Search-specific exceptions
├── registry.py                      # Provider registry
├── signals.py                       # Django signals for indexing
├── indexing/                        # Indexing engine (Phase 5.2)
│   ├── __init__.py
│   ├── documents.py                 # Search document models
│   ├── serializers.py               # Django model serializers
│   ├── index_manager.py             # Index management operations
│   ├── sync_service.py              # Synchronization engine
│   ├── bulk_indexer.py              # Bulk indexing framework
│   ├── event_handlers.py            # Django signal handlers
│   ├── metrics.py                   # Metrics collection
│   ├── verification.py              # Integrity verification
│   ├── management/
│   │   ├── __init__.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       ├── rebuild_search_index.py
│   │       ├── sync_search_index.py
│   │       ├── verify_search_index.py
│   │       └── search_index_status.py
│   └── tests/
│       ├── __init__.py
│       ├── test_documents.py
│       ├── test_serializers.py
│       ├── test_sync_service.py
│       ├── test_index_manager.py
│       └── test_bulk_indexer.py
├── providers/
│   ├── __init__.py
│   ├── base.py                      # Base provider interface
│   └── postgresql.py               # PostgreSQL provider implementation
├── schemas/
│   ├── __init__.py
│   ├── requests.py                  # Request models
│   └── responses.py                 # Response models
├── services/
│   ├── __init__.py
│   ├── base.py                      # Base search service
│   ├── entity_services.py           # Entity-specific services
│   └── factory.py                   # Service factory
├── query_builder/
│   ├── __init__.py
│   └── builder.py                   # Query builder
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

## Quick Start

```python
from apps.search.schemas.requests import SearchRequest
from apps.search.services.factory import SearchServiceFactory
from apps.search.registry import get_registry

# Get provider
registry = get_registry()
provider = registry.get_provider("postgresql", config={"connection": "default"})

# Create service
service = SearchServiceFactory.create_job_service(provider)

# Search
request = SearchRequest(entity_type="job", query="software engineer")
response = service.search(request)
```

---

## Components

### Providers
- **base.py** - Abstract interface for search providers
- **postgresql.py** - PostgreSQL provider implementation

### Schemas
- **requests.py** - SearchRequest, SearchFilter, SearchSort, PaginationRequest, AutocompleteRequest
- **responses.py** - SearchResponse, SearchResultItem, PaginationMetadata, AutocompleteResponse

### Services
- **base.py** - BaseSearchService abstract class
- **entity_services.py** - JobSearchService, CandidateSearchService, ResumeSearchService, etc.
- **factory.py** - SearchServiceFactory for creating services

### Query Builder
- **builder.py** - QueryBuilder for constructing complex queries

### Registry
- **registry.py** - SearchRegistry for provider management

### Configuration
- **config.py** - SearchConfig for accessing settings

### Utilities
- **helpers.py** - Helper functions for query sanitization, filter normalization, etc.

### Exceptions
- **exceptions.py** - SearchError, ProviderUnavailable, InvalidQuery, etc.

---

## Documentation

- [Search Infrastructure README](../../docs/search/README.md) - Complete infrastructure documentation
- [Developer Guide](../../docs/search/DEVELOPER_GUIDE.md) - Developer guide with examples

---

## Testing

Run tests:

```bash
python manage.py test apps.search
```

---

## Configuration

Configure in Django settings:

```python
SEARCH_PROVIDER = "postgresql"
SEARCH_CONFIG = {
    "postgresql": {
        "connection": "default",
    },
}
SEARCH_PAGE_SIZE = 20
SEARCH_MAX_PAGE_SIZE = 100
```
