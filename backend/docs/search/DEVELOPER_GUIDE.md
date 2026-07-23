# Search Infrastructure Developer Guide

## Phase 5.1 - Search Infrastructure

**Date:** 2026-07-23
**Status:** Complete

---

## Quick Start

### 1. Basic Search

```python
from apps.search.schemas.requests import SearchRequest
from apps.search.services.factory import SearchServiceFactory
from apps.search.registry import get_registry

# Get the registry and provider
registry = get_registry()
provider = registry.get_provider("postgresql", config={"connection": "default"})

# Create a service for the entity type
service = SearchServiceFactory.create_job_service(provider)

# Create a search request
request = SearchRequest(entity_type="job", query="software engineer")

# Execute the search
response = service.search(request)

# Access results
for result in response.results:
    print(f"ID: {result.id}, Score: {result.score}")
    print(f"Data: {result.data}")
```

### 2. Search with Filters

```python
from apps.search.schemas.requests import SearchRequest, SortDirection

request = (
    SearchRequest(entity_type="job", query="engineer")
    .add_filter("status", "active")
    .add_filter("salary", 50000, operator="gte")
    .add_filter("employment_type", "full_time")
    .add_sort("created_at", SortDirection.DESC)
    .with_pagination(page=1, page_size=20)
)

response = service.search(request)
```

### 3. Autocomplete

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
    print(f"Suggestion: {suggestion.value}")
```

### 4. Using Query Builder

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

## Architecture Overview

### Components

1. **Provider Layer** - Abstract interface for search backends
2. **Service Layer** - Business logic for search operations
3. **Schema Layer** - Request/response models
4. **Query Builder** - Query construction utilities
5. **Registry** - Provider management
6. **Configuration** - Settings management

### Data Flow

```
API Layer (Future)
    ↓
Service Layer
    ↓
Provider Layer
    ↓
Storage Layer
```

---

## Provider Implementation

### Creating a Custom Provider

To implement a custom search provider:

```python
from apps.search.providers.base import SearchProvider
from apps.search.providers.base import (
    IndexResult,
    BulkIndexResult,
    DeleteResult,
    BulkDeleteResult,
    HealthResult,
    StatisticsResult,
)

class MyCustomProvider(SearchProvider):
    """Custom search provider implementation."""

    def _initialize(self):
        """Initialize the provider connection."""
        # Initialize your search engine connection
        self.client = MySearchClient(self.config.get("host"))

    def search(self, entity_type, query, filters=None, sort=None, pagination=None, fields=None):
        """Execute a search query."""
        # Implement search logic
        results = self.client.search(
            index=entity_type,
            query=query,
            filters=filters,
            sort=sort,
            pagination=pagination,
            fields=fields,
        )

        return {
            "results": results["hits"],
            "total": results["total"],
            "took_ms": results["took_ms"],
            "metadata": {"provider": "custom", "entity_type": entity_type},
        }

    def autocomplete(self, entity_type, field, prefix, context=None, limit=10):
        """Get autocomplete suggestions."""
        suggestions = self.client.suggest(
            index=entity_type,
            field=field,
            prefix=prefix,
            limit=limit,
        )
        return [{"value": s["text"], "metadata": s.get("meta", {})} for s in suggestions]

    def index(self, entity_type, document_id, document):
        """Index a single document."""
        try:
            self.client.index(
                index=entity_type,
                id=document_id,
                document=document,
            )
            return IndexResult(success=True, document_id=document_id)
        except Exception as e:
            return IndexResult(success=False, document_id=document_id, error=str(e))

    def bulk_index(self, entity_type, documents):
        """Index multiple documents in bulk."""
        try:
            self.client.bulk_index(
                index=entity_type,
                documents=documents,
            )
            return BulkIndexResult(
                success=True,
                indexed_count=len(documents),
                failed_count=0,
                errors=[],
            )
        except Exception as e:
            return BulkIndexResult(
                success=False,
                indexed_count=0,
                failed_count=len(documents),
                errors=[{"error": str(e)}],
            )

    def delete(self, entity_type, document_id):
        """Delete a single document."""
        try:
            self.client.delete(index=entity_type, id=document_id)
            return DeleteResult(success=True, document_id=document_id)
        except Exception as e:
            return DeleteResult(success=False, document_id=document_id, error=str(e))

    def bulk_delete(self, entity_type, document_ids):
        """Delete multiple documents in bulk."""
        try:
            self.client.bulk_delete(index=entity_type, ids=document_ids)
            return BulkDeleteResult(
                success=True,
                deleted_count=len(document_ids),
                failed_count=0,
                errors=[],
            )
        except Exception as e:
            return BulkDeleteResult(
                success=False,
                deleted_count=0,
                failed_count=len(document_ids),
                errors=[{"error": str(e)}],
            )

    def health(self):
        """Check provider health."""
        try:
            self.client.ping()
            return HealthResult(
                healthy=True,
                provider_name="custom",
                details={"host": self.config.get("host")},
            )
        except Exception as e:
            return HealthResult(
                healthy=False,
                provider_name="custom",
                details={},
                error=str(e),
            )

    def statistics(self, entity_type=None):
        """Get statistics about indexed documents."""
        try:
            count = self.client.count(index=entity_type) if entity_type else self.client.count_all()
            return StatisticsResult(document_count=count)
        except Exception as e:
            raise Exception(f"Statistics query failed: {e}")
```

### Registering a Custom Provider

```python
from apps.search.registry import get_registry
from myapp.providers.custom import MyCustomProvider

registry = get_registry()
registry.register_provider("custom", MyCustomProvider)
```

### Using a Custom Provider

```python
from apps.search.registry import get_registry

registry = get_registry()
registry.set_current_provider("custom")

config = {
    "host": "localhost",
    "port": 9200,
}

provider = registry.get_provider(config=config)
```

---

## Service Implementation

### Creating a Custom Service

To implement a custom search service for a new entity type:

```python
from apps.search.services.base import BaseSearchService
from apps.search.providers.base import SearchProvider

class MyEntitySearchService(BaseSearchService):
    """Search service for MyEntity."""

    def get_entity_type(self) -> str:
        return "my_entity"

    # Override methods if needed for custom behavior
    def search(self, request):
        # Add custom logic before/after search
        response = super().search(request)

        # Post-process results
        for result in response.results:
            result.data["custom_field"] = self._calculate_custom_value(result.data)

        return response

    def _calculate_custom_value(self, data):
        # Custom calculation logic
        return data.get("field1", 0) * 2
```

### Registering the Service in Factory

```python
from apps.search.services.factory import SearchServiceFactory

class SearchServiceFactory:
    # ... existing methods ...

    @staticmethod
    def create_my_entity_service(provider: SearchProvider) -> MyEntitySearchService:
        """Create a my entity search service."""
        return MyEntitySearchService(provider=provider)
```

---

## Configuration

### Accessing Configuration

```python
from apps.search.config import SearchConfig

# Get current provider
provider = SearchConfig.get_provider()

# Get provider configuration
config = SearchConfig.get_provider_config("postgresql")

# Get pagination settings
page_size = SearchConfig.get_page_size()
max_page_size = SearchConfig.get_max_page_size()

# Check feature flags
if SearchConfig.is_feature_enabled("full_text_search"):
    # Feature is enabled
    pass

# Get ranking configuration
ranking_config = SearchConfig.get_ranking_config()
default_strategy = SearchConfig.get_default_ranking_strategy()
```

### Adding Custom Configuration

Add to `matchhire_backend/settings/base.py`:

```python
SEARCH_CUSTOM_CONFIG = {
    "option1": "value1",
    "option2": 42,
}
```

Access in code:

```python
from django.conf import settings

custom_config = getattr(settings, "SEARCH_CUSTOM_CONFIG", {})
```

---

## Error Handling

### Handling Search Errors

```python
from apps.search.exceptions import (
    SearchError,
    ProviderUnavailable,
    InvalidQuery,
    InvalidFilter,
    SearchTimeout,
    ConfigurationError,
)

try:
    response = service.search(request)
except ProviderUnavailable as e:
    # Provider is not available
    # Log error, show user message, or fallback to another provider
    pass
except InvalidQuery as e:
    # Query is invalid
    # Show user error message
    pass
except InvalidFilter as e:
    # Filter is invalid
    # Show user error message
    pass
except SearchTimeout as e:
    # Search timed out
    # Log error, show user message
    pass
except ConfigurationError as e:
    # Configuration error
    # Log error, alert administrators
    pass
except SearchError as e:
    # Generic search error
    # Log error, show user message
    pass
```

### Custom Error Handling

```python
from apps.search.exceptions import SearchError

class CustomSearchError(SearchError):
    """Custom search error."""
    pass

# Raise custom error
raise CustomSearchError("Custom error message")
```

---

## Testing

### Writing Tests for Providers

```python
import pytest
from apps.search.providers.base import SearchProvider
from apps.search.providers.postgresql import PostgreSQLProvider

class TestPostgreSQLProvider:
    """Test PostgreSQL provider."""

    def test_search(self):
        """Test search functionality."""
        provider = PostgreSQLProvider(config={"connection": "default"})
        result = provider.search(
            entity_type="job",
            query="engineer",
            pagination={"page": 1, "page_size": 10},
        )
        assert "results" in result
        assert "total" in result
        assert "took_ms" in result

    def test_autocomplete(self):
        """Test autocomplete functionality."""
        provider = PostgreSQLProvider(config={"connection": "default"})
        result = provider.autocomplete(
            entity_type="job",
            field="title",
            prefix="eng",
            limit=10,
        )
        assert isinstance(result, list)

    def test_health(self):
        """Test health check."""
        provider = PostgreSQLProvider(config={"connection": "default"})
        result = provider.health()
        assert result.healthy is True
```

### Writing Tests for Services

```python
import pytest
from apps.search.services.entity_services import JobSearchService
from apps.search.providers.postgresql import PostgreSQLProvider
from apps.search.schemas.requests import SearchRequest

class TestJobSearchService:
    """Test job search service."""

    def test_search(self):
        """Test search functionality."""
        provider = PostgreSQLProvider(config={"connection": "default"})
        service = JobSearchService(provider)
        request = SearchRequest(entity_type="job", query="engineer")
        response = service.search(request)
        assert response.total >= 0
        assert response.took_ms >= 0

    def test_autocomplete(self):
        """Test autocomplete functionality."""
        provider = PostgreSQLProvider(config={"connection": "default"})
        service = JobSearchService(provider)
        request = AutocompleteRequest(
            entity_type="job",
            field="title",
            prefix="eng",
        )
        response = service.autocomplete(request)
        assert len(response.suggestions) >= 0
```

### Writing Tests for Registry

```python
import pytest
from apps.search.registry import SearchRegistry
from apps.search.providers.postgresql import PostgreSQLProvider

class TestSearchRegistry:
    """Test search registry."""

    def test_register_provider(self):
        """Test provider registration."""
        registry = SearchRegistry()
        registry.register_provider("test", PostgreSQLProvider)
        assert registry.is_registered("test")

    def test_get_provider(self):
        """Test provider retrieval."""
        registry = SearchRegistry()
        provider = registry.get_provider(
            "postgresql",
            config={"connection": "default"},
        )
        assert isinstance(provider, PostgreSQLProvider)
```

---

## Best Practices

### 1. Always Use the Registry

```python
# Good
from apps.search.registry import get_registry

registry = get_registry()
provider = registry.get_provider("postgresql", config={"connection": "default"})

# Avoid
from apps.search.providers.postgresql import PostgreSQLProvider

provider = PostgreSQLProvider(config={"connection": "default"})
```

### 2. Use Service Factory

```python
# Good
from apps.search.services.factory import SearchServiceFactory

service = SearchServiceFactory.create_job_service(provider)

# Avoid
from apps.search.services.entity_services import JobSearchService

service = JobSearchService(provider)
```

### 3. Use Request Models

```python
# Good
from apps.search.schemas.requests import SearchRequest

request = SearchRequest(entity_type="job", query="engineer")

# Avoid
request_dict = {"entity_type": "job", "query": "engineer"}
```

### 4. Handle Errors Gracefully

```python
# Good
try:
    response = service.search(request)
except SearchError as e:
    logger.error(f"Search failed: {e}")
    return error_response(str(e))

# Avoid
response = service.search(request)  # May raise unhandled exception
```

### 5. Validate Input

```python
# Good
from apps.search.utils.helpers import sanitize_query

query = sanitize_query(user_input)

# Avoid
query = user_input  # May contain malicious content
```

---

## Performance Tips

### 1. Use Field Selection

```python
# Only fetch needed fields
request = SearchRequest(
    entity_type="job",
    query="engineer",
    fields=["title", "company", "location"],
)
```

### 2. Use Appropriate Pagination

```python
# Use reasonable page sizes
request.with_pagination(page=1, page_size=20)  # Good
request.with_pagination(page=1, page_size=1000)  # Bad
```

### 3. Use Filters Effectively

```python
# Use specific filters
request.add_filter("status", "active")  # Good
request.add_filter("title__icontains", "engineer")  # Less efficient
```

### 4. Cache Results When Appropriate

```python
# Cache frequently accessed results
cache_key = f"search:{hash(str(request))}"
cached = cache.get(cache_key)
if cached:
    return cached

response = service.search(request)
cache.set(cache_key, response, timeout=300)
```

---

## Troubleshooting

### Provider Not Available

**Problem:** `ProviderUnavailable` exception raised

**Solution:**
- Check provider configuration
- Verify provider connection
- Check provider health

```python
provider = registry.get_provider("postgresql", config={"connection": "default"})
health = provider.health()
if not health.healthy:
    print(f"Provider unhealthy: {health.error}")
```

### Invalid Query

**Problem:** `InvalidQuery` exception raised

**Solution:**
- Validate query parameters
- Sanitize user input
- Check filter values

```python
from apps.search.utils.helpers import sanitize_query

query = sanitize_query(user_input)
```

### Configuration Error

**Problem:** `ConfigurationError` exception raised

**Solution:**
- Check Django settings
- Verify environment variables
- Check provider configuration

```python
from apps.search.config import SearchConfig

provider = SearchConfig.get_provider()
config = SearchConfig.get_provider_config(provider)
print(f"Config: {config}")
```

---

## Migration Guide

### Migrating from Direct ORM Queries

**Before:**
```python
from apps.jobs.models import Job

jobs = Job.objects.filter(
    title__icontains="engineer",
    status="active",
).order_by("-created_at")[:20]
```

**After:**
```python
from apps.search.schemas.requests import SearchRequest
from apps.search.services.factory import SearchServiceFactory
from apps.search.registry import get_registry

registry = get_registry()
provider = registry.get_provider("postgresql", config={"connection": "default"})
service = SearchServiceFactory.create_job_service(provider)

request = (
    SearchRequest(entity_type="job", query="engineer")
    .add_filter("status", "active")
    .add_sort("created_at", "desc")
    .with_pagination(page=1, page_size=20)
)

response = service.search(request)
jobs = response.results
```

---

## References

- [Search Infrastructure README](./README.md)
- [Search Architecture](../search_architecture/SEARCH_ARCHITECTURE.md)
- [Provider Interface](../../apps/search/providers/base.py)
- [Service Base Class](../../apps/search/services/base.py)
