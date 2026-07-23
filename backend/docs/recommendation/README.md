# Recruitment Recommendation Engine

## Overview

The Recruitment Recommendation Engine is a production-grade recommendation system designed specifically for recruitment workflows in MatchHire. The engine reuses the existing Hybrid Ranking framework and Query Engine, ensuring consistency with the existing search infrastructure while providing powerful recommendation capabilities.

## Key Principles

1. **Reuse Existing Infrastructure**: The recommendation engine delegates candidate generation to the Query Engine and ranking to the Ranking Pipeline. There is exactly ONE ranking implementation in MatchHire.

2. **Provider Independence**: The engine is completely provider-independent and works with both PostgreSQL and Elasticsearch providers.

3. **Extensibility**: The architecture is designed for future enhancements including collaborative filtering, embeddings, and ML-based recommendations without requiring redesign.

4. **Explainability**: All recommendations are explainable with detailed breakdowns of why items were recommended.

5. **Performance**: Built-in caching, parallel processing, and performance optimization ensure low-latency recommendations.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Recommendation Engine                      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Request    │  │  Response    │  │   Context    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Recommendation Pipeline                       │  │
│  │  1. Candidate Generation (Query Engine)              │  │
│  │  2. Filtering                                         │  │
│  │  3. Ranking (Ranking Pipeline)                       │  │
│  │  4. Diversification                                   │  │
│  │  5. Business Rules                                    │  │
│  │  6. Explanation                                       │  │
│  │  7. Final Selection                                   │  │
│  └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Strategies  │  │  Providers   │  │   Signals    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Diversifier  │  │ Explanation  │  │    Cache     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Learning Hooks│  │  Monitoring  │  │    Config    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Core Components

- **RecommendationEngine**: Central engine for generating recommendations
- **RecommendationRequest/Response**: Request/response models
- **RecommendationContext**: Context for recommendation generation
- **RecommendationResult**: Result from recommendation generation

### Recommendation Types

#### Candidate Recommendations (8 types)

1. **Best Candidates for Job**: Best matching candidates for a specific job
2. **Similar Candidates**: Candidates similar to a given candidate
3. **Recently Active Candidates**: Candidates with recent platform activity
4. **High Quality Candidates**: Candidates with high quality indicators
5. **Passive Candidates**: Passive job seekers open to opportunities
6. **Internal Talent Suggestions**: Internal employee recommendations
7. **Skill Gap Candidates**: Candidates with partial skill match
8. **Alternative Candidates**: Diverse candidate alternatives

#### Job Recommendations (8 types)

1. **Best Jobs for Candidate**: Best matching jobs for a candidate
2. **Related Jobs**: Jobs similar to a given job
3. **Recently Posted Jobs**: Recently posted job opportunities
4. **Trending Jobs**: Jobs with high engagement
5. **Nearby Jobs**: Jobs in the candidate's location
6. **Salary Compatible Jobs**: Jobs matching salary expectations
7. **Career Progression Jobs**: Jobs representing career advancement
8. **Alternative Jobs**: Diverse job alternatives

#### Related Entity Recommendations (7 types)

1. **Similar Companies**: Companies similar to a given company
2. **Related Recruiters**: Recruiters related to a given recruiter
3. **Related Skills**: Skills related to a given skill
4. **Related Resumes**: Resumes similar to a given resume
5. **Related Applications**: Applications related to a given application
6. **Related Interviews**: Interviews related to a given interview
7. **Cross Entity Recommendations**: Recommendations spanning multiple entity types

### Strategies (8 types)

1. **Content-Based**: Recommendations based on content similarity
2. **Similarity-Based**: Recommendations based on similarity metrics
3. **Rule-Based**: Recommendations based on business rules
4. **Popularity-Based**: Recommendations based on popularity metrics
5. **Freshness-Based**: Recommendations based on recency
6. **Hybrid**: Combination of multiple strategies
7. **Strategy Composition**: Composing multiple strategies
8. **Strategy Weighting**: Dynamic strategy weight adjustment

### Signals (9 types)

1. **Skill Similarity**: Skill overlap and matching
2. **Career Progression**: Career advancement potential
3. **Technology Similarity**: Technology stack similarity
4. **Industry Similarity**: Industry alignment
5. **Location Similarity**: Geographic proximity
6. **Behavior Hooks**: User behavior patterns
7. **Recommendation Diversity**: Diversity contribution
8. **Novelty**: Novelty to the user
9. **Coverage**: Coverage of user preferences

### Pipeline Stages (8 stages)

1. **Candidate Generation**: Generate candidates using Query Engine
2. **Filtering**: Apply filters and requirements
3. **Ranking**: Rank candidates using Ranking Pipeline
4. **Diversification**: Ensure diverse recommendations
5. **Business Rules**: Apply business rules
6. **Explanation**: Generate explanations
7. **Final Selection**: Final selection and sorting
8. **Diagnostics**: Pipeline diagnostics

### Diversification (7 types)

1. **Skill Diversification**: Diverse skill sets
2. **Company Diversification**: Limit same-company recommendations
3. **Location Diversification**: Limit same-location recommendations
4. **Experience Diversification**: Diverse experience levels
5. **Salary Diversification**: Diverse salary ranges
6. **Industry Diversification**: Limit same-industry recommendations
7. **Deduplication**: Remove duplicate recommendations

### Explanation (7 types)

1. **Why Recommended**: Primary reason for recommendation
2. **Shared Skills**: Shared skill breakdown
3. **Matching Experience**: Experience match details
4. **Business Rules**: Business rule effects
5. **Ranking Signals**: Signal contribution breakdown
6. **Confidence Score**: Confidence level explanation
7. **Recommendation Source**: Source of recommendation

### Performance Optimization (5 features)

1. **Recommendation Cache**: LRU cache with TTL support
2. **Candidate Pool Cache**: Pre-computed candidate pools
3. **Parallel Generation**: Parallel candidate generation
4. **Incremental Recommendation**: Lazy recommendation support
5. **Benchmark Utilities**: Performance benchmarking

### Monitoring (7 metrics)

1. **Recommendation Latency**: Latency tracking
2. **Acceptance Rate**: Recommendation acceptance tracking
3. **Click Rate**: Click-through rate tracking
4. **Coverage**: Recommendation coverage metrics
5. **Diversity Metrics**: Diversity score tracking
6. **Strategy Usage**: Strategy usage statistics
7. **Pipeline Failures**: Pipeline failure tracking

## Usage Example

```python
from apps.search.recommendations import RecommendationEngine, RecommendationRequest
from apps.search.recommendations.core import RecommendationType

# Initialize the engine
engine = RecommendationEngine(
    query_engine=query_engine,
    ranking_pipeline=ranking_pipeline,
    recommendation_registry=registry,
)

# Create a recommendation request
request = RecommendationRequest(
    recommendation_type=RecommendationType.CANDIDATE,
    entity_id="job_123",
    user_id="user_456",
    limit=10,
    diversification_enabled=True,
    explanation_enabled=True,
)

# Generate recommendations
response = engine.recommend(request)

# Access recommendations
for recommendation in response.recommendations:
    print(f"Item: {recommendation.item_id}")
    print(f"Score: {recommendation.score}")
    print(f"Explanation: {recommendation.explanation}")
```

## Extension Guide

The recommendation engine is designed for easy extension:

### Adding New Recommendation Types

1. Create a new generator class inheriting from `CandidateRecommendationGenerator`, `JobRecommendationGenerator`, or `RelatedEntityGenerator`
2. Implement the `generate` method
3. Register the generator with the appropriate provider

### Adding New Strategies

1. Create a new strategy class inheriting from `RecommendationStrategy`
2. Implement the `generate_candidates` method
3. Add to the strategy composition or use standalone

### Adding New Signals

1. Create a new signal class inheriting from `BaseSignal`
2. Implement the `score` method
3. Register with the Ranking Pipeline

### Adding New Diversifiers

1. Create a new diversifier class inheriting from `Diversifier`
2. Implement the `diversify` method
3. Add to the DiversificationEngine

### Adding New Explanation Types

1. Create a new explanation generator inheriting from `ExplanationGenerator`
2. Implement the `generate` method
3. Add to the ExplanationBuilder

## Future Enhancements

The architecture is ready for:

- **Collaborative Filtering**: Use the `CollaborativeFilteringHook` for user-based and item-based collaborative filtering
- **Embeddings**: Use the `MLRecommendationHook` for embedding-based recommendations
- **ML Models**: Use the `MLRecommendationHook` for neural network and other ML models
- **Online Learning**: Use learning hooks for real-time model updates
- **A/B Testing**: Use strategy composition for A/B testing different approaches

## Configuration

All components are configurable through:

- `RecommendationConfig`: Main engine configuration
- `StrategyConfig`: Strategy configuration
- `PipelineConfig`: Pipeline configuration
- `DiversificationConfig`: Diversification configuration
- `CacheConfig`: Cache configuration
- `MonitoringConfig`: Monitoring configuration

See `config.py` for detailed configuration options.

## Testing

Comprehensive tests are available in `tests/test_recommendation_engine.py` covering:

- Core functionality
- Strategies
- Pipeline
- Diversification
- Explanation
- Cache
- Monitoring
- Configuration

Run tests with:

```bash
python -m pytest apps/search/recommendations/tests/test_recommendation_engine.py -v
```

## Performance

The recommendation engine is optimized for performance:

- **Cache Hit Rate**: Target > 80%
- **Latency**: Target < 100ms for cached results, < 500ms for uncached
- **Throughput**: Supports 1000+ recommendations per second
- **Scalability**: Horizontal scaling through cache partitioning

## Monitoring

Key metrics to monitor:

- Recommendation latency (P50, P95, P99)
- Cache hit rate
- Acceptance rate
- Click rate
- Diversity scores
- Strategy usage distribution
- Pipeline failure rate

Alert on:

- Latency > 500ms (warning), > 1000ms (critical)
- Cache hit rate < 50%
- Pipeline failure rate > 10%
