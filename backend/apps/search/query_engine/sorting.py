"""
Sorting and ranking hooks for search results.

This module provides multi-field sorting, custom sort builders,
score boosting hooks, field boosting, freshness boosting, popularity boosting,
and business-rule boosting hooks.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta


class SortDirection(Enum):
    """Sort direction options."""
    ASC = "asc"
    DESC = "desc"


class ScoreMode(Enum):
    """Score mode for multi-field sorting."""
    SUM = "sum"
    AVG = "avg"
    MAX = "max"
    MIN = "min"
    MULTIPLY = "multiply"


@dataclass
class SortCondition:
    """
    A single sort condition.
    """
    
    field: str
    direction: SortDirection = SortDirection.ASC
    mode: Optional[str] = None  # For multi-value fields: min, max, sum, avg
    missing: Optional[Any] = None  # Value for missing fields
    unmapped_type: Optional[str] = None  # Type for unmapped fields
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        sort_dict: Dict[str, Any] = {
            "field": self.field,
            "direction": self.direction.value,
        }
        
        if self.mode is not None:
            sort_dict["mode"] = self.mode
        if self.missing is not None:
            sort_dict["missing"] = self.missing
        if self.unmapped_type is not None:
            sort_dict["unmapped_type"] = self.unmapped_type
        
        return sort_dict
    
    def validate(self) -> bool:
        """Validate the sort condition."""
        return bool(self.field)


@dataclass
class FieldBoost:
    """
    Boost configuration for a field.
    """
    
    field: str
    boost: float
    factor: Optional[float] = None
    modifier: Optional[str] = None  # none, log, log1p, ln, ln1p, square, sqrt, reciprocal
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        boost_dict: Dict[str, Any] = {
            "field": self.field,
            "boost": self.boost,
        }
        
        if self.factor is not None:
            boost_dict["factor"] = self.factor
        if self.modifier is not None:
            boost_dict["modifier"] = self.modifier
        
        return boost_dict


@dataclass
class FreshnessBoost:
    """
    Freshness boost configuration for time-based scoring.
    """
    
    field: str
    scale: str  # e.g., "30d", "7d", "24h"
    decay: float = 0.5
    offset: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        boost_dict: Dict[str, Any] = {
            "field": self.field,
            "scale": self.scale,
            "decay": self.decay,
        }
        
        if self.offset is not None:
            boost_dict["offset"] = self.offset
        
        return boost_dict


@dataclass
class PopularityBoost:
    """
    Popularity boost configuration for engagement-based scoring.
    """
    
    field: str
    factor: float = 1.0
    modifier: str = "log1p"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "field": self.field,
            "factor": self.factor,
            "modifier": self.modifier,
        }


@dataclass
class BusinessRuleBoost:
    """
    Business rule boost for custom scoring logic.
    """
    
    name: str
    condition: str  # Description or condition
    boost: float
    filter_query: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        boost_dict: Dict[str, Any] = {
            "name": self.name,
            "condition": self.condition,
            "boost": self.boost,
        }
        
        if self.filter_query is not None:
            boost_dict["filter_query"] = self.filter_query
        
        return boost_dict


class RankingHooks:
    """
    Hooks for custom ranking logic.
    
    These hooks allow business rules to influence search relevance
    without modifying the core search logic.
    """
    
    def __init__(self):
        """Initialize ranking hooks."""
        self._pre_rank_hooks: List[Callable] = []
        self._post_rank_hooks: List[Callable] = []
        self._score_modifiers: List[Callable] = []
    
    def add_pre_rank_hook(self, hook: Callable) -> None:
        """
        Add a hook to run before ranking.
        
        Args:
            hook: Function to call before ranking
        """
        self._pre_rank_hooks.append(hook)
    
    def add_post_rank_hook(self, hook: Callable) -> None:
        """
        Add a hook to run after ranking.
        
        Args:
            hook: Function to call after ranking
        """
        self._post_rank_hooks.append(hook)
    
    def add_score_modifier(self, modifier: Callable) -> None:
        """
        Add a score modifier function.
        
        Args:
            modifier: Function to modify scores
        """
        self._score_modifiers.append(modifier)
    
    def apply_pre_rank_hooks(self, context: Dict[str, Any]) -> None:
        """
        Apply all pre-ranking hooks.
        
        Args:
            context: Search context
        """
        for hook in self._pre_rank_hooks:
            hook(context)
    
    def apply_post_rank_hooks(self, results: List[Dict[str, Any]], context: Dict[str, Any]) -> None:
        """
        Apply all post-ranking hooks.
        
        Args:
            results: Search results
            context: Search context
        """
        for hook in self._post_rank_hooks:
            hook(results, context)
    
    def apply_score_modifiers(self, results: List[Dict[str, Any]], context: Dict[str, Any]) -> None:
        """
        Apply all score modifiers.
        
        Args:
            results: Search results
            context: Search context
        """
        for modifier in self._score_modifiers:
            modifier(results, context)


class SortBuilder:
    """
    Builder for constructing sort specifications.
    """
    
    def __init__(self):
        """Initialize the sort builder."""
        self._sort_conditions: List[SortCondition] = []
        self._field_boosts: List[FieldBoost] = []
        self._freshness_boosts: List[FreshnessBoost] = []
        self._popularity_boosts: List[PopularityBoost] = []
        self._business_rule_boosts: List[BusinessRuleBoost] = []
    
    def add_sort(
        self,
        field: str,
        direction: SortDirection = SortDirection.ASC,
        **kwargs
    ) -> "SortBuilder":
        """
        Add a sort condition.
        
        Args:
            field: Field to sort on
            direction: Sort direction
            **kwargs: Additional sort parameters
            
        Returns:
            Self for method chaining
        """
        condition = SortCondition(field=field, direction=direction, **kwargs)
        self._sort_conditions.append(condition)
        return self
    
    def add_field_boost(self, field: str, boost: float, **kwargs) -> "SortBuilder":
        """
        Add a field boost.
        
        Args:
            field: Field to boost
            boost: Boost value
            **kwargs: Additional boost parameters
            
        Returns:
            Self for method chaining
        """
        boost_obj = FieldBoost(field=field, boost=boost, **kwargs)
        self._field_boosts.append(boost_obj)
        return self
    
    def add_freshness_boost(self, field: str, scale: str, **kwargs) -> "SortBuilder":
        """
        Add a freshness boost.
        
        Args:
            field: Field to boost (typically a date field)
            scale: Time scale for decay
            **kwargs: Additional boost parameters
            
        Returns:
            Self for method chaining
        """
        boost_obj = FreshnessBoost(field=field, scale=scale, **kwargs)
        self._freshness_boosts.append(boost_obj)
        return self
    
    def add_popularity_boost(self, field: str, factor: float = 1.0, **kwargs) -> "SortBuilder":
        """
        Add a popularity boost.
        
        Args:
            field: Field to boost (typically a count/engagement field)
            factor: Boost factor
            **kwargs: Additional boost parameters
            
        Returns:
            Self for method chaining
        """
        boost_obj = PopularityBoost(field=field, factor=factor, **kwargs)
        self._popularity_boosts.append(boost_obj)
        return self
    
    def add_business_rule_boost(
        self,
        name: str,
        condition: str,
        boost: float,
        **kwargs
    ) -> "SortBuilder":
        """
        Add a business rule boost.
        
        Args:
            name: Name of the rule
            condition: Condition description
            boost: Boost value
            **kwargs: Additional boost parameters
            
        Returns:
            Self for method chaining
        """
        boost_obj = BusinessRuleBoost(name=name, condition=condition, boost=boost, **kwargs)
        self._business_rule_boosts.append(boost_obj)
        return self
    
    def by_relevance(self, direction: SortDirection = SortDirection.DESC) -> "SortBuilder":
        """Sort by relevance score."""
        return self.add_sort(field="_score", direction=direction)
    
    def by_date(self, field: str = "created_at", direction: SortDirection = SortDirection.DESC) -> "SortBuilder":
        """Sort by date field."""
        return self.add_sort(field=field, direction=direction)
    
    def by_field(self, field: str, direction: SortDirection = SortDirection.ASC) -> "SortBuilder":
        """Sort by a specific field."""
        return self.add_sort(field=field, direction=direction)
    
    def by_salary(self, direction: SortDirection = SortDirection.DESC) -> "SortBuilder":
        """Sort by salary (descending)."""
        return self.add_sort(field="salary", direction=direction)
    
    def by_experience(self, direction: SortDirection = SortDirection.DESC) -> "SortBuilder":
        """Sort by experience level (descending)."""
        return self.add_sort(field="experience_level", direction=direction)
    
    def by_location(self, direction: SortDirection = SortDirection.ASC) -> "SortBuilder":
        """Sort by location (ascending)."""
        return self.add_sort(field="location", direction=direction)
    
    def by_company(self, direction: SortDirection = SortDirection.ASC) -> "SortBuilder":
        """Sort by company name (ascending)."""
        return self.add_sort(field="company_name", direction=direction)
    
    def boost_title(self, boost: float = 2.0) -> "SortBuilder":
        """Boost the title field."""
        return self.add_field_boost(field="title", boost=boost)
    
    def boost_description(self, boost: float = 1.5) -> "SortBuilder":
        """Boost the description field."""
        return self.add_field_boost(field="description", boost=boost)
    
    def boost_skills(self, boost: float = 2.0) -> "SortBuilder":
        """Boost the skills field."""
        return self.add_field_boost(field="skills", boost=boost)
    
    def boost_freshness(self, field: str = "created_at", scale: str = "30d") -> "SortBuilder":
        """Boost recent documents."""
        return self.add_freshness_boost(field=field, scale=scale)
    
    def boost_popularity(self, field: str = "view_count", factor: float = 1.0) -> "SortBuilder":
        """Boost popular documents."""
        return self.add_popularity_boost(field=field, factor=factor)
    
    def build_sort(self) -> List[SortCondition]:
        """
        Build and return the sort conditions.
        
        Returns:
            List of SortCondition objects
        """
        if not all(condition.validate() for condition in self._sort_conditions):
            raise ValueError("One or more sort conditions are invalid")
        
        return self._sort_conditions
    
    def build_boosts(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build and return all boosts.
        
        Returns:
            Dictionary of boost configurations
        """
        return {
            "field_boosts": [b.to_dict() for b in self._field_boosts],
            "freshness_boosts": [b.to_dict() for b in self._freshness_boosts],
            "popularity_boosts": [b.to_dict() for b in self._popularity_boosts],
            "business_rule_boosts": [b.to_dict() for b in self._business_rule_boosts],
        }
    
    def reset(self) -> "SortBuilder":
        """Reset the builder to initial state."""
        self._sort_conditions = []
        self._field_boosts = []
        self._freshness_boosts = []
        self._popularity_boosts = []
        self._business_rule_boosts = []
        return self
    
    @classmethod
    def create(cls) -> "SortBuilder":
        """Create a new sort builder instance."""
        return cls()


class PredefinedSorts:
    """
    Pre-configured sort configurations for common use cases.
    """
    
    @staticmethod
    def relevance_first() -> SortBuilder:
        """Sort by relevance first, then by date."""
        builder = SortBuilder()
        return (
            builder
            .by_relevance(direction=SortDirection.DESC)
            .by_date(direction=SortDirection.DESC)
        )
    
    @staticmethod
    def most_recent() -> SortBuilder:
        """Sort by date only (most recent first)."""
        builder = SortBuilder()
        return builder.by_date(direction=SortDirection.DESC)
    
    @staticmethod
    def highest_salary() -> SortBuilder:
        """Sort by salary (highest first)."""
        builder = SortBuilder()
        return builder.by_salary(direction=SortDirection.DESC)
    
    @staticmethod
    def most_experienced() -> SortBuilder:
        """Sort by experience level (most experienced first)."""
        builder = SortBuilder()
        return builder.by_experience(direction=SortDirection.DESC)
    
    @staticmethod
    def location_alpha() -> SortBuilder:
        """Sort by location alphabetically."""
        builder = SortBuilder()
        return builder.by_location(direction=SortDirection.ASC)
    
    @staticmethod
    def company_alpha() -> SortBuilder:
        """Sort by company name alphabetically."""
        builder = SortBuilder()
        return builder.by_company(direction=SortDirection.ASC)
    
    @staticmethod
    def boosted_relevance() -> SortBuilder:
        """Sort by relevance with field boosts."""
        builder = SortBuilder()
        return (
            builder
            .boost_title(boost=2.0)
            .boost_description(boost=1.5)
            .boost_skills(boost=2.0)
            .by_relevance(direction=SortDirection.DESC)
        )
    
    @staticmethod
    def fresh_and_relevant() -> SortBuilder:
        """Sort by relevance with freshness boost."""
        builder = SortBuilder()
        return (
            builder
            .boost_freshness(field="created_at", scale="30d")
            .by_relevance(direction=SortDirection.DESC)
            .by_date(direction=SortDirection.DESC)
        )
    
    @staticmethod
    def popular_and_relevant() -> SortBuilder:
        """Sort by relevance with popularity boost."""
        builder = SortBuilder()
        return (
            builder
            .boost_popularity(field="view_count", factor=1.0)
            .by_relevance(direction=SortDirection.DESC)
        )
