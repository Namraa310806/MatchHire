# Recommendation Engine Architecture

## System Overview

The Recruitment Recommendation Engine is a modular, extensible system designed to provide intelligent recommendations for recruitment workflows. The architecture follows a layered approach, separating concerns and enabling independent evolution of components.

## Design Principles

### 1. Single Ranking Implementation

The recommendation engine **reuses** the existing Ranking Pipeline. There is exactly ONE ranking implementation in MatchHire. The recommendation engine:

- Uses the Query Engine to generate candidate items
- Delegates ranking to the existing Ranking Pipeline
- Applies recommendation-specific signals that extend the base ranking signals
- Never duplicates ranking logic

### 2. Provider Independence

The engine is completely provider-independent:

- Works with PostgreSQL and Elasticsearch providers
- Abstracts provider-specific details through the Query Engine
- No provider-specific code in recommendation logic
- Easy to add new providers without changing recommendation code

### 3. Separation of Concerns

Each component has a single, well-defined responsibility:

- **Engine**: Orchestrates the recommendation process
- **Providers**: Generate candidates for different recommendation types
- **Strategies**: Implement different recommendation approaches
- **Pipeline**: Executes the recommendation stages
- **Signals**: Score items based on specific criteria
- **Diversifiers**: Ensure diversity in recommendations
- **Explainers**: Generate explanations for recommendations
- **Cache**: Improve performance through caching
- **Monitor**: Track metrics and performance

### 4. Extensibility

The architecture is designed for future enhancements:

- Learning hooks for collaborative filtering and ML
- Strategy composition for A/B testing
- Plugin architecture for custom components
- Interface-based design for easy extension

## Component Architecture

### Layer 1: Core Models

```
RecommendationRequest
    ├── recommendation_type: RecommendationType
    ├── entity_id: str
    ├── user_id: Optional[str]
    ├── recruiter_id: Optional[str]
    ├── limit: int
    ├── filters: Dict[str, Any]
    ├── context: Dict[str, Any]
    ├── strategy: Optional[str]
    ├── diversification_enabled: bool
    └── explanation_enabled: bool

RecommendationResponse
    ├── recommendations: List[RecommendationResult]
    ├── total: int
    ├── took_ms: float
    ├── recommendation_type: RecommendationType
    ├── strategy_used: Optional[str]
    ├── diversification_applied: bool
    ├── pipeline_diagnostics: Optional[Dict[str, Any]]
    └── metadata: Dict[str, Any]

RecommendationContext
    ├── user_id: Optional[str]
    ├── recruiter_id: Optional[str]
    ├── entity_type: Optional[str]
    ├── entity_id: Optional[str]
    ├── user_preferences: Dict[str, Any]
    ├── recruiter_preferences: Dict[str, Any]
    ├── business_rules: Dict[str, Any]
    ├── session_context: Dict[str, Any]
    └── temporal_context: Dict[str, Any]

RecommendationResult
    ├── item_id: str
    ├── item_type: str
    ├── score: float
    ├── rank: int
    ├── source: RecommendationSource
    ├── item_data: Dict[str, Any]
    ├── explanation: Optional[Dict[str, Any]]
    ├── signals: Dict[str, float]
    └── metadata: Dict[str, Any]
```

### Layer 2: Recommendation Engine

```
RecommendationEngine
    ├── _query_engine: QueryEngine
    ├── _ranking_pipeline: RankingPipeline
    ├── _recommendation_registry: RecommendationRegistry
    ├── _pipeline: RecommendationPipeline
    ├── _diversification_engine: DiversificationEngine
    ├── _explanation_builder: ExplanationBuilder
    ├── _cache: RecommendationCache
    └── _monitor: RecommendationMonitor

Methods:
    ├── recommend(request, use_cache) -> RecommendationResponse
    ├── _build_context(request) -> RecommendationContext
    ├── _generate_candidates(request, context, provider) -> List[Dict]
    ├── _rank_candidates(candidates, context) -> List[Dict]
    ├── _add_explanations(candidates, context) -> None
    ├── _build_recommendation_results(candidates, context) -> List[RecommendationResult]
    ├── _apply_pagination(recommendations, limit, offset) -> List[RecommendationResult]
    ├── get_cache_stats() -> Dict[str, Any]
    ├── clear_cache() -> None
    └── get_monitoring_stats() -> Dict[str, Any]
```

### Layer 3: Providers

```
RecommendationProvider (Abstract)
    ├── _query_engine: QueryEngine
    └── _config: Dict[str, Any]

Methods:
    ├── generate_candidates(entity_id, context, limit, filters) -> List[Dict]

Implementations:
    ├── CandidateRecommendationProvider
    ├── JobRecommendationProvider
    └── RelatedEntityRecommendationProvider

RecommendationRegistry (Singleton)
    ├── _providers: Dict[RecommendationProviderType, RecommendationProvider]
    
Methods:
    ├── register_provider(provider) -> None
    ├── unregister_provider(provider_type) -> None
    ├── get_provider(provider_type) -> Optional[RecommendationProvider]
    ├── get_provider_by_name(recommendation_type) -> Optional[RecommendationProvider]
    ├── list_providers() -> List[RecommendationProviderType]
    └── is_registered(provider_type) -> bool
```

### Layer 4: Strategies

```
RecommendationStrategy (Abstract)
    ├── _config: StrategyConfig
    
Methods:
    ├── generate_candidates(entity_id, context, limit) -> List[Dict]

Implementations:
    ├── ContentBasedStrategy
    ├── SimilarityBasedStrategy
    ├── RuleBasedStrategy
    ├── PopularityBasedStrategy
    ├── FreshnessBasedStrategy
    └── HybridRecommendationStrategy

StrategyComposition
    ├── _strategies: List[RecommendationStrategy]
    
Methods:
    ├── compose(entity_id, context, limit, method) -> List[Dict]
    ├── _weighted_composition(entity_id, context, limit) -> List[Dict]
    ├── _rank_composition(entity_id, context, limit) -> List[Dict]
    ├── _hybrid_composition(entity_id, context, limit) -> List[Dict]
    ├── _weighted_combine(strategy_results) -> List[Dict]
    └── _rank_combine(strategy_results) -> List[Dict]

StrategyWeighting
    ├── _weights: Dict[str, float]
    ├── _performance_history: Dict[str, List[float]]
    
Methods:
    ├── get_weight(strategy_name) -> float
    ├── set_weight(strategy_name, weight) -> None
    ├── adjust_weight(strategy_name, performance, learning_rate) -> None
    ├── get_performance_score(strategy_name) -> Optional[float]
    └── reset_weights() -> None
```

### Layer 5: Pipeline

```
RecommendationPipeline
    ├── _query_engine: QueryEngine
    ├── _ranking_pipeline: RankingPipeline
    ├── _config: PipelineConfig
    ├── _stages: List[PipelineStage]
    ├── _cache: Dict[str, Any]
    └── _diagnostics: PipelineDiagnostics

Methods:
    ├── generate_candidates(request, context, provider) -> List[Dict]
    ├── _execute_candidate_generation(request, context, provider) -> List[Dict]
    ├── _execute_filtering(candidates, context) -> List[Dict]
    ├── _execute_ranking(candidates, context) -> List[Dict]
    ├── _execute_business_rules(candidates, context) -> List[Dict]
    ├── _execute_explanation(candidates, context) -> List[Dict]
    ├── _execute_final_selection(candidates, context) -> List[Dict]
    ├── get_diagnostics() -> PipelineDiagnostics
    └── to_dict() -> Dict[str, Any]

Pipeline Stages:
    1. Candidate Generation (Query Engine)
    2. Filtering
    3. Ranking (Ranking Pipeline)
    4. Diversification
    5. Business Rules
    6. Explanation
    7. Final Selection
    8. Diagnostics
```

### Layer 6: Signals

```
BaseSignal (from ranking.signals)
    ├── _config: SignalConfig
    
Methods:
    ├── score(document, context) -> float

Recommendation Signals:
    ├── SkillSimilaritySignal
    ├── CareerProgressionSignal
    ├── TechnologySimilaritySignal
    ├── IndustrySimilaritySignal
    ├── LocationSimilaritySignal
    ├── BehaviorHooksSignal
    ├── RecommendationDiversitySignal
    ├── NoveltySignal
    └── CoverageSignal
```

### Layer 7: Diversification

```
Diversifier (Abstract)
    ├── _config: DiversificationConfig
    
Methods:
    ├── diversify(candidates, context) -> List[Dict]

Implementations:
    ├── SkillDiversifier
    ├── CompanyDiversifier
    ├── LocationDiversifier
    ├── ExperienceDiversifier
    ├── SalaryDiversifier
    ├── IndustryDiversifier

DeduplicationEngine
    ├── _config: DiversificationConfig
    
Methods:
    ├── deduplicate(candidates, context) -> List[Dict]

DiversificationEngine
    ├── _config: DiversificationConfig
    ├── _diversifiers: List[Diversifier]
    └── _deduplication_engine: DeduplicationEngine
    
Methods:
    ├── diversify(candidates, context) -> List[Dict]
    ├── add_diversifier(diversifier) -> None
    ├── remove_diversifier(diversification_type) -> None
    └── get_config() -> DiversificationConfig
```

### Layer 8: Explanation

```
ExplanationGenerator (Abstract)
Methods:
    ├── generate(candidate, context) -> RecommendationExplanation

Implementations:
    ├── WhyRecommendedExplanation
    ├── SharedSkillsExplanation
    ├── MatchingExperienceExplanation
    ├── BusinessRulesExplanation
    ├── RankingSignalsExplanation
    ├── ConfidenceScoreExplanation
    └── RecommendationSourceExplanation

ExplanationBuilder
    ├── _explanation_generators: Dict[ExplanationType, ExplanationGenerator]
    
Methods:
    ├── build_explanation(candidate, context) -> Dict[str, Any]
    └── add_explanation_generator(exp_type, generator) -> None
```

### Layer 9: Learning Hooks

```
RecommendationLearningHook (Abstract)
    ├── _config: Dict[str, Any]
    ├── _enabled: bool
    
Methods:
    ├── process_feedback(event) -> None
    ├── is_enabled() -> bool
    ├── enable() -> None
    └── disable() -> None

Implementations:
    ├── ClickHook
    ├── ApplicationHook
    ├── HireHook
    ├── BookmarkHook
    ├── IgnoredRecommendationHook
    ├── RecruiterActionHook
    ├── CollaborativeFilteringHook
    └── MLRecommendationHook

LearningHookRegistry
    ├── _hooks: Dict[FeedbackType, List[RecommendationLearningHook]]
    
Methods:
    ├── register_hook(hook) -> None
    ├── unregister_hook(feedback_type, hook) -> None
    ├── process_feedback(event) -> None
    ├── get_hooks(feedback_type) -> List[RecommendationLearningHook]
    ├── enable_hook(feedback_type, hook_index) -> None
    └── disable_hook(feedback_type, hook_index) -> None
```

### Layer 10: Cache

```
RecommendationCache
    ├── _config: Dict[str, Any]
    ├── _max_size: int
    ├── _default_ttl: int
    ├── _cache: OrderedDict[str, CacheEntry]
    ├── _lock: RLock
    └── _stats: CacheStats
    
Methods:
    ├── get(request, context) -> Optional[Any]
    ├── set(request, context, value, ttl) -> None
    ├── delete(request, context) -> bool
    ├── clear() -> None
    ├── invalidate_by_entity(entity_id) -> int
    ├── invalidate_by_user(user_id) -> int
    ├── cleanup_expired() -> int
    ├── get_stats() -> CacheStats
    └── get_size() -> int

CandidatePoolCache
    ├── _config: Dict[str, Any]
    ├── _max_size: int
    ├── _default_ttl: int
    ├── _cache: Dict[str, tuple]
    └── _lock: RLock
    
Methods:
    ├── get(pool_key) -> Optional[List[Dict]]
    ├── set(pool_key, candidates, ttl) -> None
    ├── clear() -> None
    └── get_size() -> int
```

### Layer 11: Monitoring

```
RecommendationMonitor
    ├── _lock: RLock
    ├── _recommendation_metrics: RecommendationMetrics
    ├── _strategy_metrics: StrategyMetrics
    ├── _pipeline_metrics: PipelineMetrics
    ├── _diversification_metrics: DiversificationMetrics
    ├── _metrics_history: List[tuple]
    └── _max_history_size: int
    
Methods:
    ├── record_recommendation(recommendation_type, count, latency_ms) -> None
    ├── record_cache_hit() -> None
    ├── record_cache_miss() -> None
    ├── record_strategy_usage(strategy_name, performance, latency_ms) -> None
    ├── record_pipeline_execution(stage_times, ...) -> None
    ├── record_stage_failure(stage_name) -> None
    ├── record_diversification(diversity_scores, duplicates_removed) -> None
    ├── record_acceptance(accepted) -> None
    ├── record_click(clicked) -> None
    ├── get_recommendation_metrics() -> RecommendationMetrics
    ├── get_strategy_metrics() -> StrategyMetrics
    ├── get_pipeline_metrics() -> PipelineMetrics
    ├── get_diversification_metrics() -> DiversificationMetrics
    ├── get_stats() -> Dict[str, Any]
    ├── reset() -> None
    ├── snapshot_metrics() -> None
    └── get_metrics_history(limit) -> List[Dict[str, Any]]
```

## Data Flow

### Recommendation Generation Flow

```
1. User Request
   ↓
2. RecommendationRequest
   ↓
3. RecommendationEngine.recommend()
   ↓
4. Build RecommendationContext
   ↓
5. Check Cache (if enabled)
   ↓
6. Get RecommendationProvider
   ↓
7. RecommendationPipeline.generate_candidates()
   ├─ 7.1 Candidate Generation (Query Engine)
   ├─ 7.2 Filtering
   ├─ 7.3 Ranking (Ranking Pipeline)
   ├─ 7.4 Diversification
   ├─ 7.5 Business Rules
   ├─ 7.6 Explanation
   └─ 7.7 Final Selection
   ↓
8. Build RecommendationResults
   ↓
9. Apply Pagination
   ↓
10. Build RecommendationResponse
   ↓
11. Cache Result (if enabled)
   ↓
12. Record Metrics
   ↓
13. Return Response
```

### Feedback Learning Flow

```
1. User Action (Click, Application, Hire, etc.)
   ↓
2. Create FeedbackEvent
   ↓
3. LearningHookRegistry.process_feedback()
   ↓
4. Route to appropriate hooks
   ↓
5. Hook.process_feedback()
   ├─ 5.1 Update user preferences
   ├─ 5.2 Update collaborative filtering matrices
   ├─ 5.3 Update ML models (if configured)
   └─ 5.4 Update strategy weights
   ↓
6. Improve future recommendations
```

## Integration Points

### With Query Engine

- Candidate generation uses Query Engine's search capabilities
- Leverages Query DSL for complex queries
- Benefits from Query Engine's performance optimizations

### With Ranking Pipeline

- Ranking delegated to existing Ranking Pipeline
- Reuses ranking signals (lexical, metadata, freshness, etc.)
- Adds recommendation-specific signals
- No duplication of ranking logic

### With Search Providers

- Works with PostgreSQL and Elasticsearch providers
- Provider-agnostic through Query Engine abstraction
- No provider-specific code in recommendation logic

## Scalability Considerations

### Horizontal Scaling

- Cache can be partitioned across instances
- Stateless recommendation generation (except cache)
- Monitoring can be aggregated across instances

### Vertical Scaling

- Parallel candidate generation
- Parallel signal scoring
- Configurable worker counts

### Performance Optimization

- Multi-level caching (recommendation cache + candidate pool cache)
- Lazy ranking for large result sets
- Incremental recommendation generation
- Parallel diversification

## Security Considerations

- Access control through user/recruiter context
- Business rules for sensitive recommendations
- Audit trail through monitoring
- No exposure of internal ranking logic

## Error Handling

- Graceful degradation on component failures
- Fallback to default strategies
- Error logging and monitoring
- Circuit breaker pattern for external dependencies
