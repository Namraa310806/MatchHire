"""
Hybrid Search & Intelligent Ranking Framework for MatchHire.

This module provides a production-grade ranking system that combines multiple
ranking signals into a unified score. The ranking layer sits above the Query Engine
and is completely provider-independent.

Key components:
- RankingPipeline: Modular pipeline for combining multiple scoring signals
- RankingSignals: Reusable scoring signals (lexical, metadata, freshness, etc.)
- HybridSearch: Framework for fusing multiple search strategies
- BusinessRulesEngine: Configurable ranking rules (pinning, boosting, blocking)
- ScoreExplanation: Explainable ranking with detailed score breakdowns
- RankingProfiles: Pre-configured ranking profiles for different use cases
- LearningHooks: Interfaces for future ML-based reranking
- RankingCache: Performance optimization through caching
- RankingMonitoring: Metrics and observability for ranking operations
"""

from .pipeline import (
    RankingPipeline,
    PipelineConfig,
    PipelineStage,
    ScoreNormalizer,
    NormalizationMethod,
)
from .signals import (
    BaseSignal,
    LexicalSignal,
    MetadataSignal,
    BusinessRuleSignal,
    FreshnessSignal,
    PopularitySignal,
    QualitySignal,
    SkillOverlapSignal,
    ExperienceOverlapSignal,
    EducationOverlapSignal,
    LocationProximitySignal,
    SalaryCompatibilitySignal,
    EmploymentTypeCompatibilitySignal,
    CompanyPreferenceSignal,
    RecruiterPreferenceSignal,
    ProfileCompletenessSignal,
    CandidateActivitySignal,
    JobFreshnessSignal,
    ApplicationHistorySignal,
)
from .hybrid import (
    HybridSearchEngine,
    FusionStrategy,
    WeightedFusion,
    RankFusion,
    ReciprocalRankFusion,
    CondorcetFusion,
    SearchStrategy,
    LexicalStrategy,
    MetadataStrategy,
    SemanticStrategy,
    VectorStrategy,
)
from .business_rules import (
    BusinessRulesEngine,
    BusinessRule,
    RuleType,
    RulePriority,
    RuleAction,
    PinnedResultRule,
    HiddenResultRule,
    PromotedJobRule,
    BlockedCandidateRule,
    PriorityCompanyRule,
    SponsoredRule,
    ManualBoostRule,
)
from .explanation import (
    ScoreExplanation,
    SignalContribution,
    BoostExplanation,
    BusinessRuleExplanation,
    RankingBreakdown,
    ExplanationBuilder,
)
from .profiles import (
    RankingProfile,
    RankingProfileRegistry,
    RecruiterSearchProfile,
    CandidateSearchProfile,
    JobDiscoveryProfile,
    ResumeSearchProfile,
    AdminSearchProfile,
)
from .learning_hooks import (
    LearningHook,
    FeedbackType,
    ClickFeedbackHook,
    ApplicationFeedbackHook,
    RecruiterInteractionHook,
    SavedJobHook,
    IgnoredJobHook,
    InterviewOutcomeHook,
    MLRerankingHook,
)
from .cache import (
    RankingCache,
    CacheKey,
    CacheStats,
)
from .monitoring import (
    RankingMonitor,
    RankingMetrics,
    SignalMetrics,
    PipelineMetrics,
    CacheMetrics,
)
from .config import (
    RankingConfig,
    SignalConfig,
    ProfileConfig,
    CacheConfig,
    MonitoringConfig,
)

__all__ = [
    # Pipeline
    "RankingPipeline",
    "PipelineConfig",
    "PipelineStage",
    "ScoreNormalizer",
    "NormalizationMethod",
    # Signals
    "BaseSignal",
    "LexicalSignal",
    "MetadataSignal",
    "BusinessRuleSignal",
    "FreshnessSignal",
    "PopularitySignal",
    "QualitySignal",
    "SkillOverlapSignal",
    "ExperienceOverlapSignal",
    "EducationOverlapSignal",
    "LocationProximitySignal",
    "SalaryCompatibilitySignal",
    "EmploymentTypeCompatibilitySignal",
    "CompanyPreferenceSignal",
    "RecruiterPreferenceSignal",
    "ProfileCompletenessSignal",
    "CandidateActivitySignal",
    "JobFreshnessSignal",
    "ApplicationHistorySignal",
    # Hybrid Search
    "HybridSearchEngine",
    "FusionStrategy",
    "WeightedFusion",
    "RankFusion",
    "ReciprocalRankFusion",
    "CondorcetFusion",
    "SearchStrategy",
    "LexicalStrategy",
    "MetadataStrategy",
    "SemanticStrategy",
    "VectorStrategy",
    # Business Rules
    "BusinessRulesEngine",
    "BusinessRule",
    "RuleType",
    "RulePriority",
    "RuleAction",
    "PinnedResultRule",
    "HiddenResultRule",
    "PromotedJobRule",
    "BlockedCandidateRule",
    "PriorityCompanyRule",
    "SponsoredRule",
    "ManualBoostRule",
    # Explanation
    "ScoreExplanation",
    "SignalContribution",
    "BoostExplanation",
    "BusinessRuleExplanation",
    "RankingBreakdown",
    "ExplanationBuilder",
    # Profiles
    "RankingProfile",
    "RankingProfileRegistry",
    "RecruiterSearchProfile",
    "CandidateSearchProfile",
    "JobDiscoveryProfile",
    "ResumeSearchProfile",
    "AdminSearchProfile",
    # Learning Hooks
    "LearningHook",
    "FeedbackType",
    "ClickFeedbackHook",
    "ApplicationFeedbackHook",
    "RecruiterInteractionHook",
    "SavedJobHook",
    "IgnoredJobHook",
    "InterviewOutcomeHook",
    "MLRerankingHook",
    # Cache
    "RankingCache",
    "CacheKey",
    "CacheStats",
    # Monitoring
    "RankingMonitor",
    "RankingMetrics",
    "SignalMetrics",
    "PipelineMetrics",
    "CacheMetrics",
    # Config
    "RankingConfig",
    "SignalConfig",
    "ProfileConfig",
    "CacheConfig",
    "MonitoringConfig",
]
