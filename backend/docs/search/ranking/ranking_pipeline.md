# Ranking Pipeline

## Overview

The Ranking Pipeline is the core orchestrator of the MatchHire ranking system. It executes multiple ranking stages in sequence, applying signals with configurable weights and normalization methods to produce a unified ranking score.

## Pipeline Architecture

### Pipeline Stages

The pipeline consists of multiple stages, each applying a set of signals:

```
┌─────────────────────────────────────────────────────────────┐
│                    Ranking Pipeline                          │
├─────────────────────────────────────────────────────────────┤
│  Stage 1: Lexical Relevance                                 │
│  - LexicalSignal (weight: 1.0)                              │
│  - Normalization: min_max                                   │
├─────────────────────────────────────────────────────────────┤
│  Stage 2: Domain Matching                                   │
│  - SkillOverlapSignal (weight: 2.0)                         │
│  - ExperienceOverlapSignal (weight: 1.5)                    │
│  - EducationOverlapSignal (weight: 1.0)                      │
│  - Normalization: min_max                                   │
├─────────────────────────────────────────────────────────────┤
│  Stage 3: Quality Signals                                   │
│  - QualitySignal (weight: 1.0)                              │
│  - ProfileCompletenessSignal (weight: 1.0)                  │
│  - CandidateActivitySignal (weight: 1.5)                    │
│  - Normalization: min_max                                   │
├─────────────────────────────────────────────────────────────┤
│  Stage 4: Business Rules                                    │
│  - BusinessRuleSignal (weight: 3.0)                         │
│  - Normalization: none                                      │
└─────────────────────────────────────────────────────────────┘
```

### Pipeline Execution

1. **Input**: Search results from Query Engine
2. **Stage Execution**: Execute each enabled stage in sequence
3. **Signal Scoring**: Calculate scores for each signal in the stage
4. **Normalization**: Normalize scores using configured method
5. **Weight Application**: Apply weights to normalized scores
6. **Score Accumulation**: Accumulate scores across stages
7. **Sorting**: Sort results by final score
8. **Output**: Ranked results with score breakdowns

## Configuration

### PipelineConfig

```python
from apps.search.ranking.pipeline import PipelineConfig

config = PipelineConfig(
    enable_parallel_scoring=True,      # Enable parallel signal execution
    max_parallel_workers=4,            # Maximum parallel workers
    enable_early_termination=False,    # Enable early termination
    early_termination_threshold=0.95, # Threshold for early termination
    max_scoring_depth=1000,           # Maximum documents to score
    enable_lazy_scoring=False,         # Enable lazy evaluation
    cache_enabled=True,                # Enable signal caching
    cache_ttl_seconds=300,            # Cache TTL in seconds
    enable_diagnostics=True,          # Enable pipeline diagnostics
)
```

### PipelineStage

```python
from apps.search.ranking.pipeline import PipelineStage, NormalizationMethod

stage = PipelineStage(
    name="skill_matching",
    signals=["skill_overlap", "experience_overlap"],
    weights={
        "skill_overlap": 2.0,
        "experience_overlap": 1.5,
    },
    normalization=NormalizationMethod.MIN_MAX,
    enabled=True,
    condition=lambda ctx: ctx.get("entity_type") == "candidate",
)
```

## Normalization Methods

### Min-Max Normalization

Scales scores to [0, 1] range:

```
normalized = (score - min) / (max - min)
```

**Use Case**: When scores have known bounds

### Z-Score Normalization

Standardizes scores to mean=0, std=1:

```
normalized = (score - mean) / std
```

**Use Case**: When scores follow normal distribution

### Logistic Normalization

Applies logistic function:

```
normalized = 1 / (1 + exp(-k * score))
```

**Use Case**: When scores need to be bounded in (0, 1)

### Tanh Normalization

Applies hyperbolic tangent:

```
normalized = (tanh(score) + 1) / 2
```

**Use Case**: When scores need symmetric scaling

### Softmax Normalization

Converts scores to probability distribution:

```
normalized = exp(score / temperature) / sum(exp(score / temperature))
```

**Use Case**: When scores need to sum to 1

### Binary Normalization

Converts scores to binary values:

```
normalized = 1 if score >= threshold else 0
```

**Use Case**: When scores represent binary decisions

## Performance Optimization

### Parallel Scoring

Signals within a stage can be executed in parallel:

```python
config = PipelineConfig(
    enable_parallel_scoring=True,
    max_parallel_workers=4,
)
```

**Benefits:**
- Reduces latency for CPU-bound signal calculations
- Utilizes multiple CPU cores
- Configurable worker count

**Trade-offs:**
- Increased memory usage
- Thread synchronization overhead
- Not beneficial for I/O-bound signals

### Caching

Signal scores are cached to avoid recomputation:

```python
config = PipelineConfig(
    cache_enabled=True,
    cache_ttl_seconds=300,
)
```

**Cache Key Components:**
- Signal name
- Document IDs
- Query string
- Context metadata

**Cache Invalidation:**
- TTL-based expiration
- Manual cache clearing
- Entity-type invalidation

### Early Termination

Stop scoring when top results are stable:

```python
config = PipelineConfig(
    enable_early_termination=True,
    early_termination_threshold=0.95,
)
```

**Termination Condition:**
- Top N results have stable scores
- Score confidence exceeds threshold
- Remaining results unlikely to change order

### Lazy Scoring

Score only top results initially:

```python
config = PipelineConfig(
    enable_lazy_scoring=True,
    max_scoring_depth=100,
)
```

**Benefits:**
- Reduces initial ranking latency
- Scores remaining results on demand
- Better for large result sets

## Diagnostics

The pipeline provides detailed diagnostics:

```python
ranked_results, diagnostics = pipeline.execute(results, context)

print(f"Total time: {diagnostics.total_time_ms}ms")
print(f"Stage times: {diagnostics.stage_times_ms}")
print(f"Signal times: {diagnostics.signal_times_ms}")
print(f"Cache hits: {diagnostics.cache_hits}")
print(f"Cache misses: {diagnostics.cache_misses}")
print(f"Parallel workers: {diagnostics.parallel_workers_used}")
```

### PipelineDiagnostics

- `total_time_ms`: Total pipeline execution time
- `stage_times_ms`: Time per stage
- `signal_times_ms`: Time per signal
- `cache_hits`: Number of cache hits
- `cache_misses`: Number of cache misses
- `early_termination_triggered`: Whether early termination occurred
- `parallel_workers_used`: Number of parallel workers used
- `errors`: List of errors encountered

## Usage Examples

### Basic Pipeline Usage

```python
from apps.search.ranking.pipeline import RankingPipeline, PipelineConfig
from apps.search.ranking.signals import LexicalSignal, SkillOverlapSignal

# Create pipeline
config = PipelineConfig(cache_enabled=True)
pipeline = RankingPipeline(config=config)

# Register signals
pipeline.register_signal("lexical", LexicalSignal())
pipeline.register_signal("skill_overlap", SkillOverlapSignal())

# Add stage
from apps.search.ranking.pipeline import PipelineStage, NormalizationMethod

stage = PipelineStage(
    name="matching",
    signals=["lexical", "skill_overlap"],
    weights={"lexical": 1.0, "skill_overlap": 2.0},
    normalization=NormalizationMethod.MIN_MAX,
)
pipeline.add_stage(stage)

# Execute
results = [
    {"id": "1", "title": "Software Engineer", "_score": 1.0},
    {"id": "2", "title": "Data Scientist", "_score": 0.5},
]
context = {"query": "engineer", "required_skills": ["Python"]}

ranked_results, diagnostics = pipeline.execute(results, context)
```

### Conditional Stages

```python
def only_for_candidates(context):
    return context.get("entity_type") == "candidate"

stage = PipelineStage(
    name="candidate_specific",
    signals=["skill_overlap"],
    weights={"skill_overlap": 2.0},
    condition=only_for_candidates,
)
pipeline.add_stage(stage)
```

### Custom Normalization

```python
from apps.search.ranking.pipeline import ScoreNormalizer

scores = [1.0, 2.0, 3.0, 4.0, 5.0]

# Min-max with custom bounds
normalized = ScoreNormalizer.min_max(scores, min_val=0.0, max_val=10.0)

# Z-score
normalized = ScoreNormalizer.z_score(scores)

# Logistic with custom k
normalized = ScoreNormalizer.logistic(scores, k=2.0)
```

## Best Practices

### Signal Weighting

- Assign higher weights to more important signals
- Balance weights to prevent signal dominance
- Test weight combinations with A/B testing

### Stage Ordering

- Place fast signals in early stages
- Place expensive signals in later stages
- Use conditional stages for entity-specific signals

### Normalization Selection

- Use min-max for bounded scores
- Use z-score for normally distributed scores
- Use logistic for unbounded positive scores
- Use binary for threshold-based decisions

### Performance Tuning

- Enable parallel scoring for CPU-bound signals
- Use caching for frequently executed queries
- Enable early termination for large result sets
- Use lazy scoring for initial page loads

## Troubleshooting

### Pipeline Slow

**Symptoms**: High latency in ranking

**Solutions**:
- Enable parallel scoring
- Increase cache TTL
- Enable early termination
- Reduce max_scoring_depth
- Profile slow signals

### Inconsistent Rankings

**Symptoms**: Same query produces different rankings

**Solutions**:
- Check cache configuration
- Verify signal determinism
- Review business rules
- Check random factors in signals

### Memory Issues

**Symptoms**: High memory usage

**Solutions**:
- Reduce max_scoring_depth
- Reduce max_parallel_workers
- Reduce cache size
- Enable lazy scoring

### Cache Not Working

**Symptoms**: Low cache hit rate

**Solutions**:
- Verify cache is enabled
- Check cache TTL
- Review cache key generation
- Check for cache invalidation
