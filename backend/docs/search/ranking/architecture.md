# Ranking Architecture

## Overview

The MatchHire Ranking System is a production-grade, provider-independent ranking layer that sits above the Query Engine and below application services. It combines multiple ranking signals into a unified score while maintaining full explainability, configurability, and extensibility.

## Design Principles

1. **Provider Independence**: The ranking system works with any search provider (PostgreSQL, Elasticsearch) through the existing SearchProvider interface.

2. **Explainability**: Every ranking decision can be explained through detailed score breakdowns, signal contributions, and business rule applications.

3. **Configurability**: All ranking behavior is configurable through profiles, signal weights, and business rules without code changes.

4. **Extensibility**: New signals, fusion strategies, and ranking profiles can be added without modifying core architecture.

5. **Performance**: Built-in caching, parallel scoring, and lazy evaluation ensure production-grade performance.

6. **No LLM Dependency**: Pure deterministic ranking based on signals, rules, and metadata. No LLM reasoning or recommendation engines.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Services                      │
│  (Job Search, Candidate Search, Resume Search, etc.)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ranking Layer                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Ranking Profiles                         │  │
│  │  (Recruiter, Candidate, Job Discovery, Resume, Admin) │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Business Rules Engine                    │  │
│  │  (Pin, Hide, Promote, Block, Priority, Sponsored)    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Ranking Pipeline                         │  │
│  │  (Stages, Signals, Normalization, Fusion)             │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Hybrid Search Engine                      │  │
│  │  (Lexical, Metadata, Semantic, Vector Strategies)     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Score Explanation                         │  │
│  │  (Signal Breakdown, Boosts, Business Rules)          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Query Engine                             │
│  (DSL, Filters, Facets, Aggregations, Highlighting)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Search Providers                         │
│  (PostgreSQL, Elasticsearch, Future: Vector, Semantic)      │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Ranking Pipeline

The `RankingPipeline` is the core orchestrator that:

- Executes ranking stages in sequence
- Applies signals with configurable weights
- Normalizes scores across different ranges
- Supports parallel scoring for performance
- Provides pipeline diagnostics

**Key Features:**
- Modular stage-based architecture
- Configurable normalization methods (min-max, z-score, logistic, etc.)
- Parallel signal execution with configurable worker count
- Early termination for performance optimization
- Built-in caching for signal scores

### 2. Ranking Signals

Signals are reusable scoring components that calculate scores for documents based on specific criteria:

**Core Signals:**
- `LexicalSignal`: Text matching and relevance
- `MetadataSignal`: Structured field matching
- `BusinessRuleSignal`: Business rule application
- `FreshnessSignal`: Time-based decay
- `PopularitySignal`: Engagement metrics
- `QualitySignal`: Quality indicators

**Domain-Specific Signals:**
- `SkillOverlapSignal`: Skill matching for candidates/jobs
- `ExperienceOverlapSignal`: Experience compatibility
- `EducationOverlapSignal`: Education level matching
- `LocationProximitySignal`: Geographic proximity
- `SalaryCompatibilitySignal`: Salary range matching
- `EmploymentTypeCompatibilitySignal`: Employment type matching
- `CompanyPreferenceSignal`: Company preferences
- `RecruiterPreferenceSignal`: Recruiter-specific preferences
- `ProfileCompletenessSignal`: Profile completeness scoring
- `CandidateActivitySignal`: Recent activity tracking
- `JobFreshnessSignal`: Job posting freshness
- `ApplicationHistorySignal`: Historical application patterns

### 3. Hybrid Search Engine

The `HybridSearchEngine` combines multiple search strategies using various fusion algorithms:

**Search Strategies:**
- `LexicalStrategy`: Traditional full-text search
- `MetadataStrategy`: Structured field search
- `SemanticStrategy`: Future semantic embedding search (interface only)
- `VectorStrategy`: Future vector similarity search (interface only)

**Fusion Algorithms:**
- `WeightedFusion`: Weighted averaging of scores
- `RankFusion`: Rank-based combination
- `ReciprocalRankFusion`: RRF algorithm (k=60 by default)
- `CondorcetFusion`: Pairwise comparison voting

### 4. Business Rules Engine

The `BusinessRulesEngine` applies configurable business rules:

**Rule Types:**
- `PinnedResultRule`: Pin results to specific positions
- `HiddenResultRule`: Hide results from search
- `PromotedJobRule`: Promote specific jobs
- `BlockedCandidateRule`: Block specific candidates
- `PriorityCompanyRule`: Boost priority companies
- `SponsoredRule`: Mark and boost sponsored content
- `ManualBoostRule`: Custom field-based boosts
- `CustomRule`: User-defined custom rules

**Features:**
- Priority-based rule execution
- Conflict resolution
- Rule validation
- Enable/disable individual rules

### 5. Score Explanation

The `ScoreExplanation` system provides detailed breakdowns:

**Components:**
- `SignalContribution`: Individual signal scores and weights
- `BoostExplanation`: Applied boosts and reasons
- `BusinessRuleExplanation`: Rules applied and their effects
- `RankingBreakdown`: Complete score calculation breakdown

**Output Formats:**
- API-ready JSON
- UI-friendly summaries
- Log-formatted details
- Statistical summaries

### 6. Ranking Profiles

Pre-configured profiles for different use cases:

**Available Profiles:**
- `RecruiterSearchProfile`: Optimized for recruiter candidate search
- `CandidateSearchProfile`: Optimized for candidate job search
- `JobDiscoveryProfile`: Optimized for job exploration
- `ResumeSearchProfile`: Optimized for resume/CV search
- `AdminSearchProfile`: Comprehensive search with diagnostics

**Profile Features:**
- Different signal weightings per profile
- Profile-specific pipeline stages
- Custom normalization methods
- Metadata for profile identification

### 7. Learning Hooks

Interfaces for future ML-based reranking (no implementation):

**Hook Types:**
- `ClickFeedbackHook`: Track result clicks
- `ApplicationFeedbackHook`: Track job applications
- `RecruiterInteractionHook`: Track recruiter interactions
- `SavedJobHook`: Track saved jobs
- `IgnoredJobHook`: Track ignored jobs
- `InterviewOutcomeHook`: Track interview results
- `MLRerankingHook`: Interface for future ML models

**Purpose:**
- Collect feedback for future ML training
- Provide structure for ML integration
- No model training in this phase

### 8. Performance Optimization

**Caching:**
- `RankingCache`: LRU cache with TTL
- Signal score caching
- Pipeline result caching
- Configurable cache size and TTL

**Parallel Execution:**
- Parallel signal scoring
- Configurable worker count
- Thread-safe execution

**Lazy Evaluation:**
- Configurable lazy scoring
- Early termination
- Maximum scoring depth

### 9. Monitoring

**Metrics Collected:**
- Signal execution metrics (latency, cache hits, errors)
- Pipeline metrics (execution time, stage times, parallel vs sequential)
- Cache metrics (hit rate, miss rate, evictions)
- Ranking metrics (latency percentiles, document counts)

**Monitoring Interface:**
- `RankingMonitor`: Central metrics collector
- Real-time statistics
- Historical data retention
- Summary reports

## Data Flow

### Ranking Execution Flow

1. **Search Request**: Application service initiates search
2. **Profile Selection**: Select appropriate ranking profile
3. **Query Execution**: Query Engine executes search through provider
4. **Business Rules**: Apply business rules (pin, hide, promote, block)
5. **Pipeline Execution**: Execute ranking pipeline stages
   - Stage 1: Lexical relevance
   - Stage 2: Domain-specific matching
   - Stage 3: Quality signals
   - Stage 4: Business rule boosts
6. **Signal Scoring**: Calculate individual signal scores
7. **Normalization**: Normalize scores using configured method
8. **Fusion**: Combine normalized scores with weights
9. **Explanation**: Generate score explanation
10. **Return Results**: Return ranked results with explanations

### Hybrid Search Flow

1. **Strategy Selection**: Select search strategies to use
2. **Parallel Execution**: Execute strategies in parallel
3. **Result Collection**: Collect results from each strategy
4. **Fusion**: Apply fusion algorithm to combine results
5. **Ranking**: Apply ranking pipeline to fused results
6. **Return**: Return hybrid search results

## Integration Points

### With Query Engine

The ranking layer integrates with the Query Engine through:

- `SearchExecutionContext`: Context passed to ranking
- `EngineResult`: Results returned from Query Engine
- Ranking hooks in Query Engine for pre/post ranking

### With Search Providers

The ranking layer is provider-independent:

- Works with any `SearchProvider` implementation
- No provider-specific logic in ranking
- Uses provider's `_score` for lexical relevance

### With Application Services

Application services interact with ranking through:

- Profile selection based on use case
- Context passing for ranking
- Explanation retrieval for UI display

## Configuration

### Pipeline Configuration

```python
from apps.search.ranking.pipeline import PipelineConfig

config = PipelineConfig(
    enable_parallel_scoring=True,
    max_parallel_workers=4,
    enable_early_termination=False,
    max_scoring_depth=1000,
    cache_enabled=True,
    cache_ttl_seconds=300,
    enable_diagnostics=True,
)
```

### Signal Configuration

```python
from apps.search.ranking.signals import SignalConfig

signal_config = SignalConfig(
    enabled=True,
    weight=2.0,
    normalization="min_max",
    params={"scale_days": 30},
)
```

### Profile Configuration

Profiles are pre-configured but can be customized:

```python
from apps.search.ranking.profiles import RankingProfileRegistry

registry = RankingProfileRegistry()
profile = registry.get_profile("candidate_search")
```

## Extensibility

### Adding New Signals

1. Extend `BaseSignal` class
2. Implement `score()` method
3. Register signal in pipeline
4. Add to profile stages

### Adding New Fusion Algorithms

1. Extend `FusionAlgorithm` class
2. Implement `fuse()` method
3. Register in HybridSearchEngine

### Adding New Business Rules

1. Extend `BusinessRule` class
2. Implement `matches()` and `apply()` methods
3. Register in BusinessRulesEngine

### Adding New Profiles

1. Extend `RankingProfile` class
2. Configure stages and weights
3. Register in RankingProfileRegistry

## Performance Considerations

### Caching Strategy

- Cache signal scores to avoid recomputation
- Cache pipeline results for identical queries
- TTL-based expiration to ensure freshness
- LRU eviction for memory management

### Parallel Execution

- Parallel signal scoring for CPU-bound operations
- Configurable worker count based on resources
- Thread-safe execution with proper locking

### Early Termination

- Stop scoring when top results are stable
- Configurable threshold for early termination
- Reduces latency for large result sets

### Lazy Evaluation

- Score only top N results initially
- Score remaining results on demand
- Reduces initial ranking latency

## Security Considerations

### Business Rules

- Rule validation before application
- Priority-based execution to prevent conflicts
- Audit logging of rule applications

### Score Explanation

- No sensitive data in explanations
- Configurable detail level for different users
- Admin-only access to full diagnostics

### Caching

- Cache key includes user context for personalization
- Separate cache per entity type
- Cache invalidation on data changes

## Future Extensions

### Semantic Search

- `SemanticStrategy` interface ready for implementation
- Vector embeddings for semantic similarity
- Fusion with lexical search

### ML Reranking

- `MLRerankingHook` interface ready for implementation
- Learning-to-rank models
- Personalized ranking based on user behavior

### Advanced Business Rules

- Time-based rule scheduling
- A/B testing for rules
- Rule performance analytics

### Real-time Personalization

- User-specific signal weights
- Dynamic profile selection
- Real-time feedback integration
