# Filter Guide

## Overview

The Filter system provides reusable filters for all entity types in MatchHire. Filters support various comparison operators, date ranges, location filtering, experience levels, salary ranges, and more.

## Basic Filters

### Simple Filter

```python
from apps.search.query_engine.filters import Filter, FilterOperator

filter_obj = Filter(
    field="status",
    operator=FilterOperator.EQ,
    value="active"
)
```

### Range Filter

```python
from apps.search.query_engine.filters import RangeFilter

filter_obj = RangeFilter(
    field="salary",
    gte=50000,
    lte=100000
)
```

### Boolean Filter

```python
from apps.search.query_engine.filters import BooleanFilter, Filter, FilterOperator

filter_obj = BooleanFilter(
    operator="AND",
    filters=[
        Filter(field="status", operator=FilterOperator.EQ, value="active"),
        Filter(field="type", operator=FilterOperator.EQ, value="full-time"),
    ]
)
```

## Filter Operators

- `EQ`: Exact match
- `NE`: Not equal
- `GT`: Greater than
- `GTE`: Greater than or equal
- `LT`: Less than
- `LTE`: Less than or equal
- `IN`: In list
- `NOT_IN`: Not in list
- `CONTAINS`: Contains substring
- `NOT_CONTAINS`: Does not contain substring
- `STARTS_WITH`: Starts with
- `ENDS_WITH`: Ends with
- `EXISTS`: Field exists
- `NOT_EXISTS`: Field does not exist
- `IS_NULL`: Field is null
- `IS_NOT_NULL`: Field is not null

## FilterBuilder

The FilterBuilder provides a fluent interface for constructing filters.

```python
from apps.search.query_engine.filters import FilterBuilder

builder = FilterBuilder()

# Simple filters
filters = (
    builder
    .eq(field="status", value="active")
    .range(field="salary", gte=50000, lte=100000)
    .in_(field="industry", values=["Technology", "Finance"])
    .build()
)

# Boolean filters
filters = (
    builder
    .and_(
        Filter(field="status", operator=FilterOperator.EQ, value="active"),
        Filter(field="type", operator=FilterOperator.EQ, value="full-time")
    )
    .build()
)
```

## Predefined Filters

### JobFilters

```python
from apps.search.query_engine.filters import JobFilters

# By status
filter_obj = JobFilters.by_status("active")

# By employment type
filter_obj = JobFilters.by_employment_type("full-time")

# By employment types (multiple)
filter_obj = JobFilters.by_employment_types(["full-time", "contract"])

# By experience level
filter_obj = JobFilters.by_experience_level("senior")

# By salary range
filter_obj = JobFilters.by_salary_range(min_salary=50000, max_salary=100000)

# By location
filter_obj = JobFilters.by_location("San Francisco")

# By remote status
filter_obj = JobFilters.by_remote(is_remote=True)

# By company
filter_obj = JobFilters.by_company(company_id="123")

# By companies (multiple)
filter_obj = JobFilters.by_companies(["123", "456"])

# By industry
filter_obj = JobFilters.by_industry("Technology")

# By skill
filter_obj = JobFilters.by_skill("python")

# By skills (multiple)
filter_obj = JobFilters.by_skills(["python", "django"])

# By posted date range
filter_obj = JobFilters.by_posted_date_range(
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Active jobs
filter_obj = JobFilters.active()

# Urgent jobs
filter_obj = JobFilters.urgent()
```

### CandidateFilters

```python
from apps.search.query_engine.filters import CandidateFilters

# By status
filter_obj = CandidateFilters.by_status("available")

# By experience level
filter_obj = CandidateFilters.by_experience_level("senior")

# By experience years
filter_obj = CandidateFilters.by_experience_years(min_years=3, max_years=10)

# By location
filter_obj = CandidateFilters.by_location("San Francisco")

# By willingness to relocate
filter_obj = CandidateFilters.by_willing_to_relocate(is_willing=True)

# By skill
filter_obj = CandidateFilters.by_skill("python")

# By skills (multiple)
filter_obj = CandidateFilters.by_skills(["python", "django"])

# By education level
filter_obj = CandidateFilters.by_education_level("bachelor")

# By salary expectation
filter_obj = CandidateFilters.by_salary_expectation(min_salary=80000, max_salary=120000)

# By employment type
filter_obj = CandidateFilters.by_employment_type("full-time")

# By availability
filter_obj = CandidateFilters.by_availability("immediate")

# Active candidates
filter_obj = CandidateFilters.active()

# Verified candidates
filter_obj = CandidateFilters.verified()
```

### ResumeFilters

```python
from apps.search.query_engine.filters import ResumeFilters

# By candidate ID
filter_obj = ResumeFilters.by_candidate_id("123")

# By skill
filter_obj = ResumeFilters.by_skill("python")

# By skills (multiple)
filter_obj = ResumeFilters.by_skills(["python", "django"])

# By experience years
filter_obj = ResumeFilters.by_experience_years(min_years=3, max_years=10)

# By education level
filter_obj = ResumeFilters.by_education_level("bachelor")

# By degree
filter_obj = ResumeFilters.by_degree("Computer Science")

# By field of study
filter_obj = ResumeFilters.by_field_of_study("Computer Science")

# By company
filter_obj = ResumeFilters.by_company("Google")

# By job title
filter_obj = ResumeFilters.by_job_title("Software Engineer")

# By updated date range
filter_obj = ResumeFilters.by_updated_date_range(
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Recent resumes
filter_obj = ResumeFilters.recent(days=30)
```

### CompanyFilters

```python
from apps.search.query_engine.filters import CompanyFilters

# By industry
filter_obj = CompanyFilters.by_industry("Technology")

# By company size
filter_obj = CompanyFilters.by_size("medium")

# By location
filter_obj = CompanyFilters.by_location("San Francisco")

# By funding stage
filter_obj = CompanyFilters.by_funding_stage("Series B")

# By employee count
filter_obj = CompanyFilters.by_employee_count(min_employees=50, max_employees=500)

# By revenue range
filter_obj = CompanyFilters.by_revenue_range(min_revenue=1000000, max_revenue=10000000)

# Verified companies
filter_obj = CompanyFilters.verified()

# Active companies
filter_obj = CompanyFilters.active()
```

### RecruiterFilters

```python
from apps.search.query_engine.filters import RecruiterFilters

# By company ID
filter_obj = RecruiterFilters.by_company_id("123")

# By company IDs (multiple)
filter_obj = RecruiterFilters.by_company_ids(["123", "456"])

# By role
filter_obj = RecruiterFilters.by_role("Senior Recruiter")

# By department
filter_obj = RecruiterFilters.by_department("Engineering")

# By location
filter_obj = RecruiterFilters.by_location("San Francisco")

# Verified recruiters
filter_obj = RecruiterFilters.verified()

# Active recruiters
filter_obj = RecruiterFilters.active()
```

### ApplicationFilters

```python
from apps.search.query_engine.filters import ApplicationFilters

# By job ID
filter_obj = ApplicationFilters.by_job_id("123")

# By candidate ID
filter_obj = ApplicationFilters.by_candidate_id("456")

# By status
filter_obj = ApplicationFilters.by_status("pending")

# By statuses (multiple)
filter_obj = ApplicationFilters.by_statuses(["pending", "reviewing"])

# By stage
filter_obj = ApplicationFilters.by_stage("screening")

# By stages (multiple)
filter_obj = ApplicationFilters.by_stages(["screening", "interview"])

# By applied date range
filter_obj = ApplicationFilters.by_applied_date_range(
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# By source
filter_obj = ApplicationFilters.by_source("direct")

# By recruiter ID
filter_obj = ApplicationFilters.by_recruiter_id("789")

# Pending applications
filter_obj = ApplicationFilters.pending()

# In-progress applications
filter_obj = ApplicationFilters.in_progress()
```

### InterviewFilters

```python
from apps.search.query_engine.filters import InterviewFilters

# By application ID
filter_obj = InterviewFilters.by_application_id("123")

# By job ID
filter_obj = InterviewFilters.by_job_id("456")

# By candidate ID
filter_obj = InterviewFilters.by_candidate_id("789")

# By recruiter ID
filter_obj = InterviewFilters.by_recruiter_id("101")

# By status
filter_obj = InterviewFilters.by_status("scheduled")

# By statuses (multiple)
filter_obj = InterviewFilters.by_statuses(["scheduled", "completed"])

# By type
filter_obj = InterviewFilters.by_type("video")

# By scheduled date range
filter_obj = InterviewFilters.by_scheduled_date_range(
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Upcoming interviews
filter_obj = InterviewFilters.upcoming()

# Past interviews
filter_obj = InterviewFilters.past()
```

### SkillFilters

```python
from apps.search.query_engine.filters import SkillFilters

# By category
filter_obj = SkillFilters.by_category("Programming")

# By name
filter_obj = SkillFilters.by_name("Python")

# By popularity
filter_obj = SkillFilters.by_popularity(min_popularity=100)

# Trending skills
filter_obj = SkillFilters.trending()

# Verified skills
filter_obj = SkillFilters.verified()
```

## Nested Filters

Filters can be applied to nested fields:

```python
from apps.search.query_engine.filters import Filter, FilterOperator

filter_obj = Filter(
    field="name",
    operator=FilterOperator.EQ,
    value="python",
    nested_path="skills"
)
```

## Filter Validation

All filters support validation:

```python
filter_obj = Filter(field="status", operator=FilterOperator.EQ, value="active")
if filter_obj.validate():
    # Filter is valid
    pass
```

## Serialization

All filters can be serialized to dictionaries:

```python
filter_obj = Filter(field="status", operator=FilterOperator.EQ, value="active")
filter_dict = filter_obj.to_dict()
```

## Provider Translation

Filters are automatically translated to the provider's native query language:

- **PostgreSQL**: Translated to Django ORM Q objects
- **Elasticsearch**: Translated to Elasticsearch filter context

No application code changes are needed when switching providers.
