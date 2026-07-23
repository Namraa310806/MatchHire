"""
Provider-independent Query DSL.

This module defines a comprehensive Query DSL that can be translated
to any search provider (PostgreSQL, Elasticsearch, etc.). The DSL supports
all common query types including match, multi-match, phrase, prefix,
wildcard, fuzzy, range, exists, term, terms, nested, bool, dis_max,
and function_score queries.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class QueryType(Enum):
    """Query type enumeration."""
    MATCH = "match"
    MULTI_MATCH = "multi_match"
    PHRASE = "phrase"
    PREFIX = "prefix"
    WILDCARD = "wildcard"
    FUZZY = "fuzzy"
    RANGE = "range"
    EXISTS = "exists"
    TERM = "term"
    TERMS = "terms"
    NESTED = "nested"
    BOOL = "bool"
    DIS_MAX = "dis_max"
    FUNCTION_SCORE = "function_score"


class BooleanOperator(Enum):
    """Boolean operators for combining queries."""
    MUST = "must"
    SHOULD = "should"
    MUST_NOT = "must_not"
    FILTER = "filter"


class MatchType(Enum):
    """Match type for multi-match queries."""
    BEST_FIELDS = "best_fields"
    MOST_FIELDS = "most_fields"
    CROSS_FIELDS = "cross_fields"
    PHRASE = "phrase"
    PHRASE_PREFIX = "phrase_prefix"


class ZeroTermsQuery(Enum):
    """Behavior when no terms match."""
    NONE = "none"
    ALL = "all"


@dataclass
class Query(ABC):
    """
    Base class for all query types.
    
    All query types inherit from this base class and implement
    the to_dict method for serialization.
    """
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the query to a dictionary representation.
        
        Returns:
            Dictionary representation of the query
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """
        Validate the query structure.
        
        Returns:
            True if valid, False otherwise
        """
        pass
    
    def and_(self, other: "Query") -> "BoolQuery":
        """
        Combine this query with another using AND logic.
        
        Args:
            other: Query to combine with
            
        Returns:
            BoolQuery with MUST clauses
        """
        return BoolQuery(must=[self, other])
    
    def or_(self, other: "Query") -> "BoolQuery":
        """
        Combine this query with another using OR logic.
        
        Args:
            other: Query to combine with
            
        Returns:
            BoolQuery with SHOULD clauses
        """
        return BoolQuery(should=[self, other])
    
    def not_(self) -> "BoolQuery":
        """
        Negate this query.
        
        Returns:
            BoolQuery with MUST_INOT clause
        """
        return BoolQuery(must_not=[self])


@dataclass
class MatchQuery(Query):
    """
    Match query for full-text search.
    
    This is the most basic query that performs full-text search
    on a single field.
    """
    
    field: str
    query: str
    operator: Optional[str] = None  # or, and
    minimum_should_match: Optional[int] = None
    fuzziness: Optional[str] = None  # AUTO, 0, 1, 2
    prefix_length: Optional[int] = None
    max_expansions: Optional[int] = None
    lenient: Optional[bool] = None
    zero_terms_query: Optional[ZeroTermsQuery] = None
    boost: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        query_dict: Dict[str, Any] = {
            "type": QueryType.MATCH.value,
            "field": self.field,
            "query": self.query,
        }
        
        if self.operator is not None:
            query_dict["operator"] = self.operator
        if self.minimum_should_match is not None:
            query_dict["minimum_should_match"] = self.minimum_should_match
        if self.fuzziness is not None:
            query_dict["fuzziness"] = self.fuzziness
        if self.prefix_length is not None:
            query_dict["prefix_length"] = self.prefix_length
        if self.max_expansions is not None:
            query_dict["max_expansions"] = self.max_expansions
        if self.lenient is not None:
            query_dict["lenient"] = self.lenient
        if self.zero_terms_query is not None:
            query_dict["zero_terms_query"] = self.zero_terms_query.value
        if self.boost is not None:
            query_dict["boost"] = self.boost
        
        return query_dict
    
    def validate(self) -> bool:
        """Validate the query."""
        return bool(self.field and self.query)


@dataclass
class MultiMatchQuery(Query):
    """
    Multi-match query for searching across multiple fields.
    
    This query allows searching across multiple fields with
    different match types.
    """
    
    query: str
    fields: List[str]
    type: MatchType = MatchType.BEST_FIELDS
    operator: Optional[str] = None
    minimum_should_match: Optional[int] = None
    fuzziness: Optional[str] = None
    prefix_length: Optional[int] = None
    max_expansions: Optional[int] = None
    lenient: Optional[bool] = None
    zero_terms_query: Optional[ZeroTermsQuery] = None
    tie_breaker: Optional[float] = None
    boost: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        query_dict: Dict[str, Any] = {
            "type": QueryType.MULTI_MATCH.value,
            "query": self.query,
            "fields": self.fields,
            "match_type": self.type.value,
        }
        
        if self.operator is not None:
            query_dict["operator"] = self.operator
        if self.minimum_should_match is not None:
            query_dict["minimum_should_match"] = self.minimum_should_match
        if self.fuzziness is not None:
            query_dict["fuzziness"] = self.fuzziness
        if self.prefix_length is not None:
            query_dict["prefix_length"] = self.prefix_length
        if self.max_expansions is not None:
            query_dict["max_expansions"] = self.max_expansions
        if self.lenient is not None:
            query_dict["lenient"] = self.lenient
        if self.zero_terms_query is not None:
            query_dict["zero_terms_query"] = self.zero_terms_query.value
        if self.tie_breaker is not None:
            query_dict["tie_breaker"] = self.tie_breaker
        if self.boost is not None:
            query_dict["boost"] = self.boost
        
        return query_dict
    
    def validate(self) -> bool:
        """Validate the query."""
        return bool(self.query and self.fields)


@dataclass
class PhraseQuery(Query):
    """
    Phrase query for exact phrase matching.
    
    This query matches documents containing the exact phrase.
    """
    
    field: str
    query: str
    slop: Optional[int] = None
    zero_terms_query: Optional[ZeroTermsQuery] = None
    boost: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        query_dict: Dict[str, Any] = {
            "type": QueryType.PHRASE.value,
            "field": self.field,
            "query": self.query,
        }
        
        if self.slop is not None:
            query_dict["slop"] = self.slop
        if self.zero_terms_query is not None:
            query_dict["zero_terms_query"] = self.zero_terms_query.value
        if self.boost is not None:
            query_dict["boost"] = self.boost
        
        return query_dict
    
    def validate(self) -> bool:
        """Validate the query."""
        return bool(self.field and self.query)


@dataclass
class PrefixQuery(Query):
    """
    Prefix query for matching terms that start with a prefix.
    
    This is useful for autocomplete and prefix-based searches.
    """
    
    field: str
    value: str
    rewrite: Optional[str] = None
    boost: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        query_dict: Dict[str, Any] = {
            "type": QueryType.PREFIX.value,
            "field": self.field,
            "value": self.value,
        }
        
        if self.rewrite is not None:
            query_dict["rewrite"] = self.rewrite
        if self.boost is not None:
            query_dict["boost"] = self.boost
        
        return query_dict
    
    def validate(self) -> bool:
        """Validate the query."""
        return bool(self.field and self.value)


@dataclass
class WildcardQuery(Query):
    """
    Wildcard query for pattern matching.
    
    Supports * (matches any number of characters) and ? (matches single character).
    """
    
    field: str
    value: str
    rewrite: Optional[str] = None
    boost: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        query_dict: Dict[str, Any] = {
            "type": QueryType.WILDCARD.value,
            "field": self.field,
            "value": self.value,
        }
        
        if self.rewrite is not None:
            query_dict["rewrite"] = self.rewrite
        if self.boost is not None:
            query_dict["boost"] = self.boost
        
        return query_dict
    
    def validate(self) -> bool:
        """Validate the query."""
        return bool(self.field and self.value)


@dataclass
class FuzzyQuery(Query):
    """
    Fuzzy query for approximate matching.
    
    This query matches terms that are similar to the search term,
    useful for handling typos and spelling variations.
    """
    
    field: str
    value: str
    fuzziness: Optional[str] = None  # AUTO, 0, 1, 2
    prefix_length: Optional[int] = None
    max_expansions: Optional[int] = None
    transpositions: Optional[bool] = None
    rewrite: Optional[str] = None
    boost: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        query_dict: Dict[str, Any] = {
            "type": QueryType.FUZZY.value,
            "field": self.field,
            "value": self.value,
        }
        
        if self.fuzziness is not None:
            query_dict["fuzziness"] = self.fuzziness
        if self.prefix_length is not None:
            query_dict["prefix_length"] = self.prefix_length
        if self.max_expansions is not None:
            query_dict["max_expansions"] = self.max_expansions
        if self.transpositions is not None:
            query_dict["transpositions"] = self.transpositions
        if self.rewrite is not None:
            query_dict["rewrite"] = self.rewrite
        if self.boost is not None:
            query_dict["boost"] = self.boost
        
        return query_dict
    
    def validate(self) -> bool:
        """Validate the query."""
        return bool(self.field and self.value)


@dataclass
class RangeQuery(Query):
    """
    Range query for matching values within a range.
    
    Supports inclusive and exclusive bounds for numeric, date, and string fields.
    """
    
    field: str
    gte: Optional[Any] = None
    gt: Optional[Any] = None
    lte: Optional[Any] = None
    lt: Optional[Any] = None
    format: Optional[str] = None  # For date ranges
    boost: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        query_dict: Dict[str, Any] = {
            "type": QueryType.RANGE.value,
            "field": self.field,
        }
        
        range_dict: Dict[str, Any] = {}
        if self.gte is not None:
            range_dict["gte"] = self.gte
        if self.gt is not None:
            range_dict["gt"] = self.gt
        if self.lte is not None:
            range_dict["lte"] = self.lte
        if self.lt is not None:
            range_dict["lt"] = self.lt
        
        query_dict["range"] = range_dict
        
        if self.format is not None:
            query_dict["format"] = self.format
        if self.boost is not None:
            query_dict["boost"] = self.boost
        
        return query_dict
    
    def validate(self) -> bool:
        """Validate the query."""
        has_bounds = any([self.gte, self.gt, self.lte, self.lt])
        return bool(self.field and has_bounds)


@dataclass
class ExistsQuery(Query):
    """
    Exists query for matching documents that have a field.
    
    This query matches documents where the specified field exists and has a non-null value.
    """
    
    field: str
    boost: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        query_dict: Dict[str, Any] = {
            "type": QueryType.EXISTS.value,
            "field": self.field,
        }
        
        if self.boost is not None:
            query_dict["boost"] = self.boost
        
        return query_dict
    
    def validate(self) -> bool:
        """Validate the query."""
        return bool(self.field)


@dataclass
class TermQuery(Query):
    """
    Term query for exact value matching.
    
    This query matches documents that contain the exact term.
    Useful for structured data like IDs, status codes, etc.
    """
    
    field: str
    value: Any
    boost: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        query_dict: Dict[str, Any] = {
            "type": QueryType.TERM.value,
            "field": self.field,
            "value": self.value,
        }
        
        if self.boost is not None:
            query_dict["boost"] = self.boost
        
        return query_dict
    
    def validate(self) -> bool:
        """Validate the query."""
        return bool(self.field and self.value is not None)


@dataclass
class TermsQuery(Query):
    """
    Terms query for matching any of multiple values.
    
    This query matches documents where the field matches any of the provided values.
    """
    
    field: str
    values: List[Any]
    boost: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        query_dict: Dict[str, Any] = {
            "type": QueryType.TERMS.value,
            "field": self.field,
            "values": self.values,
        }
        
        if self.boost is not None:
            query_dict["boost"] = self.boost
        
        return query_dict
    
    def validate(self) -> bool:
        """Validate the query."""
        return bool(self.field and self.values)


@dataclass
class NestedQuery(Query):
    """
    Nested query for searching nested objects.
    
    This query allows searching within nested document structures.
    """
    
    path: str
    query: Query
    score_mode: Optional[str] = None  # avg, sum, max, min, none
    ignore_unmapped: Optional[bool] = None
    boost: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        query_dict: Dict[str, Any] = {
            "type": QueryType.NESTED.value,
            "path": self.path,
            "query": self.query.to_dict(),
        }
        
        if self.score_mode is not None:
            query_dict["score_mode"] = self.score_mode
        if self.ignore_unmapped is not None:
            query_dict["ignore_unmapped"] = self.ignore_unmapped
        if self.boost is not None:
            query_dict["boost"] = self.boost
        
        return query_dict
    
    def validate(self) -> bool:
        """Validate the query."""
        return bool(self.path and self.query and self.query.validate())


@dataclass
class BoolQuery(Query):
    """
    Boolean query for combining multiple queries.
    
    This is the most powerful query type, allowing complex combinations
    of must, should, must_not, and filter clauses.
    """
    
    must: List[Query] = field(default_factory=list)
    should: List[Query] = field(default_factory=list)
    must_not: List[Query] = field(default_factory=list)
    filter: List[Query] = field(default_factory=list)
    minimum_should_match: Optional[int] = None
    boost: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        query_dict: Dict[str, Any] = {
            "type": QueryType.BOOL.value,
        }
        
        if self.must:
            query_dict["must"] = [q.to_dict() for q in self.must]
        if self.should:
            query_dict["should"] = [q.to_dict() for q in self.should]
        if self.must_not:
            query_dict["must_not"] = [q.to_dict() for q in self.must_not]
        if self.filter:
            query_dict["filter"] = [q.to_dict() for q in self.filter]
        if self.minimum_should_match is not None:
            query_dict["minimum_should_match"] = self.minimum_should_match
        if self.boost is not None:
            query_dict["boost"] = self.boost
        
        return query_dict
    
    def validate(self) -> bool:
        """Validate the query."""
        has_clauses = any([self.must, self.should, self.must_not, self.filter])
        if not has_clauses:
            return False
        
        # Validate all sub-queries
        for query in self.must + self.should + self.must_not + self.filter:
            if not query.validate():
                return False
        
        return True
    
    def add_must(self, query: Query) -> "BoolQuery":
        """Add a MUST clause."""
        self.must.append(query)
        return self
    
    def add_should(self, query: Query) -> "BoolQuery":
        """Add a SHOULD clause."""
        self.should.append(query)
        return self
    
    def add_must_not(self, query: Query) -> "BoolQuery":
        """Add a MUST_NOT clause."""
        self.must_not.append(query)
        return self
    
    def add_filter(self, query: Query) -> "BoolQuery":
        """Add a FILTER clause."""
        self.filter.append(query)
        return self


@dataclass
class DisMaxQuery(Query):
    """
    Disjunction max query for taking the maximum score from multiple queries.
    
    This query returns documents matching any clause, using the maximum
    score from all matching clauses.
    """
    
    queries: List[Query]
    tie_breaker: Optional[float] = None
    boost: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        query_dict: Dict[str, Any] = {
            "type": QueryType.DIS_MAX.value,
            "queries": [q.to_dict() for q in self.queries],
        }
        
        if self.tie_breaker is not None:
            query_dict["tie_breaker"] = self.tie_breaker
        if self.boost is not None:
            query_dict["boost"] = self.boost
        
        return query_dict
    
    def validate(self) -> bool:
        """Validate the query."""
        if not self.queries:
            return False
        
        for query in self.queries:
            if not query.validate():
                return False
        
        return True


@dataclass
class ScoreFunction(ABC):
    """Base class for score functions."""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        pass


@dataclass
class WeightFunction(ScoreFunction):
    """Weight score function."""
    
    weight: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {"weight": self.weight}


@dataclass
class FieldValueFactorFunction(ScoreFunction):
    """Field value factor score function."""
    
    field: str
    factor: Optional[float] = None
    modifier: Optional[str] = None  # none, log, log1p, ln, ln1p, square, sqrt, reciprocal
    missing: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        func_dict: Dict[str, Any] = {"field": self.field}
        
        if self.factor is not None:
            func_dict["factor"] = self.factor
        if self.modifier is not None:
            func_dict["modifier"] = self.modifier
        if self.missing is not None:
            func_dict["missing"] = self.missing
        
        return {"field_value_factor": func_dict}


@dataclass
class RandomScoreFunction(ScoreFunction):
    """Random score function."""
    
    seed: Optional[int] = None
    field: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        func_dict: Dict[str, Any] = {}
        
        if self.seed is not None:
            func_dict["seed"] = self.seed
        if self.field is not None:
            func_dict["field"] = self.field
        
        return {"random_score": func_dict}


@dataclass
class ScriptScoreFunction(ScoreFunction):
    """Script score function."""
    
    script: str
    params: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        func_dict: Dict[str, Any] = {"script": self.script}
        
        if self.params is not None:
            func_dict["params"] = self.params
        
        return {"script_score": func_dict}


@dataclass
class DecayFunction(ScoreFunction):
    """Decay score function for distance/time-based scoring."""
    
    function_type: str  # gauss, exp, linear
    field: str
    origin: Any
    scale: Any
    offset: Optional[Any] = None
    decay: Optional[float] = None
    multi_value_mode: Optional[str] = None  # min, max, avg, sum
    
    def to_dict(self) -> Dict[str, Any]:
        func_dict: Dict[str, Any] = {
            self.function_type: {
                "field": self.field,
                "origin": self.origin,
                "scale": self.scale,
            }
        }
        
        if self.offset is not None:
            func_dict[self.function_type]["offset"] = self.offset
        if self.decay is not None:
            func_dict[self.function_type]["decay"] = self.decay
        if self.multi_value_mode is not None:
            func_dict[self.function_type]["multi_value_mode"] = self.multi_value_mode
        
        return func_dict


@dataclass
class FunctionScoreQuery(Query):
    """
    Function score query for custom scoring.
    
    This query allows modifying the score of documents using custom functions.
    """
    
    query: Optional[Query] = None
    boost: Optional[float] = None
    functions: List[Dict[str, Any]] = field(default_factory=list)
    score_mode: Optional[str] = None  # multiply, sum, avg, first, max, min
    boost_mode: Optional[str] = None  # multiply, replace, sum, avg, max, min
    max_boost: Optional[float] = None
    min_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        query_dict: Dict[str, Any] = {
            "type": QueryType.FUNCTION_SCORE.value,
        }
        
        if self.query is not None:
            query_dict["query"] = self.query.to_dict()
        
        if self.functions:
            query_dict["functions"] = self.functions
        
        if self.score_mode is not None:
            query_dict["score_mode"] = self.score_mode
        if self.boost_mode is not None:
            query_dict["boost_mode"] = self.boost_mode
        if self.max_boost is not None:
            query_dict["max_boost"] = self.max_boost
        if self.min_score is not None:
            query_dict["min_score"] = self.min_score
        if self.boost is not None:
            query_dict["boost"] = self.boost
        
        return query_dict
    
    def validate(self) -> bool:
        """Validate the query."""
        # Either query or functions must be present
        if not self.query and not self.functions:
            return False
        
        if self.query and not self.query.validate():
            return False
        
        return True
    
    def add_function(
        self,
        function: ScoreFunction,
        filter_query: Optional[Query] = None,
        weight: Optional[float] = None,
    ) -> "FunctionScoreQuery":
        """
        Add a score function.
        
        Args:
            function: Score function to add
            filter_query: Optional filter to apply this function to
            weight: Optional weight for this function
            
        Returns:
            Self for method chaining
        """
        func_dict: Dict[str, Any] = function.to_dict()
        
        if filter_query is not None:
            func_dict["filter"] = filter_query.to_dict()
        if weight is not None:
            func_dict["weight"] = weight
        
        self.functions.append(func_dict)
        return self


class DSLQueryBuilder:
    """
    Builder for constructing complex queries using the DSL.
    
    This builder provides a fluent interface for constructing
    complex queries with multiple clauses and functions.
    """
    
    def __init__(self):
        """Initialize the query builder."""
        self._query: Optional[Query] = None
    
    def match(self, field: str, query: str, **kwargs) -> "DSLQueryBuilder":
        """Add a match query."""
        self._query = MatchQuery(field=field, query=query, **kwargs)
        return self
    
    def multi_match(self, query: str, fields: List[str], **kwargs) -> "DSLQueryBuilder":
        """Add a multi-match query."""
        self._query = MultiMatchQuery(query=query, fields=fields, **kwargs)
        return self
    
    def phrase(self, field: str, query: str, **kwargs) -> "DSLQueryBuilder":
        """Add a phrase query."""
        self._query = PhraseQuery(field=field, query=query, **kwargs)
        return self
    
    def prefix(self, field: str, value: str, **kwargs) -> "DSLQueryBuilder":
        """Add a prefix query."""
        self._query = PrefixQuery(field=field, value=value, **kwargs)
        return self
    
    def wildcard(self, field: str, value: str, **kwargs) -> "DSLQueryBuilder":
        """Add a wildcard query."""
        self._query = WildcardQuery(field=field, value=value, **kwargs)
        return self
    
    def fuzzy(self, field: str, value: str, **kwargs) -> "DSLQueryBuilder":
        """Add a fuzzy query."""
        self._query = FuzzyQuery(field=field, value=value, **kwargs)
        return self
    
    def range(self, field: str, **kwargs) -> "DSLQueryBuilder":
        """Add a range query."""
        self._query = RangeQuery(field=field, **kwargs)
        return self
    
    def exists(self, field: str, **kwargs) -> "DSLQueryBuilder":
        """Add an exists query."""
        self._query = ExistsQuery(field=field, **kwargs)
        return self
    
    def term(self, field: str, value: Any, **kwargs) -> "DSLQueryBuilder":
        """Add a term query."""
        self._query = TermQuery(field=field, value=value, **kwargs)
        return self
    
    def terms(self, field: str, values: List[Any], **kwargs) -> "DSLQueryBuilder":
        """Add a terms query."""
        self._query = TermsQuery(field=field, values=values, **kwargs)
        return self
    
    def nested(self, path: str, query: Query, **kwargs) -> "DSLQueryBuilder":
        """Add a nested query."""
        self._query = NestedQuery(path=path, query=query, **kwargs)
        return self
    
    def bool(self) -> "DSLQueryBuilder":
        """Start a boolean query."""
        self._query = BoolQuery()
        return self
    
    def dis_max(self, queries: List[Query], **kwargs) -> "DSLQueryBuilder":
        """Add a dis_max query."""
        self._query = DisMaxQuery(queries=queries, **kwargs)
        return self
    
    def function_score(self, query: Optional[Query] = None, **kwargs) -> "DSLQueryBuilder":
        """Add a function_score query."""
        self._query = FunctionScoreQuery(query=query, **kwargs)
        return self
    
    def must(self, query: Query) -> "DSLQueryBuilder":
        """Add a MUST clause to a boolean query."""
        if not isinstance(self._query, BoolQuery):
            raise ValueError("Current query is not a BoolQuery")
        self._query.add_must(query)
        return self
    
    def should(self, query: Query) -> "DSLQueryBuilder":
        """Add a SHOULD clause to a boolean query."""
        if not isinstance(self._query, BoolQuery):
            raise ValueError("Current query is not a BoolQuery")
        self._query.add_should(query)
        return self
    
    def must_not(self, query: Query) -> "DSLQueryBuilder":
        """Add a MUST_NOT clause to a boolean query."""
        if not isinstance(self._query, BoolQuery):
            raise ValueError("Current query is not a BoolQuery")
        self._query.add_must_not(query)
        return self
    
    def filter(self, query: Query) -> "DSLQueryBuilder":
        """Add a FILTER clause to a boolean query."""
        if not isinstance(self._query, BoolQuery):
            raise ValueError("Current query is not a BoolQuery")
        self._query.add_filter(query)
        return self
    
    def add_score_function(
        self,
        function: ScoreFunction,
        filter_query: Optional[Query] = None,
        weight: Optional[float] = None,
    ) -> "DSLQueryBuilder":
        """Add a score function to a function_score query."""
        if not isinstance(self._query, FunctionScoreQuery):
            raise ValueError("Current query is not a FunctionScoreQuery")
        self._query.add_function(function, filter_query, weight)
        return self
    
    def build(self) -> Query:
        """
        Build and return the query.
        
        Returns:
            Constructed Query object
            
        Raises:
            ValueError: If query is invalid
        """
        if self._query is None:
            raise ValueError("No query has been built")
        
        if not self._query.validate():
            raise ValueError("Query validation failed")
        
        return self._query
    
    def reset(self) -> "DSLQueryBuilder":
        """Reset the builder to initial state."""
        self._query = None
        return self
    
    @classmethod
    def create(cls) -> "DSLQueryBuilder":
        """Create a new query builder instance."""
        return cls()
