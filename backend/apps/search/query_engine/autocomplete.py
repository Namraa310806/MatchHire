"""
Advanced autocomplete system.

This module provides intelligent autocomplete with suggestions,
popular queries, prefix completion, field-specific autocomplete,
entity-aware suggestions, deduplication, and ranking.
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta


class AutocompleteType(Enum):
    """Autocomplete suggestion type."""
    PREFIX = "prefix"
    FUZZY = "fuzzy"
    POPULAR = "popular"
    RECENT = "recent"
    ENTITY = "entity"
    CONTEXTUAL = "contextual"


class SuggestionSource(Enum):
    """Source of the suggestion."""
    INDEX = "index"
    POPULAR_QUERIES = "popular_queries"
    RECENT_SEARCHES = "recent_searches"
    ENTITY_INDEX = "entity_index"
    CUSTOM = "custom"


@dataclass
class AutocompleteContext:
    """
    Context for autocomplete suggestions.
    
    Provides additional context to improve suggestion relevance.
    """
    
    user_id: Optional[str] = None
    entity_type: Optional[str] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    recent_queries: List[str] = field(default_factory=list)
    location: Optional[str] = None
    industry: Optional[str] = None
    experience_level: Optional[str] = None
    custom_context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "user_id": self.user_id,
            "entity_type": self.entity_type,
            "filters": self.filters,
            "recent_queries": self.recent_queries,
            "location": self.location,
            "industry": self.industry,
            "experience_level": self.experience_level,
            "custom_context": self.custom_context,
        }


@dataclass
class AutocompleteSuggestion:
    """
    A single autocomplete suggestion.
    """
    
    value: str
    score: float = 0.0
    type: AutocompleteType = AutocompleteType.PREFIX
    source: SuggestionSource = SuggestionSource.INDEX
    field: Optional[str] = None
    entity_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "value": self.value,
            "score": self.score,
            "type": self.type.value,
            "source": self.source.value,
            "field": self.field,
            "entity_type": self.entity_type,
            "metadata": self.metadata,
        }
    
    def __lt__(self, other: "AutocompleteSuggestion") -> bool:
        """Compare suggestions by score (for sorting)."""
        return self.score > other.score  # Higher score first


@dataclass
class AutocompleteRequest:
    """
    Request for autocomplete suggestions.
    """
    
    prefix: str
    field: str
    entity_type: str
    context: Optional[AutocompleteContext] = None
    limit: int = 10
    fuzzy: bool = False
    include_popular: bool = True
    include_recent: bool = True
    min_score: float = 0.0
    
    def __post_init__(self):
        """Validate request parameters."""
        if not self.prefix:
            raise ValueError("prefix is required")
        if not self.field:
            raise ValueError("field is required")
        if not self.entity_type:
            raise ValueError("entity_type is required")
        if self.limit < 1:
            raise ValueError("limit must be >= 1")
        if self.limit > 50:
            raise ValueError("limit must be <= 50")
        
        if self.context is None:
            self.context = AutocompleteContext()


@dataclass
class AutocompleteResponse:
    """
    Response containing autocomplete suggestions.
    """
    
    suggestions: List[AutocompleteSuggestion]
    took_ms: int
    prefix: str
    field: str
    entity_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "suggestions": [s.to_dict() for s in self.suggestions],
            "took_ms": self.took_ms,
            "prefix": self.prefix,
            "field": self.field,
            "entity_type": self.entity_type,
            "metadata": self.metadata,
        }
    
    def deduplicate(self) -> "AutocompleteResponse":
        """Remove duplicate suggestions by value."""
        seen: Set[str] = set()
        unique_suggestions = []
        
        for suggestion in self.suggestions:
            if suggestion.value not in seen:
                seen.add(suggestion.value)
                unique_suggestions.append(suggestion)
        
        self.suggestions = unique_suggestions
        return self
    
    def sort_by_score(self) -> "AutocompleteResponse":
        """Sort suggestions by score (descending)."""
        self.suggestions.sort(key=lambda s: s.score, reverse=True)
        return self
    
    def limit_to(self, limit: int) -> "AutocompleteResponse":
        """Limit suggestions to the top N."""
        self.suggestions = self.suggestions[:limit]
        return self
    
    def filter_by_score(self, min_score: float) -> "AutocompleteResponse":
        """Filter suggestions by minimum score."""
        self.suggestions = [s for s in self.suggestions if s.score >= min_score]
        return self


class AutocompleteEngine:
    """
    Engine for generating autocomplete suggestions.
    
    Combines multiple sources of suggestions including prefix matching,
    fuzzy matching, popular queries, recent searches, and entity-specific
    suggestions.
    """
    
    def __init__(self):
        """Initialize the autocomplete engine."""
        self._popular_queries: Dict[str, float] = {}
        self._recent_searches: Dict[str, List[datetime]] = {}
        self._entity_suggestions: Dict[str, List[str]] = {}
    
    def add_popular_query(self, query: str, weight: float = 1.0) -> None:
        """
        Add or update a popular query.
        
        Args:
            query: Query string
            weight: Weight to add to the query's popularity
        """
        self._popular_queries[query] = self._popular_queries.get(query, 0.0) + weight
    
    def add_recent_search(self, user_id: str, query: str) -> None:
        """
        Add a recent search for a user.
        
        Args:
            user_id: User identifier
            query: Query string
        """
        if user_id not in self._recent_searches:
            self._recent_searches[user_id] = []
        
        self._recent_searches[user_id].append(datetime.now())
        
        # Keep only last 50 searches per user
        if len(self._recent_searches[user_id]) > 50:
            self._recent_searches[user_id] = self._recent_searches[user_id][-50:]
    
    def add_entity_suggestions(self, entity_type: str, suggestions: List[str]) -> None:
        """
        Add entity-specific suggestions.
        
        Args:
            entity_type: Type of entity
            suggestions: List of suggestion values
        """
        if entity_type not in self._entity_suggestions:
            self._entity_suggestions[entity_type] = []
        
        self._entity_suggestions[entity_type].extend(suggestions)
    
    def get_prefix_suggestions(
        self,
        prefix: str,
        field: str,
        entity_type: str,
        limit: int = 10,
    ) -> List[AutocompleteSuggestion]:
        """
        Get prefix-based suggestions from entity index.
        
        Args:
            prefix: Prefix to match
            field: Field to search
            entity_type: Type of entity
            limit: Maximum suggestions to return
            
        Returns:
            List of suggestions
        """
        # This would typically call the provider's autocomplete method
        # For now, return empty list - to be implemented by provider
        return []
    
    def get_fuzzy_suggestions(
        self,
        prefix: str,
        field: str,
        entity_type: str,
        limit: int = 5,
    ) -> List[AutocompleteSuggestion]:
        """
        Get fuzzy matching suggestions.
        
        Args:
            prefix: Prefix to match (with tolerance for typos)
            field: Field to search
            entity_type: Type of entity
            limit: Maximum suggestions to return
            
        Returns:
            List of suggestions
        """
        # This would typically call the provider with fuzzy matching
        # For now, return empty list - to be implemented by provider
        return []
    
    def get_popular_suggestions(
        self,
        prefix: str,
        limit: int = 5,
    ) -> List[AutocompleteSuggestion]:
        """
        Get popular query suggestions.
        
        Args:
            prefix: Prefix to match
            limit: Maximum suggestions to return
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        for query, score in self._popular_queries.items():
            if query.lower().startswith(prefix.lower()):
                suggestions.append(
                    AutocompleteSuggestion(
                        value=query,
                        score=score,
                        type=AutocompleteType.POPULAR,
                        source=SuggestionSource.POPULAR_QUERIES,
                    )
                )
        
        return sorted(suggestions, key=lambda s: s.score, reverse=True)[:limit]
    
    def get_recent_suggestions(
        self,
        prefix: str,
        user_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[AutocompleteSuggestion]:
        """
        Get recent search suggestions.
        
        Args:
            prefix: Prefix to match
            user_id: User identifier (optional")
            limit: Maximum suggestions to return
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # If user_id provided, get their recent searches
        if user_id and user_id in self._recent_searches:
            # Get recent searches from all users if no user_id
            pass
        
        # For now, return empty - would need to store query strings
        return []
    
    def get_entity_suggestions(
        self,
        prefix: str,
        entity_type: str,
        limit: int = 10,
    ) -> List[AutocompleteSuggestion]:
        """
        Get entity-specific suggestions.
        
        Args:
            prefix: Prefix to match
            entity_type: Type of entity
            limit: Maximum suggestions to return
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        if entity_type in self._entity_suggestions:
            for value in self._entity_suggestions[entity_type]:
                if value.lower().startswith(prefix.lower()):
                    suggestions.append(
                        AutocompleteSuggestion(
                            value=value,
                            score=1.0,
                            type=AutocompleteType.ENTITY,
                            source=SuggestionSource.ENTITY_INDEX,
                            entity_type=entity_type,
                        )
                    )
        
        return suggestions[:limit]
    
    def generate_suggestions(
        self,
        request: AutocompleteRequest,
    ) -> AutocompleteResponse:
        """
        Generate autocomplete suggestions.
        
        Args:
            request: Autocomplete request
            
        Returns:
            Autocomplete response with suggestions
        """
        import time
        start_time = time.time()
        
        all_suggestions: List[AutocompleteSuggestion] = []
        
        # Get prefix suggestions
        prefix_suggestions = self.get_prefix_suggestions(
            prefix=request.prefix,
            field=request.field,
            entity_type=request.entity_type,
            limit=request.limit,
        )
        all_suggestions.extend(prefix_suggestions)
        
        # Get fuzzy suggestions if enabled
        if request.fuzzy:
            fuzzy_suggestions = self.get_fuzzy_suggestions(
                prefix=request.prefix,
                field=request.field,
                entity_type=request.entity_type,
                limit=request.limit // 2,
            )
            all_suggestions.extend(fuzzy_suggestions)
        
        # Get popular suggestions if enabled
        if request.include_popular:
            popular_suggestions = self.get_popular_suggestions(
                prefix=request.prefix,
                limit=request.limit // 2,
            )
            all_suggestions.extend(popular_suggestions)
        
        # Get recent suggestions if enabled and context has user_id
        if request.include_recent and request.context and request.context.user_id:
            recent_suggestions = self.get_recent_suggestions(
                prefix=request.prefix,
                user_id=request.context.user_id,
                limit=request.limit // 2,
            )
            all_suggestions.extend(recent_suggestions)
        
        # Get entity-specific suggestions
        entity_suggestions = self.get_entity_suggestions(
            prefix=request.prefix,
            entity_type=request.entity_type,
            limit=request.limit,
        )
        all_suggestions.extend(entity_suggestions)
        
        # Build response
        response = AutocompleteResponse(
            suggestions=all_suggestions,
            took_ms=int((time.time() - start_time) * 1000),
            prefix=request.prefix,
            field=request.field,
            entity_type=request.entity_type,
        )
        
        # Post-process
        response.deduplicate()
        response.sort_by_score()
        response.filter_by_score(request.min_score)
        response.limit_to(request.limit)
        
        return response
    
    def cleanup_old_searches(self, days: int = 30) -> None:
        """
        Clean up old recent searches.
        
        Args:
            days: Number of days to keep searches
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        for user_id in self._recent_searches:
            self._recent_searches[user_id] = [
                timestamp for timestamp in self._recent_searches[user_id]
                if timestamp > cutoff
            ]
    
    def decay_popular_queries(self, factor: float = 0.95) -> None:
        """
        Decay popularity scores over time.
        
        Args:
            factor: Decay factor (0-1)
        """
        for query in self._popular_queries:
            self._popular_queries[query] *= factor
        
        # Remove queries with very low scores
        self._popular_queries = {
            query: score
            for query, score in self._popular_queries.items()
            if score > 0.01
        }
