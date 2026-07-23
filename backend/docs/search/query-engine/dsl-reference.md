# Query DSL Reference

## Overview

The Query DSL (Domain Specific Language) provides a provider-independent way to construct search queries. All query types can be translated to both PostgreSQL and Elasticsearch.

## Query Types

### MatchQuery

Full-text search on a single field.

```python
from apps.search.query_engine.dsl import MatchQuery

query = MatchQuery(
    field="title",
    query="software engineer",
    operator="and",              # Optional: "and" or "or"
    minimum_should_match=1,      # Optional
    fuzziness="AUTO",            # Optional
    boost=2.0                   # Optional
)
```

### MultiMatchQuery

Full-text search across multiple fields.

```python
from apps.search.query_engine.dsl import MultiMatchQuery, MatchType

query = MultiMatchQuery(
    query="software engineer",
    fields=["title", "description", "requirements"],
    type=MatchType.BEST_FIELDS,  # or MOST_FIELDS, CROSS_FIELDS, PHRASE
    tie_breaker=0.3,             # Optional
    boost=1.5                    # Optional
)
```

### PhraseQuery

Exact phrase matching.

```python
from apps.search.query_engine.dsl import PhraseQuery

query = PhraseQuery(
    field="title",
    query="software engineer",
    slop=2,                      # Optional: allowed word distance
    boost=1.5                    # Optional
)
```

### PrefixQuery

Prefix matching (useful for autocomplete).

```python
from apps.search.query_engine.dsl import PrefixQuery

query = PrefixQuery(
    field="title",
    value="soft",
    boost=1.0                    # Optional
)
```

### WildcardQuery

Pattern matching with `*` (any characters) and `?` (single character).

```python
from apps.search.query_engine.dsl import WildcardQuery

query = WildcardQuery(
    field="title",
    value="soft*",
    boost=1.0                    # Optional
)
```

### FuzzyQuery

Approximate matching for typos and spelling variations.

```python
from apps.search.query_engine.dsl import FuzzyQuery

query = FuzzyQuery(
    field="title",
    value="softwere",             # Typo
    fuzziness="AUTO",            # or "0", "1", "2"
    prefix_length=2,             # Optional
    max_expansions=50,           # Optional
    boost=1.0                    # Optional
)
```

### RangeQuery

Numeric and date range queries.

```python
from apps.search.query_engine.dsl import RangeQuery

query = RangeQuery(
    field="salary",
    gte=50000,                   # Greater than or equal
    lte=100000,                  # Less than or equal
    # Also supports: gt, lt
    format="yyyy-MM-dd",         # Optional for dates
    boost=1.0                    # Optional
)
```

### ExistsQuery

Match documents where a field exists.

```python
from apps.search.query_engine.dsl import ExistsQuery

query = ExistsQuery(
    field="company_name",
    boost=1.0                    # Optional
)
```

### TermQuery

Exact value matching.

```python
from apps.search.query_engine.dsl import TermQuery

query = TermQuery(
    field="status",
    value="active",
    boost=1.0                    # Optional
)
```

### TermsQuery

Match any of multiple values.

```python
from apps.search.query_engine.dsl import TermsQuery

query = TermsQuery(
    field="status",
    values=["active", "pending"],
    boost=1.0                    # Optional
)
```

### BoolQuery

Combine multiple queries with boolean logic.

```python
from apps.search.query_engine.dsl import BoolQuery, MatchQuery, RangeQuery

query = BoolQuery(
    must=[MatchQuery(field="title", query="software")],
    should=[MatchQuery(field="description", query="engineer")],
    must_not=[TermQuery(field="status", value="closed")],
    filter=[RangeQuery(field="salary", gte=50000)],
    minimum_should_match=1,      # Optional
    boost=1.0                    # Optional
)
```

### DisMaxQuery

Take the maximum score from multiple queries.

```python
from apps.search.query_engine.dsl import DisMaxQuery, MatchQuery

query = DisMaxQuery(
    queries=[
        MatchQuery(field="title", query="software"),
        MatchQuery(field="description", query="engineer"),
    ],
    tie_breaker=0.3,             # Optional
    boost=1.0                    # Optional
)
```

### FunctionScoreQuery

Custom scoring with functions.

```python
from apps.search.query_engine.dsl import (
    FunctionScoreQuery, MatchQuery,
    FieldValueFactorFunction, WeightFunction
)

base_query = MatchQuery(field="title", query="software")

query = FunctionScoreQuery(
    query=base_query,
    functions=[
        {"field_value_factor": {"field": "popularity", "factor": 1.5}},
        {"weight": 2.0, "filter": {"term": {"is_featured": True}}},
    ],
    score_mode="multiply",       # Optional: sum, avg, max, min
    boost_mode="multiply",      # Optional: replace, sum, avg, max, min
    max_boost=10.0,             # Optional
)
```

## Query Composition

### AND Composition

```python
query1 = MatchQuery(field="title", query="software")
query2 = MatchQuery(field="description", query="engineer")
combined = query1.and_(query2)
```

### OR Composition

```python
query1 = MatchQuery(field="title", query="software")
query2 = MatchQuery(field="description", query="engineer")
combined = query1.or_(query2)
```

### NOT Composition

```python
query = MatchQuery(field="title", query="software")
negated = query.not_()
```

## DSL Builder

The DSLBuilder provides a fluent interface for constructing queries.

```python
from apps.search.query_engine.dsl import DSLQueryBuilder

builder = DSLQueryBuilder()

# Simple match
query = builder.match(field="title", query="software engineer").build()

# Complex boolean query
query = (
    builder
    .bool()
    .must(MatchQuery(field="title", query="software"))
    .should(MatchQuery(field="description", query="engineer"))
    .filter(RangeQuery(field="salary", gte=50000))
    .build()
)
```

## Validation

All queries support validation:

```python
query = MatchQuery(field="title", query="software")
if query.validate():
    # Query is valid
    pass
```

## Serialization

All queries can be serialized to dictionaries:

```python
query = MatchQuery(field="title", query="software")
query_dict = query.to_dict()
```

## Provider Translation

The DSL is automatically translated to the provider's native query language:

- **PostgreSQL**: Translated to Django ORM queries with full-text search
- **Elasticsearch**: Translated to Elasticsearch Query DSL

No application code changes are needed when switching providers.
