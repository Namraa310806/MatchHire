# Unified Search Guide

## Overview

Unified Search allows searching across multiple entity types simultaneously, with unified response formatting, entity grouping, and cross-entity pagination.

## Unified Search Request

```python
from apps.search.query_engine.unified_search import UnifiedSearchRequest, EntityType

request = UnifiedSearchRequest(
    query="software engineer",
    entity_types=[EntityType.JOB, EntityType.CANDIDATE],
    filters={"location": "San Francisco"},
    sort=[{"field": "created_at", "direction": "desc"}],
    pagination={"page": 1, "page_size": 20},
    per_entity_limit=10,
    total_limit=50,
    include_facets=True,
)
```

## Entity Types

```python
from apps.search.query_engine.unified_search import EntityType

EntityType.JOB
EntityType.CANDIDATE
EntityType.RESUME
EntityType.COMPANY
EntityType.RECRUITER
EntityType.SKILL
EntityType.APPLICATION
EntityType.INTERVIEW
```

## Unified Search Engine

### Basic Usage

```python
from apps.search.query_engine.unified_search import UnifiedSearchEngine, UnifiedSearchRequest, EntityType

engine = UnifiedSearchEngine(provider_registry)

request = UnifiedSearchRequest(
    query="software engineer",
    entity_types=[EntityType.JOB, EntityType.CANDIDATE],
)

response = engine.search(request)

# Access results by entity type
job_results = response.get_entity_results(EntityType.JOB)
candidate_results = response.get_entity_results(EntityType.CANDIDATE)

# Get all results across all entities
all_results = response.get_all_results()

# Get searched entity types
searched_types = response.get_searched_entity_types()
```

### Convenience Methods

```python
# Search jobs and candidates
response = engine.search_jobs_and_candidates(
    query="software engineer",
    filters={"location": "San Francisco"}
)

# Search all entities
response = engine.search_all_entities(
    query="software engineer"
)
```

## Unified Search Response

```python
from apps.search.query_engine.unified_search import UnifiedSearchResponse

response = UnifiedSearchResponse(
    query="software engineer",
    entity_results={
        EntityType.JOB: EntitySearchResult(...),
        EntityType.CANDIDATE: EntitySearchResult(...),
    },
    total_results=150,
    took_ms=45,
    pagination={"page": 1, "page_size": 20},
    facets={},
    metadata={"provider": "elasticsearch"},
)

# Get results for specific entity type
job_results = response.get_entity_results(EntityType.JOB)

# Get count for specific entity type
job_count = response.get_entity_count(EntityType.JOB)

# Get all results
all_results = response.get_all_results()

# Get searched entity types
searched_types = response.get_searched_entity_types()
```

## Entity Search Result

```python
from apps.search.query_engine.unified_search import EntitySearchResult

result = EntitySearchResult(
    entity_type=EntityType.JOB,
    results=[...],
    total=100,
    took_ms=20,
    metadata={"provider": "elasticsearch"},
)
```

## Cross-Entity Pagination

Unified search supports pagination across multiple entities:

```python
request = UnifiedSearchRequest(
    query="software engineer",
    entity_types=[EntityType.JOB, EntityType.CANDIDATE],
    per_entity_limit=10,      # Max results per entity
    total_limit=50,           # Max total results across all entities
    pagination={"page": 1, "page_size": 20},
)
```

## Entity Grouping

Results are grouped by entity type:

```python
response = engine.search(request)

for entity_type, result in response.entity_results.items():
    print(f"{entity_type.value}: {result.total} results")
    for item in result.results:
        print(f"  {item['id']}")
```

## Unified Facets

Facets can be computed across all entity types:

```python
request = UnifiedSearchRequest(
    query="software engineer",
    entity_types=[EntityType.JOB, EntityType.CANDIDATE],
    include_facets=True,
    facet_configs=[
        {"field": "location", "name": "Location", "size": 20},
    ],
)

response = engine.search(request)

# Access facets
for facet_name, facet_data in response.facets.items():
    print(f"{facet_name}: {facet_data}")
```

## Use Cases

### Job and Candidate Search

Search for jobs and candidates simultaneously:

```python
request = UnifiedSearchRequest(
    query="python developer",
    entity_types=[EntityType.JOB, EntityType.CANDIDATE],
    filters={"location": "San Francisco"},
)

response = engine.search(request)

# Display jobs
jobs = response.get_entity_results(EntityType.JOB)
print(f"Found {jobs.total} jobs")

# Display candidates
candidates = response.get_entity_results(EntityType.CANDIDATE)
print(f"Found {candidates.total} candidates")
```

### Company and Recruiter Search

Search for companies and recruiters:

```python
request = UnifiedSearchRequest(
    query="technology",
    entity_types=[EntityType.COMPANY, EntityType.RECRUITER],
)

response = engine.search(request)
```

### Skill Search Across Entities

Search for skills across jobs, candidates, and resumes:

```python
request = UnifiedSearchRequest(
    query="python",
    entity_types=[EntityType.JOB, EntityType.CANDIDATE, EntityType.RESUME],
)

response = engine.search(request)
```

### Application and Interview Search

Search for applications and interviews:

```python
request = UnifiedSearchRequest(
    query="pending",
    entity_types=[EntityType.APPLICATION, EntityType.INTERVIEW],
)

response = engine.search(request)
```

## Performance Considerations

### Per-Entity Limits

Set appropriate per-entity limits to control resource usage:

```python
request = UnifiedSearchRequest(
    query="software engineer",
    entity_types=[EntityType.JOB, EntityType.CANDIDATE, EntityType.COMPANY],
    per_entity_limit=5,       # Only 5 results per entity
    total_limit=15,           # Max 15 total results
)
```

### Selective Entity Types

Only search relevant entity types:

```python
# Good: Only search 2 entity types
request = UnifiedSearchRequest(
    query="software engineer",
    entity_types=[EntityType.JOB, EntityType.CANDIDATE],
)

# Avoid: Search all entity types unless necessary
request = UnifiedSearchRequest(
    query="software engineer",
    entity_types=list(EntityType),  # All 8 entity types
)
```

## Provider Translation

Unified search is automatically translated to the provider's native search:

- **PostgreSQL**: Translated to multiple Django ORM queries
- **Elasticsearch**: Translated to multi-index search

No application code changes are needed when switching providers.

## Error Handling

```python
try:
    response = engine.search(request)
except ValueError as e:
    print(f"Invalid request: {e}")
except Exception as e:
    print(f"Search failed: {e}")
```

## Validation

Unified search requests are validated automatically:

```python
request = UnifiedSearchRequest(
    query="software engineer",
    entity_types=[EntityType.JOB, EntityType.CANDIDATE],
)

# Validation happens in __post_init__
# Raises ValueError if invalid
```

## Best Practices

1. **Use specific entity types**: Only search the entity types you need
2. **Set appropriate limits**: Use per_entity_limit and total_limit to control resource usage
3. **Leverage facets**: Use facets to provide filtering options across entities
4. **Cache results**: Use the query engine's cache for repeated searches
5. **Handle partial results**: Be prepared for some entity types to return no results
