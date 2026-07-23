# Query DSL Reference

This document provides a comprehensive reference for the MatchHire Query DSL, a provider-independent query language for expressing search requests.

## Table of Contents

- [Query Types](#query-types)
- [Query Composition](#query-composition)
- [Query Builder](#query-builder)
- [Validation](#validation)
- [Serialization](#serialization)

## Query Types

### MatchQuery

Full-text search for a single field.

```python
from apps.search.query_engine.dsl import MatchQuery

query = MatchQuery(
    field="title",
    query="software engineer",
    operator="and",              # Optional: "and" or "or"
    minimum_should_match="75%",   # Optional
    fuzziness="AUTO",            # Optional
    prefix_length=0,             # Optional
    max_expansions=50,           # Optional
    lenient=False,               # Optional
    zero_terms_query="none",     # Optional: "none" or "all"
    boost=1.0                    # Optional
)
```

**Parameters:**
- `field` (str): Field to search
- `query` (str): Query string
- `operator` (str, optional): Boolean operator for multi-term queries
- `minimum_should_match` (str, optional): Minimum terms that must match
- `fuzziness` (str, optional): Fuzziness for matching
- `prefix_length` (int, optional): Prefix length for fuzzy matching
- `max_expansions` (int, optional): Maximum expansions for fuzzy matching
- `lenient` (bool, optional): Ignore format-based errors
- `zero_terms_query` (ZeroTermsQuery, optional): Behavior when no terms match
- `boost` (float, optional): Query boost value

### MultiMatchQuery

Full-text search across multiple fields.

```python
from apps.search.query_engine.dsl import MultiMatchQuery, MatchType

query = MultiMatchQuery(
    query="software engineer",
    fields=["title", "description", "skills"],
    type=MatchType.BEST_FIELDS,    # Optional
    operator="and",                # Optional
    minimum_should_match="75%",     # Optional
    fuzziness="AUTO",              # Optional
    tie_breaker=0.3,               # Optional
    boost=1.0                      # Optional
)
```

**Parameters:**
- `query` (str): Query string
- `fields` (List[str]): Fields to search
- `type` (MatchType, optional): Multi-match type
  - `BEST_FIELDS`: Best score from any field
  - `MOST_FIELDS`: Most fields matching
  - `CROSS_FIELDS`: Cross-field scoring
  - `PHRASE`: Phrase matching
  - `PHRASE_PREFIX`: Phrase prefix matching
- `operator` (str, optional): Boolean operator
- `minimum_should_match` (str, optional): Minimum terms that must match
- `fuzziness` (str, optional): Fuzziness for matching
- `tie_breaker` (float, optional): Tie-breaking value
- `boost` (float, optional): Query boost value

### PhraseQuery

Exact phrase matching.

```python
from apps.search.query_engine.dsl import PhraseQuery

query = PhraseQuery(
    field="title",
    query="software engineer",
    slop=0,                       # Optional: phrase slop
    zero_terms_query="none",       # Optional
    boost=1.0                      # Optional
)
```

**Parameters:**
- `field` (str): Field to search
- `query` (str): Phrase to match
- `slop` (int, optional): Phrase slop (allowed transpositions)
- `zero_terms_query` (ZeroTermsQuery, optional): Behavior when no terms match
- `boost` (float, optional): Query boost value

### PrefixQuery

Prefix matching for a field.

```python
from apps.search.query_engine.dsl import PrefixQuery

query = PrefixQuery(
    field="title",
    value="soft",
    rewrite="constant_score",      # Optional
    boost=1.0                      # Optional
)
```

**Parameters:**
- `field` (str): Field to search
- `value` (str): Prefix value
- `rewrite` (str, optional): Rewrite method
- `boost` (float, optional): Query boost value

### WildcardQuery

Wildcard pattern matching.

```python
from apps.search.query_engine.dsl import WildcardQuery

query = WildcardQuery(
    field="title",
    value="soft*",
    rewrite="constant_score",      # Optional
    boost=1.0                      # Optional
)
```

**Parameters:**
- `field` (str): Field to search
- `value` (str): Wildcard pattern (* matches any, ? matches single)
- `rewrite` (str, optional): Rewrite method
- `boost` (float, optional): Query boost value

### FuzzyQuery

Fuzzy matching for typos.

```python
from apps.search.query_engine.dsl import FuzzyQuery

query = FuzzyQuery(
    field="title",
    value="pyton",
    fuzziness="AUTO",              # Optional
    prefix_length=0,               # Optional
    max_expansions=50,             # Optional
    transpositions=True,           # Optional
    rewrite="constant_score",      # Optional
    boost=1.0                      # Optional
)
```

**Parameters:**
- `field` (str): Field to search
- `value` (str): Value to match fuzzily
- `fuzziness` (str, optional): Fuzziness level
- `prefix_length` (int, optional): Prefix length
- `max_expansions` (int, optional): Maximum expansions
- `transpositions` (bool, optional): Allow transpositions
- `rewrite` (str, optional): Rewrite method
- `boost` (float, optional): Query boost value

### RangeQuery

Range matching for numeric/date fields.

```python
from apps.search.query_engine.dsl import RangeQuery

query = RangeQuery(
    field="salary",
    gte=50000,                     # Optional: greater than or equal
    gt=40000,                      # Optional: greater than
    lte=100000,                    # Optional: less than or equal
    lt=110000,                     # Optional: less than
    format="yyyy-MM-dd",           # Optional: date format
    boost=1.0                      # Optional
)
```

**Parameters:**
- `field` (str): Field to search
- `gte` (Any, optional): Greater than or equal
- `gt` (Any, optional): Greater than
- `lte` (Any, optional): Less than or equal
- `lt` (Any, optional): Less than
- `format` (str, optional): Date format for date fields
- `boost` (float, optional): Query boost value

### ExistsQuery

Check if a field exists.

```python
from apps.search.query_engine.dsl import ExistsQuery

query = ExistsQuery(
    field="skills",
    boost=1.0                      # Optional
)
```

**Parameters:**
- `field` (str): Field to check
- `boost` (float, optional): Query boost value

### TermQuery

Exact term matching.

```python
from apps.search.query_engine.dsl import TermQuery

query = TermQuery(
    field="status",
    value="active",
    boost=1.0                      # Optional
)
```

**Parameters:**
- `field` (str): Field to search
- `value` (Any): Exact value to match
- `boost` (float, optional): Query boost value

### TermsQuery

Multiple exact term matching (IN clause).

```python
from apps.search.query_engine.dsl import TermsQuery

query = TermsQuery(
    field="status",
    values=["active", "pending"],
    boost=1.0                      # Optional
)
```

**Parameters:**
- `field` (str): Field to search
- `values` (List[Any]): Values to match
- `boost` (float, optional): Query boost value

### NestedQuery

Search within nested objects.

```python
from apps.search.query_engine.dsl import NestedQuery, MatchQuery

query = NestedQuery(
    path="skills",
    query=MatchQuery(field="skills.name", query="python"),
    score_mode="avg",              # Optional: "avg", "sum", "max", "none"
    ignore_unmapped=False,         # Optional
    boost=1.0                      # Optional
)
```

**Parameters:**
- `path` (str): Nested object path
- `query` (Query): Query to execute within nested object
- `score_mode` (str, optional): Score mode for nested matches
- `ignore_unmapped` (bool, optional): Ignore unmapped nested fields
- `boost` (float, optional): Query boost value

### BoolQuery

Boolean combination of queries.

```python
from apps.search.query_engine.dsl import BoolQuery, MatchQuery

query = BoolQuery(
    must=[MatchQuery(field="title", query="software")],      # Optional
    should=[MatchQuery(field="description", query="engineer")],  # Optional
    must_not=[MatchQuery(field="status", query="closed")],   # Optional
    filter=[MatchQuery(field="active", query="true")],       # Optional
    minimum_should_match=1,          # Optional
    boost=1.0                        # Optional
)
```

**Parameters:**
- `must` (List[Query], optional): Queries that must match
- `should` (List[Query], optional): Queries that should match
- `must_not` (List[Query], optional): Queries that must not match
- `filter` (List[Query], optional): Filter queries (no scoring)
- `minimum_should_match` (int, optional): Minimum should clauses to match
- `boost` (float, optional): Query boost value

### DisMaxQuery

Disjunction max query (best score from multiple queries).

```python
from apps.search.query_engine.dsl import DisMaxQuery, MatchQuery

query = DisMaxQuery(
    queries=[
        MatchQuery(field="title", query="software"),
        MatchQuery(field="description", query="engineer")
    ],
    tie_breaker=0.3,               # Optional
    boost=1.0                      # Optional
)
```

**Parameters:**
- `queries` (List[Query]): Queries to combine
- `tie_breaker` (float, optional): Tie-breaking value
- `boost` (float, optional): Query boost value

### FunctionScoreQuery

Custom scoring with functions.

```python
from apps.search.query_engine.dsl import (
    FunctionScoreQuery,
    MatchQuery,
    WeightFunction,
    FieldValueFactorFunction,
    DecayFunction
)

query = FunctionScoreQuery(
    query=MatchQuery(field="title", query="software"),
    functions=[
        WeightFunction(weight=2.0),
        FieldValueFactorFunction(field="popularity", factor=1.0),
        DecayFunction(field="created_at", decay=0.5, scale="30d")
    ],
    score_mode="multiply",          # Optional: "multiply", "sum", "avg", "max", "min"
    boost_mode="replace",           # Optional: "multiply", "replace", "sum", "avg", "max", "min"
    max_boost=10.0,                 # Optional
    min_score=0.5,                  # Optional
    boost=1.0                       # Optional
)
```

**Parameters:**
- `query` (Query, optional): Base query
- `functions` (List[ScoreFunction]): Score functions
- `score_mode` (str, optional): Score combination mode
- `boost_mode` (str, optional): Boost combination mode
- `max_boost` (float, optional): Maximum boost value
- `min_score` (float, optional): Minimum score threshold
- `boost` (float, optional): Query boost value

## Query Composition

### AND Composition

```python
from apps.search.query_engine.dsl import MatchQuery

query1 = MatchQuery(field="title", query="software")
query2 = MatchQuery(field="description", query="engineer")
combined = query1.and_(query2)
```

### OR Composition

```python
from apps.search.query_engine.dsl import MatchQuery

query1 = MatchQuery(field="title", query="software")
query2 = MatchQuery(field="description", query="engineer")
combined = query1.or_(query2)
```

### NOT Composition

```python
from apps.search.query_engine.dsl import MatchQuery

query = MatchQuery(field="title", query="software")
negated = query.not_()
```

## Query Builder

The `DSLQueryBuilder` provides a fluent interface for constructing queries.

```python
from apps.search.query_engine.dsl import DSLQueryBuilder, MatchType

builder = DSLQueryBuilder()

# Match query
query = builder.match(field="title", query="software engineer").build()

# Multi-match query
query = builder.multi_match(
    query="software engineer",
    fields=["title", "description"],
    type=MatchType.BEST_FIELDS
).build()

# Bool query
query = builder.bool()
query = builder.must(MatchQuery(field="title", query="software"))
query = builder.should(MatchQuery(field="description", query="engineer"))
query = builder.build()

# Reset builder
builder.reset()
```

### Builder Methods

- `match(field, query, **kwargs)`: Add match query
- `multi_match(query, fields, **kwargs)`: Add multi-match query
- `phrase(field, query, **kwargs)`: Add phrase query
- `prefix(field, value, **kwargs)`: Add prefix query
- `wildcard(field, value, **kwargs)`: Add wildcard query
- `fuzzy(field, value, **kwargs)`: Add fuzzy query
- `range(field, **kwargs)`: Add range query
- `exists(field, **kwargs)`: Add exists query
- `term(field, value, **kwargs)`: Add term query
- `terms(field, values, **kwargs)`: Add terms query
- `bool()`: Start bool query
- `must(query)`: Add must clause to bool query
- `should(query)`: Add should clause to bool query
- `must_not(query)`: Add must_not clause to bool query
- `filter(query)`: Add filter clause to bool query
- `dis_max(queries, **kwargs)`: Add dis_max query
- `function_score(query, functions, **kwargs)`: Add function_score query
- `build()`: Build and return the query
- `reset()`: Reset the builder

## Validation

All query types support validation:

```python
query = MatchQuery(field="title", query="software engineer")
is_valid = query.validate()
```

Validation checks:
- Required fields are present
- Field names are non-empty
- Query strings are non-empty
- Range queries have at least one bound
- Bool queries with clauses have valid sub-queries

## Serialization

All query types support serialization to dictionary:

```python
query = MatchQuery(field="title", query="software engineer")
query_dict = query.to_dict()
```

Output format:
```python
{
    "type": "match",
    "field": "title",
    "query": "software engineer",
    "operator": null,
    "minimum_should_match": null,
    ...
}
```

## Examples

### Simple Full-Text Search

```python
from apps.search.query_engine.dsl import MatchQuery

query = MatchQuery(field="title", query="software engineer")
```

### Multi-Field Search

```python
from apps.search.query_engine.dsl import MultiMatchQuery, MatchType

query = MultiMatchQuery(
    query="software engineer",
    fields=["title", "description", "skills"],
    type=MatchType.BEST_FIELDS
)
```

### Boolean Query

```python
from apps.search.query_engine.dsl import BoolQuery, MatchQuery, RangeQuery

query = BoolQuery(
    must=[
        MatchQuery(field="title", query="software"),
        RangeQuery(field="salary", gte=50000, lte=100000)
    ],
    must_not=[
        MatchQuery(field="status", query="closed")
    ]
)
```

### Phrase Search

```python
from apps.search.query_engine.dsl import PhraseQuery

query = PhraseQuery(field="title", query="senior software engineer")
```

### Fuzzy Search

```python
from apps.search.query_engine.dsl import FuzzyQuery

query = FuzzyQuery(field="title", value="pyton", fuzziness="AUTO")
```

### Custom Scoring

```python
from apps.search.query_engine.dsl import (
    FunctionScoreQuery,
    MatchQuery,
    FieldValueFactorFunction,
    DecayFunction
)

query = FunctionScoreQuery(
    query=MatchQuery(field="title", query="software"),
    functions=[
        FieldValueFactorFunction(field="popularity", factor=1.5),
        DecayFunction(field="created_at", decay=0.5, scale="30d")
    ]
)
```

### Nested Query

```python
from apps.search.query_engine.dsl import NestedQuery, MatchQuery

query = NestedQuery(
    path="skills",
    query=MatchQuery(field="skills.name", query="python")
)
```
