# Aggregation Guide

This guide provides comprehensive documentation for the MatchHire Aggregation system, which enables provider-independent aggregations for metrics and bucketing.

## Table of Contents

- [Aggregation Basics](#aggregation-basics)
- [Aggregation Types](#aggregation-types)
- [Bucket Aggregations](#bucket-aggregations)
- [Metric Aggregations](#metric-aggregations)
- [Nested Aggregations](#nested-aggregations)
- [Aggregation Builder](#aggregation-builder)
- [Predefined Aggregations](#predefined-aggregations)
- [Examples](#examples)

## Aggregation Basics

### Creating a Simple Aggregation

```python
from apps.search.query_engine.aggregations import TermsAggregation

agg = TermsAggregation(
    name="location_agg",
    field="location",
    size=10
)
```

### Aggregation Parameters

- `name` (str): Unique name for the aggregation
- `field` (str): Field to aggregate on
- Additional parameters specific to aggregation type

## Aggregation Types

### Bucket Aggregations

Bucket aggregations group documents into buckets based on criteria.

#### Terms Aggregation

Group documents by unique field values.

```python
from apps.search.query_engine.aggregations import TermsAggregation

agg = TermsAggregation(
    name="location_agg",
    field="location",
    size=10,                      # Optional: number of buckets
    min_doc_count=1,              # Optional: minimum documents per bucket
    order={"_count": "desc"},     # Optional: sort order
    missing="unknown"              # Optional: value for missing fields
)
```

**Parameters:**
- `size` (int, optional): Number of buckets to return
- `min_doc_count` (int, optional): Minimum documents per bucket
- `order` (Dict[str, str], optional): Sort order for buckets
- `missing` (Any, optional): Value for documents missing the field

#### Range Aggregation

Group documents into custom ranges.

```python
from apps.search.query_engine.aggregations import RangeAggregation, RangeBucket

agg = RangeAggregation(
    name="salary_agg",
    field="salary",
    ranges=[
        RangeBucket(key="0-50k", from_=0, to=50000),
        RangeBucket(key="50k-100k", from_=50000, to=100000),
        RangeBucket(key="100k+", from_=100000)
    ]
)
```

**Parameters:**
- `ranges` (List[RangeBucket]): Range buckets

**RangeBucket Parameters:**
- `key` (str): Bucket key
- `from_` (Any, optional): Start value (inclusive)
- `to` (Any, optional): End value (exclusive)

#### Histogram Aggregation

Group documents into numeric intervals.

```python
from apps.search.query_engine.aggregations import HistogramAggregation

agg = HistogramAggregation(
    name="salary_histogram",
    field="salary",
    interval=10000,                # Interval size
    min_doc_count=1,               # Optional: minimum documents per bucket
    missing=0                      # Optional: value for missing fields
)
```

**Parameters:**
- `interval` (int): Interval size
- `min_doc_count` (int, optional): Minimum documents per bucket
- `missing` (Any, optional): Value for documents missing the field

#### Date Histogram Aggregation

Group documents into time intervals.

```python
from apps.search.query_engine.aggregations import DateHistogramAggregation, HistogramInterval

agg = DateHistogramAggregation(
    name="created_at_histogram",
    field="created_at",
    interval=HistogramInterval.DAY,  # Interval type
    min_doc_count=1,                  # Optional: minimum documents per bucket
    format="yyyy-MM-dd"               # Optional: date format
)
```

**Parameters:**
- `interval` (HistogramInterval): Time interval
  - `SECOND`, `MINUTE`, `HOUR`, `DAY`, `WEEK`, `MONTH`, `QUARTER`, `YEAR`
- `min_doc_count` (int, optional): Minimum documents per bucket
- `format` (str, optional): Date format for bucket keys

### Metric Aggregations

Metric aggregations calculate statistics over document fields.

#### Count Aggregation

Count documents (optionally with a field).

```python
from apps.search.query_engine.aggregations import CountAggregation

agg = CountAggregation(
    name="total_count",
    field=None  # None for document count, or field name for value count
)
```

#### Stats Aggregation

Basic statistics (count, min, max, avg, sum).

```python
from apps.search.query_engine.aggregations import StatsAggregation

agg = StatsAggregation(
    name="salary_stats",
    field="salary"
)
```

**Result Fields:**
- `count`: Number of documents
- `min`: Minimum value
- `max`: Maximum value
- `avg`: Average value
- `sum`: Sum of values

#### Average Aggregation

Calculate average value.

```python
from apps.search.query_engine.aggregations import AverageAggregation

agg = AverageAggregation(
    name="avg_salary",
    field="salary"
)
```

#### Min/Max Aggregation

Calculate minimum or maximum value.

```python
from apps.search.query_engine.aggregations import MinAggregation, MaxAggregation

min_agg = MinAggregation(
    name="min_salary",
    field="salary"
)

max_agg = MaxAggregation(
    name="max_salary",
    field="salary"
)
```

#### Sum Aggregation

Calculate sum of values.

```python
from apps.search.query_engine.aggregations import SumAggregation

agg = SumAggregation(
    name="total_applications",
    field="application_count"
)
```

#### Percentiles Aggregation

Calculate percentiles.

```python
from apps.search.query_engine.aggregations import PercentilesAggregation

agg = PercentilesAggregation(
    name="salary_percentiles",
    field="salary",
    percents=[1.0, 5.0, 25.0, 50.0, 75.0, 95.0, 99.0]  # Optional
)
```

**Parameters:**
- `percents` (List[float], optional): Percentiles to calculate

#### Cardinality Aggregation

Count unique values.

```python
from apps.search.query_engine.aggregations import CardinalityAggregation

agg = CardinalityAggregation(
    name="unique_locations",
    field="location"
)
```

## Nested Aggregations

Aggregations can be nested to compute sub-aggregations within buckets.

```python
from apps.search.query_engine.aggregations import (
    AggregationBuilder,
    TermsAggregation,
    StatsAggregation
)

builder = AggregationBuilder()

# Location aggregation with nested salary stats
builder.add_aggregation(
    TermsAggregation(name="by_location", field="location", size=10)
)
builder.add_sub_aggregation(
    "by_location",
    StatsAggregation(name="salary_stats", field="salary")
)

aggregations = builder.build()
```

## Aggregation Builder

The `AggregationBuilder` provides a fluent interface for constructing aggregations.

```python
from apps.search.query_engine.aggregations import AggregationBuilder

builder = AggregationBuilder()

# Add aggregation
builder.add_aggregation(TermsAggregation(name="by_location", field="location"))

# Add sub-aggregation
builder.add_sub_aggregation(
    "by_location",
    StatsAggregation(name="salary_stats", field="salary")
)

# Build aggregations
aggregations = builder.build()
```

### Builder Methods

- `add_aggregation(aggregation)`: Add a top-level aggregation
- `add_sub_aggregation(parent_name, aggregation)`: Add a sub-aggregation
- `terms(name, field, **kwargs)`: Add terms aggregation
- `range(name, field, ranges, **kwargs)`: Add range aggregation
- `histogram(name, field, interval, **kwargs)`: Add histogram aggregation
- `date_histogram(name, field, interval, **kwargs)`: Add date histogram aggregation
- `stats(name, field)`: Add stats aggregation
- `avg(name, field)`: Add average aggregation
- `min(name, field)`: Add min aggregation
- `max(name, field)`: Add max aggregation
- `sum(name, field)`: Add sum aggregation
- `percentiles(name, field, **kwargs)`: Add percentiles aggregation
- `cardinality(name, field)`: Add cardinality aggregation
- `build()`: Build and return aggregations
- `reset()`: Reset the builder

## Predefined Aggregations

### Job Search Aggregations

```python
from apps.search.query_engine.aggregations import PredefinedAggregations

aggregations = PredefinedAggregations.job_search_aggregations()
```

Includes:
- Location terms aggregation
- Company terms aggregation
- Employment type terms aggregation
- Experience level terms aggregation
- Salary range aggregation
- Industry terms aggregation

### Candidate Search Aggregations

```python
from apps.search.query_engine.aggregations import PredefinedAggregations

aggregations = PredefinedAggregations.candidate_search_aggregations()
```

Includes:
- Location terms aggregation
- Skills terms aggregation (nested)
- Experience level terms aggregation
- Education level terms aggregation
- Salary range aggregation

### Company Search Aggregations

```python
from apps.search.query_engine.aggregations import PredefinedAggregations

aggregations = PredefinedAggregations.company_search_aggregations()
```

Includes:
- Industry terms aggregation
- Company size terms aggregation
- Location terms aggregation
- Employee count range aggregation

## Examples

### Simple Terms Aggregation

```python
from apps.search.query_engine.aggregations import TermsAggregation

agg = TermsAggregation(
    name="by_location",
    field="location",
    size=10
)
```

### Salary Range Aggregation

```python
from apps.search.query_engine.aggregations import RangeAggregation, RangeBucket

agg = RangeAggregation(
    name="salary_ranges",
    field="salary",
    ranges=[
        RangeBucket(key="0-50k", from_=0, to=50000),
        RangeBucket(key="50k-100k", from_=50000, to=100000),
        RangeBucket(key="100k-150k", from_=100000, to=150000),
        RangeBucket(key="150k+", from_=150000)
    ]
)
```

### Date Histogram Aggregation

```python
from apps.search.query_engine.aggregations import DateHistogramAggregation, HistogramInterval

agg = DateHistogramAggregation(
    name="jobs_by_month",
    field="created_at",
    interval=HistogramInterval.MONTH
)
```

### Stats Aggregation

```python
from apps.search.query_engine.aggregations import StatsAggregation

agg = StatsAggregation(
    name="salary_statistics",
    field="salary"
)
```

### Nested Aggregations

```python
from apps.search.query_engine.aggregations import AggregationBuilder

builder = AggregationBuilder()

# Location with nested salary stats
builder.terms(name="by_location", field="location", size=10)
builder.add_sub_aggregation(
    "by_location",
    StatsAggregation(name="salary_stats", field="salary")
)

aggregations = builder.build()
```

### Multiple Aggregations

```python
from apps.search.query_engine.aggregations import AggregationBuilder

builder = AggregationBuilder()

builder.terms(name="by_location", field="location", size=10)
builder.stats(name="salary_stats", field="salary")
builder.cardinality(name="unique_companies", field="company_id")

aggregations = builder.build()
```

### Using Predefined Aggregations

```python
from apps.search.query_engine.aggregations import PredefinedAggregations, AggregationBuilder

# Start with predefined aggregations
builder = AggregationBuilder()
predefined = PredefinedAggregations.job_search_aggregations()

for agg in predefined:
    builder.add_aggregation(agg)

# Add custom aggregation
builder.avg(name="avg_views", field="view_count")

aggregations = builder.build()
```

### Aggregation with Validation

```python
from apps.search.query_engine.aggregations import TermsAggregation

agg = TermsAggregation(
    name="by_location",
    field="location",
    size=10
)

is_valid = agg.validate()
```

### Aggregation Serialization

```python
from apps.search.query_engine.aggregations import TermsAggregation

agg = TermsAggregation(
    name="by_location",
    field="location",
    size=10
)

agg_dict = agg.to_dict()
# Output: {"name": "by_location", "type": "terms", "field": "location", "size": 10}
```

## Best Practices

1. **Limit Bucket Size**: Use reasonable `size` values to avoid excessive memory usage
2. **Use Min Doc Count**: Set `min_doc_count` to filter out noisy buckets
3. **Nest Carefully**: Deep nesting can impact performance
4. **Use Predefined Aggregations**: Leverage predefined aggregations for common patterns
5. **Consider Cardinality**: Cardinality aggregations are approximate for large datasets
6. **Index Appropriately**: Ensure aggregated fields are properly indexed
7. **Monitor Performance**: Aggregations can be expensive on large datasets

## Performance Considerations

1. **Bucket Size**: Larger bucket sizes require more memory and computation
2. **Nesting Depth**: Deep nesting increases complexity exponentially
3. **Field Cardinality**: High cardinality fields (e.g., unique IDs) are poor candidates for terms aggregations
4. **Date Histograms**: Use appropriate intervals for your data volume
5. **Scripted Aggregations**: Avoid scripted aggregations when possible
6. **Caching**: Aggregation results can be cached for identical queries
