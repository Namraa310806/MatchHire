"""
Recommendation Engine Core.

This module provides the central recommendation engine that orchestrates
candidate generation, ranking, diversification, and explanation generation.
The engine reuses the existing Query Engine for candidate generation and
the Ranking Pipeline for ranking.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import time


class RecommendationType(Enum):
    """Types of recommendations."""
    CANDIDATE = "candidate"
    JOB = "job"
    RELATED_ENTITY = "related_entity"


class RecommendationSource(Enum):
    """Sources of recommendations."""
    QUERY_ENGINE = "query_engine"
    SIMILARITY = "similarity"
    COLLABORATIVE_FILTERING = "collaborative_filtering"
    CONTENT_BASED = "content_based"
    RULE_BASED = "rule_based"
    POPULARITY = "popularity"
    FRESHNESS = "freshness"
    HYBRID = "hybrid"


@dataclass
class RecommendationRequest:
    """
    Request for recommendations.
    
    Contains all information needed to generate recommendations.
    """
    
    recommendation_type: RecommendationType
    entity_id: str
    user_id: Optional[str] = None
    recruiter_id: Optional[str] = None
    limit: int = 10
    offset: int = 0
    filters: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    strategy: Optional[str] = None
    diversification_enabled: bool = True
    explanation_enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "recommendation_type": self.recommendation_type.value,
            "entity_id": self.entity_id,
            "user_id": self.user_id,
            "recruiter_id": self.recruiter_id,
            "limit": self.limit,
            "offset": self.offset,
            "filters": self.filters,
            "context": self.context,
            "strategy": self.strategy,
            "diversification_enabled": self.diversification_enabled,
            "explanation_enabled": self.explanation_enabled,
        }


@dataclass
class RecommendationContext:
    """
    Context for recommendation generation.
    
    Contains contextual information for generating recommendations.
    """
    
    user_id: Optional[str] = None
    recruiter_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    recruiter_preferences: Dict[str, Any] = field(default_factory=dict)
    business_rules: Dict[str, Any] = field(default_factory=dict)
    session_context: Dict[str, Any] = field(default_factory=dict)
    temporal_context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "user_id": self.user_id,
            "recruiter_id": self.recruiter_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "user_preferences": self.user_preferences,
            "recruiter_preferences": self.recruiter_preferences,
            "business_rules": self.business_rules,
            "session_context": self.session_context,
            "temporal_context": self.temporal_context,
        }


@dataclass
class RecommendationResult:
    """
    Result from recommendation generation.
    
    Contains the recommended items along with metadata.
    """
    
    item_id: str
    item_type: str
    score: float
    rank: int
    source: RecommendationSource
    item_data: Dict[str, Any] = field(default_factory=dict)
    explanation: Optional[Dict[str, Any]] = None
    signals: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "item_id": self.item_id,
            "item_type": self.item_type,
            "score": self.score,
            "rank": self.rank,
            "source": self.source.value,
            "item_data": self.item_data,
            "explanation": self.explanation,
            "signals": self.signals,
            "metadata": self.metadata,
        }


@dataclass
class RecommendationResponse:
    """
    Response from recommendation engine.
    
    Contains the list of recommendations along with metadata.
    """
    
    recommendations: List[RecommendationResult]
    total: int
    took_ms: float
    recommendation_type: RecommendationType
    strategy_used: Optional[str] = None
    diversification_applied: bool = False
    pipeline_diagnostics: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "recommendations": [r.to_dict() for r in self.recommendations],
            "total": self.total,
            "took_ms": self.took_ms,
            "recommendation_type": self.recommendation_type.value,
            "strategy_used": self.strategy_used,
            "diversification_applied": self.diversification_applied,
            "pipeline_diagnostics": self.pipeline_diagnostics,
            "metadata": self.metadata,
        }


class RecommendationEngine:
    """
    Central Recommendation Engine for MatchHire.
    
    This engine generates recommendations by:
    1. Using the Query Engine to generate candidate items
    2. Delegating ranking to the existing Ranking Pipeline
    3. Applying diversification to ensure variety
    4. Generating explanations for recommendations
    
    The engine is provider-independent and reuses the existing search
    and ranking infrastructure.
    """
    
    def __init__(
        self,
        query_engine,
        ranking_pipeline,
        recommendation_registry,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the recommendation engine.
        
        Args:
            query_engine: Query engine for candidate generation
            ranking_pipeline: Ranking pipeline for ranking candidates
            recommendation_registry: Registry for recommendation providers
            config: Configuration for the engine
        """
        self._query_engine = query_engine
        self._ranking_pipeline = ranking_pipeline
        self._recommendation_registry = recommendation_registry
        self._config = config or {}
        
        # Initialize components
        from .pipeline import RecommendationPipeline
        from .diversification import DiversificationEngine
        from .explanation import ExplanationBuilder
        from .cache import RecommendationCache
        from .monitoring import RecommendationMonitor
        
        self._pipeline = RecommendationPipeline(
            query_engine=query_engine,
            ranking_pipeline=ranking_pipeline,
            config=self._config.get("pipeline", {}),
        )
        self._diversification_engine = DiversificationEngine(
            config=self._config.get("diversification", {}),
        )
        self._explanation_builder = ExplanationBuilder()
        self._cache = RecommendationCache(
            config=self._config.get("cache", {}),
        )
        self._monitor = RecommendationMonitor()
    
    def recommend(
        self,
        request: RecommendationRequest,
        use_cache: bool = True,
    ) -> RecommendationResponse:
        """
        Generate recommendations.
        
        Args:
            request: Recommendation request
            use_cache: Whether to use cache
            
        Returns:
            Recommendation response
        """
        start_time = time.time()
        
        # Build context
        context = self._build_context(request)
        
        # Check cache if enabled
        if use_cache and self._config.get("cache_enabled", True):
            cached_response = self._cache.get(request, context)
            if cached_response is not None:
                self._monitor.record_cache_hit()
                return cached_response
        
        self._monitor.record_cache_miss()
        
        # Get recommendation provider
        provider = self._recommendation_registry.get_provider(
            request.recommendation_type
        )
        
        # Generate candidates using query engine
        candidates = self._generate_candidates(request, context, provider)
        
        # Rank candidates using ranking pipeline
        ranked_candidates = self._rank_candidates(candidates, context)
        
        # Apply diversification if enabled
        if request.diversification_enabled:
            diversified_candidates = self._diversification_engine.diversify(
                ranked_candidates,
                context,
            )
        else:
            diversified_candidates = ranked_candidates
        
        # Generate explanations if enabled
        if request.explanation_enabled:
            self._add_explanations(diversified_candidates, context)
        
        # Build recommendation results
        recommendations = self._build_recommendation_results(
            diversified_candidates,
            context,
        )
        
        # Apply pagination
        paginated_recommendations = self._apply_pagination(
            recommendations,
            request.limit,
            request.offset,
        )
        
        # Build response
        took_ms = (time.time() - start_time) * 1000
        
        response = RecommendationResponse(
            recommendations=paginated_recommendations,
            total=len(recommendations),
            took_ms=took_ms,
            recommendation_type=request.recommendation_type,
            strategy_used=request.strategy,
            diversification_applied=request.diversification_enabled,
            pipeline_diagnostics=self._pipeline.get_diagnostics().to_dict(),
            metadata={
                "provider": provider.__class__.__name__,
                "cached": False,
            },
        )
        
        # Cache response if enabled
        if use_cache and self._config.get("cache_enabled", True):
            self._cache.set(request, context, response)
        
        # Record metrics
        self._monitor.record_recommendation(
            request.recommendation_type,
            len(paginated_recommendations),
            took_ms,
        )
        
        return response
    
    def _build_context(
        self,
        request: RecommendationRequest,
    ) -> RecommendationContext:
        """
        Build recommendation context from request.
        
        Args:
            request: Recommendation request
            
        Returns:
            Recommendation context
        """
        return RecommendationContext(
            user_id=request.user_id,
            recruiter_id=request.recruiter_id,
            entity_id=request.entity_id,
            user_preferences=request.context.get("user_preferences", {}),
            recruiter_preferences=request.context.get("recruiter_preferences", {}),
            business_rules=request.context.get("business_rules", {}),
            session_context=request.context.get("session_context", {}),
            temporal_context={
                "timestamp": datetime.now().isoformat(),
            },
        )
    
    def _generate_candidates(
        self,
        request: RecommendationRequest,
        context: RecommendationContext,
        provider,
    ) -> List[Dict[str, Any]]:
        """
        Generate candidate items using query engine.
        
        Args:
            request: Recommendation request
            context: Recommendation context
            provider: Recommendation provider
            
        Returns:
            List of candidate items
        """
        # Use the pipeline to generate candidates
        candidates = self._pipeline.generate_candidates(
            request=request,
            context=context,
            provider=provider,
        )
        
        return candidates
    
    def _rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        context: RecommendationContext,
    ) -> List[Dict[str, Any]]:
        """
        Rank candidates using ranking pipeline.
        
        Args:
            candidates: List of candidate items
            context: Recommendation context
            
        Returns:
            Ranked candidates
        """
        # Build ranking context
        ranking_context = context.to_dict()
        
        # Execute ranking pipeline
        ranked_candidates, diagnostics = self._ranking_pipeline.execute(
            results=candidates,
            context=ranking_context,
        )
        
        return ranked_candidates
    
    def _add_explanations(
        self,
        candidates: List[Dict[str, Any]],
        context: RecommendationContext,
    ) -> None:
        """
        Add explanations to candidates.
        
        Args:
            candidates: List of candidate items (modified in place)
            context: Recommendation context
        """
        for candidate in candidates:
            explanation = self._explanation_builder.build_explanation(
                candidate,
                context,
            )
            candidate["_explanation"] = explanation
    
    def _build_recommendation_results(
        self,
        candidates: List[Dict[str, Any]],
        context: RecommendationContext,
    ) -> List[RecommendationResult]:
        """
        Build recommendation results from candidates.
        
        Args:
            candidates: List of ranked candidates
            context: Recommendation context
            
        Returns:
            List of recommendation results
        """
        results = []
        for rank, candidate in enumerate(candidates, start=1):
            result = RecommendationResult(
                item_id=candidate.get("id", ""),
                item_type=candidate.get("type", "unknown"),
                score=candidate.get("_ranking_score", 0.0),
                rank=rank,
                source=candidate.get("_source", RecommendationSource.HYBRID),
                item_data=candidate,
                explanation=candidate.get("_explanation"),
                signals=candidate.get("_ranking_signals", {}),
                metadata={
                    "original_rank": candidate.get("_original_rank", rank),
                },
            )
            results.append(result)
        
        return results
    
    def _apply_pagination(
        self,
        recommendations: List[RecommendationResult],
        limit: int,
        offset: int,
    ) -> List[RecommendationResult]:
        """
        Apply pagination to recommendations.
        
        Args:
            recommendations: List of recommendations
            limit: Number of items to return
            offset: Offset for pagination
            
        Returns:
            Paginated recommendations
        """
        start = offset
        end = offset + limit
        return recommendations[start:end]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        return self._cache.get_stats()
    
    def clear_cache(self) -> None:
        """Clear the recommendation cache."""
        self._cache.clear()
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """
        Get monitoring statistics.
        
        Returns:
            Monitoring statistics
        """
        return self._monitor.get_stats()
    
    def reset_monitoring(self) -> None:
        """Reset monitoring statistics."""
        self._monitor.reset()
