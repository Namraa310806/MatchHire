"""
Recruitment Recommendation Engine for MatchHire.

This module provides a production-grade recommendation system that reuses the
existing Hybrid Ranking framework. The engine generates candidates using the
Query Engine and delegates ranking to the Ranking Pipeline.

Key components:
- RecommendationEngine: Central engine for all recommendations
- RecommendationRequest/Response: Request/response models
- RecommendationContext: Context for recommendation generation
- RecommendationStrategy: Different recommendation strategies
- RecommendationProvider: Provider-independent recommendation interface
- RecommendationRegistry: Registry for recommendation providers
- RecommendationPipeline: Pipeline for candidate generation, ranking, diversification
- RecommendationResult: Result from recommendation generation
- RecommendationSignals: Reuse existing ranking signals + recommendation-specific signals
- Diversification: Ensure diverse recommendations
- Explanation: Explainable recommendations
- LearningHooks: Interfaces for future ML-based recommendations
- RecommendationCache: Performance optimization
- RecommendationMonitoring: Metrics and observability
"""

from .core import (
    RecommendationEngine,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationContext,
    RecommendationResult,
)
from .strategies import (
    RecommendationStrategy,
    ContentBasedStrategy,
    SimilarityBasedStrategy,
    RuleBasedStrategy,
    PopularityBasedStrategy,
    FreshnessBasedStrategy,
    HybridRecommendationStrategy,
    StrategyComposition,
    StrategyWeighting,
)
from .providers import (
    RecommendationProvider,
    RecommendationRegistry,
    CandidateRecommendationProvider,
    JobRecommendationProvider,
    RelatedEntityRecommendationProvider,
)
from .pipeline import (
    RecommendationPipeline,
    PipelineConfig,
    PipelineStage,
    PipelineDiagnostics,
)
from .candidate_recommendations import (
    CandidateRecommendationType,
    CandidateRecommendationGenerator,
    BestCandidatesForJob,
    SimilarCandidates,
    RecentlyActiveCandidates,
    HighQualityCandidates,
    PassiveCandidates,
    InternalTalentSuggestions,
    SkillGapCandidates,
    AlternativeCandidates,
)
from .job_recommendations import (
    JobRecommendationType,
    JobRecommendationGenerator,
    BestJobsForCandidate,
    RelatedJobs,
    RecentlyPostedJobs,
    TrendingJobs,
    NearbyJobs,
    SalaryCompatibleJobs,
    CareerProgressionJobs,
    AlternativeJobs,
)
from .related_entities import (
    RelatedEntityType,
    RelatedEntityGenerator,
    SimilarCompanies,
    RelatedRecruiters,
    RelatedSkills,
    RelatedResumes,
    RelatedApplications,
    RelatedInterviews,
    CrossEntityRecommendations,
)
from .signals import (
    SkillSimilaritySignal,
    CareerProgressionSignal,
    TechnologySimilaritySignal,
    IndustrySimilaritySignal,
    LocationSimilaritySignal,
    BehaviorHooksSignal,
    RecommendationDiversitySignal,
    NoveltySignal,
    CoverageSignal,
)
from .diversification import (
    DiversificationEngine,
    DiversificationConfig,
    SkillDiversifier,
    CompanyDiversifier,
    LocationDiversifier,
    ExperienceDiversifier,
    SalaryDiversifier,
    IndustryDiversifier,
    DeduplicationEngine,
)
from .explanation import (
    RecommendationExplanation,
    ExplanationBuilder,
    WhyRecommendedExplanation,
    SharedSkillsExplanation,
    MatchingExperienceExplanation,
    BusinessRulesExplanation,
    RankingSignalsExplanation,
    ConfidenceScoreExplanation,
    RecommendationSourceExplanation,
)
from .learning_hooks import (
    RecommendationLearningHook,
    ClickHook,
    ApplicationHook,
    HireHook,
    BookmarkHook,
    IgnoredRecommendationHook,
    RecruiterActionHook,
    CollaborativeFilteringHook,
    MLRecommendationHook,
)
from .cache import (
    RecommendationCache,
    CacheKey,
    CacheStats,
)
from .monitoring import (
    RecommendationMonitor,
    RecommendationMetrics,
    StrategyMetrics,
    PipelineMetrics,
    DiversificationMetrics,
)
from .config import (
    RecommendationConfig,
    StrategyConfig,
    PipelineConfig as RecPipelineConfig,
    DiversificationConfig as DivConfig,
    CacheConfig as RecCacheConfig,
    MonitoringConfig as RecMonitoringConfig,
)

__all__ = [
    # Core
    "RecommendationEngine",
    "RecommendationRequest",
    "RecommendationResponse",
    "RecommendationContext",
    "RecommendationResult",
    # Strategies
    "RecommendationStrategy",
    "ContentBasedStrategy",
    "SimilarityBasedStrategy",
    "RuleBasedStrategy",
    "PopularityBasedStrategy",
    "FreshnessBasedStrategy",
    "HybridRecommendationStrategy",
    "StrategyComposition",
    "StrategyWeighting",
    # Providers
    "RecommendationProvider",
    "RecommendationRegistry",
    "CandidateRecommendationProvider",
    "JobRecommendationProvider",
    "RelatedEntityRecommendationProvider",
    # Pipeline
    "RecommendationPipeline",
    "PipelineConfig",
    "PipelineStage",
    "PipelineDiagnostics",
    # Candidate Recommendations
    "CandidateRecommendationType",
    "CandidateRecommendationGenerator",
    "BestCandidatesForJob",
    "SimilarCandidates",
    "RecentlyActiveCandidates",
    "HighQualityCandidates",
    "PassiveCandidates",
    "InternalTalentSuggestions",
    "SkillGapCandidates",
    "AlternativeCandidates",
    # Job Recommendations
    "JobRecommendationType",
    "JobRecommendationGenerator",
    "BestJobsForCandidate",
    "RelatedJobs",
    "RecentlyPostedJobs",
    "TrendingJobs",
    "NearbyJobs",
    "SalaryCompatibleJobs",
    "CareerProgressionJobs",
    "AlternativeJobs",
    # Related Entities
    "RelatedEntityType",
    "RelatedEntityGenerator",
    "SimilarCompanies",
    "RelatedRecruiters",
    "RelatedSkills",
    "RelatedResumes",
    "RelatedApplications",
    "RelatedInterviews",
    "CrossEntityRecommendations",
    # Signals
    "SkillSimilaritySignal",
    "CareerProgressionSignal",
    "TechnologySimilaritySignal",
    "IndustrySimilaritySignal",
    "LocationSimilaritySignal",
    "BehaviorHooksSignal",
    "RecommendationDiversitySignal",
    "NoveltySignal",
    "CoverageSignal",
    # Diversification
    "DiversificationEngine",
    "DiversificationConfig",
    "SkillDiversifier",
    "CompanyDiversifier",
    "LocationDiversifier",
    "ExperienceDiversifier",
    "SalaryDiversifier",
    "IndustryDiversifier",
    "DeduplicationEngine",
    # Explanation
    "RecommendationExplanation",
    "ExplanationBuilder",
    "WhyRecommendedExplanation",
    "SharedSkillsExplanation",
    "MatchingExperienceExplanation",
    "BusinessRulesExplanation",
    "RankingSignalsExplanation",
    "ConfidenceScoreExplanation",
    "RecommendationSourceExplanation",
    # Learning Hooks
    "RecommendationLearningHook",
    "ClickHook",
    "ApplicationHook",
    "HireHook",
    "BookmarkHook",
    "IgnoredRecommendationHook",
    "RecruiterActionHook",
    "CollaborativeFilteringHook",
    "MLRecommendationHook",
    # Cache
    "RecommendationCache",
    "CacheKey",
    "CacheStats",
    # Monitoring
    "RecommendationMonitor",
    "RecommendationMetrics",
    "StrategyMetrics",
    "PipelineMetrics",
    "DiversificationMetrics",
    # Config
    "RecommendationConfig",
    "StrategyConfig",
    "RecPipelineConfig",
    "DivConfig",
    "RecCacheConfig",
    "RecMonitoringConfig",
]
