"""
Recommendation Strategies.

This module provides different recommendation strategies that can be used
to generate recommendations. Strategies can be composed and weighted.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


class StrategyType(Enum):
    """Types of recommendation strategies."""
    CONTENT_BASED = "content_based"
    SIMILARITY_BASED = "similarity_based"
    RULE_BASED = "rule_based"
    POPULARITY_BASED = "popularity_based"
    FRESHNESS_BASED = "freshness_based"
    HYBRID = "hybrid"
    COLLABORATIVE_FILTERING = "collaborative_filtering"
    ML_BASED = "ml_based"


@dataclass
class StrategyConfig:
    """Configuration for a recommendation strategy."""
    
    enabled: bool = True
    weight: float = 1.0
    params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "enabled": self.enabled,
            "weight": self.weight,
            "params": self.params,
        }


class RecommendationStrategy(ABC):
    """
    Abstract base class for recommendation strategies.
    
    Each strategy implements a different approach to generating recommendations.
    """
    
    def __init__(self, config: Optional[StrategyConfig] = None):
        """
        Initialize the strategy.
        
        Args:
            config: Strategy configuration
        """
        self._config = config or StrategyConfig()
    
    @property
    def strategy_type(self) -> StrategyType:
        """Get the strategy type."""
        return StrategyType.CONTENT_BASED
    
    @abstractmethod
    def generate_candidates(
        self,
        entity_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate candidate recommendations.
        
        Args:
            entity_id: ID of the entity to generate recommendations for
            context: Recommendation context
            limit: Maximum number of candidates to generate
            
        Returns:
            List of candidate items
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if strategy is enabled."""
        return self._config.enabled
    
    def get_weight(self) -> float:
        """Get the strategy weight."""
        return self._config.weight
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """Get a configuration parameter."""
        return self._config.params.get(key, default)


class ContentBasedStrategy(RecommendationStrategy):
    """
    Content-based recommendation strategy.
    
    Generates recommendations based on content similarity between items.
    Uses features like skills, experience, education, etc.
    """
    
    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.CONTENT_BASED
    
    def generate_candidates(
        self,
        entity_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate candidates based on content similarity.
        
        Args:
            entity_id: ID of the entity
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        # This would use the query engine to find similar items
        # based on content features
        # For now, return empty list
        return []


class SimilarityBasedStrategy(RecommendationStrategy):
    """
    Similarity-based recommendation strategy.
    
    Generates recommendations based on similarity metrics like
    cosine similarity, Jaccard similarity, etc.
    """
    
    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.SIMILARITY_BASED
    
    def generate_candidates(
        self,
        entity_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate candidates based on similarity.
        
        Args:
            entity_id: ID of the entity
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        # This would use similarity metrics to find similar items
        # For now, return empty list
        return []


class RuleBasedStrategy(RecommendationStrategy):
    """
    Rule-based recommendation strategy.
    
    Generates recommendations based on configurable business rules.
    """
    
    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.RULE_BASED
    
    def generate_candidates(
        self,
        entity_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate candidates based on business rules.
        
        Args:
            entity_id: ID of the entity
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        # This would apply business rules to filter and rank candidates
        # For now, return empty list
        return []


class PopularityBasedStrategy(RecommendationStrategy):
    """
    Popularity-based recommendation strategy.
    
    Generates recommendations based on popularity metrics like
    views, applications, saves, etc.
    """
    
    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.POPULARITY_BASED
    
    def generate_candidates(
        self,
        entity_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate candidates based on popularity.
        
        Args:
            entity_id: ID of the entity
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        # This would use popularity metrics to rank candidates
        # For now, return empty list
        return []


class FreshnessBasedStrategy(RecommendationStrategy):
    """
    Freshness-based recommendation strategy.
    
    Generates recommendations based on recency/freshness of items.
    """
    
    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.FRESHNESS_BASED
    
    def generate_candidates(
        self,
        entity_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate candidates based on freshness.
        
        Args:
            entity_id: ID of the entity
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        # This would use freshness metrics to rank candidates
        # For now, return empty list
        return []


class HybridRecommendationStrategy(RecommendationStrategy):
    """
    Hybrid recommendation strategy.
    
    Combines multiple strategies using composition and weighting.
    """
    
    def __init__(
        self,
        strategies: List[RecommendationStrategy],
        config: Optional[StrategyConfig] = None,
    ):
        """
        Initialize the hybrid strategy.
        
        Args:
            strategies: List of strategies to combine
            config: Strategy configuration
        """
        super().__init__(config)
        self._strategies = strategies
    
    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.HYBRID
    
    def add_strategy(self, strategy: RecommendationStrategy) -> None:
        """
        Add a strategy to the hybrid.
        
        Args:
            strategy: Strategy to add
        """
        self._strategies.append(strategy)
    
    def generate_candidates(
        self,
        entity_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate candidates by combining strategies.
        
        Args:
            entity_id: ID of the entity
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        # Generate candidates from each strategy
        all_candidates = []
        for strategy in self._strategies:
            if not strategy.is_enabled():
                continue
            
            candidates = strategy.generate_candidates(
                entity_id, context, limit
            )
            
            # Add strategy metadata
            for candidate in candidates:
                candidate.setdefault("_sources", []).append(
                    strategy.strategy_type.value
                )
            
            all_candidates.extend(candidates)
        
        # Combine and deduplicate candidates
        combined = self._combine_candidates(all_candidates, context)
        
        return combined[:limit]
    
    def _combine_candidates(
        self,
        candidates: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Combine candidates from multiple strategies.
        
        Args:
            candidates: List of candidates from all strategies
            context: Recommendation context
            
        Returns:
            Combined and deduplicated candidates
        """
        # Deduplicate by ID
        seen_ids = set()
        combined = []
        
        for candidate in candidates:
            candidate_id = candidate.get("id")
            if candidate_id and candidate_id not in seen_ids:
                seen_ids.add(candidate_id)
                combined.append(candidate)
        
        return combined


class StrategyComposition:
    """
    Strategy composition for combining multiple strategies.
    
    Supports different composition methods like weighted sum,
    rank fusion, etc.
    """
    
    def __init__(self, strategies: List[RecommendationStrategy]):
        """
        Initialize strategy composition.
        
        Args:
            strategies: List of strategies to compose
        """
        self._strategies = strategies
    
    def compose(
        self,
        entity_id: str,
        context: Dict[str, Any],
        limit: int,
        method: str = "weighted",
    ) -> List[Dict[str, Any]]:
        """
        Compose strategies to generate candidates.
        
        Args:
            entity_id: ID of the entity
            context: Recommendation context
            limit: Maximum number of candidates
            method: Composition method (weighted, rank, hybrid)
            
        Returns:
            List of candidate items
        """
        if method == "weighted":
            return self._weighted_composition(entity_id, context, limit)
        elif method == "rank":
            return self._rank_composition(entity_id, context, limit)
        elif method == "hybrid":
            return self._hybrid_composition(entity_id, context, limit)
        else:
            return self._weighted_composition(entity_id, context, limit)
    
    def _weighted_composition(
        self,
        entity_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Weighted composition of strategies.
        
        Args:
            entity_id: ID of the entity
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        # Generate candidates from each strategy
        strategy_results = []
        for strategy in self._strategies:
            if not strategy.is_enabled():
                continue
            
            candidates = strategy.generate_candidates(
                entity_id, context, limit
            )
            strategy_results.append({
                "strategy": strategy,
                "candidates": candidates,
                "weight": strategy.get_weight(),
            })
        
        # Combine using weighted scores
        combined = self._weighted_combine(strategy_results)
        
        return combined[:limit]
    
    def _rank_composition(
        self,
        entity_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Rank-based composition of strategies.
        
        Args:
            entity_id: ID of the entity
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        # Generate candidates from each strategy
        strategy_results = []
        for strategy in self._strategies:
            if not strategy.is_enabled():
                continue
            
            candidates = strategy.generate_candidates(
                entity_id, context, limit
            )
            strategy_results.append({
                "strategy": strategy,
                "candidates": candidates,
                "weight": strategy.get_weight(),
            })
        
        # Combine using rank fusion
        combined = self._rank_combine(strategy_results)
        
        return combined[:limit]
    
    def _hybrid_composition(
        self,
        entity_id: str,
        context: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid composition of strategies.
        
        Args:
            entity_id: ID of the entity
            context: Recommendation context
            limit: Maximum number of candidates
            
        Returns:
            List of candidate items
        """
        # Use weighted composition as default
        return self._weighted_composition(entity_id, context, limit)
    
    def _weighted_combine(
        self,
        strategy_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Combine strategy results using weighted averaging.
        
        Args:
            strategy_results: Results from each strategy
            
        Returns:
            Combined candidates
        """
        # Collect all candidates by ID
        all_candidates: Dict[str, Dict[str, Any]] = {}
        
        for result in strategy_results:
            weight = result["weight"]
            candidates = result["candidates"]
            
            for candidate in candidates:
                candidate_id = candidate.get("id", "")
                if candidate_id not in all_candidates:
                    all_candidates[candidate_id] = {
                        "id": candidate_id,
                        "data": candidate,
                        "scores": [],
                        "total_weight": 0.0,
                    }
                
                score = candidate.get("_score", 0.0)
                all_candidates[candidate_id]["scores"].append(score * weight)
                all_candidates[candidate_id]["total_weight"] += weight
        
        # Calculate weighted average scores
        combined = []
        for candidate_id, data in all_candidates.items():
            if data["total_weight"] > 0:
                avg_score = sum(data["scores"]) / data["total_weight"]
            else:
                avg_score = 0.0
            
            candidate = data["data"].copy()
            candidate["_score"] = avg_score
            candidate["_weighted"] = True
            combined.append(candidate)
        
        # Sort by score
        combined.sort(key=lambda x: x.get("_score", 0.0), reverse=True)
        
        return combined
    
    def _rank_combine(
        self,
        strategy_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Combine strategy results using rank fusion.
        
        Args:
            strategy_results: Results from each strategy
            
        Returns:
            Combined candidates
        """
        # Collect all candidates by ID with ranks
        all_candidates: Dict[str, Dict[str, Any]] = {}
        
        for result in strategy_results:
            weight = result["weight"]
            candidates = result["candidates"]
            
            for rank, candidate in enumerate(candidates, start=1):
                candidate_id = candidate.get("id", "")
                if candidate_id not in all_candidates:
                    all_candidates[candidate_id] = {
                        "id": candidate_id,
                        "data": candidate,
                        "ranks": [],
                        "total_weight": 0.0,
                    }
                
                all_candidates[candidate_id]["ranks"].append((rank, weight))
                all_candidates[candidate_id]["total_weight"] += weight
        
        # Calculate rank-based scores (reciprocal rank)
        combined = []
        for candidate_id, data in all_candidates.items():
            rank_score = 0.0
            for rank, weight in data["ranks"]:
                rank_score += weight / rank
            
            candidate = data["data"].copy()
            candidate["_score"] = rank_score
            candidate["_rank_fused"] = True
            combined.append(candidate)
        
        # Sort by score
        combined.sort(key=lambda x: x.get("_score", 0.0), reverse=True)
        
        return combined


class StrategyWeighting:
    """
    Strategy weighting for adjusting strategy weights dynamically.
    
    Supports dynamic weight adjustment based on performance,
    user feedback, etc.
    """
    
    def __init__(self, initial_weights: Optional[Dict[str, float]] = None):
        """
        Initialize strategy weighting.
        
        Args:
            initial_weights: Initial weights for strategies
        """
        self._weights = initial_weights or {}
        self._performance_history: Dict[str, List[float]] = {}
    
    def get_weight(self, strategy_name: str) -> float:
        """
        Get the weight for a strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Strategy weight
        """
        return self._weights.get(strategy_name, 1.0)
    
    def set_weight(self, strategy_name: str, weight: float) -> None:
        """
        Set the weight for a strategy.
        
        Args:
            strategy_name: Name of the strategy
            weight: New weight
        """
        self._weights[strategy_name] = weight
    
    def adjust_weight(
        self,
        strategy_name: str,
        performance: float,
        learning_rate: float = 0.1,
    ) -> None:
        """
        Adjust strategy weight based on performance.
        
        Args:
            strategy_name: Name of the strategy
            performance: Performance metric (0-1)
            learning_rate: Learning rate for adjustment
        """
        current_weight = self.get_weight(strategy_name)
        
        # Adjust weight based on performance
        if performance > 0.5:
            # Increase weight for good performance
            new_weight = current_weight * (1 + learning_rate * performance)
        else:
            # Decrease weight for poor performance
            new_weight = current_weight * (1 - learning_rate * (1 - performance))
        
        # Clamp weight to reasonable range
        new_weight = max(0.1, min(10.0, new_weight))
        
        self.set_weight(strategy_name, new_weight)
        
        # Record performance
        if strategy_name not in self._performance_history:
            self._performance_history[strategy_name] = []
        self._performance_history[strategy_name].append(performance)
    
    def get_performance_score(self, strategy_name: str) -> Optional[float]:
        """
        Get the average performance score for a strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Average performance score or None
        """
        history = self._performance_history.get(strategy_name)
        if not history:
            return None
        
        return sum(history) / len(history)
    
    def reset_weights(self) -> None:
        """Reset all weights to 1.0."""
        self._weights = {}
        self._performance_history = {}
