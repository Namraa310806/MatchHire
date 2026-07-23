"""
Search suggestions system.

This module provides related queries, spelling correction hooks,
did-you-mean placeholders, recent searches, saved searches,
trending searches, and search templates.
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta


class SuggestionType(Enum):
    """Type of search suggestion."""
    RELATED = "related"
    SPELLING = "spelling"
    DID_YOU_MEAN = "did_you_mean"
    RECENT = "recent"
    SAVED = "saved"
    TRENDING = "trending"
    TEMPLATE = "template"


@dataclass
class RelatedQuery:
    """
    A related query suggestion.
    """
    
    query: str
    score: float = 0.0
    source: str = "algorithm"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query": self.query,
            "score": self.score,
            "source": self.source,
            "metadata": self.metadata,
        }


@dataclass
class SpellingCorrection:
    """
    A spelling correction suggestion.
    """
    
    original: str
    corrected: str
    confidence: float = 0.0
    suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "original": self.original,
            "corrected": self.corrected,
            "confidence": self.confidence,
            "suggestions": self.suggestions,
        }


@dataclass
class DidYouMean:
    """
    A did-you-mean suggestion.
    """
    
    suggestion: str
    original_query: str
    score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "suggestion": self.suggestion,
            "original_query": self.original_query,
            "score": self.score,
        }


@dataclass
class RecentSearch:
    """
    A recent search entry.
    """
    
    query: str
    entity_type: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    result_count: int = 0
    filters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query": self.query,
            "entity_type": self.entity_type,
            "timestamp": self.timestamp.isoformat(),
            "result_count": self.result_count,
            "filters": self.filters,
        }


@dataclass
class SavedSearch:
    """
    A saved search entry.
    """
    
    id: str
    name: str
    query: str
    entity_type: Optional[str] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    alert_enabled: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "query": self.query,
            "entity_type": self.entity_type,
            "filters": self.filters,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "alert_enabled": self.alert_enabled,
        }


@dataclass
class TrendingSearch:
    """
    A trending search query.
    """
    
    query: str
    count: int = 0
    trend_score: float = 0.0
    entity_type: Optional[str] = None
    period: str = "24h"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query": self.query,
            "count": self.count,
            "trend_score": self.trend_score,
            "entity_type": self.entity_type,
            "period": self.period,
        }


@dataclass
class SearchTemplate:
    """
    A search template with parameters.
    """
    
    id: str
    name: str
    template: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None
    entity_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "template": self.template,
            "parameters": self.parameters,
            "description": self.description,
            "entity_type": self.entity_type,
        }


class SearchSuggestionEngine:
    """
    Engine for generating search suggestions.
    
    Provides related queries, spelling corrections, did-you-mean
    suggestions, recent searches, saved searches, trending searches,
    and search templates.
    """
    
    def __init__(self):
        """Initialize the search suggestion engine."""
        self._recent_searches: Dict[str, List[RecentSearch]] = {}
        self._saved_searches: Dict[str, List[SavedSearch]] = {}
        self._trending_searches: List[TrendingSearch] = []
        self._search_templates: Dict[str, SearchTemplate] = {}
        self._query_cooccurrence: Dict[str, Dict[str, int]] = {}
    
    def add_recent_search(
        self,
        user_id: str,
        query: str,
        entity_type: Optional[str] = None,
        result_count: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a recent search for a user.
        
        Args:
            user_id: User identifier
            query: Search query
            entity_type: Entity type searched
            result_count: Number of results
            filters: Filters applied
        """
        if user_id not in self._recent_searches:
            self._recent_searches[user_id] = []
        
        recent_search = RecentSearch(
            query=query,
            entity_type=entity_type,
            result_count=result_count,
            filters=filters or {},
        )
        
        self._recent_searches[user_id].insert(0, recent_search)
        
        # Keep only last 20 searches
        if len(self._recent_searches[user_id]) > 20:
            self._recent_searches[user_id] = self._recent_searches[user_id][:20]
        
        # Update co-occurrence data
        self._update_cooccurrence(query, entity_type)
    
    def get_recent_searches(
        self,
        user_id: str,
        limit: int = 10,
    ) -> List[RecentSearch]:
        """
        Get recent searches for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number to return
            
        Returns:
            List of recent searches
        """
        if user_id not in self._recent_searches:
            return []
        
        return self._recent_searches[user_id][:limit]
    
    def add_saved_search(
        self,
        user_id: str,
        saved_search: SavedSearch,
    ) -> None:
        """
        Add a saved search for a user.
        
        Args:
            user_id: User identifier
            saved_search: Saved search object
        """
        if user_id not in self._saved_searches:
            self._saved_searches[user_id] = []
        
        self._saved_searches[user_id].append(saved_search)
    
    def get_saved_searches(
        self,
        user_id: str,
    ) -> List[SavedSearch]:
        """
        Get saved searches for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of saved searches
        """
        if user_id not in self._saved_searches:
            return []
        
        return self._saved_searches[user_id]
    
    def delete_saved_search(
        self,
        user_id: str,
        search_id: str,
    ) -> bool:
        """
        Delete a saved search.
        
        Args:
            user_id: User identifier
            search_id: Saved search ID
            
        Returns:
            True if deleted, False otherwise
        """
        if user_id not in self._saved_searches:
            return False
        
        original_length = len(self._saved_searches[user_id])
        self._saved_searches[user_id] = [
            s for s in self._saved_searches[user_id] if s.id != search_id
        ]
        
        return len(self._saved_searches[user_id]) < original_length
    
    def update_trending_searches(
        self,
        queries: List[str],
        entity_type: Optional[str] = None,
    ) -> None:
        """
        Update trending searches based on recent query data.
        
        Args:
            queries: List of recent queries
            entity_type: Entity type
        """
        # Count query frequencies
        query_counts: Dict[str, int] = {}
        for query in queries:
            query_counts[query] = query_counts.get(query, 0) + 1
        
        # Update trending searches
        self._trending_searches = []
        for query, count in query_counts.items():
            if count >= 5:  # Minimum threshold
                trending = TrendingSearch(
                    query=query,
                    count=count,
                    trend_score=float(count),
                    entity_type=entity_type,
                )
                self._trending_searches.append(trending)
        
        # Sort by trend score
        self._trending_searches.sort(key=lambda t: t.trend_score, reverse=True)
        
        # Keep top 50
        self._trending_searches = self._trending_searches[:50]
    
    def get_trending_searches(
        self,
        entity_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[TrendingSearch]:
        """
        Get trending searches.
        
        Args:
            entity_type: Filter by entity type
            limit: Maximum number to return
            
        Returns:
            List of trending searches
        """
        trending = self._trending_searches
        
        if entity_type:
            trending = [t for t in trending if t.entity_type == entity_type]
        
        return trending[:limit]
    
    def add_search_template(
        self,
        template: SearchTemplate,
    ) -> None:
        """
        Add a search template.
        
        Args:
            template: Search template object
        """
        self._search_templates[template.id] = template
    
    def get_search_template(
        self,
        template_id: str,
    ) -> Optional[SearchTemplate]:
        """
        Get a search template by ID.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Search template or None
        """
        return self._search_templates.get(template_id)
    
    def get_search_templates(
        self,
        entity_type: Optional[str] = None,
    ) -> List[SearchTemplate]:
        """
        Get search templates.
        
        Args:
            entity_type: Filter by entity type
            
        Returns:
            List of search templates
        """
        templates = list(self._search_templates.values())
        
        if entity_type:
            templates = [t for t in templates if t.entity_type == entity_type]
        
        return templates
    
    def get_related_queries(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 5,
    ) -> List[RelatedQuery]:
        """
        Get related queries based on co-occurrence.
        
        Args:
            query: Original query
            entity_type: Entity type
            limit: Maximum number to return
            
        Returns:
            List of related queries
        """
        related = []
        
        if query in self._query_cooccurrence:
            for related_query, count in self._query_cooccurrence[query].items():
                related.append(
                    RelatedQuery(
                        query=related_query,
                        score=float(count),
                        source="cooccurrence",
                    )
                )
        
        # Sort by score and limit
        related.sort(key=lambda r: r.score, reverse=True)
        return related[:limit]
    
    def get_spelling_correction(
        self,
        query: str,
    ) -> Optional[SpellingCorrection]:
        """
        Get spelling correction for a query.
        
        This is a placeholder - actual implementation would use
        a spelling correction service or algorithm.
        
        Args:
            query: Query to correct
            
        Returns:
            Spelling correction or None
        """
        # Placeholder implementation
        # In production, integrate with a spelling correction service
        return None
    
    def get_did_you_mean(
        self,
        query: str,
        entity_type: Optional[str] = None,
    ) -> Optional[DidYouMean]:
        """
        Get did-you-mean suggestion.
        
        Args:
            query: Original query
            entity_type: Entity type
            
        Returns:
            Did-you-mean suggestion or None
        """
        # Check if query has low results or is likely misspelled
        # This would typically use search result count and spelling correction
        return None
    
    def _update_cooccurrence(
        self,
        query: str,
        entity_type: Optional[str] = None,
    ) -> None:
        """
        Update query co-occurrence data.
        
        Args:
            query: Query to update
            entity_type: Entity type
        """
        # This is a simplified implementation
        # In production, you'd track which queries are often used together
        pass
    
    def cleanup_old_recent_searches(
        self,
        days: int = 30,
    ) -> None:
        """
        Clean up old recent searches.
        
        Args:
            days: Number of days to keep
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        for user_id in self._recent_searches:
            self._recent_searches[user_id] = [
                search for search in self._recent_searches[user_id]
                if search.timestamp > cutoff
            ]
    
    def decay_trending_scores(
        self,
        factor: float = 0.9,
    ) -> None:
        """
        Decay trending search scores.
        
        Args:
            factor: Decay factor
        """
        for trending in self._trending_searches:
            trending.trend_score *= factor
            trending.count = int(trending.count * factor)
        
        # Remove low-score trending searches
        self._trending_searches = [
            t for t in self._trending_searches
            if t.trend_score > 1.0
        ]
