# Faceted Search Guide

## Overview

Faceted search allows users to filter and explore search results by various dimensions like location, company, skills, experience, salary, education, and more.

## Facet Configuration

### Basic Facet

```python
from apps.search.query_engine.facets import FacetConfig, FacetSort

config = FacetConfig(
    field="location",
    name="Location",
    size=20,                      # Number of facet values
    sort=FacetSort.COUNT,         # Sort by count or value
    show_missing=False,           # Include missing values
    min_doc_count=1,              # Minimum documents per bucket
    nested_path=None,             # For nested fields
)
```

### Facet with Nested Path

```python
config = FacetConfig(
    field="name",
    name="Skills",
    size=30,
    nested_path="skills",         # Nested field path
)
```

## FacetBuilder

The FacetBuilder provides a fluent interface for constructing facet configurations.

```python
from apps.search.query_engine.facets import FacetBuilder

builder = FacetBuilder()

# Single facet
facets = builder.add_facet(field="location", name="Location").build()

# Multiple facets
facets = (
    builder
    .add_facet(field="location", name="Location", size=20)
    .add_facet(field="industry", name="Industry", size=15)
    .build()
)
```

## Predefined Facets

### Job Search Facets

```python
from apps.search.query_engine.facets import PredefinedFacets

facets = PredefinedFacets.job_search_facets()
# Returns: location, company_name, name (skills), experience_level,
#          employment_type, industry, salary_range
```

### Candidate Search Facets

```python
facets = PredefinedFacets.candidate_search_facets()
# Returns: location, name (skills), experience_level, education_level,
#          preferred_employment_type, salary_range
```

### Company Search Facets

```python
facets = PredefinedFacets.company_search_facets()
# Returns: industry, company_size, headquarters_location, funding_stage
```

### Application Search Facets

```python
facets = PredefinedFacets.application_search_facets()
# Returns: status, stage, company_name
```

### Interview Search Facets

```python
facets = PredefinedFacets.interview_search_facets()
# Returns: status, interview_type
```

## Facet Presets

The FacetBuilder includes convenient presets for common facets:

```python
from apps.search.query_engine.facets import FacetBuilder

builder = FacetBuilder()

# Location facet
facets = builder.location_facet(size=20).build()

# Company facet
facets = builder.company_facet(size=15).build()

# Skills facet
facets = builder.skills_facet(size=30, nested_path="skills").build()

# Experience facet
facets = builder.experience_facet(size=5).build()

# Salary facet
facets = builder.salary_facet(size=10).build()

# Education facet
facets = builder.education_facet(size=5).build()

# Employment type facet
facets = builder.employment_type_facet(size=5).build()

# Industry facet
facets = builder.industry_facet(size=20).build()

# Status facet
facets = builder.status_facet(size=10).build()

# Application stage facet
facets = builder.application_stage_facet(size=10).build()

# Company size facet
facets = builder.company_size_facet(size=5).build()

# Funding stage facet
facets = builder.funding_stage_facet(size=10).build()

# Interview type facet
facets = builder.interview_type_facet(size=5).build()

# Posted date facet
facets = builder.posted_date_facet(size=10).build()
```

## Facet State

FacetState tracks which facet values are currently selected.

```python
from apps.search.query_engine.facets import FacetState

state = FacetState()

# Add selections
state.add_selection("location", "San Francisco")
state.add_selection("location", "New York")
state.add_selection("industry", "Technology")

# Check if selected
is_selected = state.is_selected("location", "San Francisco")

# Get selections for a field
selections = state.get_selections("location")
# Returns: ["San Francisco", "New York"]

# Remove selection
state.remove_selection("location", "San Francisco")

# Clear field
state.clear_field("location")

# Clear all
state.clear_all()

# Check if any selections exist
has_selections = state.has_selections()

# Serialize to dictionary
state_dict = state.to_dict()

# Create from dictionary
state = FacetState.from_dict(state_dict)
```

## Facet Response

FacetResponse contains facet values with counts.

```python
from apps.search.query_engine.facets import FacetResponse, FacetValue

values = [
    FacetValue(value="San Francisco", count=100, selected=True),
    FacetValue(value="New York", count=80, selected=False),
]

response = FacetResponse(
    field="location",
    name="Location",
    values=values,
    total=180,
    other=50,                     # Count of values not returned
    missing=10,                   # Count of missing values
)

# Get selected values
selected = response.get_selected_values()

# Get selected count
count = response.get_selected_count()
```

## Using Facets in Search

```python
from apps.search.query_engine import QueryEngine, SearchExecutionContext
from apps.search.query_engine.facets import FacetBuilder

# Create facet configurations
builder = FacetBuilder()
facets = (
    builder
    .location_facet(size=20)
    .company_facet(size=15)
    .skills_facet(size=30)
    .build()
)

# Create search context with facets
context = SearchExecutionContext(
    entity_type="job",
    query="software engineer",
    facets=facets,
)

# Execute search
result = engine.search(context)

# Access facet results
for facet in result.facets:
    print(f"{facet.name}:")
    for value in facet.values:
        print(f"  {value.value}: {value.count}")
```

## Dynamic Facets

Facets can be dynamically configured based on search context:

```python
from apps.search.query_engine.facets import FacetConfig

# Dynamic facet based on user location
if user_location:
    config = FacetConfig(
        field="location",
        name="Nearby Locations",
        size=10,
        value_filter={"location": user_location}
    )
```

## Facet Sorting

Facets can be sorted by count or value:

```python
from apps.search.query_engine.facets import FacetSort, FacetConfig

# Sort by count (most popular first)
config = FacetConfig(
    field="location",
    name="Location",
    sort=FacetSort.COUNT
)

# Sort by value (alphabetical)
config = FacetConfig(
    field="location",
    name="Location",
    sort=FacetSort.VALUE
)
```

## Facet Pagination

Facets support pagination for large result sets:

```python
config = FacetConfig(
    field="location",
    name="Location",
    size=20,                      # Return top 20 values
)
```

## Validation

All facet configurations support validation:

```python
config = FacetConfig(field="location", name="Location")
if config.validate():
    # Configuration is valid
    pass
```

## Serialization

All facet configurations can be serialized to dictionaries:

```python
config = FacetConfig(field="location", name="Location")
config_dict = config.to_dict()
```

## Provider Translation

Facets are automatically translated to the provider's native facet/aggregation language:

- **PostgreSQL**: Translated to Django ORM aggregations
- **Elasticsearch**: Translated to Elasticsearch terms aggregations

No application code changes are needed when switching providers.
