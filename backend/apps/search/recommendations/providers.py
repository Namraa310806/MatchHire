"""
Recommendation Providers.

This module provides provider-independent recommendation interfaces.
Providers are responsible for generating candidates for different
recommendation types (candidates, jobs, related entities).
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
from threading import Lock


class RecommendationProviderType(Enum):
    """Types of recommendation providers."""
    CANDIDATE = "candidate"
    JOB = "job"
    RELATED_ENTITY = "related_entity"


class RecommendationProvider(ABC):
    """
    Abstract base class for recommendation providers.
    
    Each provider implements candidate generation for a specific
    recommendation type. Providers are provider-independent and
    use the Query Engine for candidate generation.
    """
    
    def __init__(self, query_engine, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the recommendation provider.
        
        Args:
            query_engine: Query engine for candidate generation
            config: Provider configuration
        """
        self._query_engine = query_engine
        self._config = config or {}
    
    @property
    def provider_type(self) -> RecommendationProviderType:
        """Get the provider type."""
        return RecommendationProviderType.CANDIDATE
    
    @abstractmethod
    def generate_candidates(
        self,
        entity_id: str,
        context: Dict[str, Any],
        limit: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate candidate recommendations.
        
        Args:
            entity_id: ID of the entity to generate recommendations for
            context: Recommendation context
            limit: Maximum number of candidates to generate
            filters: Optional filters to apply
            
        Returns:
            List of candidate items
        """
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get provider configuration.
        
        Returns:
            Provider configuration
        """
        return self._config.copy()


class CandidateRecommendationProvider(RecommendationProvider):
    """
    Provider for candidate recommendations.
    
    Generates candidate recommendations for jobs and recruiters.
    """
    
    @property
    def provider_type(self) -> RecommendationProviderType:
        return RecommendationProviderType.CANDIDATE
    
    def generate_candidates(
        self,
        entity_id: str,
        context: Dict[str, Any],
        limit: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate candidate recommendations.
        
        Args:
            entity_id: ID of the job or recruiter
            context: Recommendation context
            limit: Maximum number of candidates
            filters: Optional filters
            
        Returns:
            List of candidate items
        """
        # Use query engine to search for candidates
        from apps.search.query_engine import SearchExecutionContext
        
        # Build search context from recommendation context
        search_context = SearchExecutionContext(
            entity_type="candidate",
            query=context.get("query", ""),
            filters=self._build_filters(context, filters),
            pagination={"limit": limit * 2, "offset": 0},  # Get more for diversification
            user_id=context.get("user_id"),
            metadata=context,
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        return result.results
    
    def _build_filters(
        self,
        context: Dict[str, Any],
        additional_filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build search filters from context.
        
        Args:
            context: Recommendation context
            additional_filters: Additional filters
            
        Returns:
            Combined filters
        """
        filters = {}
        
        # Add skill filters
        if "required_skills" in context:
            filters["skills"] = context["required_skills"]
        
        # Add experience filter
        if "required_experience" in context:
            filters["experience_years"] = context["required_experience"]
        
        # Add location filter
        if "required_location" in context:
            filters["location"] = context["required_location"]
        
        # Add education filter
        if "required_education" in context:
            filters["education_level"] = context["required_education"]
        
        # Add additional filters
        if additional_filters:
            filters.update(additional_filters)
        
        return filters


class JobRecommendationProvider(RecommendationProvider):
    """
    Provider for job recommendations.
    
    Generates job recommendations for candidates.
    """
    
    @property
    def provider_type(self) -> RecommendationProviderType:
        return RecommendationProviderType.JOB
    
    def generate_candidates(
        self,
        entity_id: str,
        context: Dict[str, Any],
        limit: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate job recommendations.
        
        Args:
            entity_id: ID of the candidate
            context: Recommendation context
            limit: Maximum number of jobs
            filters: Optional filters
            
        Returns:
            List of job items
        """
        # Use query engine to search for jobs
        from apps.search.query_engine import SearchExecutionContext
        
        # Build search context from recommendation context
        search_context = SearchExecutionContext(
            entity_type="job",
            query=context.get("query", ""),
            filters=self._build_filters(context, filters),
            pagination={"limit": limit * 2, "offset": 0},
            user_id=context.get("user_id"),
            metadata=context,
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        return result.results
    
    def _build_filters(
        self,
        context: Dict[str, Any],
        additional_filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build search filters from context.
        
        Args:
            context: Recommendation context
            additional_filters: Additional filters
            
        Returns:
            Combined filters
        """
        filters = {}
        
        # Add skill filters
        if "candidate_skills" in context:
            filters["skills"] = context["candidate_skills"]
        
        # Add location filter
        if "candidate_location" in context:
            filters["location"] = context["candidate_location"]
        
        # Add salary filter
        if "salary_range" in context:
            filters.update(context["salary_range"])
        
        # Add employment type filter
        if "employment_types" in context:
            filters["employment_type"] = context["employment_types"]
        
        # Add additional filters
        if additional_filters:
            filters.update(additional_filters)
        
        return filters


class RelatedEntityRecommendationProvider(RecommendationProvider):
    """
    Provider for related entity recommendations.
    
    Generates recommendations for related entities like companies,
    recruiters, skills, etc.
    """
    
    @property
    def provider_type(self) -> RecommendationProviderType:
        return RecommendationProviderType.RELATED_ENTITY
    
    def generate_candidates(
        self,
        entity_id: str,
        context: Dict[str, Any],
        limit: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate related entity recommendations.
        
        Args:
            entity_id: ID of the entity
            context: Recommendation context
            limit: Maximum number of entities
            filters: Optional filters
            
        Returns:
            List of related entity items
        """
        # Determine entity type from context
        entity_type = context.get("related_entity_type", "company")
        
        # Use query engine to search for related entities
        from apps.search.query_engine import SearchExecutionContext
        
        # Build search context
        search_context = SearchExecutionContext(
            entity_type=entity_type,
            query=context.get("query", ""),
            filters=self._build_filters(context, filters),
            pagination={"limit": limit * 2, "offset": 0},
            user_id=context.get("user_id"),
            metadata=context,
        )
        
        # Execute search
        result = self._query_engine.search(search_context)
        
        return result.results
    
    def _build_filters(
        self,
        context: Dict[str, Any],
        additional_filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build search filters from context.
        
        Args:
            context: Recommendation context
            additional_filters: Additional filters
            
        Returns:
            Combined filters
        """
        filters = {}
        
        # Add entity-specific filters
        if "industry" in context:
            filters["industry"] = context["industry"]
        
        if "location" in context:
            filters["location"] = context["location"]
        
        # Add additional filters
        if additional_filters:
            filters.update(additional_filters)
        
        return filters


class RecommendationRegistry:
    """
    Registry for recommendation providers.
    
    Manages registration and retrieval of recommendation providers.
    Implements a singleton pattern to ensure only one registry instance exists.
    """
    
    _instance: Optional["RecommendationRegistry"] = None
    _lock = Lock()
    
    def __new__(cls) -> "RecommendationRegistry":
        """Create or return the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the registry (only once)."""
        if self._initialized:
            return
        
        self._providers: Dict[RecommendationProviderType, RecommendationProvider] = {}
        self._initialized = True
    
    def register_provider(
        self,
        provider: RecommendationProvider,
    ) -> None:
        """
        Register a recommendation provider.
        
        Args:
            provider: Provider to register
        """
        self._providers[provider.provider_type] = provider
    
    def unregister_provider(
        self,
        provider_type: RecommendationProviderType,
    ) -> None:
        """
        Unregister a recommendation provider.
        
        Args:
            provider_type: Type of provider to unregister
        """
        if provider_type in self._providers:
            del self._providers[provider_type]
    
    def get_provider(
        self,
        provider_type: RecommendationProviderType,
    ) -> Optional[RecommendationProvider]:
        """
        Get a recommendation provider.
        
        Args:
            provider_type: Type of provider to get
            
        Returns:
            Provider instance or None
        """
        return self._providers.get(provider_type)
    
    def get_provider_by_name(
        self,
        recommendation_type: str,
    ) -> Optional[RecommendationProvider]:
        """
        Get a provider by recommendation type name.
        
        Args:
            recommendation_type: Name of recommendation type
            
        Returns:
            Provider instance or None
        """
        from .core import RecommendationType
        
        type_mapping = {
            RecommendationType.CANDIDATE: RecommendationProviderType.CANDIDATE,
            RecommendationType.JOB: RecommendationProviderType.JOB,
            RecommendationType.RELATED_ENTITY: RecommendationProviderType.RELATED_ENTITY,
        }
        
        rec_type = RecommendationType(recommendation_type)
        provider_type = type_mapping.get(rec_type)
        
        if provider_type:
            return self.get_provider(provider_type)
        
        return None
    
    def list_providers(self) -> List[RecommendationProviderType]:
        """
        List all registered provider types.
        
        Returns:
            List of registered provider types
        """
        return list(self._providers.keys())
    
    def is_registered(
        self,
        provider_type: RecommendationProviderType,
    ) -> bool:
        """
        Check if a provider is registered.
        
        Args:
            provider_type: Type of provider to check
            
        Returns:
            True if provider is registered, False otherwise
        """
        return provider_type in self._providers


# Global registry instance
registry = RecommendationRegistry()


def get_registry() -> RecommendationRegistry:
    """
    Get the global recommendation registry instance.
    
    Returns:
        RecommendationRegistry singleton instance
    """
    return registry
