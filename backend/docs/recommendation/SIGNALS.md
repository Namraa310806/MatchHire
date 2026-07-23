# Recommendation Signals

## Overview

Recommendation signals extend the existing ranking signals to provide recommendation-specific scoring. These signals are designed for recommendation scenarios and can be used in the Ranking Pipeline alongside the base ranking signals.

## Signal Types

### 1. Skill Similarity Signal

**Description**: Scores items based on skill similarity to the target entity. Uses Jaccard similarity and weighted skill matching.

**Use Cases**:
- Matching candidates to job requirements
- Matching jobs to candidate skills
- Finding similar skill profiles

**Configuration**:
```python
from apps.search.recommendations.signals import SkillSimilaritySignal, SignalConfig

config = SignalConfig(
    enabled=True,
    weight=1.0,
    params={
        "important_skills": ["python", "django"],
    }
)
signal = SkillSimilaritySignal(config)
```

**Scoring**:
- Jaccard similarity between required and available skills
- Bonus for exact match
- Weighted important skills
- Range: [0, 1]

### 2. Career Progression Signal

**Description**: Scores items based on career progression potential, such as seniority level and career path alignment.

**Use Cases**:
- Career advancement recommendations
- Senior role matching
- Leadership potential assessment

**Configuration**:
```python
from apps.search.recommendations.signals import CareerProgressionSignal

signal = CareerProgressionSignal()
```

**Scoring**:
- Progressive steps (next level = 1.0)
- Same level = 0.6
- Lower level = 0.3
- Range: [0, 1]

### 3. Technology Similarity Signal

**Description**: Scores items based on technology stack similarity.

**Use Cases**:
- Tech stack matching
- Tool compatibility
- Platform alignment

**Configuration**:
```python
from apps.search.recommendations.signals import TechnologySimilaritySignal

signal = TechnologySimilaritySignal(
    params={"target_technologies": ["react", "node.js"]}
)
```

**Scoring**:
- Overlap ratio between target and available technologies
- Bonus for exact match
- Range: [0, 1]

### 4. Industry Similarity Signal

**Description**: Scores items based on industry alignment.

**Use Cases**:
- Industry-specific recommendations
- Sector matching
- Domain expertise alignment

**Configuration**:
```python
from apps.search.recommendations.signals import IndustrySimilaritySignal

signal = IndustrySimilaritySignal(
    params={"target_industry": "technology", "target_sector": "software"}
)
```

**Scoring**:
- Exact industry match = 1.0
- Same sector = 0.7
- Different = 0.0
- Range: [0, 1]

### 5. Location Similarity Signal

**Description**: Scores items based on geographic proximity and location preferences.

**Use Cases**:
- Location-based recommendations
- Remote work compatibility
- Regional matching

**Configuration**:
```python
from apps.search.recommendations.signals import LocationSimilaritySignal

signal = LocationSimilaritySignal(
    params={"target_location": "San Francisco, CA"}
)
```

**Scoring**:
- Exact match = 1.0
- Same city = 0.8
- Same country/region = 0.5
- Different = 0.0
- Range: [0, 1]

### 6. Behavior Hooks Signal

**Description**: Scores items based on user behavior patterns like click history, application history, saved items, etc.

**Use Cases**:
- Personalized recommendations
- Preference learning
- Behavior-based ranking

**Configuration**:
```python
from apps.search.recommendations.signals import BehaviorHooksSignal

signal = BehaviorHooksSignal(
    params={
        "viewed_items": ["item_1", "item_2"],
        "similar_companies": ["Google", "Microsoft"],
        "similar_skills": ["python", "django"],
    }
)
```

**Scoring**:
- Viewed item = +0.3
- Similar items = +0.5
- Similar company = +0.4
- Similar skills = +0.3
- Range: [0, 1]

### 7. Recommendation Diversity Signal

**Description**: Scores items based on how much they add diversity to the recommendation set.

**Use Cases**:
- Diversity optimization
- Novelty enhancement
- Coverage improvement

**Configuration**:
```python
from apps.search.recommendations.signals import RecommendationDiversitySignal

signal = RecommendationDiversitySignal(
    params={"current_recommendations": [...]}
)
```

**Scoring**:
- New company = +0.3
- New skills = +0.3 * (new_skills / total_skills)
- New location = +0.2
- New industry = +0.2
- Range: [0, 1]

### 8. Novelty Signal

**Description**: Scores items based on how novel they are to the user (items the user hasn't seen before).

**Use Cases**:
- Discovery recommendations
- Exploration optimization
- Avoiding repetition

**Configuration**:
```python
from apps.search.recommendations.signals import NoveltySignal

signal = NoveltySignal(
    params={
        "seen_items": ["item_1", "item_2"],
        "seen_companies": ["Google"],
    }
)
```

**Scoring**:
- Already seen = 0.0
- Similar items seen = 0.3
- Same company seen = 0.5
- Completely new = 1.0
- Range: [0, 1]

### 9. Coverage Signal

**Description**: Scores items based on how well they cover the user's preferences and requirements.

**Use Cases**:
- Preference satisfaction
- Requirement coverage
- Comprehensive matching

**Configuration**:
```python
from apps.search.recommendations.signals import CoverageSignal

signal = CoverageSignal(
    params={
        "required_skills": ["python", "django"],
        "preferred_locations": ["San Francisco", "New York"],
        "preferred_employment_types": ["full-time", "remote"],
        "salary_range": {"min": 100000, "max": 150000},
    }
)
```

**Scoring**:
- Skill coverage = 0.4 * (skill_overlap / required_skills)
- Location coverage = 0.3 if location matches
- Employment type coverage = 0.2 if type matches
- Salary coverage = 0.1 if salary in range
- Range: [0, 1]

## Using Signals

### Register with Ranking Pipeline

```python
from apps.search.ranking.pipeline import RankingPipeline
from apps.search.recommendations.signals import SkillSimilaritySignal

pipeline = RankingPipeline()
pipeline.register_signal("skill_similarity", SkillSimilaritySignal())
```

### Create Pipeline Stage with Signals

```python
from apps.search.ranking.pipeline import PipelineStage, NormalizationMethod

stage = PipelineStage(
    name="recommendation_signals",
    signals=["skill_similarity", "career_progression"],
    weights={
        "skill_similarity": 0.7,
        "career_progression": 0.3,
    },
    normalization=NormalizationMethod.MIN_MAX,
)
pipeline.add_stage(stage)
```

### Signal Composition

Combine multiple signals in a stage:

```python
stage = PipelineStage(
    name="hybrid_signals",
    signals=[
        "skill_similarity",
        "career_progression",
        "location_similarity",
        "behavior_hooks",
    ],
    weights={
        "skill_similarity": 0.4,
        "career_progression": 0.2,
        "location_similarity": 0.2,
        "behavior_hooks": 0.2,
    },
)
```

## Signal Weights

Tune signal weights based on your use case:

```python
# For skill-focused recommendations
weights = {
    "skill_similarity": 0.6,
    "career_progression": 0.2,
    "technology_similarity": 0.2,
}

# For behavior-focused recommendations
weights = {
    "behavior_hooks": 0.5,
    "novelty": 0.3,
    "recommendation_diversity": 0.2,
}

# For balanced recommendations
weights = {
    "skill_similarity": 0.25,
    "career_progression": 0.25,
    "location_similarity": 0.25,
    "behavior_hooks": 0.25,
}
```

## Signal Normalization

Different normalization methods can be applied:

```python
from apps.search.ranking.pipeline import NormalizationMethod

# Min-max normalization (default)
normalization = NormalizationMethod.MIN_MAX

# Z-score normalization
normalization = NormalizationMethod.Z_SCORE

# Logistic normalization
normalization = NormalizationMethod.LOGISTIC

# Softmax normalization
normalization = NormalizationMethod.SOFTMAX
```

## Best Practices

### 1. Use Appropriate Signals

Choose signals that match your recommendation goal:
- **Skill matching**: Skill similarity, Technology similarity
- **Career growth**: Career progression
- **Personalization**: Behavior hooks, Novelty
- **Diversity**: Recommendation diversity, Novelty
- **Coverage**: Coverage signal

### 2. Tune Weights

Experiment with different weight combinations to find the optimal balance.

### 3. Monitor Signal Performance

Use the monitoring system to track signal effectiveness:

```python
signal_metrics = monitor.get_recommendation_metrics()
```

### 4. Combine with Base Signals

Use recommendation signals alongside base ranking signals:

```python
stage = PipelineStage(
    name="full_ranking",
    signals=[
        # Base signals
        "lexical",
        "metadata",
        "freshness",
        # Recommendation signals
        "skill_similarity",
        "career_progression",
    ],
)
```

### 5. Consider Context

Different contexts may require different signal weights:
- **Job search**: Higher weight on skill similarity
- **Candidate discovery**: Higher weight on novelty
- **Career growth**: Higher weight on career progression

## Performance Considerations

- **Skill Similarity**: Moderate cost, can be cached
- **Career Progression**: Low cost
- **Technology Similarity**: Moderate cost
- **Industry Similarity**: Low cost
- **Location Similarity**: Low cost
- **Behavior Hooks**: Moderate cost, depends on history size
- **Recommendation Diversity**: High cost for large sets
- **Novelty**: Low cost with efficient lookups
- **Coverage**: Moderate cost

## Future Enhancements

The signal framework is ready for:

- **Embedding Similarity**: Add embedding-based similarity signals
- **Graph-based Signals**: Add network-based signals
- **Time-decay Signals**: Add time-aware signals
- **Cross-domain Signals**: Add signals spanning multiple domains
- **ML-based Signals**: Add learned signal weights
