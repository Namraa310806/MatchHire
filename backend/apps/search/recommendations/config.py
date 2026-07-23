"""
Recommendation Configuration.

This module provides configuration classes for the recommendation engine,
strategies, pipeline, diversification, cache, and monitoring.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class RecommendationConfig:
    """
    Main configuration for the recommendation engine.
    
    Contains all configuration options for the recommendation system.
    """
    
    # Engine settings
    enable_caching: bool = True
    enable_monitoring: bool = True
    enable_diagnostics: bool = True
    
    # Default limits
    default_limit: int = 10
    max_limit: int = 100
    
    # Performance settings
    enable_parallel_generation: bool = True
    max_parallel_workers: int = 4
    enable_lazy_ranking: bool = False
    
    # Strategy settings
    default_strategy: str = "hybrid"
    enable_strategy_composition: bool = True
    
    # Diversification settings
    diversification_enabled: bool = True
    diversification_threshold: float = 0.3
    
    # Explanation settings
    explanation_enabled: bool = True
    
    # Learning settings
    enable_learning_hooks: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "enable_caching": self.enable_caching,
            "enable_monitoring": self.enable_monitoring,
            "enable_diagnostics": self.enable_diagnostics,
            "default_limit": self.default_limit,
            "max_limit": self.max_limit,
            "enable_parallel_generation": self.enable_parallel_generation,
            "max_parallel_workers": self.max_parallel_workers,
            "enable_lazy_ranking": self.enable_lazy_ranking,
            "default_strategy": self.default_strategy,
            "enable_strategy_composition": self.enable_strategy_composition,
            "diversification_enabled": self.diversification_enabled,
            "diversification_threshold": self.diversification_threshold,
            "explanation_enabled": self.explanation_enabled,
            "enable_learning_hooks": self.enable_learning_hooks,
        }


@dataclass
class StrategyConfig:
    """
    Configuration for recommendation strategies.
    
    Contains configuration for individual strategies.
    """
    
    strategy_name: str
    enabled: bool = True
    weight: float = 1.0
    params: Dict[str, Any] = field(default_factory=dict)
    
    # Strategy-specific settings
    enable_content_based: bool = True
    enable_similarity_based: bool = True
    enable_rule_based: bool = True
    enable_popularity_based: bool = True
    enable_freshness_based: bool = True
    
    # Composition settings
    composition_method: str = "weighted"  # weighted, rank, hybrid
    enable_dynamic_weighting: bool = False
    learning_rate: float = 0.1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "strategy_name": self.strategy_name,
            "enabled": self.enabled,
            "weight": self.weight,
            "params": self.params,
            "enable_content_based": self.enable_content_based,
            "enable_similarity_based": self.enable_similarity_based,
            "enable_rule_based": self.enable_rule_based,
            "enable_popularity_based": self.enable_popularity_based,
            "enable_freshness_based": self.enable_freshness_based,
            "composition_method": self.composition_method,
            "enable_dynamic_weighting": self.enable_dynamic_weighting,
            "learning_rate": self.learning_rate,
        }


@dataclass
class PipelineConfig:
    """
    Configuration for the recommendation pipeline.
    
    Contains configuration for pipeline stages and execution.
    """
    
    # Stage configuration
    enable_candidate_generation: bool = True
    enable_filtering: bool = True
    enable_ranking: bool = True
    enable_diversification: bool = True
    enable_business_rules: bool = True
    enable_explanation: bool = True
    enable_final_selection: bool = True
    
    # Performance configuration
    enable_parallel_scoring: bool = True
    max_parallel_workers: int = 4
    max_candidates: int = 1000
    enable_early_termination: bool = False
    early_termination_threshold: float = 0.95
    
    # Cache configuration
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    
    # Diagnostics
    enable_diagnostics: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "enable_candidate_generation": self.enable_candidate_generation,
            "enable_filtering": self.enable_filtering,
            "enable_ranking": self.enable_ranking,
            "enable_diversification": self.enable_diversification,
            "enable_business_rules": self.enable_business_rules,
            "enable_explanation": self.enable_explanation,
            "enable_final_selection": self.enable_final_selection,
            "enable_parallel_scoring": self.enable_parallel_scoring,
            "max_parallel_workers": self.max_parallel_workers,
            "max_candidates": self.max_candidates,
            "enable_early_termination": self.enable_early_termination,
            "early_termination_threshold": self.early_termination_threshold,
            "cache_enabled": self.cache_enabled,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "enable_diagnostics": self.enable_diagnostics,
        }


@dataclass
class DiversificationConfig:
    """
    Configuration for diversification.
    
    Contains configuration for diversification algorithms.
    """
    
    # Enable/disable diversifiers
    enable_skill_diversification: bool = True
    enable_company_diversification: bool = True
    enable_location_diversification: bool = True
    enable_experience_diversification: bool = True
    enable_salary_diversification: bool = True
    enable_industry_diversification: bool = True
    enable_deduplication: bool = True
    
    # Thresholds
    skill_diversity_threshold: float = 0.3
    company_diversity_threshold: int = 2
    location_diversity_threshold: int = 2
    experience_diversity_threshold: float = 0.5
    salary_diversity_threshold: float = 0.2
    industry_diversity_threshold: int = 2
    
    # Limits
    max_same_company: int = 3
    max_same_location: int = 3
    max_same_industry: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "enable_skill_diversification": self.enable_skill_diversification,
            "enable_company_diversification": self.enable_company_diversification,
            "enable_location_diversification": self.enable_location_diversification,
            "enable_experience_diversification": self.enable_experience_diversification,
            "enable_salary_diversification": self.enable_salary_diversification,
            "enable_industry_diversification": self.enable_industry_diversification,
            "enable_deduplication": self.enable_deduplication,
            "skill_diversity_threshold": self.skill_diversity_threshold,
            "company_diversity_threshold": self.company_diversity_threshold,
            "location_diversity_threshold": self.location_diversity_threshold,
            "experience_diversity_threshold": self.experience_diversity_threshold,
            "salary_diversity_threshold": self.salary_diversity_threshold,
            "industry_diversity_threshold": self.industry_diversity_threshold,
            "max_same_company": self.max_same_company,
            "max_same_location": self.max_same_location,
            "max_same_industry": self.max_same_industry,
        }


@dataclass
class CacheConfig:
    """
    Configuration for recommendation cache.
    
    Contains configuration for caching behavior.
    """
    
    # Cache settings
    enabled: bool = True
    max_size: int = 1000
    default_ttl: int = 300  # 5 minutes
    
    # Candidate pool cache
    candidate_pool_cache_enabled: bool = True
    candidate_pool_max_size: int = 500
    candidate_pool_ttl: int = 600  # 10 minutes
    
    # Cache invalidation
    auto_cleanup: bool = True
    cleanup_interval: int = 3600  # 1 hour
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "enabled": self.enabled,
            "max_size": self.max_size,
            "default_ttl": self.default_ttl,
            "candidate_pool_cache_enabled": self.candidate_pool_cache_enabled,
            "candidate_pool_max_size": self.candidate_pool_max_size,
            "candidate_pool_ttl": self.candidate_pool_ttl,
            "auto_cleanup": self.auto_cleanup,
            "cleanup_interval": self.cleanup_interval,
        }


@dataclass
class MonitoringConfig:
    """
    Configuration for monitoring.
    
    Contains configuration for metrics collection and reporting.
    """
    
    # Monitoring settings
    enabled: bool = True
    metrics_history_size: int = 1000
    snapshot_interval: int = 60  # seconds
    
    # Metrics to track
    track_recommendations: bool = True
    track_strategies: bool = True
    track_pipeline: bool = True
    track_diversification: bool = True
    track_cache: bool = True
    
    # Alerting thresholds
    latency_warning_threshold_ms: float = 500.0
    latency_critical_threshold_ms: float = 1000.0
    cache_hit_rate_warning_threshold: float = 0.5
    pipeline_failure_rate_warning_threshold: float = 0.1
    
    # Learning hooks
    enable_feedback_tracking: bool = True
    feedback_types: List[str] = field(default_factory=lambda: [
        "click", "application", "hire", "bookmark", "ignore"
    ])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "enabled": self.enabled,
            "metrics_history_size": self.metrics_history_size,
            "snapshot_interval": self.snapshot_interval,
            "track_recommendations": self.track_recommendations,
            "track_strategies": self.track_strategies,
            "track_pipeline": self.track_pipeline,
            "track_diversification": self.track_diversification,
            "track_cache": self.track_cache,
            "latency_warning_threshold_ms": self.latency_warning_threshold_ms,
            "latency_critical_threshold_ms": self.latency_critical_threshold_ms,
            "cache_hit_rate_warning_threshold": self.cache_hit_rate_warning_threshold,
            "pipeline_failure_rate_warning_threshold": self.pipeline_failure_rate_warning_threshold,
            "enable_feedback_tracking": self.enable_feedback_tracking,
            "feedback_types": self.feedback_types,
        }


def get_default_config() -> RecommendationConfig:
    """
    Get the default recommendation configuration.
    
    Returns:
        Default configuration
    """
    return RecommendationConfig()


def get_default_strategy_config() -> StrategyConfig:
    """
    Get the default strategy configuration.
    
    Returns:
        Default strategy configuration
    """
    return StrategyConfig(strategy_name="hybrid")


def get_default_pipeline_config() -> PipelineConfig:
    """
    Get the default pipeline configuration.
    
    Returns:
        Default pipeline configuration
    """
    return PipelineConfig()


def get_default_diversification_config() -> DiversificationConfig:
    """
    Get the default diversification configuration.
    
    Returns:
        Default diversification configuration
    """
    return DiversificationConfig()


def get_default_cache_config() -> CacheConfig:
    """
    Get the default cache configuration.
    
    Returns:
        Default cache configuration
    """
    return CacheConfig()


def get_default_monitoring_config() -> MonitoringConfig:
    """
    Get the default monitoring configuration.
    
    Returns:
        Default monitoring configuration
    """
    return MonitoringConfig()
