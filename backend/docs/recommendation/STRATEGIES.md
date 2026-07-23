# Recommendation Strategies

## Overview

Recommendation strategies define different approaches to generating recommendations. The engine supports multiple strategies that can be used individually or combined through strategy composition.

## Available Strategies

### 1. Content-Based Strategy

**Description**: Generates recommendations based on content similarity between items. Uses features like skills, experience, education, and other content attributes.

**Use Cases**:
- Finding candidates with similar skills to a job
- Finding jobs similar to a candidate's profile
- Finding resumes with similar content

**Configuration**:
```python
from apps.search.recommendations.strategies import ContentBasedStrategy, StrategyConfig

config = StrategyConfig(
    strategy_name="content_based",
    enabled=True,
    weight=1.0,
    params={
        "skill_weight": 0.4,
        "experience_weight": 0.3,
        "education_weight": 0.2,
        "location_weight": 0.1,
    }
)
strategy = ContentBasedStrategy(config)
```

### 2. Similarity-Based Strategy

**Description**: Generates recommendations based on similarity metrics like cosine similarity, Jaccard similarity, etc.

**Use Cases**:
- Finding similar candidates
- Finding similar jobs
- Finding similar companies

**Configuration**:
```python
from apps.search.recommendations.strategies import SimilarityBasedStrategy

strategy = SimilarityBasedStrategy(weight=0.8)
```

### 3. Rule-Based Strategy

**Description**: Generates recommendations based on configurable business rules.

**Use Cases**:
- Enforcing hiring policies
- Applying diversity requirements
- Implementing priority rules

**Configuration**:
```python
from apps.search.recommendations.strategies import RuleBasedStrategy

strategy = RuleBasedStrategy(
    params={
        "rules": [
            {"type": "priority_company", "value": ["Google", "Microsoft"]},
            {"type": "min_experience", "value": 3},
        ]
    }
)
```

### 4. Popularity-Based Strategy

**Description**: Generates recommendations based on popularity metrics like views, applications, saves, etc.

**Use Cases**:
- Trending jobs
- Popular candidates
- High-engagement content

**Configuration**:
```python
from apps.search.recommendations.strategies import PopularityBasedStrategy

strategy = PopularityBasedStrategy(
    params={
        "view_weight": 0.3,
        "application_weight": 0.5,
        "save_weight": 0.2,
    }
)
```

### 5. Freshness-Based Strategy

**Description**: Generates recommendations based on recency/freshness of items.

**Use Cases**:
- Recently posted jobs
- Recently active candidates
- New opportunities

**Configuration**:
```python
from apps.search.recommendations.strategies import FreshnessBasedStrategy

strategy = FreshnessBasedStrategy(
    params={
        "decay_days": 30,
        "decay_rate": 0.5,
    }
)
```

### 6. Hybrid Strategy

**Description**: Combines multiple strategies using composition and weighting.

**Use Cases**:
- Balanced recommendations
- A/B testing different approaches
- Adaptive recommendations

**Configuration**:
```python
from apps.search.recommendations.strategies import (
    HybridRecommendationStrategy,
    ContentBasedStrategy,
    PopularityBasedStrategy,
)

strategies = [
    ContentBasedStrategy(weight=0.7),
    PopularityBasedStrategy(weight=0.3),
]
hybrid = HybridRecommendationStrategy(strategies)
```

## Strategy Composition

Strategy composition allows you to combine multiple strategies with different composition methods.

### Weighted Composition

Combines strategies using weighted averaging of scores:

```python
from apps.search.recommendations.strategies import StrategyComposition

composition = StrategyComposition(strategies)
candidates = composition.compose(
    entity_id="job_123",
    context={},
    limit=10,
    method="weighted",
)
```

### Rank Composition

Combines strategies using rank fusion (reciprocal rank):

```python
candidates = composition.compose(
    entity_id="job_123",
    context={},
    limit=10,
    method="rank",
)
```

### Hybrid Composition

Uses a combination of weighted and rank-based methods:

```python
candidates = composition.compose(
    entity_id="job_123",
    context={},
    limit=10,
    method="hybrid",
)
```

## Strategy Weighting

Strategy weighting allows dynamic adjustment of strategy weights based on performance.

### Static Weighting

Set fixed weights for strategies:

```python
from apps.search.recommendations.strategies import StrategyWeighting

weighting = StrategyWeighting(
    initial_weights={
        "content": 1.0,
        "popularity": 0.5,
        "freshness": 0.3,
    }
)
```

### Dynamic Weighting

Adjust weights based on performance:

```python
# Record performance
weighting.adjust_weight("content", performance=0.8, learning_rate=0.1)

# Get current weight
weight = weighting.get_weight("content")

# Get performance score
perf_score = weighting.get_performance_score("content")
```

## Strategy Selection

### Default Strategy

Use the default hybrid strategy:

```python
request = RecommendationRequest(
    recommendation_type=RecommendationType.CANDIDATE,
    entity_id="job_123",
    strategy="hybrid",  # Default
)
```

### Custom Strategy

Use a specific strategy:

```python
request = RecommendationRequest(
    recommendation_type=RecommendationType.CANDIDATE,
    entity_id="job_123",
    strategy="content_based",
)
```

### A/B Testing

Use strategy composition for A/B testing:

```python
# Group A: Content-based only
strategies_a = [ContentBasedStrategy(weight=1.0)]
composition_a = StrategyComposition(strategies_a)

# Group B: Hybrid approach
strategies_b = [
    ContentBasedStrategy(weight=0.7),
    PopularityBasedStrategy(weight=0.3),
]
composition_b = StrategyComposition(strategies_b)

# Compare performance
```

## Best Practices

### 1. Choose the Right Strategy

- **Content-based**: Best for skill/experience matching
- **Popularity-based**: Best for discovery and trending content
- **Freshness-based**: Best for time-sensitive recommendations
- **Hybrid**: Best for balanced recommendations

### 2. Tune Weights

Experiment with different weight combinations to find the optimal balance for your use case.

### 3. Monitor Performance

Use the monitoring system to track strategy performance and adjust weights dynamically.

### 4. Use Composition

Combine multiple strategies to get the benefits of each approach.

### 5. Consider Context

Different contexts may require different strategies (e.g., job search vs. candidate discovery).

## Performance Considerations

- **Content-based**: Moderate computational cost
- **Similarity-based**: Higher computational cost for large datasets
- **Rule-based**: Low computational cost
- **Popularity-based**: Low computational cost with caching
- **Freshness-based**: Low computational cost
- **Hybrid**: Higher computational cost, but better quality

## Future Enhancements

The strategy framework is ready for:

- **Collaborative Filtering**: Add collaborative filtering strategies
- **Embedding-Based**: Add vector similarity strategies
- **ML-Based**: Add neural network strategies
- **Context-Aware**: Add context-aware strategies
- **Multi-Armed Bandit**: Add exploration-exploitation strategies
