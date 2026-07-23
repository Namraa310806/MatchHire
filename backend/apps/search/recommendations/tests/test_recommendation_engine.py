"""
Tests for Recommendation Engine.

This module contains comprehensive tests for the recommendation engine,
covering core functionality, strategies, pipeline, diversification, and more.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from typing import Dict, Any

from apps.search.recommendations.core import (
    RecommendationEngine,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationContext,
    RecommendationResult,
    RecommendationType,
    RecommendationSource,
)
from apps.search.recommendations.strategies import (
    ContentBasedStrategy,
    SimilarityBasedStrategy,
    RuleBasedStrategy,
    PopularityBasedStrategy,
    FreshnessBasedStrategy,
    HybridRecommendationStrategy,
    StrategyComposition,
    StrategyWeighting,
)
from apps.search.recommendations.providers import (
    CandidateRecommendationProvider,
    JobRecommendationProvider,
    RelatedEntityRecommendationProvider,
    RecommendationRegistry,
)
from apps.search.recommendations.pipeline import (
    RecommendationPipeline,
    PipelineConfig,
    PipelineStage,
    PipelineStageType,
)
from apps.search.recommendations.diversification import (
    DiversificationEngine,
    DiversificationConfig,
    SkillDiversifier,
    CompanyDiversifier,
    DeduplicationEngine,
)
from apps.search.recommendations.explanation import (
    ExplanationBuilder,
    RecommendationExplanation,
    ExplanationType,
)
from apps.search.recommendations.cache import (
    RecommendationCache,
    CacheKey,
    CacheEntry,
    CandidatePoolCache,
)
from apps.search.recommendations.monitoring import (
    RecommendationMonitor,
    RecommendationMetrics,
    StrategyMetrics,
    PipelineMetrics,
    DiversificationMetrics,
)
from apps.search.recommendations.config import (
    RecommendationConfig,
    StrategyConfig,
    PipelineConfig as RecPipelineConfig,
    DiversificationConfig as DivConfig,
    CacheConfig,
    MonitoringConfig,
)


class TestRecommendationRequest:
    """Tests for RecommendationRequest."""
    
    def test_recommendation_request_creation(self):
        """Test creating a recommendation request."""
        request = RecommendationRequest(
            recommendation_type=RecommendationType.CANDIDATE,
            entity_id="job_123",
            user_id="user_456",
            limit=10,
        )
        
        assert request.recommendation_type == RecommendationType.CANDIDATE
        assert request.entity_id == "job_123"
        assert request.user_id == "user_456"
        assert request.limit == 10
    
    def test_recommendation_request_to_dict(self):
        """Test converting request to dictionary."""
        request = RecommendationRequest(
            recommendation_type=RecommendationType.JOB,
            entity_id="candidate_789",
            limit=5,
        )
        
        request_dict = request.to_dict()
        
        assert request_dict["recommendation_type"] == "job"
        assert request_dict["entity_id"] == "candidate_789"
        assert request_dict["limit"] == 5


class TestRecommendationContext:
    """Tests for RecommendationContext."""
    
    def test_recommendation_context_creation(self):
        """Test creating a recommendation context."""
        context = RecommendationContext(
            user_id="user_123",
            recruiter_id="recruiter_456",
            entity_type="job",
        )
        
        assert context.user_id == "user_123"
        assert context.recruiter_id == "recruiter_456"
        assert context.entity_type == "job"
    
    def test_recommendation_context_to_dict(self):
        """Test converting context to dictionary."""
        context = RecommendationContext(
            user_id="user_123",
        )
        
        context_dict = context.to_dict()
        
        assert context_dict["user_id"] == "user_123"


class TestRecommendationResult:
    """Tests for RecommendationResult."""
    
    def test_recommendation_result_creation(self):
        """Test creating a recommendation result."""
        result = RecommendationResult(
            item_id="item_123",
            item_type="candidate",
            score=0.85,
            rank=1,
            source=RecommendationSource.HYBRID,
        )
        
        assert result.item_id == "item_123"
        assert result.item_type == "candidate"
        assert result.score == 0.85
        assert result.rank == 1
        assert result.source == RecommendationSource.HYBRID
    
    def test_recommendation_result_to_dict(self):
        """Test converting result to dictionary."""
        result = RecommendationResult(
            item_id="item_123",
            item_type="job",
            score=0.9,
            rank=1,
            source=RecommendationSource.QUERY_ENGINE,
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["item_id"] == "item_123"
        assert result_dict["score"] == 0.9
        assert result_dict["source"] == "query_engine"


class TestRecommendationResponse:
    """Tests for RecommendationResponse."""
    
    def test_recommendation_response_creation(self):
        """Test creating a recommendation response."""
        results = [
            RecommendationResult(
                item_id="item_1",
                item_type="candidate",
                score=0.9,
                rank=1,
                source=RecommendationSource.HYBRID,
            )
        ]
        
        response = RecommendationResponse(
            recommendations=results,
            total=1,
            took_ms=50.0,
            recommendation_type=RecommendationType.CANDIDATE,
        )
        
        assert len(response.recommendations) == 1
        assert response.total == 1
        assert response.took_ms == 50.0
        assert response.recommendation_type == RecommendationType.CANDIDATE


class TestStrategyComposition:
    """Tests for StrategyComposition."""
    
    def test_strategy_composition_weighted(self):
        """Test weighted strategy composition."""
        strategies = [
            ContentBasedStrategy(),
            PopularityBasedStrategy(),
        ]
        
        composition = StrategyComposition(strategies)
        
        # Test weighted composition
        candidates = composition.compose(
            entity_id="entity_123",
            context={},
            limit=10,
            method="weighted",
        )
        
        assert isinstance(candidates, list)
    
    def test_strategy_composition_rank(self):
        """Test rank-based strategy composition."""
        strategies = [
            ContentBasedStrategy(),
            PopularityBasedStrategy(),
        ]
        
        composition = StrategyComposition(strategies)
        
        # Test rank composition
        candidates = composition.compose(
            entity_id="entity_123",
            context={},
            limit=10,
            method="rank",
        )
        
        assert isinstance(candidates, list)


class TestStrategyWeighting:
    """Tests for StrategyWeighting."""
    
    def test_strategy_weighting_initialization(self):
        """Test initializing strategy weighting."""
        weighting = StrategyWeighting(
            initial_weights={"content": 1.0, "popularity": 0.5}
        )
        
        assert weighting.get_weight("content") == 1.0
        assert weighting.get_weight("popularity") == 0.5
    
    def test_strategy_weighting_adjust(self):
        """Test adjusting strategy weights."""
        weighting = StrategyWeighting()
        
        weighting.adjust_weight("content", 0.8, learning_rate=0.1)
        
        weight = weighting.get_weight("content")
        assert weight > 1.0  # Should increase for good performance
    
    def test_strategy_weighting_performance(self):
        """Test recording and retrieving performance."""
        weighting = StrategyWeighting()
        
        weighting.adjust_weight("content", 0.9)
        weighting.adjust_weight("content", 0.8)
        
        performance = weighting.get_performance_score("content")
        assert performance is not None
        assert 0 <= performance <= 1


class TestDiversificationEngine:
    """Tests for DiversificationEngine."""
    
    def test_diversification_engine_initialization(self):
        """Test initializing diversification engine."""
        config = DiversificationConfig()
        engine = DiversificationEngine(config)
        
        assert engine is not None
    
    def test_diversification_engine_diversify(self):
        """Test diversifying candidates."""
        config = DiversificationConfig()
        engine = DiversificationEngine(config)
        
        candidates = [
            {
                "id": f"candidate_{i}",
                "company_name": f"Company_{i % 3}",
                "skills": ["python", "django"],
                "location": "New York",
                "experience_years": 5,
            }
            for i in range(10)
        ]
        
        diversified = engine.diversify(candidates, {})
        
        assert isinstance(diversified, list)
        assert len(diversified) <= len(candidates)
    
    def test_diversification_add_diversifier(self):
        """Test adding a custom diversifier."""
        config = DiversificationConfig()
        engine = DiversificationEngine(config)
        
        custom_diversifier = SkillDiversifier(config)
        engine.add_diversifier(custom_diversifier)
        
        # Should not raise an error
        assert True


class TestDeduplicationEngine:
    """Tests for DeduplicationEngine."""
    
    def test_deduplication_engine_deduplicate(self):
        """Test deduplicating candidates."""
        config = DiversificationConfig()
        engine = DeduplicationEngine(config)
        
        candidates = [
            {"id": "candidate_1", "name": "John"},
            {"id": "candidate_2", "name": "Jane"},
            {"id": "candidate_1", "name": "John"},  # Duplicate
        ]
        
        deduplicated = engine.deduplicate(candidates, {})
        
        assert len(deduplicated) == 2
        assert all(c["id"] == "candidate_1" for c in deduplicated if c["id"] == "candidate_1")


class TestExplanationBuilder:
    """Tests for ExplanationBuilder."""
    
    def test_explanation_builder_initialization(self):
        """Test initializing explanation builder."""
        builder = ExplanationBuilder()
        
        assert builder is not None
    
    def test_explanation_builder_build_explanation(self):
        """Test building explanation for a candidate."""
        builder = ExplanationBuilder()
        
        candidate = {
            "id": "candidate_123",
            "skills": ["python", "django"],
            "experience_years": 5,
            "_ranking_signals": {
                "skill_overlap": 0.9,
                "experience_overlap": 0.8,
            },
        }
        
        context = {
            "required_skills": ["python", "django"],
            "required_experience": 5,
        }
        
        explanation = builder.build_explanation(candidate, context)
        
        assert isinstance(explanation, dict)
        assert "why_recommended" in explanation
        assert "shared_skills" in explanation


class TestRecommendationCache:
    """Tests for RecommendationCache."""
    
    def test_cache_initialization(self):
        """Test initializing cache."""
        config = {"max_size": 100, "default_ttl": 300}
        cache = RecommendationCache(config)
        
        assert cache is not None
    
    def test_cache_set_and_get(self):
        """Test setting and getting cache entries."""
        cache = RecommendationCache()
        
        request = Mock()
        request.recommendation_type = RecommendationType.CANDIDATE
        request.entity_id = "job_123"
        request.user_id = "user_456"
        request.filters = {}
        
        context = RecommendationContext(user_id="user_456")
        
        value = {"results": ["candidate_1", "candidate_2"]}
        
        cache.set(request, context, value)
        cached_value = cache.get(request, context)
        
        assert cached_value == value
    
    def test_cache_miss(self):
        """Test cache miss."""
        cache = RecommendationCache()
        
        request = Mock()
        request.recommendation_type = RecommendationType.CANDIDATE
        request.entity_id = "job_123"
        request.user_id = "user_456"
        request.filters = {}
        
        context = RecommendationContext(user_id="user_456")
        
        cached_value = cache.get(request, context)
        
        assert cached_value is None
    
    def test_cache_clear(self):
        """Test clearing cache."""
        cache = RecommendationCache()
        
        request = Mock()
        request.recommendation_type = RecommendationType.CANDIDATE
        request.entity_id = "job_123"
        request.user_id = "user_456"
        request.filters = {}
        
        context = RecommendationContext(user_id="user_456")
        
        cache.set(request, context, {"results": []})
        cache.clear()
        
        cached_value = cache.get(request, context)
        assert cached_value is None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = RecommendationCache()
        
        request = Mock()
        request.recommendation_type = RecommendationType.CANDIDATE
        request.entity_id = "job_123"
        request.user_id = "user_456"
        request.filters = {}
        
        context = RecommendationContext(user_id="user_456")
        
        cache.set(request, context, {"results": []})
        cache.get(request, context)  # Hit
        
        stats = cache.get_stats()
        
        assert stats.hits == 1
        assert stats.misses == 0


class TestCandidatePoolCache:
    """Tests for CandidatePoolCache."""
    
    def test_candidate_pool_cache_set_and_get(self):
        """Test setting and getting candidate pool."""
        cache = CandidatePoolCache()
        
        pool_key = "job_123_skills"
        candidates = [
            {"id": "candidate_1", "name": "John"},
            {"id": "candidate_2", "name": "Jane"},
        ]
        
        cache.set(pool_key, candidates)
        cached_candidates = cache.get(pool_key)
        
        assert cached_candidates == candidates
    
    def test_candidate_pool_cache_clear(self):
        """Test clearing candidate pool cache."""
        cache = CandidatePoolCache()
        
        pool_key = "job_123_skills"
        cache.set(pool_key, [])
        cache.clear()
        
        cached_candidates = cache.get(pool_key)
        assert cached_candidates is None


class TestRecommendationMonitor:
    """Tests for RecommendationMonitor."""
    
    def test_monitor_initialization(self):
        """Test initializing monitor."""
        monitor = RecommendationMonitor()
        
        assert monitor is not None
    
    def test_monitor_record_recommendation(self):
        """Test recording recommendation."""
        monitor = RecommendationMonitor()
        
        monitor.record_recommendation(
            recommendation_type="candidate",
            count=10,
            latency_ms=50.0,
        )
        
        metrics = monitor.get_recommendation_metrics()
        
        assert metrics.total_recommendations == 1
        assert metrics.candidate_recommendations == 1
    
    def test_monitor_record_cache_hit(self):
        """Test recording cache hit."""
        monitor = RecommendationMonitor()
        
        monitor.record_cache_hit()
        
        metrics = monitor.get_recommendation_metrics()
        
        assert metrics.cache_hits == 1
    
    def test_monitor_record_cache_miss(self):
        """Test recording cache miss."""
        monitor = RecommendationMonitor()
        
        monitor.record_cache_miss()
        
        metrics = monitor.get_recommendation_metrics()
        
        assert metrics.cache_misses == 1
    
    def test_monitor_record_strategy_usage(self):
        """Test recording strategy usage."""
        monitor = RecommendationMonitor()
        
        monitor.record_strategy_usage(
            strategy_name="content",
            performance=0.8,
            latency_ms=30.0,
        )
        
        strategy_metrics = monitor.get_strategy_metrics()
        
        assert strategy_metrics.strategy_usage.get("content") == 1
    
    def test_monitor_record_pipeline_execution(self):
        """Test recording pipeline execution."""
        monitor = RecommendationMonitor()
        
        stage_times = {
            "candidate_generation": 10.0,
            "filtering": 5.0,
            "ranking": 20.0,
        }
        
        monitor.record_pipeline_execution(
            stage_times=stage_times,
            candidates_generated=100,
            candidates_filtered=80,
            candidates_ranked=80,
            candidates_diversified=70,
        )
        
        pipeline_metrics = monitor.get_pipeline_metrics()
        
        assert pipeline_metrics.total_pipeline_executions == 1
        assert pipeline_metrics.candidates_generated == 100
    
    def test_monitor_get_stats(self):
        """Test getting all statistics."""
        monitor = RecommendationMonitor()
        
        monitor.record_recommendation("candidate", 10, 50.0)
        
        stats = monitor.get_stats()
        
        assert "recommendation" in stats
        assert "strategy" in stats
        assert "pipeline" in stats
        assert "diversification" in stats
    
    def test_monitor_reset(self):
        """Test resetting monitor."""
        monitor = RecommendationMonitor()
        
        monitor.record_recommendation("candidate", 10, 50.0)
        monitor.reset()
        
        metrics = monitor.get_recommendation_metrics()
        
        assert metrics.total_recommendations == 0


class TestRecommendationConfig:
    """Tests for configuration classes."""
    
    def test_recommendation_config(self):
        """Test recommendation configuration."""
        config = RecommendationConfig()
        
        assert config.enable_caching == True
        assert config.default_limit == 10
        
        config_dict = config.to_dict()
        assert "enable_caching" in config_dict
    
    def test_strategy_config(self):
        """Test strategy configuration."""
        config = StrategyConfig(strategy_name="hybrid")
        
        assert config.strategy_name == "hybrid"
        assert config.enabled == True
        
        config_dict = config.to_dict()
        assert "strategy_name" in config_dict
    
    def test_pipeline_config(self):
        """Test pipeline configuration."""
        config = PipelineConfig()
        
        assert config.enable_ranking == True
        assert config.max_candidates == 1000
        
        config_dict = config.to_dict()
        assert "enable_ranking" in config_dict
    
    def test_diversification_config(self):
        """Test diversification configuration."""
        config = DiversificationConfig()
        
        assert config.enable_skill_diversification == True
        assert config.max_same_company == 3
        
        config_dict = config.to_dict()
        assert "enable_skill_diversification" in config_dict
    
    def test_cache_config(self):
        """Test cache configuration."""
        config = CacheConfig()
        
        assert config.enabled == True
        assert config.max_size == 1000
        
        config_dict = config.to_dict()
        assert "enabled" in config_dict
    
    def test_monitoring_config(self):
        """Test monitoring configuration."""
        config = MonitoringConfig()
        
        assert config.enabled == True
        assert config.track_recommendations == True
        
        config_dict = config.to_dict()
        assert "enabled" in config_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
