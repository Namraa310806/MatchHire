# Filter Guide

This guide provides comprehensive documentation for the MatchHire Filter system, which enables reusable and composable filtering for search queries.

## Table of Contents

- [Filter Basics](#filter-basics)
- [Filter Operators](#filter-operators)
- [Filter Types](#filter-types)
- [Filter Composition](#filter-composition)
- [Predefined Filters](#predefined-filters)
- [Filter Builder](#filter-builder)
- [Examples](#examples)

## Filter Basics

### Creating a Simple Filter

```python
from apps.search.query_engine.filters import Filter, FilterOperator

filter_obj = Filter(
    field="status",
    operator=FilterOperator.EQ,
    value="active"
)
```

### Filter Parameters

- `field` (str): The field to filter on
- `operator` (FilterOperator): The comparison operator
- `value` (Any): The value to compare against
- `nested_path` (str, optional): Path for nested fields

## Filter Operators

### Comparison Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `EQ` | Equal to | `Filter(field="status", operator=FilterOperator.EQ, value="active")` |
| `NE` | Not equal to | `Filter(field="status", operator=FilterOperator.NE, value="closed")` |
| `GT` | Greater than | `Filter(field="salary", operator=FilterOperator.GT, value=50000)` |
| `GTE` | Greater than or equal to | `Filter(field="salary", operator=FilterOperator.GTE, value=50000)` |
| `LT` | Less than | `Filter(field="salary", operator=FilterOperator.LT, value=100000)` |
| `LTE` | Less than or equal to | `Filter(field="salary", operator=FilterOperator.LTE, value=100000)` |

### Collection Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `IN` | In list | `Filter(field="status", operator=FilterOperator.IN, value=["active", "pending"])` |
| `NOT_IN` | Not in list | `Filter(field="status", operator=FilterOperator.NOT_IN, value=["closed", "archived"])` |

### String Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `CONTAINS` | Contains substring | `Filter(field="title", operator=FilterOperator.CONTAINS, value="software")` |
| `NOT_CONTAINS` | Does not contain substring | `Filter(field="title", operator=FilterOperator.NOT_CONTAINS, value="intern")` |
| `STARTS_WITH` | Starts with | `Filter(field="title", operator=FilterOperator.STARTS_WITH, value="senior")` |
| `ENDS_WITH` | Ends with | `Filter(field="title", operator=FilterOperator.ENDS_WITH, value="engineer")` |

### Existence Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `EXISTS` | Field exists | `Filter(field="skills", operator=FilterOperator.EXISTS, value=None)` |
| `NOT_EXISTS` | Field does not exist | `Filter(field="skills", operator=FilterOperator.NOT_EXISTS, value=None)` |
| `IS_NULL` | Field is null | `Filter(field="archived_at", operator=FilterOperator.IS_NULL, value=None)` |
| `IS_NOT_NULL` | Field is not null | `Filter(field="archived_at", operator=FilterOperator.IS_NOT_NULL, value=None)` |

## Filter Types

### Simple Filter

Basic single-field filter.

```python
from apps.search.query_engine.filters import Filter, FilterOperator

filter_obj = Filter(
    field="status",
    operator=FilterOperator.EQ,
    value="active"
)
```

### Range Filter

Filter for numeric or date ranges.

```python
from apps.search.query_engine.filters import RangeFilter

filter_obj = RangeFilter(
    field="salary",
    gte=50000,
    lte=100000
)
```

**Parameters:**
- `field` (str): Field to filter on
- `gte` (Any, optional): Greater than or equal
- `gt` (Any, optional): Greater than
- `lte` (Any, optional): Less than or equal
- `lt` (Any, optional): Less than

### Boolean Filter

Combination of multiple filters with AND/OR/NOT logic.

```python
from apps.search.query_engine.filters import BooleanFilter, Filter, FilterOperator

filter_obj = BooleanFilter(
    operator="AND",
    filters=[
        Filter(field="status", operator=FilterOperator.EQ, value="active"),
        Filter(field="employment_type", operator=FilterOperator.EQ, value="full-time")
    ]
)
```

**Parameters:**
- `operator` (str): "AND", "OR", or "NOT"
- `filters` (List[Filter]): List of filters to combine

## Filter Composition

### AND Composition

```python
from apps.search.query_engine.filters import FilterBuilder

builder = FilterBuilder()
filters = builder.and_(
    Filter(field="status", operator=FilterOperator.EQ, value="active"),
    Filter(field="employment_type", operator=FilterOperator.EQ, value="full-time")
).build()
```

### OR Composition

```python
from apps.search.query_engine.filters import FilterBuilder

builder = FilterBuilder()
filters = builder.or_(
    Filter(field="status", operator=FilterOperator.EQ, value="active"),
    Filter(field="status", operator=FilterOperator.EQ, value="pending")
).build()
```

### NOT Composition

```python
from apps.search.query_engine.filters import FilterBuilder

builder = FilterBuilder()
filters = builder.not_(
    Filter(field="status", operator=FilterOperator.EQ, value="closed")
).build()
```

### Nested Composition

```python
from apps.search.query_engine.filters import FilterBuilder, Filter, FilterOperator

builder = FilterBuilder()
filters = builder.and_(
    Filter(field="status", operator=FilterOperator.EQ, value="active"),
    builder.or_(
        Filter(field="employment_type", operator=FilterOperator.EQ, value="full-time"),
        Filter(field="employment_type", operator=FilterOperator.EQ, value="contract")
    ).build()[0]
).build()
```

## Predefined Filters

### Job Filters

```python
from apps.search.query_engine.filters import JobFilters

# By status
filter_obj = JobFilters.by_status("active")

# By employment type
filter_obj = JobFilters.by_employment_type("full-time")

# By salary range
filter_obj = JobFilters.by_salary_range(min_salary=50000, max_salary=100000)

# By location
filter_obj = JobFilters.by_location("San Francisco")

# By industry
filter_obj = JobFilters.by_industry("Technology")

# By experience level
filter_obj = JobFilters.by_experience_level("senior")

# By company
filter_obj = JobFilters.by_company("Google")

# Active jobs only
filter_obj = JobFilters.active()

# Remote jobs only
filter_obj = JobFilters.remote()
```

### Candidate Filters

```python
from apps.search.query_engine.filters import CandidateFilters

# By status
filter_obj = CandidateFilters.by_status("available")

# By experience years
filter_obj = CandidateFilters.by_experience_years(min_years=3, max_years=10)

# By skill
filter_obj = CandidateFilters.by_skill("python")

# By location
filter_obj = CandidateFilters.by_location("San Francisco")

# By education level
filter_obj = CandidateFilters.by_education_level("bachelor")

# Active candidates only
filter_obj = CandidateFilters.active()

# Available for work
filter_obj = CandidateFilters.available()
```

### Resume Filters

```python
from apps.search.query_engine.filters import ResumeFilters

# By skill
filter_obj = ResumeFilters.by_skill("python")

# By experience years
filter_obj = ResumeFilters.by_experience_years(min_years=3)

# By education level
filter_obj = ResumeFilters.by_education_level("master")

# By location
filter_obj = ResumeFilters.by_location("San Francisco")

# By title
filter_obj = ResumeFilters.by_title("Software Engineer")
```

### Company Filters

```python
from apps.search.query_engine.filters import CompanyFilters

# By industry
filter_obj = CompanyFilters.by_industry("Technology")

# By company size
filter_obj = CompanyFilters.by_size("medium")

# By employee count
filter_obj = CompanyFilters.by_employee_count(min_employees=50, max_employees=500)

# By location
filter_obj = CompanyFilters.by_location("San Francisco")

# Verified companies only
filter_obj = CompanyFilters.verified()

# Active companies only
filter_obj = CompanyFilters.active()
```

### Recruiter Filters

```python
from apps.search.query_engine.filters import RecruiterFilters

# By status
filter_obj = RecruiterFilters.by_status("active")

# By company
filter_obj = RecruiterFilters.by_company("Google")

# By location
filter_obj = RecruiterFilters.by_location("San Francisco")

# Active recruiters only
filter_obj = RecruiterFilters.active()
```

### Application Filters

```python
from apps.search.query_engine.filters import ApplicationFilters

# By status
filter_obj = ApplicationFilters.by_status("pending")

# By job
filter_obj = ApplicationFilters.by_job("job123")

# By candidate
filter_obj = ApplicationFilters.by_candidate("candidate123")

# By date range
filter_obj = ApplicationFilters.by_date_range(
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Active applications only
filter_obj = ApplicationFilters.active()
```

### Interview Filters

```python
from apps.search.query_engine.filters import InterviewFilters

# By status
filter_obj = InterviewFilters.by_status("scheduled")

# By job
filter_obj = InterviewFilters.by_job("job123")

# By candidate
filter_obj = InterviewFilters.by_candidate("candidate123")

# By date range
filter_obj = InterviewFilters.by_date_range(
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Upcoming interviews only
filter_obj = InterviewFilters.upcoming()
```

### Skill Filters

```python
from apps.search.query_engine.filters import SkillFilters

# By category
filter_obj = SkillFilters.by_category("programming")

# By popularity
filter_obj = SkillFilters.by_popularity("high")

# By name
filter_obj = SkillFilters.by_name("python")
```

## Filter Builder

The `FilterBuilder` provides a fluent interface for constructing filters.

```python
from apps.search.query_engine.filters import FilterBuilder

builder = FilterBuilder()

# Add equality filter
builder.eq(field="status", value="active")

# Add range filter
builder.range(field="salary", gte=50000, lte=100000)

# Add IN filter
builder.in_(field="status", values=["active", "pending"])

# Add contains filter
builder.contains(field="title", value="software")

# Build filters
filters = builder.build()
```

### Builder Methods

- `eq(field, value)`: Add equality filter
- `ne(field, value)`: Add not-equal filter
- `gt(field, value)`: Add greater-than filter
- `gte(field, value)`: Add greater-than-or-equal filter
- `lt(field, value)`: Add less-than filter
- `lte(field, value)`: Add less-than-or-equal filter
- `in_(field, values)`: Add IN filter
- `not_in(field, values)`: Add NOT IN filter
- `contains(field, value)`: Add contains filter
- `not_contains(field, value)`: Add not-contains filter
- `starts_with(field, value)`: Add starts-with filter
- `ends_with(field, value)`: Add ends-with filter
- `exists(field)`: Add exists filter
- `not_exists(field)`: Add not-exists filter
- `is_null(field)`: Add is-null filter
- `is_not_null(field)`: Add is-not-null filter
- `range(field, **kwargs)`: Add range filter
- `and_(*filters)`: Add AND boolean filter
- `or_(*filters)`: Add OR boolean filter
- `not_(filter)`: Add NOT boolean filter
- `build()`: Build and return filters
- `reset()`: Reset the builder

## Examples

### Simple Status Filter

```python
from apps.search.query_engine.filters import Filter, FilterOperator

filter_obj = Filter(
    field="status",
    operator=FilterOperator.EQ,
    value="active"
)
```

### Salary Range Filter

```python
from apps.search.query_engine.filters import RangeFilter

filter_obj = RangeFilter(
    field="salary",
    gte=50000,
    lte=100000
)
```

### Multiple Conditions with AND

```python
from apps.search.query_engine.filters import FilterBuilder

builder = FilterBuilder()
filters = (
    builder
    .eq(field="status", value="active")
    .range(field="salary", gte=50000)
    .contains(field="location", value="San Francisco")
    .build()
)
```

### Multiple Conditions with OR

```python
from apps.search.query_engine.filters import FilterBuilder, Filter, FilterOperator

builder = FilterBuilder()
filters = builder.or_(
    Filter(field="status", operator=FilterOperator.EQ, value="active"),
    Filter(field="status", operator=FilterOperator.EQ, value="pending")
).build()
```

### Nested Field Filter

```python
from apps.search.query_engine.filters import Filter, FilterOperator

filter_obj = Filter(
    field="name",
    operator=FilterOperator.EQ,
    value="python",
    nested_path="skills"
)
```

### Complex Filter Composition

```python
from apps.search.query_engine.filters import FilterBuilder, Filter, FilterOperator

builder = FilterBuilder()

# (status = active AND (employment_type = full-time OR employment_type = contract))
filters = builder.and_(
    Filter(field="status", operator=FilterOperator.EQ, value="active"),
    builder.or_(
        Filter(field="employment_type", operator=FilterOperator.EQ, value="full-time"),
        Filter(field="employment_type", operator=FilterOperator.EQ, value="contract")
    ).build()[0]
).build()
```

### Using Predefined Filters

```python
from apps.search.query_engine.filters import JobFilters, FilterBuilder

builder = FilterBuilder()

# Combine predefined filters with custom filters
filters = (
    builder
    .add_filter(JobFilters.active())
    .add_filter(JobFilters.by_salary_range(min_salary=50000))
    .contains(field="title", value="senior")
    .build()
)
```

### Filter with Validation

```python
from apps.search.query_engine.filters import Filter, FilterOperator

filter_obj = Filter(
    field="status",
    operator=FilterOperator.EQ,
    value="active"
)

is_valid = filter_obj.validate()
```

### Filter Serialization

```python
from apps.search.query_engine.filters import Filter, FilterOperator

filter_obj = Filter(
    field="status",
    operator=FilterOperator.EQ,
    value="active"
)

filter_dict = filter_obj.to_dict()
# Output: {"field": "status", "operator": "eq", "value": "active"}
```

## Best Practices

1. **Use Predefined Filters**: Leverage predefined entity filters for common patterns
2. **Validate Filters**: Always validate filters before using them in queries
3. **Use Builder for Complex Filters**: Use FilterBuilder for complex filter compositions
4. **Consider Performance**: Range filters on large datasets can be expensive
5. **Index Appropriately**: Ensure filtered fields are properly indexed
6. **Use Exists for Optional Fields**: Use EXISTS/NOT_EXISTS for optional fields instead of IS_NULL
7. **Combine Filters Efficiently**: Combine multiple conditions into a single boolean filter when possible
