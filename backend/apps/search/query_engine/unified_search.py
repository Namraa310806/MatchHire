"""
Unified multi-entity search.

This module provides the ability to search across multiple entity types
simultaneously, with unified response formatting, entity grouping,
and cross-entity pagination.
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class EntityType(Enum):
    """Entity types that can be searched."""
    JOB = "job"
    CANDIDATE = "candidate"
    RESUME = "resume"
    COMPANY = "company"
    RECRUITER = "recruiter"
    SKILL = "skill"
    APPLICATION = "application"
    INTERVIEW = "interview"


@dataclass
class UnifiedSearchRequest:
    """
    Request for unified multi-entity search.
    """
    
    query: str
    entity_types: List[EntityType]
    filters: Dict[str, Any] = field(default_factory=dict)
    sort: Optional[List[Dict[str, Any]]] = None
    pagination: Optional[Dict[str, Any]] = None
    fields: Optional[List[str]] = None
    per_entity_limit: int = 10
    total_limit: int = 50
    include_facets: bool = False
    facet_configs: Optional[List[Dict[str, Any]]] = None
    
    def __post_init__(self):
        """Validate request parameters."""
        if not self.query:
            raise ValueError("query is required")
        if not self.entity_types:
            raise ValueError("at least one entity_type is required")
        if self.per_entity_limit < 1:
            raise ValueError("per_entity_limit must be >= 1")
        if self.total_limit < 1:
            raise ValueError("total_limit must be >= 1")
        
        # Set default pagination if not provided
        if self.pagination is None:
            self.pagination = {"page": 1, "page_size": 20}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query": self.query,
            "entity_types": [et.value for et in self.entity_types],
            "filters": self.filters,
            "sort": self.sort,
            "pagination": self.pagination,
            "fields": self.fields,
            "per_entity_limit": self.per_entity_limit,
            "total_limit": self.total_limit,
            "include_facets": self.include_facets,
            "facet_configs": self.facet_configs,
        }


@dataclass
class EntitySearchResult:
    """
    Search results for a single entity type.
    """
    
    entity_type: EntityType
    results: List[Dict[str, Any]]
    total: int
    took_ms: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "entity_type": self.entity_type.value,
            "results": self.results,
            "total": self.total,
            "took_ms": self.took_ms,
            "metadata": self.metadata,
        }


@dataclass
class UnifiedSearchResponse:
    """
    Response from unified multi-entity search.
    """
    
    query: str
    entity_results: Dict[EntityType, EntitySearchResult]
    total_results: int
    took_ms: int
    pagination: Optional[Dict[str, Any]] = None
    facets: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query": self.query,
            "entity_results": {
                et.value: result.to_dict()
                for et, result in self.entity_results.items()
            },
            "total_results": self.total_results,
            "took_ms": self.took_ms,
            "pagination": self.pagination,
            "facets": self.facets,
            "metadata": self.metadata,
        }
    
    def get_entity_results(self, entity_type: EntityType) -> Optional[EntitySearchResult]:
        """Get results for a specific entity type."""
        return self.entity_results.get(entity_type)
    
    def get_all_results(self) -> List[Dict[str, Any]]:
        """Get all results across all entity types."""
        all_results = []
        for result in self.entity_results.values():
            all_results.extend(result.results)
        return all_results
    
    def get_entity_count(self, entity_type: EntityType) -> int:
        """Get the count of results for a specific entity type."""
        if entity_type in self.entity_results:
            return self.entity_results[entity_type].total
        return 0
    
    def get_searched_entity_types(self) -> List[EntityType]:
        """Get list of entity types that were searched."""
        return list(self.entity_results.keys())


class UnifiedSearchEngine:
    """
    Engine for executing unified multi-entity searches.
    
    This engine coordinates searches across multiple entity types,
    aggregates results, and provides a unified response format.
    """
    
    def __init__(self, provider_registry):
        """
        Initialize the unified search engine.
        
        Args:
            provider_registry: Search provider registry
        """
        self._provider_registry = provider_registry
    
    def search(
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
        import time
        start_time = time.time()
        
        entity_results: Dict[EntityType, EntitySearchResult] = {}
        total_results = 0
        
        # Get the current provider
        provider = self._provider_registry.get_current_provider()
        if not provider:
            raise ValueError("No search provider configured")
        
        provider_instance = self._provider_registry.get_provider(provider)
        
        # Search each entity type
        for entity_type in request.entity_types:
            entity_search_start = time.time()
            
            try:
                # Convert filters for this entity type
                entity_filters = self._convert_filters_for_entity(
                    request.filters,
                    entity_type
                )
                
                # Execute search
                provider_response = provider_instance.search(
                    entity_type=entity_type.value,
                    query=request.query,
                    filters=entity_filters,
                    sort=request.sort,
                    pagination={"offset": 0, "limit": request.per_entity_limit},
                    fields=request.fields,
                )
                
                # Create entity result
                entity_result = EntitySearchResult(
                    entity_type=entity_type,
                    results=provider_response.get("results", []),
                    total=provider_response.get("total", 0),
                    took_ms=provider_response.get("took_ms", 0),
                    metadata=provider_response.get("metadata", {}),
                )
                
                entity_results[entity_type] = entity_result
                total_results += entity_result.total
                
            except Exception as e:
                # Log error but continue with other entity types
                entity_results[entity_type] = EntitySearchResult(
                    entity_type=entity_type,
                    results=[],
                    total=0,
                    took_ms=0,
                    metadata={"error": str(e)},
                )
        
        # Apply total limit across all entities
        all_results = []
        for entity_type in request.entity_types:
            if entity_type in entity_results:
                all_results.extend(entity_results[entity_type].results)
        
        # Truncate to total limit
        if len(all_results) > request.total_limit:
            all_results = all_results[:request.total_limit]
            
            # Update entity results to reflect truncation
            # This is a simplified approach - in production, you'd want
            # more sophisticated cross-entity pagination
            remaining = request.total_limit
            for entity_type in request.entity_types:
                if entity_type in entity_results:
                    entity_result = entity_results[entity_type]
                    take = min(len(entity_result.results), remaining)
                    entity_result.results = entity_result.results[:take]
                    remaining -= take
                    if remaining <= 0:
                        break
        
        took_ms = int((time.time() - start_time) * 1000)
        
        return UnifiedSearchResponse(
            query=request.query,
            entity_results=entity_results,
            total_results=total_results,
            took_ms=took_ms,
            pagination=request.pagination,
            facets=self._compute_facets(request, entity_results) if request.include_facets else {},
            metadata={
                "provider": provider,
                "entity_types_searched": [et.value for et in request.entity_types],
            },
        )
    
    def _convert_filters_for_entity(
        self,
        filters: Dict[str, Any],
        entity_type: EntityType,
    ) -> Dict[str, Any]:
        """
        Convert generic filters to entity-specific filters.
        
        Args:
            filters: Generic filters
            entity_type: Target entity type
            
        Returns:
            Entity-specific filters
        """
        # This is a simplified implementation
        # In production, you'd have a more sophisticated filter mapping
        entity_filters = filters.copy()
        
        # Add entity-specific filter mappings here
        # For example, "location" might map to different fields for different entities
        
        return entity_filters
    
    def _compute_facets(
        self,
        request: UnifiedSearchRequest,
        entity_results: Dict[EntityType, EntitySearchResult],
    ) -> Dict[str, Any]:
        """
        Compute facets across all entity types.
        
        Args:
            request: Search request
            entity_results: Results by entity type
            
        Returns:
            Facet results
        """
        # This is a placeholder - actual facet computation would be
        # done by the provider or a separate facet aggregation
        return {}
    
    def search_jobs_and_candidates(
        self,
        query: str,
        **kwargs
    ) -> UnifiedSearchResponse:
        """
        Convenience method to search jobs and candidates.
        
        Args:
            query: Search query
            **kwargs: Additional search parameters
            
        Returns:
            Unified search response
        """
        request = UnifiedSearchRequest(
            query=query,
            entity_types=[EntityType.JOB, EntityType.CANDIDATE],
            **kwargs
        )
        return self.search(request)
    
    def search_all_entities(
        self,
        query: str,
        **kwargs
    ) -> UnifiedSearchResponse:
        """
        Convenience method to search all entity types.
        
        Args:
            query: Search query
            **kwargs: Additional search parameters
            
        Returns:
            Unified search response
        """
        request = UnifiedSearchRequest(
            query=query,
            entity_types=list(EntityType),
            **kwargs
        )
        return self.search(request)
