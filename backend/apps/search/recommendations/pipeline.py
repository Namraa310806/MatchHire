"""
Recommendation Pipeline.

This module provides the pipeline for candidate generation, ranking,
diversification, and explanation generation. The pipeline reuses the
existing Query Engine for candidate generation and Ranking Pipeline
for ranking.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time


class PipelineStageType(Enum):
    """Types of pipeline stages."""
    CANDIDATE_GENERATION = "candidate_generation"
    FILTERING = "filtering"
    RANKING = "ranking"
    DIVERSIFICATION = "diversification"
    BUSINESS_RULES = "business_rules"
    EXPLANATION = "explanation"
    FINAL_SELECTION = "final_selection"
    DIAGNOSTICS = "diagnostics"


@dataclass
class PipelineConfig:
    """Configuration for the recommendation pipeline."""
    
    enable_parallel_generation: bool = True
    max_parallel_workers: int = 4
    max_candidates: int = 1000
    enable_early_termination: bool = False
    early_termination_threshold: float = 0.95
    enable_lazy_ranking: bool = False
    diversification_enabled: bool = True
    explanation_enabled: bool = True
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    enable_diagnostics: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "enable_parallel_generation": self.enable_parallel_generation,
            "max_parallel_workers": self.max_parallel_workers,
            "max_candidates": self.max_candidates,
            "enable_early_termination": self.enable_early_termination,
            "early_termination_threshold": self.early_termination_threshold,
            "enable_lazy_ranking": self.enable_lazy_ranking,
            "diversification_enabled": self.diversification_enabled,
            "explanation_enabled": self.explanation_enabled,
            "cache_enabled": self.cache_enabled,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "enable_diagnostics": self.enable_diagnostics,
        }


@dataclass
class PipelineStage:
    """
    A single stage in the recommendation pipeline.
    
    Each stage performs a specific operation on the candidates.
    """
    
    name: str
    stage_type: PipelineStageType
    enabled: bool = True
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "stage_type": self.stage_type.value,
            "enabled": self.enabled,
            "config": self.config,
        }
    
    def should_execute(self, context: Dict[str, Any]) -> bool:
        """
        Check if this stage should execute based on conditions.
        
        Args:
            context: Recommendation context
            
        Returns:
            True if stage should execute
        """
        if not self.enabled:
            return False
        if self.condition is not None:
            return self.condition(context)
        return True


@dataclass
class PipelineDiagnostics:
    """Diagnostics information for pipeline execution."""
    
    total_time_ms: float = 0.0
    stage_times_ms: Dict[str, float] = field(default_factory=dict)
    candidates_generated: int = 0
    candidates_filtered: int = 0
    candidates_ranked: int = 0
    candidates_diversified: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    early_termination_triggered: bool = False
    parallel_workers_used: int = 0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total_time_ms": self.total_time_ms,
            "stage_times_ms": self.stage_times_ms,
            "candidates_generated": self.candidates_generated,
            "candidates_filtered": self.candidates_filtered,
            "candidates_ranked": self.candidates_ranked,
            "candidates_diversified": self.candidates_diversified,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "early_termination_triggered": self.early_termination_triggered,
            "parallel_workers_used": self.parallel_workers_used,
            "errors": self.errors,
        }


class RecommendationPipeline:
    """
    Pipeline for recommendation generation.
    
    The pipeline executes stages in sequence:
    1. Candidate Generation (using Query Engine)
    2. Filtering
    3. Ranking (using Ranking Pipeline)
    4. Diversification
    5. Business Rules
    6. Explanation
    7. Final Selection
    8. Diagnostics
    """
    
    def __init__(
        self,
        query_engine,
        ranking_pipeline,
        config: Optional[PipelineConfig] = None,
    ):
        """
        Initialize the recommendation pipeline.
        
        Args:
            query_engine: Query engine for candidate generation
            ranking_pipeline: Ranking pipeline for ranking candidates
            config: Pipeline configuration
        """
        self._query_engine = query_engine
        self._ranking_pipeline = ranking_pipeline
        self._config = config or PipelineConfig()
        self._stages: List[PipelineStage] = []
        self._cache: Dict[str, Any] = {}
        self._diagnostics = PipelineDiagnostics()
        
        # Initialize default stages
        self._initialize_default_stages()
    
    def _initialize_default_stages(self) -> None:
        """Initialize the default pipeline stages."""
        self._stages = [
            PipelineStage(
                name="candidate_generation",
                stage_type=PipelineStageType.CANDIDATE_GENERATION,
                enabled=True,
            ),
            PipelineStage(
                name="filtering",
                stage_type=PipelineStageType.FILTERING,
                enabled=True,
            ),
            PipelineStage(
                name="ranking",
                stage_type=PipelineStageType.RANKING,
                enabled=True,
            ),
            PipelineStage(
                name="diversification",
                stage_type=PipelineStageType.DIVERSIFICATION,
                enabled=self._config.diversification_enabled,
            ),
            PipelineStage(
                name="business_rules",
                stage_type=PipelineStageType.BUSINESS_RULES,
                enabled=True,
            ),
            PipelineStage(
                name="explanation",
                stage_type=PipelineStageType.EXPLANATION,
                enabled=self._config.explanation_enabled,
            ),
            PipelineStage(
                name="final_selection",
                stage_type=PipelineStageType.FINAL_SELECTION,
                enabled=True,
            ),
        ]
    
    def add_stage(self, stage: PipelineStage) -> "RecommendationPipeline":
        """
        Add a stage to the pipeline.
        
        Args:
            stage: Pipeline stage to add
            
        Returns:
            Self for method chaining
        """
        self._stages.append(stage)
        return self
    
    def generate_candidates(
        self,
        request,
        context,
        provider,
    ) -> List[Dict[str, Any]]:
        """
        Generate candidates using the pipeline.
        
        Args:
            request: Recommendation request
            context: Recommendation context
            provider: Recommendation provider
            
        Returns:
            List of candidate items
        """
        start_time = time.time()
        self._diagnostics = PipelineDiagnostics()
        
        # Stage 1: Candidate Generation
        candidates = self._execute_candidate_generation(
            request, context, provider
        )
        self._diagnostics.candidates_generated = len(candidates)
        
        # Apply max candidates limit
        if self._config.max_candidates > 0:
            candidates = candidates[:self._config.max_candidates]
        
        # Stage 2: Filtering
        candidates = self._execute_filtering(candidates, context)
        self._diagnostics.candidates_filtered = len(candidates)
        
        # Stage 3: Ranking (delegated to Ranking Pipeline)
        candidates = self._execute_ranking(candidates, context)
        self._diagnostics.candidates_ranked = len(candidates)
        
        # Stage 4: Diversification
        if self._config.diversification_enabled:
            from .diversification import DiversificationEngine
            diversifier = DiversificationEngine(self._config)
            candidates = diversifier.diversify(candidates, context)
            self._diagnostics.candidates_diversified = len(candidates)
        
        # Stage 5: Business Rules
        candidates = self._execute_business_rules(candidates, context)
        
        # Stage 6: Explanation
        if self._config.explanation_enabled:
            candidates = self._execute_explanation(candidates, context)
        
        # Stage 7: Final Selection
        candidates = self._execute_final_selection(candidates, context)
        
        self._diagnostics.total_time_ms = (time.time() - start_time) * 1000
        
        return candidates
    
    def _execute_candidate_generation(
        self,
        request,
        context: Dict[str, Any],
        provider,
    ) -> List[Dict[str, Any]]:
        """
        Execute candidate generation stage.
        
        Args:
            request: Recommendation request
            context: Recommendation context
            provider: Recommendation provider
            
        Returns:
            List of candidate items
        """
        stage_start = time.time()
        
        # Use provider to generate candidates
        candidates = provider.generate_candidates(
            entity_id=request.entity_id,
            context=context.to_dict(),
            limit=request.limit * 3,  # Get more for filtering/ranking
            filters=request.filters,
        )
        
        # Add metadata
        for candidate in candidates:
            candidate.setdefault("_source", "query_engine")
            candidate.setdefault("_stage", "candidate_generation")
        
        stage_time = (time.time() - stage_start) * 1000
        self._diagnostics.stage_times_ms["candidate_generation"] = stage_time
        
        return candidates
    
    def _execute_filtering(
        self,
        candidates: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Execute filtering stage.
        
        Args:
            candidates: List of candidate items
            context: Recommendation context
            
        Returns:
            Filtered candidates
        """
        stage_start = time.time()
        
        # Apply business rule filters
        business_rules = context.get("business_rules", {})
        
        filtered_candidates = []
        for candidate in candidates:
            # Check if candidate is blocked
            blocked_ids = business_rules.get("blocked_ids", [])
            if candidate.get("id") in blocked_ids:
                continue
            
            # Check if candidate meets minimum requirements
            if not self._meets_requirements(candidate, context):
                continue
            
            filtered_candidates.append(candidate)
        
        stage_time = (time.time() - stage_start) * 1000
        self._diagnostics.stage_times_ms["filtering"] = stage_time
        
        return filtered_candidates
    
    def _meets_requirements(
        self,
        candidate: Dict[str, Any],
        context: Dict[str, Any],
    ) -> bool:
        """
        Check if candidate meets minimum requirements.
        
        Args:
            candidate: Candidate item
            context: Recommendation context
            
        Returns:
            True if candidate meets requirements
        """
        # Check experience requirement
        required_experience = context.get("required_experience", 0)
        candidate_experience = candidate.get("experience_years", 0) or 0
        if required_experience > 0 and candidate_experience < required_experience * 0.5:
            return False
        
        # Check location requirement
        required_location = context.get("required_location", "")
        candidate_location = candidate.get("location", "")
        if required_location and candidate_location:
            # Simple check - in production, use geo-distance
            if required_location.lower() not in candidate_location.lower():
                return False
        
        return True
    
    def _execute_ranking(
        self,
        candidates: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Execute ranking stage using Ranking Pipeline.
        
        Args:
            candidates: List of candidate items
            context: Recommendation context
            
        Returns:
            Ranked candidates
        """
        stage_start = time.time()
        
        # Build ranking context
        ranking_context = context.copy()
        ranking_context["entity_type"] = context.get("entity_type", "candidate")
        
        # Execute ranking pipeline
        ranked_candidates, _ = self._ranking_pipeline.execute(
            results=candidates,
            context=ranking_context,
        )
        
        stage_time = (time.time() - stage_start) * 1000
        self._diagnostics.stage_times_ms["ranking"] = stage_time
        
        return ranked_candidates
    
    def _execute_business_rules(
        self,
        candidates: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Execute business rules stage.
        
        Args:
            candidates: List of candidate items
            context: Recommendation context
            
        Returns:
            Candidates with business rules applied
        """
        stage_start = time.time()
        
        business_rules = context.get("business_rules", {})
        
        # Apply pinned results
        pinned_ids = business_rules.get("pinned_ids", [])
        if pinned_ids:
            # Move pinned results to top
            pinned = [c for c in candidates if c.get("id") in pinned_ids]
            others = [c for c in candidates if c.get("id") not in pinned_ids]
            candidates = pinned + others
        
        # Apply promoted results boost
        promoted_ids = business_rules.get("promoted_ids", [])
        for candidate in candidates:
            if candidate.get("id") in promoted_ids:
                candidate["_ranking_score"] = candidate.get("_ranking_score", 0.0) + 5.0
                candidate.setdefault("_boosts", []).append("promoted")
        
        stage_time = (time.time() - stage_start) * 1000
        self._diagnostics.stage_times_ms["business_rules"] = stage_time
        
        return candidates
    
    def _execute_explanation(
        self,
        candidates: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Execute explanation stage.
        
        Args:
            candidates: List of candidate items
            context: Recommendation context
            
        Returns:
            Candidates with explanations
        """
        stage_start = time.time()
        
        from .explanation import ExplanationBuilder
        builder = ExplanationBuilder()
        
        for candidate in candidates:
            explanation = builder.build_explanation(candidate, context)
            candidate["_explanation"] = explanation
        
        stage_time = (time.time() - stage_start) * 1000
        self._diagnostics.stage_times_ms["explanation"] = stage_time
        
        return candidates
    
    def _execute_final_selection(
        self,
        candidates: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Execute final selection stage.
        
        Args:
            candidates: List of candidate items
            context: Recommendation context
            
        Returns:
            Final selected candidates
        """
        stage_start = time.time()
        
        # Sort by final score
        candidates.sort(key=lambda x: x.get("_ranking_score", 0.0), reverse=True)
        
        # Assign final ranks
        for rank, candidate in enumerate(candidates, start=1):
            candidate["_final_rank"] = rank
        
        stage_time = (time.time() - stage_start) * 1000
        self._diagnostics.stage_times_ms["final_selection"] = stage_time
        
        return candidates
    
    def get_diagnostics(self) -> PipelineDiagnostics:
        """
        Get pipeline diagnostics.
        
        Returns:
            Pipeline diagnostics
        """
        return self._diagnostics
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline to dictionary representation."""
        return {
            "config": self._config.to_dict(),
            "stages": [stage.to_dict() for stage in self._stages],
        }
