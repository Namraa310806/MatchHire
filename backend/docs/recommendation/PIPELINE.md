# Recommendation Pipeline

## Overview

The Recommendation Pipeline is a modular, multi-stage pipeline that processes recommendations through several stages. The pipeline reuses the existing Query Engine for candidate generation and the Ranking Pipeline for ranking, ensuring consistency with the existing search infrastructure.

## Pipeline Stages

### Stage 1: Candidate Generation

**Purpose**: Generate candidate items using the Query Engine.

**Process**:
1. Build search context from recommendation request
2. Execute search through Query Engine
3. Retrieve candidate items from the search provider
4. Add metadata (source, stage information)

**Configuration**:
```python
from apps.search.recommendations.pipeline import PipelineConfig

config = PipelineConfig(
    enable_candidate_generation=True,
    max_candidates=1000,
)
```

**Output**: List of candidate items with basic metadata

### Stage 2: Filtering

**Purpose**: Apply filters and requirements to candidates.

**Process**:
1. Check business rule filters (blocked IDs, etc.)
2. Verify minimum requirements (experience, location, etc.)
3. Apply custom filters from request
4. Remove candidates that don't meet criteria

**Configuration**:
```python
config = PipelineConfig(
    enable_filtering=True,
)
```

**Output**: Filtered list of candidates

### Stage 3: Ranking

**Purpose**: Rank candidates using the Ranking Pipeline.

**Process**:
1. Build ranking context from recommendation context
2. Execute Ranking Pipeline with registered signals
3. Apply signal weights and normalization
4. Sort candidates by final score

**Configuration**:
```python
config = PipelineConfig(
    enable_ranking=True,
    enable_parallel_scoring=True,
    max_parallel_workers=4,
)
```

**Output**: Ranked list of candidates with scores

### Stage 4: Diversification

**Purpose**: Ensure diverse recommendations across multiple dimensions.

**Process**:
1. Apply skill diversification
2. Apply company diversification
3. Apply location diversification
4. Apply experience diversification
5. Apply salary diversification
6. Apply industry diversification
7. Remove duplicates

**Configuration**:
```python
from apps.search.recommendations.diversification import DiversificationConfig

div_config = DiversificationConfig(
    enable_skill_diversification=True,
    enable_company_diversification=True,
    max_same_company=3,
)
```

**Output**: Diversified list of candidates

### Stage 5: Business Rules

**Purpose**: Apply business rules to recommendations.

**Process**:
1. Apply pinned results (move to top)
2. Apply promoted results (boost score)
3. Apply priority company boosts
4. Apply custom business rules

**Configuration**:
```python
config = PipelineConfig(
    enable_business_rules=True,
)
```

**Output**: Candidates with business rules applied

### Stage 6: Explanation

**Purpose**: Generate explanations for recommendations.

**Process**:
1. Generate why recommended explanation
2. Generate shared skills explanation
3. Generate matching experience explanation
4. Generate business rules explanation
5. Generate ranking signals explanation
6. Generate confidence score explanation
7. Generate recommendation source explanation

**Configuration**:
```python
config = PipelineConfig(
    enable_explanation=True,
)
```

**Output**: Candidates with explanations attached

### Stage 7: Final Selection

**Purpose**: Final selection and sorting of recommendations.

**Process**:
1. Sort by final score
2. Assign final ranks
3. Apply pagination limits
4. Return final list

**Configuration**:
```python
config = PipelineConfig(
    enable_final_selection=True,
)
```

**Output**: Final list of recommendations

### Stage 8: Diagnostics

**Purpose**: Collect pipeline diagnostics for monitoring.

**Process**:
1. Record stage execution times
2. Record candidate counts per stage
3. Record cache hits/misses
4. Record errors and failures
5. Record parallel worker usage

**Configuration**:
```python
config = PipelineConfig(
    enable_diagnostics=True,
)
```

**Output**: Pipeline diagnostics object

## Pipeline Configuration

### Basic Configuration

```python
from apps.search.recommendations.pipeline import PipelineConfig

config = PipelineConfig(
    # Stage enablement
    enable_candidate_generation=True,
    enable_filtering=True,
    enable_ranking=True,
    enable_diversification=True,
    enable_business_rules=True,
    enable_explanation=True,
    enable_final_selection=True,
    
    # Performance
    enable_parallel_scoring=True,
    max_parallel_workers=4,
    max_candidates=1000,
    enable_early_termination=False,
    early_termination_threshold=0.95,
    
    # Cache
    cache_enabled=True,
    cache_ttl_seconds=300,
    
    # Diagnostics
    enable_diagnostics=True,
)
```

### Custom Stages

You can add custom stages to the pipeline:

```python
from apps.search.recommendations.pipeline import PipelineStage, PipelineStageType

custom_stage = PipelineStage(
    name="custom_filtering",
    stage_type=PipelineStageType.FILTERING,
    enabled=True,
    config={
        "custom_param": "value",
    },
)

pipeline.add_stage(custom_stage)
```

### Conditional Stages

Stages can be conditional based on context:

```python
def should_execute(context):
    return context.get("user_tier") == "premium"

stage = PipelineStage(
    name="premium_features",
    stage_type=PipelineStageType.BUSINESS_RULES,
    enabled=True,
    condition=should_execute,
)
```

## Pipeline Diagnostics

The pipeline provides detailed diagnostics:

```python
diagnostics = pipeline.get_diagnostics()

print(f"Total time: {diagnostics.total_time_ms}ms")
print(f"Candidates generated: {diagnostics.candidates_generated}")
print(f"Candidates filtered: {diagnostics.candidates_filtered}")
print(f"Candidates ranked: {diagnostics.candidates_ranked}")
print(f"Candidates diversified: {diagnostics.candidates_diversified}")
print(f"Stage times: {diagnostics.stage_times_ms}")
print(f"Cache hits: {diagnostics.cache_hits}")
print(f"Cache misses: {diagnostics.cache_misses}")
```

## Performance Optimization

### Parallel Scoring

Enable parallel scoring for faster ranking:

```python
config = PipelineConfig(
    enable_parallel_scoring=True,
    max_parallel_workers=4,
)
```

### Early Termination

Enable early termination for top results:

```python
config = PipelineConfig(
    enable_early_termination=True,
    early_termination_threshold=0.95,
)
```

### Lazy Ranking

Enable lazy ranking for large result sets:

```python
config = PipelineConfig(
    enable_lazy_ranking=True,
)
```

### Caching

Enable caching at the pipeline level:

```python
config = PipelineConfig(
    cache_enabled=True,
    cache_ttl_seconds=300,
)
```

## Error Handling

The pipeline handles errors gracefully:

- Individual stage failures don't stop the pipeline
- Errors are logged in diagnostics
- Fallback to default behavior on failure
- Continue with remaining stages

## Best Practices

### 1. Enable Diagnostics in Development

Always enable diagnostics in development to understand pipeline behavior:

```python
config = PipelineConfig(
    enable_diagnostics=True,
)
```

### 2. Tune Parallel Workers

Adjust parallel workers based on your hardware:

```python
import multiprocessing

workers = min(4, multiprocessing.cpu_count())
config = PipelineConfig(
    max_parallel_workers=workers,
)
```

### 3. Set Appropriate Limits

Set reasonable limits to prevent excessive resource usage:

```python
config = PipelineConfig(
    max_candidates=1000,
)
```

### 4. Monitor Stage Times

Monitor stage times to identify bottlenecks:

```python
diagnostics = pipeline.get_diagnostics()
slow_stages = [
    stage for stage, time_ms in diagnostics.stage_times_ms.items()
    if time_ms > 100
]
```

### 5. Use Caching Wisely

Enable caching for frequently accessed recommendations:

```python
config = PipelineConfig(
    cache_enabled=True,
    cache_ttl_seconds=300,  # 5 minutes
)
```

## Integration with Ranking Pipeline

The recommendation pipeline integrates seamlessly with the existing Ranking Pipeline:

```python
# The recommendation pipeline uses the ranking pipeline
ranked_candidates, ranking_diagnostics = ranking_pipeline.execute(
    results=candidates,
    context=ranking_context,
)

# Ranking signals are applied automatically
# Recommendation-specific signals can be added
ranking_pipeline.register_signal("skill_similarity", SkillSimilaritySignal())
ranking_pipeline.register_signal("career_progression", CareerProgressionSignal())
```

## Monitoring

Monitor pipeline performance through the monitoring system:

```python
# Record pipeline execution
monitor.record_pipeline_execution(
    stage_times=stage_times,
    candidates_generated=len(candidates),
    candidates_filtered=len(filtered),
    candidates_ranked=len(ranked),
    candidates_diversified=len(diversified),
)

# Get pipeline metrics
pipeline_metrics = monitor.get_pipeline_metrics()
print(f"Total executions: {pipeline_metrics.total_pipeline_executions}")
print(f"Failure rate: {pipeline_metrics.failure_rate}")
print(f"Avg stage times: {pipeline_metrics.avg_stage_times_ms}")
```
