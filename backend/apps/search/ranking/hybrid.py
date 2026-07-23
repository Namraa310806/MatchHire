"""
Hybrid Search Framework.

This module provides a framework for combining multiple search strategies
(e.g., lexical, semantic, vector) using various fusion strategies.
The framework is provider-independent and extensible for future semantic search.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import math


class FusionStrategy(Enum):
    """Types of fusion strategies for combining search results."""
    WEIGHTED = "weighted"
    RANK = "rank"
    RECIPROCAL_RANK = "reciprocal_rank"
    CONDORCET = "condorcet"
    COMBO = "combo"


@dataclass
class SearchResult:
    """
    A single search result with metadata for fusion.
    """
    
    document_id: str
    score: float
    rank: int
    source: str
    document: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "document_id": self.document_id,
            "score": self.score,
            "rank": self.rank,
            "source": self.source,
            "document": self.document,
            "metadata": self.metadata,
        }


@dataclass
class StrategyResult:
    """
    Result from a single search strategy.
    """
    
    strategy_name: str
    results: List[SearchResult]
    total: int
    took_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "strategy_name": self.strategy_name,
            "results": [r.to_dict() for r in self.results],
            "total": self.total,
            "took_ms": self.took_ms,
            "metadata": self.metadata,
        }


class SearchStrategy(ABC):
    """
    Abstract base class for search strategies.
    
    Each strategy implements a different search approach
    (lexical, semantic, vector, metadata, etc.).
    """
    
    def __init__(self, name: str, weight: float = 1.0):
        """
        Initialize the search strategy.
        
        Args:
            name: Strategy name
            weight: Strategy weight in fusion
        """
        self.name = name
        self.weight = weight
    
    @abstractmethod
    def search(
        self,
        entity_type: str,
        query: str,
        context: Dict[str, Any],
        provider: Any,
    ) -> StrategyResult:
        """
        Execute search using this strategy.
        
        Args:
            entity_type: Type of entity to search
            query: Search query
            context: Search context
            provider: Search provider instance
            
        Returns:
            Strategy result with ranked results
        """
        pass
    
    def get_weight(self) -> float:
        """Get the strategy weight."""
        return self.weight
    
    def set_weight(self, weight: float) -> None:
        """Set the strategy weight."""
        self.weight = weight


class LexicalStrategy(SearchStrategy):
    """
    Lexical search strategy using text matching.
    
    This strategy uses traditional full-text search with
    term frequency, field matching, and relevance scoring.
    """
    
    def __init__(self, weight: float = 1.0):
        """Initialize the lexical strategy."""
        super().__init__("lexical", weight)
    
    def search(
        self,
        entity_type: str,
        query: str,
        context: Dict[str, Any],
        provider: Any,
    ) -> StrategyResult:
        """
        Execute lexical search.
        
        Args:
            entity_type: Type of entity to search
            query: Search query
            context: Search context
            provider: Search provider instance
            
        Returns:
            Strategy result with ranked results
        """
        import time
        
        start_time = time.time()
        
        # Execute search through provider
        response = provider.search(
            entity_type=entity_type,
            query=query,
            filters=context.get("filters"),
            sort=context.get("sort"),
            pagination=context.get("pagination"),
            fields=context.get("fields"),
        )
        
        took_ms = (time.time() - start_time) * 1000
        
        # Convert to SearchResult objects
        results = []
        for rank, doc in enumerate(response.get("results", []), start=1):
            result = SearchResult(
                document_id=doc.get("id", ""),
                score=doc.get("_score", 0.0),
                rank=rank,
                source=self.name,
                document=doc,
            )
            results.append(result)
        
        return StrategyResult(
            strategy_name=self.name,
            results=results,
            total=response.get("total", 0),
            took_ms=took_ms,
        )


class MetadataStrategy(SearchStrategy):
    """
    Metadata search strategy using structured field matching.
    
    This strategy searches based on structured metadata fields
    like category, tags, industry, location, etc.
    """
    
    def __init__(self, weight: float = 0.5):
        """Initialize the metadata strategy."""
        super().__init__("metadata", weight)
    
    def search(
        self,
        entity_type: str,
        query: str,
        context: Dict[str, Any],
        provider: Any,
    ) -> StrategyResult:
        """
        Execute metadata search.
        
        Args:
            entity_type: Type of entity to search
            query: Search query
            context: Search context
            provider: Search provider instance
            
        Returns:
            Strategy result with ranked results
        """
        import time
        
        start_time = time.time()
        
        # Build metadata-based filters
        filters = context.get("filters", {}).copy()
        
        # Add query as a filter if it matches metadata fields
        if query:
            filters["title"] = query
        
        # Execute search
        response = provider.search(
            entity_type=entity_type,
            query="",  # Empty query for pure metadata search
            filters=filters,
            sort=context.get("sort"),
            pagination=context.get("pagination"),
            fields=context.get("fields"),
        )
        
        took_ms = (time.time() - start_time) * 1000
        
        # Convert to SearchResult objects
        results = []
        for rank, doc in enumerate(response.get("results", []), start=1):
            result = SearchResult(
                document_id=doc.get("id", ""),
                score=doc.get("_score", 0.0),
                rank=rank,
                source=self.name,
                document=doc,
            )
            results.append(result)
        
        return StrategyResult(
            strategy_name=self.name,
            results=results,
            total=response.get("total", 0),
            took_ms=took_ms,
        )


class SemanticStrategy(SearchStrategy):
    """
    Semantic search strategy using embeddings.
    
    This strategy uses semantic embeddings for vector similarity search.
    This is an interface for future semantic search implementation.
    """
    
    def __init__(self, weight: float = 0.8):
        """Initialize the semantic strategy."""
        super().__init__("semantic", weight)
    
    def search(
        self,
        entity_type: str,
        query: str,
        context: Dict[str, Any],
        provider: Any,
    ) -> StrategyResult:
        """
        Execute semantic search.
        
        Args:
            entity_type: Type of entity to search
            query: Search query
            context: Search context
            provider: Search provider instance
            
        Returns:
            Strategy result with ranked results
        """
        import time
        
        start_time = time.time()
        
        # Placeholder for future semantic search implementation
        # For now, fall back to lexical search
        response = provider.search(
            entity_type=entity_type,
            query=query,
            filters=context.get("filters"),
            sort=context.get("sort"),
            pagination=context.get("pagination"),
            fields=context.get("fields"),
        )
        
        took_ms = (time.time() - start_time) * 1000
        
        # Convert to SearchResult objects
        results = []
        for rank, doc in enumerate(response.get("results", []), start=1):
            result = SearchResult(
                document_id=doc.get("id", ""),
                score=doc.get("_score", 0.0),
                rank=rank,
                source=self.name,
                document=doc,
                metadata={"semantic_score": doc.get("_score", 0.0)},
            )
            results.append(result)
        
        return StrategyResult(
            strategy_name=self.name,
            results=results,
            total=response.get("total", 0),
            took_ms=took_ms,
            metadata={"note": "Semantic search not yet implemented, using lexical fallback"},
        )


class VectorStrategy(SearchStrategy):
    """
    Vector search strategy using dense vectors.
    
    This strategy uses vector similarity for search.
    This is an interface for future vector search implementation.
    """
    
    def __init__(self, weight: float = 0.7):
        """Initialize the vector strategy."""
        super().__init__("vector", weight)
    
    def search(
        self,
        entity_type: str,
        query: str,
        context: Dict[str, Any],
        provider: Any,
    ) -> StrategyResult:
        """
        Execute vector search.
        
        Args:
            entity_type: Type of entity to search
            query: Search query
            context: Search context
            provider: Search provider instance
            
        Returns:
            Strategy result with ranked results
        """
        import time
        
        start_time = time.time()
        
        # Placeholder for future vector search implementation
        # For now, return empty results
        took_ms = (time.time() - start_time) * 1000
        
        return StrategyResult(
            strategy_name=self.name,
            results=[],
            total=0,
            took_ms=took_ms,
            metadata={"note": "Vector search not yet implemented"},
        )


class FusionAlgorithm(ABC):
    """
    Abstract base class for fusion algorithms.
    
    Each algorithm implements a different method for combining
    results from multiple search strategies.
    """
    
    @abstractmethod
    def fuse(
        self,
        strategy_results: List[StrategyResult],
    ) -> List[SearchResult]:
        """
        Fuse results from multiple strategies.
        
        Args:
            strategy_results: Results from each strategy
            
        Returns:
            Fused and ranked results
        """
        pass


class WeightedFusion(FusionAlgorithm):
    """
    Weighted fusion algorithm.
    
    Combines scores from multiple strategies using weighted averaging.
    """
    
    def __init__(self, normalize_scores: bool = True):
        """
        Initialize weighted fusion.
        
        Args:
            normalize_scores: Whether to normalize scores before fusion
        """
        self.normalize_scores = normalize_scores
    
    def fuse(
        self,
        strategy_results: List[StrategyResult],
    ) -> List[SearchResult]:
        """
        Fuse results using weighted averaging.
        
        Args:
            strategy_results: Results from each strategy
            
        Returns:
            Fused and ranked results
        """
        # Collect all document IDs
        all_results: Dict[str, Dict[str, Any]] = {}
        
        for strategy_result in strategy_results:
            weight = strategy_result.strategy_name  # Will be replaced with actual weight
            results = strategy_result.results
            
            if self.normalize_scores:
                # Normalize scores to [0, 1]
                scores = [r.score for r in results]
                if scores:
                    min_score = min(scores)
                    max_score = max(scores)
                    if max_score > min_score:
                        for r in results:
                            r.score = (r.score - min_score) / (max_score - min_score)
            
            for result in results:
                doc_id = result.document_id
                if doc_id not in all_results:
                    all_results[doc_id] = {
                        "document_id": doc_id,
                        "document": result.document,
                        "scores": {},
                        "sources": [],
                    }
                
                all_results[doc_id]["scores"][strategy_result.strategy_name] = result.score
                all_results[doc_id]["sources"].append(strategy_result.strategy_name)
        
        # Calculate weighted scores
        fused_results = []
        for doc_id, data in all_results.items():
            weighted_score = 0.0
            total_weight = 0.0
            
            for strategy_name, score in data["scores"].items():
                # Find strategy weight (simplified)
                weight = 1.0  # In production, get from strategy config
                weighted_score += score * weight
                total_weight += weight
            
            if total_weight > 0:
                weighted_score /= total_weight
            
            fused_result = SearchResult(
                document_id=doc_id,
                score=weighted_score,
                rank=0,  # Will be assigned after sorting
                source="hybrid",
                document=data["document"],
                metadata={
                    "sources": data["sources"],
                    "strategy_scores": data["scores"],
                },
            )
            fused_results.append(fused_result)
        
        # Sort by score and assign ranks
        fused_results.sort(key=lambda x: x.score, reverse=True)
        for rank, result in enumerate(fused_results, start=1):
            result.rank = rank
        
        return fused_results


class RankFusion(FusionAlgorithm):
    """
    Rank fusion algorithm.
    
    Combines results based on rank positions rather than scores.
    """
    
    def fuse(
        self,
        strategy_results: List[StrategyResult],
    ) -> List[SearchResult]:
        """
        Fuse results using rank-based fusion.
        
        Args:
            strategy_results: Results from each strategy
            
        Returns:
            Fused and ranked results
        """
        # Collect all document IDs with ranks
        all_results: Dict[str, Dict[str, Any]] = {}
        
        for strategy_result in strategy_results:
            results = strategy_result.results
            
            for result in results:
                doc_id = result.document_id
                if doc_id not in all_results:
                    all_results[doc_id] = {
                        "document_id": doc_id,
                        "document": result.document,
                        "ranks": {},
                        "sources": [],
                    }
                
                all_results[doc_id]["ranks"][strategy_result.strategy_name] = result.rank
                all_results[doc_id]["sources"].append(strategy_result.strategy_name)
        
        # Calculate rank-based scores (inverse rank)
        fused_results = []
        for doc_id, data in all_results.items():
            rank_score = 0.0
            
            for strategy_name, rank in data["ranks"].items():
                # Inverse rank: higher rank (lower number) = higher score
                rank_score += 1.0 / rank
            
            fused_result = SearchResult(
                document_id=doc_id,
                score=rank_score,
                rank=0,
                source="hybrid",
                document=data["document"],
                metadata={
                    "sources": data["sources"],
                    "strategy_ranks": data["ranks"],
                },
            )
            fused_results.append(fused_result)
        
        # Sort by score and assign ranks
        fused_results.sort(key=lambda x: x.score, reverse=True)
        for rank, result in enumerate(fused_results, start=1):
            result.rank = rank
        
        return fused_results


class ReciprocalRankFusion(FusionAlgorithm):
    """
    Reciprocal Rank Fusion (RRF) algorithm.
    
    A well-established fusion algorithm that uses reciprocal rank
    with a constant parameter to control the influence of rank.
    """
    
    def __init__(self, k: int = 60):
        """
        Initialize RRF.
        
        Args:
            k: Constant parameter (typically 60)
        """
        self.k = k
    
    def fuse(
        self,
        strategy_results: List[StrategyResult],
    ) -> List[SearchResult]:
        """
        Fuse results using RRF.
        
        Args:
            strategy_results: Results from each strategy
            
        Returns:
            Fused and ranked results
        """
        # Collect all document IDs with ranks
        all_results: Dict[str, Dict[str, Any]] = {}
        
        for strategy_result in strategy_results:
            results = strategy_result.results
            
            for result in results:
                doc_id = result.document_id
                if doc_id not in all_results:
                    all_results[doc_id] = {
                        "document_id": doc_id,
                        "document": result.document,
                        "ranks": {},
                        "sources": [],
                    }
                
                all_results[doc_id]["ranks"][strategy_result.strategy_name] = result.rank
                all_results[doc_id]["sources"].append(strategy_result.strategy_name)
        
        # Calculate RRF scores
        fused_results = []
        for doc_id, data in all_results.items():
            rrf_score = 0.0
            
            for strategy_name, rank in data["ranks"].items():
                rrf_score += 1.0 / (self.k + rank)
            
            fused_result = SearchResult(
                document_id=doc_id,
                score=rrf_score,
                rank=0,
                source="hybrid",
                document=data["document"],
                metadata={
                    "sources": data["sources"],
                    "strategy_ranks": data["ranks"],
                    "fusion_method": "rrf",
                    "k": self.k,
                },
            )
            fused_results.append(fused_result)
        
        # Sort by score and assign ranks
        fused_results.sort(key=lambda x: x.score, reverse=True)
        for rank, result in enumerate(fused_results, start=1):
            result.rank = rank
        
        return fused_results


class CondorcetFusion(FusionAlgorithm):
    """
    Condorcet fusion algorithm.
    
    Uses pairwise comparisons to determine the winner.
    A document wins if it is ranked higher than another document
    by a majority of strategies.
    """
    
    def fuse(
        self,
        strategy_results: List[StrategyResult],
    ) -> List[SearchResult]:
        """
        Fuse results using Condorcet method.
        
        Args:
            strategy_results: Results from each strategy
            
        Returns:
            Fused and ranked results
        """
        # Collect all document IDs with ranks
        all_results: Dict[str, Dict[str, Any]] = {}
        
        for strategy_result in strategy_results:
            results = strategy_result.results
            
            for result in results:
                doc_id = result.document_id
                if doc_id not in all_results:
                    all_results[doc_id] = {
                        "document_id": doc_id,
                        "document": result.document,
                        "ranks": {},
                        "sources": [],
                    }
                
                all_results[doc_id]["ranks"][strategy_result.strategy_name] = result.rank
                all_results[doc_id]["sources"].append(strategy_result.strategy_name)
        
        # Calculate Condorcet scores (wins in pairwise comparisons)
        doc_ids = list(all_results.keys())
        wins: Dict[str, int] = {doc_id: 0 for doc_id in doc_ids}
        
        for i, doc_id1 in enumerate(doc_ids):
            for doc_id2 in doc_ids[i + 1:]:
                # Compare doc_id1 vs doc_id2
                wins1 = 0
                wins2 = 0
                
                for strategy_name in all_results[doc_id1]["ranks"]:
                    rank1 = all_results[doc_id1]["ranks"][strategy_name]
                    rank2 = all_results[doc_id2]["ranks"].get(strategy_name, float('inf'))
                    
                    if rank1 < rank2:
                        wins1 += 1
                    elif rank2 < rank1:
                        wins2 += 1
                
                if wins1 > wins2:
                    wins[doc_id1] += 1
                elif wins2 > wins1:
                    wins[doc_id2] += 1
        
        # Create fused results
        fused_results = []
        for doc_id, data in all_results.items():
            fused_result = SearchResult(
                document_id=doc_id,
                score=float(wins[doc_id]),
                rank=0,
                source="hybrid",
                document=data["document"],
                metadata={
                    "sources": data["sources"],
                    "strategy_ranks": data["ranks"],
                    "fusion_method": "condorcet",
                    "pairwise_wins": wins[doc_id],
                },
            )
            fused_results.append(fused_result)
        
        # Sort by score and assign ranks
        fused_results.sort(key=lambda x: x.score, reverse=True)
        for rank, result in enumerate(fused_results, start=1):
            result.rank = rank
        
        return fused_results


class HybridSearchEngine:
    """
    Hybrid search engine for combining multiple search strategies.
    
    This engine orchestrates multiple search strategies and fuses
    their results using configurable fusion algorithms.
    """
    
    def __init__(self, provider_registry):
        """
        Initialize the hybrid search engine.
        
        Args:
            provider_registry: Search provider registry
        """
        self._provider_registry = provider_registry
        self._strategies: List[SearchStrategy] = []
        self._fusion_algorithm: FusionAlgorithm = ReciprocalRankFusion()
        
        # Register default strategies
        self.register_strategy(LexicalStrategy(weight=1.0))
        self.register_strategy(MetadataStrategy(weight=0.5))
    
    def register_strategy(self, strategy: SearchStrategy) -> None:
        """
        Register a search strategy.
        
        Args:
            strategy: Search strategy to register
        """
        self._strategies.append(strategy)
    
    def set_fusion_algorithm(self, algorithm: FusionAlgorithm) -> None:
        """
        Set the fusion algorithm.
        
        Args:
            algorithm: Fusion algorithm to use
        """
        self._fusion_algorithm = algorithm
    
    def search(
        self,
        entity_type: str,
        query: str,
        context: Dict[str, Any],
        fusion_strategy: Optional[FusionStrategy] = None,
    ) -> Dict[str, Any]:
        """
        Execute hybrid search.
        
        Args:
            entity_type: Type of entity to search
            query: Search query
            context: Search context
            fusion_strategy: Fusion strategy to use (uses default if None)
            
        Returns:
            Hybrid search result with fused results
        """
        import time
        
        start_time = time.time()
        
        # Get the current provider
        provider_name = self._provider_registry.get_current_provider()
        if not provider_name:
            raise ValueError("No search provider configured")
        
        provider = self._provider_registry.get_provider(provider_name)
        
        # Execute each strategy
        strategy_results = []
        for strategy in self._strategies:
            if strategy.get_weight() == 0:
                continue
            
            try:
                result = strategy.search(entity_type, query, context, provider)
                strategy_results.append(result)
            except Exception as e:
                # Log error but continue with other strategies
                print(f"Strategy {strategy.name} failed: {e}")
        
        # Set fusion algorithm if specified
        if fusion_strategy:
            if fusion_strategy == FusionStrategy.WEIGHTED:
                self._fusion_algorithm = WeightedFusion()
            elif fusion_strategy == FusionStrategy.RANK:
                self._fusion_algorithm = RankFusion()
            elif fusion_strategy == FusionStrategy.RECIPROCAL_RANK:
                self._fusion_algorithm = ReciprocalRankFusion()
            elif fusion_strategy == FusionStrategy.CONDORCET:
                self._fusion_algorithm = CondorcetFusion()
        
        # Fuse results
        fused_results = self._fusion_algorithm.fuse(strategy_results)
        
        took_ms = (time.time() - start_time) * 1000
        
        # Build response
        return {
            "results": [r.to_dict() for r in fused_results],
            "total": len(fused_results),
            "took_ms": took_ms,
            "strategies_used": [r.strategy_name for r in strategy_results],
            "fusion_method": self._fusion_algorithm.__class__.__name__,
            "strategy_details": [r.to_dict() for r in strategy_results],
        }
    
    def get_strategies(self) -> List[SearchStrategy]:
        """
        Get registered strategies.
        
        Returns:
            List of registered strategies
        """
        return self._strategies.copy()
    
    def get_fusion_algorithm(self) -> FusionAlgorithm:
        """
        Get the current fusion algorithm.
        
        Returns:
            Current fusion algorithm
        """
        return self._fusion_algorithm
