# Faceted Search Guide

This guide provides comprehensive documentation for the MatchHire Faceted Search system, which enables dynamic faceted search with configurable sorting, pagination, and state management.

## Table of Contents

- [Facet Basics](#facet-basics)
- [Facet Configuration](#facet-configuration)
- [Facet Types](#facet-types)
- [Facet State Management](#facet-state-management)
- [Facet Builder](#facet-builder)
- [Predefined Facets](#predefined-facets)
- [Examples](#examples)

## Facet Basics

### Creating a Simple Facet

```python
from apps.search.query_engine.facets import FacetConfig

facet = FacetConfig(
    field="location",
    name="Location",
    size=10
)
```

### Facet Parameters

- `field` (str): Field to facet on
- `name` (str): Display name for the facet
- `size` (int, optional): Number of facet values to return (default: 10)
- `sort` (FacetSort, optional): Sort order for facet values
- `nested_path` (str, optional): Path for nested fields
- `min_doc_count` (int, optional): Minimum documents per facet value

## Facet Configuration

### Basic Configuration

```python
from apps.search.query_engine.facets import FacetConfig, FacetSort

facet = FacetConfig(
    field="location",
    name="Location",
    size=20,
    sort=FacetSort.COUNT_DESC  # Sort by count descending
)
```

### Sort Options

| Sort Option | Description |
|-------------|-------------|
| `COUNT_DESC` | Sort by count descending (most popular first) |
| `COUNT_ASC` | Sort by count ascending |
| `VALUE_DESC` | Sort by value descending |
| `VALUE_ASC` | Sort by value ascending |

### Nested Field Facets

```python
from apps.search.query_engine.facets import FacetConfig

facet = FacetConfig(
    field="name",
    name="Skills",
    nested_path="skills",
    size=30
)
```

## Facet Types

### Simple Field Facets

Facet on a simple field.

```python
from apps.search.query_engine.facets import FacetConfig

facet = FacetConfig(
    field="location",
    name="Location",
    size=10
)
```

### Nested Field Facets

Facet on a nested object field.

```python
from apps.search.query_engine.facets import FacetConfig

facet = FacetConfig(
    field="name",
    name="Skills",
    nested_path="skills",
    size=30
)
```

### Range Facets

Facet on a range field (requires custom implementation).

```python
from apps.search.query_engine.facets import FacetConfig

facet = FacetConfig(
    field="salary_range",
    name="Salary Range",
    size=10
)
```

## Facet State Management

### Creating Facet State

```python
from apps.search.query_engine.facets import FacetState

state = FacetState()
```

### Adding Selections

```python
state.add_selection("location", "San Francisco")
state.add_selection("location", "New York")
state.add_selection("employment_type", "full-time")
```

### Checking Selections

```python
# Check if a value is selected
is_selected = state.is_selected("location", "San Francisco")

# Check if field has any selections
has_selections = state.has_selections()

# Get all selections for a field
selections = state.get_selections("location")
# Returns: ["San Francisco", "New York"]
```

### Removing Selections

```python
# Remove specific selection
state.remove_selection("location", "San Francisco")

# Clear all selections for a field
state.clear_field("location")

# Clear all selections
state.clear_all()
```

### Serialization

```python
# Convert to dictionary
state_dict = state.to_dict()
# Output: {"location": ["San Francisco", "New York"], "employment_type": ["full-time"]}

# Create from dictionary
state = FacetState.from_dict(state_dict)
```

## Facet Builder

The `FacetBuilder` provides a fluent interface for constructing facet configurations.

```python
from apps.search.query_engine.facets import FacetBuilder

builder = FacetBuilder()

# Add facet
builder.add_facet(field="location", name="Location", size=20)

# Build facets
facets = builder.build()
```

### Builder Methods

- `add_facet(field, name, **kwargs)`: Add a facet configuration
- `location_facet(**kwargs)`: Add location facet preset
- `company_facet(**kwargs)`: Add company facet preset
- `skills_facet(**kwargs)`: Add skills facet preset
- `salary_facet(**kwargs)`: Add salary facet preset
- `employment_type_facet(**kwargs)`: Add employment type facet preset
- `experience_level_facet(**kwargs)`: Add experience level facet preset
- `education_level_facet(**kwargs)`: Add education level facet preset
- `industry_facet(**kwargs)`: Add industry facet preset
- `status_facet(**kwargs)`: Add status facet preset
- `build()`: Build and return facets
- `reset()`: Reset the builder

## Predefined Facets

### Job Search Facets

```python
from apps.search.query_engine.facets import PredefinedFacets

facets = PredefinedFacets.job_search_facets()
```

Includes:
- Location facet
- Company facet
- Employment type facet
- Experience level facet
- Salary range facet
- Industry facet

### Candidate Search Facets

```python
from apps.search.query_engine.facets import PredefinedFacets

facets = PredefinedFacets.candidate_search_facets()
```

Includes:
- Location facet
- Skills facet (nested)
- Experience level facet
- Education level facet
- Salary range facet

### Company Search Facets

```python
from apps.search.query_engine.facets import PredefinedFacets

facets = PredefinedFacets.company_search_facets()
```

Includes:
- Industry facet
- Company size facet
- Location facet
- Employee count range facet

### Application Search Facets

```python
from apps.search.query_engine.facets import PredefinedFacets

facets = PredefinedFacets.application_search_facets()
```

Includes:
- Status facet
- Job facet
- Date range facet

### Interview Search Facets

```python
from apps.search.query_engine.facets import PredefinedFacets

facets = PredefinedFacets.interview_search_facets()
```

Includes:
- Status facet
- Job facet
- Date range facet

## Examples

### Simple Faceted Search

```python
from apps.search.query_engine.facets import FacetBuilder

builder = FacetBuilder()
facets = builder.location_facet(size=20).build()

# Use in search
context = SearchExecutionContext(
    entity_type="job",
    query="software engineer",
    facets=[facets[0]]
)
```

### Multiple Facets

```python
from apps.search.query_engine.facets import FacetBuilder

builder = FacetBuilder()
facets = (
    builder
    .location_facet(size=20)
    .company_facet(size=15)
    .employment_type_facet(size=10)
    .build()
)
```

### Facets with Selection State

```python
from apps.search.query_engine.facets import FacetBuilder, FacetState

# Create facets
builder = FacetBuilder()
facets = builder.location_facet(size=20).build()

# Create state with selections
state = FacetState()
state.add_selection("location", "San Francisco")
state.add_selection("location", "New York")

# Use in search
context = SearchExecutionContext(
    entity_type="job",
    query="software engineer",
    facets=facets,
    facet_state=state
)
```

### Nested Field Facets

```python
from apps.search.query_engine.facets import FacetBuilder

builder = FacetBuilder()
facets = builder.skills_facet(size=30).build()

# Skills facet uses nested_path="skills"
```

### Custom Facet Configuration

```python
from apps.search.query_engine.facets import FacetConfig, FacetSort

facet = FacetConfig(
    field="custom_field",
    name="Custom Field",
    size=25,
    sort=FacetSort.VALUE_ASC,
    min_doc_count=5
)
```

### Using Predefined Facets

```python
from apps.search.query_engine.facets import PredefinedFacets

facets = PredefinedFacets.job_search_facets()

# Modify predefined facets if needed
for facet in facets:
    if facet.field == "location":
        facet.size = 30
```

### Facet Response Handling

```python
# After search, facet results are in EngineResult
result = engine.search(context)

for facet_response in result.facets:
    print(f"Facet: {facet_response.name}")
    print(f"Total: {facet_response.total}")
    
    for value in facet_response.values:
        print(f"  {value.value}: {value.count} (selected: {value.selected})")
```

### Facet Selection Handling

```python
# Get selected values from facet response
for facet_response in result.facets:
    selected = facet_response.get_selected_values()
    if selected:
        print(f"Selected {facet_response.name}: {selected}")
```

## Best Practices

1. **Limit Facet Size**: Use reasonable `size` values to avoid excessive computation
2. **Use Min Doc Count**: Set `min_doc_count` to filter out noisy facet values
3. **Leverage Predefined Facets**: Use predefined facets for common patterns
4. **Manage State Properly**: Always serialize/deserialize facet state for persistence
5. **Consider Performance**: Facets on high-cardinality fields can be expensive
6. **Index Appropriately**: Ensure faceted fields are properly indexed
7. **Use Nested Facets**: Use nested facets for array/object fields

## Performance Considerations

1. **Facet Count**: More facets require more computation
2. **Facet Size**: Larger facet sizes require more memory
3. **Field Cardinality**: High cardinality fields are poor candidates for faceting
4. **Nested Facets**: Nested facets are more expensive than simple facets
5. **Caching**: Facet results can be cached for identical queries
6. **Pagination**: Facet pagination can reduce initial load time
