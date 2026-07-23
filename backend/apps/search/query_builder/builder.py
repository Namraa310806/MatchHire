"""
Query builder for search operations.

This module provides a reusable query builder that constructs
search queries in a provider-agnostic way. The builder supports
boolean filters, nested filters, sorting, pagination, field selection,
and boost placeholders.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class BooleanOperator(Enum):
    """Boolean operators for combining filters."""
    AND = "and"
    OR = "or"
    NOT = "not"


class ComparisonOperator(Enum):
    """Comparison operators for filters."""
    EXACT = "exact"
    IEXACT = "iexact"
    CONTAINS = "contains"
    ICONTAINS = "icontains"
    STARTSWITH = "startswith"
    ISTARTSWITH = "istartswith"
    ENDSWITH = "endswith"
    IENDSWITH = "iendswith"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    RANGE = "range"
    ISNULL = "isnull"


@dataclass
class FilterCondition:
    """A single filter condition."""
    field: str
    operator: ComparisonOperator
    value: Any

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "field": self.field,
            "operator": self.operator.value,
            "value": self.value,
        }


@dataclass
class BooleanFilter:
    """A boolean filter combining multiple conditions."""
    operator: BooleanOperator
    conditions: List[Union["BooleanFilter", FilterCondition]] = field(default_factory=list)

    def add_condition(self, condition: Union["BooleanFilter", FilterCondition]) -> "BooleanFilter":
        """Add a condition to this boolean filter."""
        self.conditions.append(condition)
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "operator": self.operator.value,
            "conditions": [c.to_dict() for c in self.conditions],
        }


@dataclass
class SortCondition:
    """A sort condition."""
    field: str
    direction: str = "asc"  # asc or desc

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        return {"field": self.field, "direction": self.direction}


@dataclass
class FieldBoost:
    """A field boost for relevance scoring."""
    field: str
    boost: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {"field": self.field, "boost": self.boost}


@dataclass
class QueryBuilder:
    """
    Provider-agnostic query builder.

    This builder constructs search queries that can be translated
    to any search provider (PostgreSQL, Elasticsearch, etc.).
    """

    def __init__(self, entity_type: str):
        """
        Initialize the query builder.

        Args:
            entity_type: Type of entity to search
        """
        self.entity_type = entity_type
        self.query_string: Optional[str] = None
        self.filters: List[Union[BooleanFilter, FilterCondition]] = []
        self.sort_conditions: List[SortCondition] = []
        self.field_selection: Optional[List[str]] = None
        self.field_boosts: List[FieldBoost] = []
        self.pagination: Optional[Dict[str, int]] = None

    def set_query(self, query: str) -> "QueryBuilder":
        """
        Set the query string.

        Args:
            query: Search query string

        Returns:
            Self for method chaining
        """
        self.query_string = query
        return self

    def add_filter(
        self,
        field: str,
        operator: Union[ComparisonOperator, str],
        value: Any,
    ) -> "QueryBuilder":
        """
        Add a filter condition.

        Args:
            field: Field to filter on
            operator: Comparison operator
            value: Filter value

        Returns:
            Self for method chaining
        """
        if isinstance(operator, str):
            operator = ComparisonOperator(operator)

        self.filters.append(FilterCondition(field=field, operator=operator, value=value))
        return self

    def add_boolean_filter(
        self,
        operator: Union[BooleanOperator, str],
        conditions: List[Union[BooleanFilter, FilterCondition]],
    ) -> "QueryBuilder":
        """
        Add a boolean filter combining multiple conditions.

        Args:
            operator: Boolean operator (AND, OR, NOT)
            conditions: List of conditions to combine

        Returns:
            Self for method chaining
        """
        if isinstance(operator, str):
            operator = BooleanOperator(operator)

        self.filters.append(BooleanFilter(operator=operator, conditions=conditions))
        return self

    def add_sort(self, field: str, direction: str = "asc") -> "QueryBuilder":
        """
        Add a sort condition.

        Args:
            field: Field to sort on
            direction: Sort direction (asc or desc)

        Returns:
            Self for method chaining
        """
        self.sort_conditions.append(SortCondition(field=field, direction=direction))
        return self

    def set_fields(self, fields: List[str]) -> "QueryBuilder":
        """
        Set field selection.

        Args:
            fields: List of fields to return

        Returns:
            Self for method chaining
        """
        self.field_selection = fields
        return self

    def add_boost(self, field: str, boost: float) -> "QueryBuilder":
        """
        Add a field boost for relevance scoring.

        Args:
            field: Field to boost
            boost: Boost value (higher = more important)

        Returns:
            Self for method chaining
        """
        self.field_boosts.append(FieldBoost(field=field, boost=boost))
        return self

    def set_pagination(self, page: int, page_size: int) -> "QueryBuilder":
        """
        Set pagination parameters.

        Args:
            page: Page number (1-based)
            page_size: Number of results per page

        Returns:
            Self for method chaining
        """
        self.pagination = {"page": page, "page_size": page_size}
        return self

    def set_offset_limit(self, offset: int, limit: int) -> "QueryBuilder":
        """
        Set offset/limit pagination parameters.

        Args:
            offset: Number of results to skip
            limit: Maximum number of results to return

        Returns:
            Self for method chaining
        """
        self.pagination = {"offset": offset, "limit": limit}
        return self

    def build(self) -> Dict[str, Any]:
        """
        Build the query dictionary.

        Returns:
            Dictionary representation of the query
        """
        query_dict = {
            "entity_type": self.entity_type,
        }

        if self.query_string:
            query_dict["query"] = self.query_string

        if self.filters:
            query_dict["filters"] = [f.to_dict() for f in self.filters]

        if self.sort_conditions:
            query_dict["sort"] = [s.to_dict() for s in self.sort_conditions]

        if self.field_selection:
            query_dict["fields"] = self.field_selection

        if self.field_boosts:
            query_dict["boosts"] = [b.to_dict() for b in self.field_boosts]

        if self.pagination:
            query_dict["pagination"] = self.pagination

        return query_dict

    def reset(self) -> "QueryBuilder":
        """
        Reset the builder to initial state.

        Returns:
            Self for method chaining
        """
        self.query_string = None
        self.filters = []
        self.sort_conditions = []
        self.field_selection = None
        self.field_boosts = []
        self.pagination = None
        return self

    @classmethod
    def for_entity(cls, entity_type: str) -> "QueryBuilder":
        """
        Create a query builder for a specific entity type.

        Args:
            entity_type: Type of entity to search

        Returns:
            New QueryBuilder instance
        """
        return cls(entity_type=entity_type)


class QueryBuilderFactory:
    """Factory for creating pre-configured query builders."""

    @staticmethod
    def job_search() -> QueryBuilder:
        """Create a query builder configured for job search."""
        return QueryBuilder.for_entity("job")

    @staticmethod
    def candidate_search() -> QueryBuilder:
        """Create a query builder configured for candidate search."""
        return QueryBuilder.for_entity("candidate")

    @staticmethod
    def resume_search() -> QueryBuilder:
        """Create a query builder configured for resume search."""
        return QueryBuilder.for_entity("resume")

    @staticmethod
    def company_search() -> QueryBuilder:
        """Create a query builder configured for company search."""
        return QueryBuilder.for_entity("company")

    @staticmethod
    def recruiter_search() -> QueryBuilder:
        """Create a query builder configured for recruiter search."""
        return QueryBuilder.for_entity("recruiter")

    @staticmethod
    def skill_search() -> QueryBuilder:
        """Create a query builder configured for skill search."""
        return QueryBuilder.for_entity("skill")
