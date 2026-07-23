"""
Main Query Engine.

This module provides the central QueryEngine that orchestrates all search
operations using the Query DSL, filters, facets, aggregations, highlighting,
autocomplete, and other components. It serves as the single abstraction
responsible for every search request in MatchHire.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import time

from .dsl import Query, DSLQueryBuilder
from .filters import Filter, FilterBuilder, BooleanFilter
from .facets import FacetConfig, FacetBuilder, FacetState, FacetResponse
from .aggregations import Aggregation, AggregationBuilder
from .highlighting import HighlightConfig, HighlightBuilder, HighlightResult
from .autocomplete import AutocompleteEngine, AutocompleteRequest, AutocompleteResponse
from .unified_search import UnifiedSearchEngine, UnifiedSearchRequest, UnifiedSearchResponse
from .sorting import SortBuilder, RankingHooks
from .suggestions import SearchSuggestionEngine
from .performance import QueryCache, QueryOptimizer, PerformanceConfig

from apps.search.schemas.requests import SearchRequest as SchemaSearchRequest
from apps.search.schemas.responses import SearchResponse as SchemaSearchResponse


@dataclass
class SearchExecutionContext:
    """
    Context for a single search execution.
    
    Contains all information needed to execute a search operation.
    """
    
    entity_type: str
    query: str
    filters: List[Union[Filter, BooleanFilter]] = field(default_factory=list)
    sort_conditions: Optional[List[Dict[str, Any]]] = None
    pagination: Optional[Dict[str, Any]] = None
    fields: Optional[List[str]] = None
    facets: List[FacetConfig] = field(default_factory=list)
    aggregations: List[Aggregation] = field(default_factory=list)
    highlights: List[HighlightConfig] = field(default_factory=list)
    facet_state: Optional[FacetState] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "entity_type": self.entity_type,
            "query": self.query,
            "filters": [f.to_dict() for f in self.filters],
            "sort": self.sort_conditions,
            "pagination": self.pagination,
            "fields": self.fields,
            "facets": [f.to_dict() for f in self.facets],
            "aggregations": [a.to_dict() for a in self.aggregations],
            "highlights": [h.to_dict() for h in self.highlights],
            "facet_state": self.facet_state.to_dict() if self.facet_state else None,
            "user_id": self.user_id,
            "metadata": self.metadata,
        }


@dataclass
class EngineResult:
    """
    Result from the query engine.
    
    Contains search results, facets, aggregations, highlights,
    and performance metrics.
    """
    
    results: List[Dict[str, Any]]
    total: int
    took_ms: int
    facets: List[FacetResponse] = field(default_factory=list)
    aggregations: Dict[str, Any] = field(default_factory=dict)
    highlights: Dict[str, HighlightResult] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "results": self.results,
            "total": self.total,
            "took_ms": self.took_ms,
            "facets": [f.to_dict() for f in self.facets],
            "aggregations": self.aggregations,
            "highlights": {k: v.to_dict() for k, v in self.highlights.items()},
            "metadata": self.metadata,
        }


class QueryEngine:
    """
    Central Query Engine for MatchHire search.
    
    This engine is the single abstraction responsible for every search request.
    It transforms SearchRequest objects into optimized queries, applies filters,
    computes facets and aggregations, handles highlighting, and returns unified
    results regardless of the underlying provider (PostgreSQL or Elasticsearch).
    """
    
    def __init__(self, provider_registry, config: Optional[PerformanceConfig] = None):
        """
        Initialize the query engine.
        
        Args:
            provider_registry: Search provider registry
            config: Performance configuration (optional)
        """
        self._provider_registry = provider_registry
        self._config = config or PerformanceConfig()
        
        # Initialize components
        self._cache = QueryCache(self._config)
        self._optimizer = QueryOptimizer(self._config)
        self._autocomplete_engine = AutocompleteEngine()
        self._suggestion_engine = SearchSuggestionEngine()
        self._unified_search_engine = UnifiedSearchEngine(provider_registry)
        self._ranking_hooks = RankingHooks()
    
    def search(
        self,
        request: Union[SchemaSearchRequest, SearchExecutionContext],
        use_cache: bool = True,
    ) -> EngineResult:
        """
        Execute a search request.
        
        Args:
            request: Search request (either SchemaSearchRequest or SearchExecutionContext)
            use_cache: Whether to use query cache
            
        Returns:
            Engine result with search results, facets, aggregations, etc.
        """
        start_time = time.time()
        
        # Convert request to execution context if needed
        if isinstance(request, SchemaSearchRequest):
            context = self._schema_request_to_context(request)
        else:
            context = request
        
        # Check cache if enabled
        if use_cache and self._config.cache_enabled:
            cached_result = self._cache.get(
                entity_type=context.entity_type,
                query=context.query,
                filters=self._filters_to_dict(context.filters),
                sort=context.sort_conditions,
                pagination=context.pagination,
            )
            if cached_result is not None:
                return cached_result
        
        # Get the current provider
        provider_name = self._provider_registry.get_current_provider()
        if not provider_name:
            raise ValueError("No search provider configured")
        
        provider = self._provider_registry.get_provider(provider_name)
        
        # Optimize query
        optimized_query = self._optimizer.optimize_query(
            query=context.query,
            filters=self._filters_to_dict(context.filters),
        )
        
        # Apply pre-ranking hooks
        ranking_context = {
            "entity_type": context.entity_type,
            "query": optimized_query["query"],
            "filters": optimized_query["filters"],
            "user_id": context.user_id,
        }
        self._ranking_hooks.apply_pre_rank_hooks(ranking_context)
        
        # Execute search
        provider_response = provider.search(
            entity_type=context.entity_type,
            query=optimized_query["query"],
            filters=optimized_query["filters"],
            sort=context.sort_conditions,
            pagination=context.pagination,
            fields=context.fields,
        )
        
        # Apply post-ranking hooks
        results = provider_response.get("results", [])
        self._ranking_hooks.apply_post_rank_hooks(results, ranking_context)
        
        # Apply score modifiers
        self._ranking_hooks.apply_score_modifiers(results, ranking_context)
        
        # Compute facets if requested
        facets = []
        if context.facets:
            facets = self._compute_facets(context, provider)
        
        # Compute aggregations if requested
        aggregations = {}
        if context.aggregations:
            aggregations = self._compute_aggregations(context, provider)
        
        # Apply highlighting if requested
        highlights = {}
        if context.highlights:
            highlights = self._apply_highlighting(context, results, provider)
        
        # Build result
        took_ms = int((time.time() - start_time) * 1000)
        
        result = EngineResult(
            results=results,
            total=provider_response.get("total", 0),
            took_ms=took_ms,
            facets=facets,
            aggregations=aggregations,
            highlights=highlights,
            metadata={
                "provider": provider_name,
                "query": optimized_query["query"],
                "cached": False,
            },
        )
        
        # Cache result if enabled
        if use_cache and self._config.cache_enabled:
            self._cache.set(
                entity_type=context.entity_type,
                query=context.query,
                value=result,
                filters=self._filters_to_dict(context.filters),
                sort=context.sort_conditions,
                pagination=context.pagination,
            )
        
        return result
    
    def autocomplete(
        self,
        request: AutocompleteRequest,
    ) -> AutocompleteResponse:
        """
        Get autocomplete suggestions.
        
        Args:
            request: Autocomplete request
            
        Returns:
            Autocomplete response with suggestions
        """
        return self._autocomplete_engine.generate_suggestions(request)
    
    def unified_search(
        self,
        request: UnifiedSearchRequest,
    ) -> UnifiedSearchResponse:
        """
        Execute a unified multi-entity search.
        
        Args:
            request: Unified search request
            
        Returns:
            Unified search response
        """
        return self._unified_search_engine.search(request)
    
    def add_ranking_hook(
        self,
        hook_type: str,
        hook: callable,
    ) -> None:
        """
        Add a ranking hook.
        
        Args:
            hook_type: Type of hook (pre_rank, post_rank, score_modifier)
            hook: Hook function
        """
        if hook_type == "pre_rank":
            self._ranking_hooks.add_pre_rank_hook(hook)
        elif hook_type == "post_rank":
            self._ranking_hooks.add_post_rank_hook(hook)
        elif hook_type == "score_modifier":
            self._ranking_hooks.add_score_modifier(hook)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        return self._cache.get_stats()
    
    def clear_cache(self) -> None:
        """Clear the query cache."""
        self._cache.clear()
    
    def invalidate_cache(
        self,
        entity_type: Optional[str] = None,
    ) -> None:
        """
        Invalidate cache entries.
        
        Args:
            entity_type: Entity type to invalidate (None for all)
        """
        self._cache.invalidate(entity_type)
    
    def _schema_request_to_context(
        self,
        request: SchemaSearchRequest,
    ) -> SearchExecutionContext:
        """
        Convert a SchemaSearchRequest to SearchExecutionContext.
        
        Args:
            request: Schema search request
            
        Returns:
            Search execution context
        """
        # Convert filters to Filter objects
        filters = []
        for filter_obj in request.filters:
            # This is a simplified conversion
            # In production, you'd have proper filter conversion
            pass
        
        return SearchExecutionContext(
            entity_type=request.entity_type,
            query=request.query,
            filters=filters,
            sort_conditions=[s.to_dict() for s in request.sort],
            pagination=request.pagination.to_dict() if request.pagination else None,
            fields=request.fields,
        )
    
    def _filters_to_dict(
        self,
        filters: List[Union[Filter, BooleanFilter]],
    ) -> Dict[str, Any]:
        """
        Convert filters to dictionary format.
        
        Args:
            filters: List of filter objects
            
        Returns:
            Dictionary representation of filters
        """
        # This is a simplified implementation
        # In production, you'd have proper filter serialization
        filter_dict = {}
        for filter_obj in filters:
            filter_dict.update(filter_obj.to_dict())
        return filter_dict
    
    def _compute_facets(
        self,
        context: SearchExecutionContext,
        provider,
    ) -> List[FacetResponse]:
        """
        Compute facets for the search results.
        
        Args:
            context: Search execution context
            provider: Search provider
            
        Returns:
            List of facet responses
        """
        # This is a placeholder - actual facet computation would be
        # done by the provider or a separate facet aggregation
        # For now, return empty list
        return []
    
    def _compute_aggregations(
        self,
        context: SearchExecutionContext,
        provider,
    ) -> Dict[str, Any]:
        """
        Compute aggregations for the search results.
        
        Args:
            context: Search execution context
            provider: Search provider
            
        Returns:
            Aggregation results
        """
        # This is a placeholder - actual aggregation computation would be
        # done by the provider or a separate aggregation service
        # For now, return empty dict
        return {}
    
    def _apply_highlighting(
        self,
        context: SearchExecutionContext,
        results: List[Dict[str, Any]],
        provider,
    ) -> Dict[str, HighlightResult]:
        """
        Apply highlighting to search results.
        
        Args:
            context: Search execution context
            results: Search results
            provider: Search provider
            
        Returns:
            Dictionary of highlight results by document ID
        """
        # This is a placeholder - actual highlighting would be
        # done by the provider or a separate highlighting service
        # For now, return empty dict
        return {}
    
    def get_suggestion_engine(self) -> SearchSuggestionEngine:
        """
        Get the search suggestion engine.
        
        Returns:
            Search suggestion engine
        """
        return self._suggestion_engine
    
    def get_autocomplete_engine(self) -> AutocompleteEngine:
        """
        Get the autocomplete engine.
        
        Returns:
            Autocomplete engine
        """
        return self._autocomplete_engine
    
    def get_ranking_hooks(self) -> RankingHooks:
        """
        Get the ranking hooks.
        
        Returns:
            Ranking hooks
        """
        return self._ranking_hooks
