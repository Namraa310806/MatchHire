# Aggregation Guide

## Overview

The Aggregation framework provides provider-independent aggregations for computing statistics, metrics, and bucketed data from search results.

## Aggregation Types

### CountAggregation

Count documents (with or without a field).

```python
from apps.search.query_engine.aggregations import CountAggregation

# Document count
agg = CountAggregation(name="doc_count")

# Field count
agg = CountAggregation(name="field_count", field="status")
```

### TermsAggregation

Bucket by unique field values.

```python
from apps.search.query_engine.aggregations import TermsAggregation

agg = TermsAggregation(
    name="by_status",
    field="status",
    size=20,                      # Number of buckets
    order="count",                 # Sort by count or _key
    min_doc_count=1,              # Minimum documents per bucket
    missing="unknown",             # Value for missing fields
)
```

### RangeAggregation

Bucket by numeric ranges.

```python
from apps.search.query_engine.aggregations import RangeAggregation, RangeBucket

ranges = [
    RangeBucket(key="low", from_value=0, to_value=50000),
    RangeBucket(key="medium", from_value=50000, to_value=100000),
    RangeBucket(key="high", from_value=100000, to_value=None),
]

agg = RangeAggregation(
    name="salary_ranges",
    field="salary",
    ranges=ranges,
    keyed=False,                   # Return as dictionary
)
```

### HistogramAggregation

Bucket by numeric intervals.

```python
from apps.search.query_engine.aggregations import HistogramAggregation

agg = HistogramAggregation(
    name="experience_hist",
    field="years_of_experience",
    interval=1.0,                 # Interval size
    min_doc_count=1,              # Minimum documents per bucket
    offset=0,                     # Starting offset
    missing=0,                    # Value for missing fields
)
```

### DateHistogramAggregation

Bucket by time intervals.

```python
from apps.search.query_engine.aggregations import DateHistogramAggregation, HistogramInterval

agg = DateHistogramAggregation(
    name="posted_over_time",
    field="posted_date",
    interval=HistogramInterval.MONTH,  # Or "1d", "1w", "1M", "1y"
    format="yyyy-MM-dd",          # Date format
    min_doc_count=1,
    time_zone="UTC",
)
```

### StatsAggregation

Compute basic statistics (count, sum, avg, min, max).

```python
from apps.search.query_engine.aggregations import StatsAggregation

agg = StatsAggregation(
    name="salary_stats",
    field="salary",
)
```

### AverageAggregation

Compute the mean value.

```python
from apps.search.query_engine.aggregations import AverageAggregation

agg = AverageAggregation(
    name="avg_salary",
    field="salary",
    missing=0,                    # Value for missing fields
)
```

### MinAggregation

Compute the minimum value.

```python
from apps.search.query_engine.aggregations import MinAggregation

agg = MinAggregation(
    name="min_salary",
    field="salary",
)
```

### MaxAggregation

Compute the maximum value.

```python
from apps.search.query_engine.aggregations import MaxAggregation

agg = MaxAggregation(
    name="max_salary",
    field="salary",
)
```

### SumAggregation

Compute the sum of values.

```python
from apps.search.query_engine.aggregations import SumAggregation

agg = SumAggregation(
    name="total_applications",
    field="application_count",
)
```

### PercentilesAggregation

Compute percentile values.

```python
from apps.search.query_engine.aggregations import PercentilesAggregation

agg = PercentilesAggregation(
    name="salary_percentiles",
    field="salary",
    percents=[1.0, 5.0, 25.0, 50.0, 75.0, 95.0, 99.0],
    missing=0,
)
```

### CardinalityAggregation

Count unique values.

```python
from apps.search.query_engine.aggregations import CardinalityAggregation

agg = CardinalityAggregation(
    name="unique_companies",
    field="company_id",
    precision_threshold=4000,     # Trade-off memory vs accuracy
)
```

## AggregationBuilder

The AggregationBuilder provides a fluent interface for constructing aggregations.

```python
from apps.search.query_engine.aggregations import AggregationBuilder

builder = AggregationBuilder()

# Single aggregation
aggs = builder.count(name="doc_count").build()

# Multiple aggregations
aggs = (
    builder
    .count(name="doc_count")
    .terms(name="by_status", field="status", size=20)
    .stats(name="salary_stats", field="salary")
    .build()
)
```

## Predefined Aggregations

### Job Salary Stats

```python
from apps.search.query_engine.aggregations import PredefinedAggregations

aggs = PredefinedAggregations.job_salary_stats()
# Returns: salary_stats, avg_salary, min_salary, max_salary
```

### Job Location Distribution

```python
aggs = PredefinedAggregations.job_location_distribution()
# Returns: by_location (terms aggregation)
```

### Job Posting Timeline

```python
aggs = PredefinedAggregations.job_posting_timeline(interval="1M")
# Returns: posted_over_time (date histogram)
```

### Candidate Experience Stats

```python
aggs = PredefinedAggregations.candidate_experience_stats()
# Returns: experience_stats, avg_experience, experience_distribution
```

### Skill Popularity

```python
aggs = PredefinedAggregations.skill_popularity()
# Returns: skill_ranking (terms aggregation)
```

### Application Status Breakdown

```python
aggs = PredefinedAggregations.application_status_breakdown()
# Returns: by_status, by_stage
```

### Company Size Distribution

```python
aggs = PredefinedAggregations.company_size_distribution()
# Returns: by_size
```

## Nested Aggregations

Aggregations can be nested within bucket aggregations:

```python
from apps.search.query_engine.aggregations import AggregationBuilder

builder = AggregationBuilder()

# This would be implemented in the provider-specific translation
# Example: Terms aggregation with nested stats aggregation
```

## Aggregation Results

### Bucket Results

```python
from apps.search.query_engine.aggregations import Bucket

buckets = [
    Bucket(
        key="active",
        doc_count=100,
        aggregations={
            "avg_salary": AggregationResult(name="avg_salary", value=75000)
        }
    )
]
```

### Stats Results

```python
from apps.search.query_engine.aggregations import StatsResult

stats = StatsResult(
    count=100,
    sum=7500000,
    avg=75000,
    min=50000,
    max=100000
)
```

## Validation

All aggregations support validation:

```python
agg = TermsAggregation(name="by_status", field="status")
if agg.validate():
    # Aggregation is valid
    pass
```

## Serialization

All aggregations can be serialized to dictionaries:

```python
agg = TermsAggregation(name="by_status", field="status")
agg_dict = agg.to_dict()
```

## Provider Translation

Aggregations are automatically translated to the provider's native aggregation language:

- **PostgreSQL**: Translated to Django ORM aggregations
- **Elasticsearch**: Translated to Elasticsearch aggregation DSL

No application code changes are needed when switching providers.
