# Diversification

## Overview

Diversification ensures that recommendation sets are diverse across multiple dimensions, avoiding repetitive recommendations and providing users with a variety of options.

## Diversification Types

### 1. Skill Diversification

**Description**: Ensures recommendations have diverse skill sets.

**Configuration**:
```python
from apps.search.recommendations.diversification import DiversificationConfig

config = DiversificationConfig(
    enable_skill_diversification=True,
    skill_diversity_threshold=0.3,
)
```

**Behavior**:
- Calculates Jaccard similarity between candidate skills and already seen skills
- Skips candidates with skill overlap above threshold
- Ensures variety in skill composition

### 2. Company Diversification

**Description**: Limits recommendations from the same company.

**Configuration**:
```python
config = DiversificationConfig(
    enable_company_diversification=True,
    max_same_company=3,
)
```

**Behavior**:
- Limits number of recommendations from same company
- Ensures variety in employer representation
- Prevents company bias in recommendations

### 3. Location Diversification

**Description**: Limits recommendations from the same location.

**Configuration**:
```python
config = DiversificationConfig(
    enable_location_diversification=True,
    max_same_location=3,
)
```

**Behavior**:
- Limits number of recommendations from same location
- Ensures geographic variety
- Useful for remote work recommendations

### 4. Experience Diversification

**Description**: Ensures recommendations have diverse experience levels.

**Configuration**:
```python
config = DiversificationConfig(
    enable_experience_diversification=True,
    experience_diversity_threshold=0.5,
)
```

**Behavior**:
- Categorizes experience levels (junior, mid, senior, lead)
- Limits duplicates per level
- Ensures variety in seniority

### 5. Salary Diversification

**Description**: Ensures recommendations have diverse salary ranges.

**Configuration**:
```python
config = DiversificationConfig(
    enable_salary_diversification=True,
    salary_diversity_threshold=0.2,
)
```

**Behavior**:
- Groups similar salary ranges
- Limits duplicates per range
- Ensures variety in compensation

### 6. Industry Diversification

**Description**: Limits recommendations from the same industry.

**Configuration**:
```python
config = DiversificationConfig(
    enable_industry_diversification=True,
    max_same_industry=3,
)
```

**Behavior**:
- Limits number of recommendations from same industry
- Ensures industry variety
- Prevents industry bias

### 7. Deduplication

**Description**: Removes duplicate recommendations.

**Configuration**:
```python
config = DiversificationConfig(
    enable_deduplication=True,
)
```

**Behavior**:
- Removes exact duplicates by ID
- Ensures unique recommendations
- Applied before other diversification

## Using Diversification

### Basic Usage

```python
from apps.search.recommendations.diversification import DiversificationEngine, DiversificationConfig

config = DiversificationConfig(
    enable_skill_diversification=True,
    enable_company_diversification=True,
    max_same_company=3,
)

engine = DiversificationEngine(config)
diversified = engine.diversify(candidates, context)
```

### Custom Diversifiers

Create custom diversifiers:

```python
from apps.search.recommendations.diversification import Diversifier, DiversificationConfig

class CustomDiversifier(Diversifier):
    @property
    def diversification_type(self):
        return DiversificationType.DEDUPLICATION
    
    def diversify(self, candidates, context):
        # Custom diversification logic
        return diversified_candidates

engine = DiversificationEngine()
engine.add_diversifier(CustomDiversifier())
```

### Disable Specific Diversifiers

```python
engine.remove_diversifier(DiversificationType.SALARY)
```

## Diversification Configuration

### Full Configuration

```python
from apps.search.recommendations.diversification import DiversificationConfig

config = DiversificationConfig(
    # Enable/disable diversifiers
    enable_skill_diversification=True,
    enable_company_diversification=True,
    enable_location_diversification=True,
    enable_experience_diversification=True,
    enable_salary_diversification=True,
    enable_industry_diversification=True,
    enable_deduplication=True,
    
    # Thresholds
    skill_diversity_threshold=0.3,
    company_diversity_threshold=2,
    location_diversity_threshold=2,
    experience_diversity_threshold=0.5,
    salary_diversity_threshold=0.2,
    industry_diversity_threshold=2,
    
    # Limits
    max_same_company=3,
    max_same_location=3,
    max_same_industry=3,
)
```

### Conservative Diversification

More strict limits for higher diversity:

```python
config = DiversificationConfig(
    skill_diversity_threshold=0.2,
    max_same_company=2,
    max_same_location=2,
    max_same_industry=2,
)
```

### Relaxed Diversification

More lenient limits for relevance-focused recommendations:

```python
config = DiversificationConfig(
    skill_diversity_threshold=0.5,
    max_same_company=5,
    max_same_location=5,
    max_same_industry=5,
)
```

## Monitoring Diversification

Track diversification metrics:

```python
# Record diversification
monitor.record_diversification(
    diversity_scores={
        "skill": 0.8,
        "company": 0.7,
        "location": 0.6,
    },
    duplicates_removed=5,
)

# Get diversification metrics
div_metrics = monitor.get_diversification_metrics()
print(f"Skill diversity: {div_metrics.skill_diversity_score}")
print(f"Company diversity: {div_metrics.company_diversity_score}")
print(f"Duplicates removed: {div_metrics.duplicates_removed}")
```

## Best Practices

### 1. Balance Diversity and Relevance

Don't over-diversify at the cost of relevance:
- Use moderate thresholds (0.3-0.5)
- Set reasonable limits (2-5 per category)
- Monitor acceptance rates

### 2. Context-Aware Diversification

Adjust diversification based on context:
- **Job search**: Higher skill diversity, lower company diversity
- **Candidate discovery**: Higher novelty, lower skill diversity
- **Career growth**: Higher experience diversity

### 3. Monitor Diversity Scores

Track diversity metrics to ensure effectiveness:
```python
div_metrics = monitor.get_diversification_metrics()
if div_metrics.skill_diversity_score < 0.5:
    # Increase skill diversification
    config.skill_diversity_threshold = 0.25
```

### 4. Test Different Configurations

A/B test different diversification settings to find optimal balance.

### 5. Consider User Preferences

Some users may prefer more diverse recommendations, others more focused:
```python
if user_preferences.get("diversity_preference") == "high":
    config = get_high_diversity_config()
else:
    config = get_standard_diversity_config()
```

## Performance Considerations

- **Skill Diversification**: Moderate cost, O(n*m) where n=candidates, m=seen skills
- **Company Diversification**: Low cost, O(n) with hash map
- **Location Diversification**: Low cost, O(n) with hash map
- **Experience Diversification**: Low cost, O(n)
- **Salary Diversification**: Moderate cost, O(n*m) comparisons
- **Industry Diversification**: Low cost, O(n) with hash map
- **Deduplication**: Low cost, O(n) with hash set

## Common Issues

### Issue: Too Few Recommendations After Diversification

**Solution**: Relax diversification thresholds or limits:
```python
config.skill_diversity_threshold = 0.5
config.max_same_company = 5
```

### Issue: Recommendations Still Repetitive

**Solution**: Enable more diversification types:
```python
config.enable_salary_diversification = True
config.enable_industry_diversification = True
```

### Issue: Diversification Too Slow

**Solution**: Disable expensive diversifiers or use caching:
```python
config.enable_salary_diversification = False  # Most expensive
```

## Future Enhancements

The diversification framework is ready for:

- **Semantic Diversification**: Diversify based on semantic meaning
- **Graph-based Diversification**: Diversify based on network structure
- **User-Aware Diversification**: Personalize diversification per user
- **Temporal Diversification**: Diversify across time periods
- **Multi-objective Optimization**: Balance diversity with other objectives
