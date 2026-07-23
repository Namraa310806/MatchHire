"""
Advanced Query Engine for MatchHire Search.

This module provides a provider-independent Query DSL and query engine
that powers all search experiences in MatchHire. The engine supports
advanced querying, filtering, faceting, aggregations, highlighting,
autocomplete, and unified multi-entity search.

The architecture remains provider-independent - the same DSL is translated
to PostgreSQL or Elasticsearch native queries by the respective providers.
"""

from .dsl import (
    Query,
    MatchQuery,
    MultiMatchQuery,
    PhraseQuery,
    PrefixQuery,
    WildcardQuery,
    FuzzyQuery,
    RangeQuery,
    ExistsQuery,
    TermQuery,
    TermsQuery,
    NestedQuery,
    BoolQuery,
    DisMaxQuery,
    FunctionScoreQuery,
    QueryBuilder as DSLQueryBuilder,
)
from .filters import (
    Filter,
    FilterBuilder,
    JobFilters,
    CandidateFilters,
    ResumeFilters,
    CompanyFilters,
    RecruiterFilters,
    ApplicationFilters,
    InterviewFilters,
    SkillFilters,
)
from .facets import (
    FacetConfig,
    FacetBuilder,
    FacetState,
    FacetResponse,
    FacetValue,
    FacetSort,
    PredefinedFacets,
)
from .aggregations import (
    Aggregation,
    AggregationBuilder,
    CountAggregation,
    TermsAggregation,
    RangeAggregation,
    RangeBucket,
    HistogramAggregation,
    DateHistogramAggregation,
    StatsAggregation,
    AverageAggregation,
    MinAggregation,
    MaxAggregation,
    SumAggregation,
    PercentilesAggregation,
    CardinalityAggregation,
    PredefinedAggregations,
    HistogramInterval,
)
from .highlighting import (
    HighlightConfig,
    HighlightBuilder,
    HighlightResult,
    HighlightFragment,
    FieldHighlight,
    HighlighterType,
    FragmentOrder,
    PredefinedHighlights,
)
from .autocomplete import (
    AutocompleteEngine,
    AutocompleteRequest,
    AutocompleteResponse,
    AutocompleteSuggestion,
    AutocompleteContext,
    AutocompleteType,
    SuggestionSource,
)
from .unified_search import (
    UnifiedSearchRequest,
    UnifiedSearchResponse,
    UnifiedSearchEngine,
    EntitySearchResult,
    EntityType,
)
from .sorting import (
    SortBuilder,
    SortCondition,
    SortDirection,
    FieldBoost,
    FreshnessBoost,
    PopularityBoost,
    BusinessRuleBoost,
    RankingHooks,
    ScoreMode,
    PredefinedSorts,
)
from .suggestions import (
    SearchSuggestionEngine,
    RelatedQuery,
    SpellingCorrection,
    DidYouMean,
    RecentSearch,
    SavedSearch,
    TrendingSearch,
    SearchTemplate,
    SuggestionType,
)
from .performance import (
    QueryOptimizer,
    QueryCache,
    PerformanceConfig,
)
from .engine import (
    QueryEngine,
    SearchExecutionContext,
)

__all__ = [
    # DSL
    "Query",
    "MatchQuery",
    "MultiMatchQuery",
    "PhraseQuery",
    "PrefixQuery",
    "WildcardQuery",
    "FuzzyQuery",
    "RangeQuery",
    "ExistsQuery",
    "TermQuery",
    "TermsQuery",
    "NestedQuery",
    "BoolQuery",
    "DisMaxQuery",
    "FunctionScoreQuery",
    "DSLQueryBuilder",
    # Filters
    "Filter",
    "FilterBuilder",
    "JobFilters",
    "CandidateFilters",
    "ResumeFilters",
    "CompanyFilters",
    "RecruiterFilters",
    "ApplicationFilters",
    "InterviewFilters",
    "SkillFilters",
    # Facets
    "FacetConfig",
    "FacetBuilder",
    "FacetState",
    "FacetResponse",
    "FacetValue",
    "FacetSort",
    "PredefinedFacets",
    # Aggregations
    "Aggregation",
    "AggregationBuilder",
    "CountAggregation",
    "TermsAggregation",
    "RangeAggregation",
    "RangeBucket",
    "HistogramAggregation",
    "DateHistogramAggregation",
    "StatsAggregation",
    "AverageAggregation",
    "MinAggregation",
    "MaxAggregation",
    "SumAggregation",
    "PercentilesAggregation",
    "CardinalityAggregation",
    "PredefinedAggregations",
    "HistogramInterval",
    # Highlighting
    "HighlightConfig",
    "HighlightBuilder",
    "HighlightResult",
    "HighlightFragment",
    "FieldHighlight",
    "HighlighterType",
    "FragmentOrder",
    "PredefinedHighlights",
    # Autocomplete
    "AutocompleteEngine",
    "AutocompleteRequest",
    "AutocompleteResponse",
    "AutocompleteSuggestion",
    "AutocompleteContext",
    "AutocompleteType",
    "SuggestionSource",
    # Unified Search
    "UnifiedSearchRequest",
    "UnifiedSearchResponse",
    "UnifiedSearchEngine",
    "EntitySearchResult",
    "EntityType",
    # Sorting
    "SortBuilder",
    "SortCondition",
    "SortDirection",
    "FieldBoost",
    "FreshnessBoost",
    "PopularityBoost",
    "BusinessRuleBoost",
    "RankingHooks",
    "ScoreMode",
    "PredefinedSorts",
    # Suggestions
    "SearchSuggestionEngine",
    "RelatedQuery",
    "SpellingCorrection",
    "DidYouMean",
    "RecentSearch",
    "SavedSearch",
    "TrendingSearch",
    "SearchTemplate",
    "SuggestionType",
    # Performance
    "QueryOptimizer",
    "QueryCache",
    "PerformanceConfig",
    # Engine
    "QueryEngine",
    "SearchExecutionContext",
]
