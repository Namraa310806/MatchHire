# Autocomplete Guide

## Overview

The Autocomplete system provides intelligent autocomplete with suggestions, popular queries, prefix completion, field-specific autocomplete, entity-aware suggestions, deduplication, and ranking.

## Autocomplete Request

```python
from apps.search.query_engine.autocomplete import AutocompleteRequest, AutocompleteContext

context = AutocompleteContext(
    user_id="123",
    entity_type="job",
    filters={"location": "San Francisco"},
    recent_queries=["software engineer", "data scientist"],
    location="San Francisco",
    industry="Technology",
)

request = AutocompleteRequest(
    prefix="soft",
    field="title",
    entity_type="job",
    context=context,
    limit=10,
    fuzzy=True,
    include_popular=True,
    include_recent=True,
    min_score=0.0,
)
```

## Autocomplete Engine

### Basic Usage

```python
from apps.search.query_engine.autocomplete import AutocompleteEngine, AutocompleteRequest

engine = AutocompleteEngine()
request = AutocompleteRequest(
    prefix="soft",
    field="title",
    entity_type="job",
    limit=10,
)

response = engine.generate_suggestions(request)

for suggestion in response.suggestions:
    print(f"{suggestion.value} (score: {suggestion.score})")
```

### Managing Popular Queries

```python
# Add popular query
engine.add_popular_query("software engineer", weight=1.0)

# Decay popularity over time
engine.decay_popular_queries(factor=0.95)
```

### Managing Recent Searches

```python
# Add recent search for a user
engine.add_recent_search(user_id="123", query="software engineer")

# Clean up old searches
engine.cleanup_old_searches(days=30)
```

### Managing Entity Suggestions

```python
# Add entity-specific suggestions
engine.add_entity_suggestions(
    entity_type="job",
    suggestions=["Software Engineer", "Senior Developer", "Tech Lead"]
)
```

## Autocomplete Response

```python
from apps.search.query_engine.autocomplete import AutocompleteResponse

response = AutocompleteResponse(
    suggestions=[...],
    took_ms=15,
    prefix="soft",
    field="title",
    entity_type="job",
)

# Deduplicate suggestions
response.deduplicate()

# Sort by score
response.sort_by_score()

# Limit to top N
response.limit_to(5)

# Filter by minimum score
response.filter_by_score(min_score=0.5)
```

## Suggestion Types

### Prefix Suggestions

Suggestions based on prefix matching from the entity index.

```python
suggestions = engine.get_prefix_suggestions(
    prefix="soft",
    field="title",
    entity_type="job",
    limit=10,
)
```

### Fuzzy Suggestions

Suggestions with approximate matching for typos.

```python
suggestions = engine.get_fuzzy_suggestions(
    prefix="softwere",  # Typo
    field="title",
    entity_type="job",
    limit=5,
)
```

### Popular Suggestions

Suggestions based on query popularity.

```python
suggestions = engine.get_popular_suggestions(
    prefix="soft",
    limit=5,
)
```

### Recent Suggestions

Suggestions based on user's recent searches.

```python
suggestions = engine.get_recent_suggestions(
    prefix="soft",
    user_id="123",
    limit=5,
)
```

### Entity Suggestions

Suggestions from entity-specific index.

```python
suggestions = engine.get_entity_suggestions(
    prefix="soft",
    entity_type="job",
    limit=10,
)
```

## Autocomplete Suggestion

```python
from apps.search.query_engine.autocomplete import AutocompleteSuggestion, AutocompleteType, SuggestionSource

suggestion = AutocompleteSuggestion(
    value="Software Engineer",
    score=0.9,
    type=AutocompleteType.PREFIX,
    source=SuggestionSource.INDEX,
    field="title",
    entity_type="job",
    metadata={"count": 100},
)
```

## Field-Specific Autocomplete

### Title Autocomplete

```python
request = AutocompleteRequest(
    prefix="soft",
    field="title",
    entity_type="job",
    limit=10,
)
```

### Company Name Autocomplete

```python
request = AutocompleteRequest(
    prefix="goog",
    field="company_name",
    entity_type="job",
    limit=10,
)
```

### Skills Autocomplete

```python
request = AutocompleteRequest(
    prefix="pyth",
    field="name",
    entity_type="skill",
    limit=10,
)
```

## Entity-Aware Autocomplete

Autocomplete can be context-aware based on entity type:

```python
# Job autocomplete
request = AutocompleteRequest(
    prefix="soft",
    field="title",
    entity_type="job",
    context=AutocompleteContext(entity_type="job"),
)

# Candidate autocomplete
request = AutocompleteRequest(
    prefix="pyth",
    field="name",
    entity_type="skill",
    context=AutocompleteContext(entity_type="candidate"),
)
```

## Deduplication

The autocomplete engine automatically deduplicates suggestions:

```python
response = engine.generate_suggestions(request)
response.deduplicate()  # Remove duplicate values
```

## Ranking

Suggestions are ranked by score:

```python
response = engine.generate_suggestions(request)
response.sort_by_score()  # Sort by score (descending)
```

## Context-Aware Suggestions

Autocomplete can use context to improve suggestions:

```python
context = AutocompleteContext(
    user_id="123",
    entity_type="job",
    location="San Francisco",
    industry="Technology",
    recent_queries=["software engineer", "data scientist"],
)

request = AutocompleteRequest(
    prefix="soft",
    field="title",
    entity_type="job",
    context=context,
)
```

## Performance

### Cleanup

Clean up old data periodically:

```python
# Clean up old recent searches
engine.cleanup_old_searches(days=30)

# Decay popular queries
engine.decay_popular_queries(factor=0.95)
```

### Caching

Autocomplete results can be cached for performance:

```python
# The query engine's cache will cache autocomplete results
# based on the request parameters
```

## Validation

Autocomplete requests are validated automatically:

```python
request = AutocompleteRequest(
    prefix="soft",
    field="title",
    entity_type="job",
    limit=10,
)

# Validation happens in __post_init__
# Raises ValueError if invalid
```

## Provider Translation

Autocomplete is automatically translated to the provider's native autocomplete:

- **PostgreSQL**: Translated to Django ORM icontains queries
- **Elasticsearch**: Translated to Elasticsearch completion suggesters

No application code changes are needed when switching providers.
