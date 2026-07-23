"""
Elasticsearch query translator for the Query DSL.

This module translates the provider-independent Query DSL into
Elasticsearch-specific query DSL (Query DSL for Elasticsearch).
"""

from typing import Any, Dict, List, Optional, Union

from ..dsl import (
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
    ScoreFunction,
    WeightFunction,
    FieldValueFactorFunction,
    RandomScoreFunction,
    ScriptScoreFunction,
    DecayFunction,
)
from ..filters import Filter, RangeFilter, BooleanFilter, FilterOperator


class ElasticsearchQueryTranslator:
    """
    Translator for converting Query DSL to Elasticsearch queries.
    
    This translator converts the provider-independent Query DSL into
    Elasticsearch's native Query DSL format.
    """
    
    def __init__(self):
        """Initialize the translator."""
        pass
    
    def translate_query(self, query: Query) -> Dict[str, Any]:
        """
        Translate a Query DSL object to Elasticsearch query DSL.
        
        Args:
            query: Query DSL object
            
        Returns:
            Elasticsearch query DSL dictionary
        """
        if isinstance(query, MatchQuery):
            return self._translate_match_query(query)
        elif isinstance(query, MultiMatchQuery):
            return self._translate_multi_match_query(query)
        elif isinstance(query, PhraseQuery):
            return self._translate_phrase_query(query)
        elif isinstance(query, PrefixQuery):
            return self._translate_prefix_query(query)
        elif isinstance(query, WildcardQuery):
            return self._translate_wildcard_query(query)
        elif isinstance(query, FuzzyQuery):
            return self._translate_fuzzy_query(query)
        elif isinstance(query, RangeQuery):
            return self._translate_range_query(query)
        elif isinstance(query, ExistsQuery):
            return self._translate_exists_query(query)
        elif isinstance(query, TermQuery):
            return self._translate_term_query(query)
        elif isinstance(query, TermsQuery):
            return self._translate_terms_query(query)
        elif isinstance(query, NestedQuery):
            return self._translate_nested_query(query)
        elif isinstance(query, BoolQuery):
            return self._translate_bool_query(query)
        elif isinstance(query, DisMaxQuery):
            return self._translate_dis_max_query(query)
        elif isinstance(query, FunctionScoreQuery):
            return self._translate_function_score_query(query)
        else:
            raise ValueError(f"Unsupported query type: {type(query)}")
    
    def _translate_match_query(self, query: MatchQuery) -> Dict[str, Any]:
        """Translate a MatchQuery to Elasticsearch match query."""
        es_query = {
            "match": {
                query.field: {
                    "query": query.query,
                }
            }
        }
        
        if query.operator is not None:
            es_query["match"][query.field]["operator"] = query.operator
        if query.minimum_should_match is not None:
            es_query["match"][query.field]["minimum_should_match"] = query.minimum_should_match
        if query.fuzziness is not None:
            es_query["match"][query.field]["fuzziness"] = query.fuzziness
        if query.prefix_length is not None:
            es_query["match"][query.field]["prefix_length"] = query.prefix_length
        if query.max_expansions is not None:
            es_query["match"][query.field]["max_expansions"] = query.max_expansions
        if query.lenient is not None:
            es_query["match"][query.field]["lenient"] = query.lenient
        if query.zero_terms_query is not None:
            es_query["match"][query.field]["zero_terms_query"] = query.zero_terms_query.value
        if query.boost is not None:
            es_query["match"][query.field]["boost"] = query.boost
        
        return es_query
    
    def _translate_multi_match_query(self, query: MultiMatchQuery) -> Dict[str, Any]:
        """Translate a MultiMatchQuery to Elasticsearch multi_match query."""
        es_query = {
            "multi_match": {
                "query": query.query,
                "fields": query.fields,
                "type": query.type.value,
            }
        }
        
        if query.operator is not None:
            es_query["multi_match"]["operator"] = query.operator
        if query.minimum_should_match is not None:
            es_query["multi_match"]["minimum_should_match"] = query.minimum_should_match
        if query.fuzziness is not None:
            es_query["multi_match"]["fuzziness"] = query.fuzziness
        if query.prefix_length is not None:
            es_query["multi_match"]["prefix_length"] = query.prefix_length
        if query.max_expansions is not None:
            es_query["multi_match"]["max_expansions"] = query.max_expansions
        if query.lenient is not None:
            es_query["multi_match"]["lenient"] = query.lenient
        if query.zero_terms_query is not None:
            es_query["multi_match"]["zero_terms_query"] = query.zero_terms_query.value
        if query.tie_breaker is not None:
            es_query["multi_match"]["tie_breaker"] = query.tie_breaker
        if query.boost is not None:
            es_query["multi_match"]["boost"] = query.boost
        
        return es_query
    
    def _translate_phrase_query(self, query: PhraseQuery) -> Dict[str, Any]:
        """Translate a PhraseQuery to Elasticsearch match_phrase query."""
        es_query = {
            "match_phrase": {
                query.field: {
                    "query": query.query,
                }
            }
        }
        
        if query.slop is not None:
            es_query["match_phrase"][query.field]["slop"] = query.slop
        if query.zero_terms_query is not None:
            es_query["match_phrase"][query.field]["zero_terms_query"] = query.zero_terms_query.value
        if query.boost is not None:
            es_query["match_phrase"][query.field]["boost"] = query.boost
        
        return es_query
    
    def _translate_prefix_query(self, query: PrefixQuery) -> Dict[str, Any]:
        """Translate a PrefixQuery to Elasticsearch prefix query."""
        es_query = {
            "prefix": {
                query.field: {
                    "value": query.value,
                }
            }
        }
        
        if query.rewrite is not None:
            es_query["prefix"][query.field]["rewrite"] = query.rewrite
        if query.boost is not None:
            es_query["prefix"][query.field]["boost"] = query.boost
        
        return es_query
    
    def _translate_wildcard_query(self, query: WildcardQuery) -> Dict[str, Any]:
        """Translate a WildcardQuery to Elasticsearch wildcard query."""
        es_query = {
            "wildcard": {
                query.field: {
                    "value": query.value,
                }
            }
        }
        
        if query.rewrite is not None:
            es_query["wildcard"][query.field]["rewrite"] = query.rewrite
        if query.boost is not None:
            es_query["wildcard"][query.field]["boost"] = query.boost
        
        return es_query
    
    def _translate_fuzzy_query(self, query: FuzzyQuery) -> Dict[str, Any]:
        """Translate a FuzzyQuery to Elasticsearch fuzzy query."""
        es_query = {
            "fuzzy": {
                query.field: {
                    "value": query.value,
                }
            }
        }
        
        if query.fuzziness is not None:
            es_query["fuzzy"][query.field]["fuzziness"] = query.fuzziness
        if query.prefix_length is not None:
            es_query["fuzzy"][query.field]["prefix_length"] = query.prefix_length
        if query.max_expansions is not None:
            es_query["fuzzy"][query.field]["max_expansions"] = query.max_expansions
        if query.transpositions is not None:
            es_query["fuzzy"][query.field]["transpositions"] = query.transpositions
        if query.rewrite is not None:
            es_query["fuzzy"][query.field]["rewrite"] = query.rewrite
        if query.boost is not None:
            es_query["fuzzy"][query.field]["boost"] = query.boost
        
        return es_query
    
    def _translate_range_query(self, query: RangeQuery) -> Dict[str, Any]:
        """Translate a RangeQuery to Elasticsearch range query."""
        es_query = {
            "range": {
                query.field: {}
            }
        }
        
        if query.gte is not None:
            es_query["range"][query.field]["gte"] = query.gte
        if query.gt is not None:
            es_query["range"][query.field]["gt"] = query.gt
        if query.lte is not None:
            es_query["range"][query.field]["lte"] = query.lte
        if query.lt is not None:
            es_query["range"][query.field]["lt"] = query.lt
        if query.format is not None:
            es_query["range"][query.field]["format"] = query.format
        if query.boost is not None:
            es_query["range"][query.field]["boost"] = query.boost
        
        return es_query
    
    def _translate_exists_query(self, query: ExistsQuery) -> Dict[str, Any]:
        """Translate an ExistsQuery to Elasticsearch exists query."""
        es_query = {
            "exists": {
                "field": query.field,
            }
        }
        
        if query.boost is not None:
            es_query["exists"]["boost"] = query.boost
        
        return es_query
    
    def _translate_term_query(self, query: TermQuery) -> Dict[str, Any]:
        """Translate a TermQuery to Elasticsearch term query."""
        es_query = {
            "term": {
                query.field: query.value,
            }
        }
        
        if query.boost is not None:
            es_query["term"][query.field] = {"value": query.value, "boost": query.boost}
        
        return es_query
    
    def _translate_terms_query(self, query: TermsQuery) -> Dict[str, Any]:
        """Translate a TermsQuery to Elasticsearch terms query."""
        es_query = {
            "terms": {
                query.field: query.values,
            }
        }
        
        if query.boost is not None:
            es_query["terms"]["boost"] = query.boost
        
        return es_query
    
    def _translate_nested_query(self, query: NestedQuery) -> Dict[str, Any]:
        """Translate a NestedQuery to Elasticsearch nested query."""
        es_query = {
            "nested": {
                "path": query.path,
                "query": self.translate_query(query.query),
            }
        }
        
        if query.score_mode is not None:
            es_query["nested"]["score_mode"] = query.score_mode
        if query.ignore_unmapped is not None:
            es_query["nested"]["ignore_unmapped"] = query.ignore_unmapped
        if query.boost is not None:
            es_query["nested"]["boost"] = query.boost
        
        return es_query
    
    def _translate_bool_query(self, query: BoolQuery) -> Dict[str, Any]:
        """Translate a BoolQuery to Elasticsearch bool query."""
        es_query = {
            "bool": {}
        }
        
        if query.must:
            es_query["bool"]["must"] = [self.translate_query(q) for q in query.must]
        if query.should:
            es_query["bool"]["should"] = [self.translate_query(q) for q in query.should]
        if query.must_not:
            es_query["bool"]["must_not"] = [self.translate_query(q) for q in query.must_not]
        if query.filter:
            es_query["bool"]["filter"] = [self.translate_query(q) for q in query.filter]
        if query.minimum_should_match is not None:
            es_query["bool"]["minimum_should_match"] = query.minimum_should_match
        if query.boost is not None:
            es_query["bool"]["boost"] = query.boost
        
        return es_query
    
    def _translate_dis_max_query(self, query: DisMaxQuery) -> Dict[str, Any]:
        """Translate a DisMaxQuery to Elasticsearch dis_max query."""
        es_query = {
            "dis_max": {
                "queries": [self.translate_query(q) for q in query.queries],
            }
        }
        
        if query.tie_breaker is not None:
            es_query["dis_max"]["tie_breaker"] = query.tie_breaker
        if query.boost is not None:
            es_query["dis_max"]["boost"] = query.boost
        
        return es_query
    
    def _translate_function_score_query(self, query: FunctionScoreQuery) -> Dict[str, Any]:
        """Translate a FunctionScoreQuery to Elasticsearch function_score query."""
        es_query = {
            "function_score": {}
        }
        
        if query.query is not None:
            es_query["function_score"]["query"] = self.translate_query(query.query)
        
        if query.functions:
            es_query["function_score"]["functions"] = query.functions
        
        if query.score_mode is not None:
            es_query["function_score"]["score_mode"] = query.score_mode
        if query.boost_mode is not None:
            es_query["function_score"]["boost_mode"] = query.boost_mode
        if query.max_boost is not None:
            es_query["function_score"]["max_boost"] = query.max_boost
        if query.min_score is not None:
            es_query["function_score"]["min_score"] = query.min_score
        if query.boost is not None:
            es_query["function_score"]["boost"] = query.boost
        
        return es_query
    
    def translate_filter(self, filter_obj: Union[Filter, RangeFilter, BooleanFilter]) -> Dict[str, Any]:
        """
        Translate a Filter to Elasticsearch filter context.
        
        Args:
            filter_obj: Filter object
            
        Returns:
            Elasticsearch filter DSL dictionary
        """
        if isinstance(filter_obj, RangeFilter):
            return self._translate_range_filter(filter_obj)
        elif isinstance(filter_obj, BooleanFilter):
            return self._translate_boolean_filter(filter_obj)
        else:
            return self._translate_simple_filter(filter_obj)
    
    def _translate_simple_filter(self, filter_obj: Filter) -> Dict[str, Any]:
        """Translate a simple Filter to Elasticsearch term/range query."""
        field = filter_obj.field
        operator = filter_obj.operator
        value = filter_obj.value
        
        if operator == FilterOperator.EQ:
            return {"term": {field: value}}
        elif operator == FilterOperator.NE:
            return {"bool": {"must_not": [{"term": {field: value}}]}}
        elif operator == FilterOperator.GT:
            return {"range": {field: {"gt": value}}}
        elif operator == FilterOperator.GTE:
            return {"range": {field: {"gte": value}}}
        elif operator == FilterOperator.LT:
            return {"range": {field: {"lt": value}}}
        elif operator == FilterOperator.LTE:
            return {"range": {field: {"lte": value}}}
        elif operator == FilterOperator.IN:
            return {"terms": {field: value}}
        elif operator == FilterOperator.NOT_IN:
            return {"bool": {"must_not": [{"terms": {field: value}}]}}
        elif operator == FilterOperator.CONTAINS:
            return {"wildcard": {field: f"*{value}*"}}
        elif operator == FilterOperator.NOT_CONTAINS:
            return {"bool": {"must_not": [{"wildcard": {field: f"*{value}*"}}]}}
        elif operator == FilterOperator.STARTS_WITH:
            return {"prefix": {field: value}}
        elif operator == FilterOperator.ENDS_WITH:
            return {"wildcard": {field: f"*{value}"}}
        elif operator == FilterOperator.EXISTS:
            return {"exists": {"field": field}}
        elif operator == FilterOperator.NOT_EXISTS:
            return {"bool": {"must_not": [{"exists": {"field": field}}]}}
        elif operator == FilterOperator.IS_NULL:
            return {"bool": {"must_not": [{"exists": {"field": field}}]}}
        elif operator == FilterOperator.IS_NOT_NULL:
            return {"exists": {"field": field}}
        else:
            return {"term": {field: value}}
    
    def _translate_range_filter(self, filter_obj: RangeFilter) -> Dict[str, Any]:
        """Translate a RangeFilter to Elasticsearch range query."""
        es_query = {
            "range": {
                filter_obj.field: {}
            }
        }
        
        if filter_obj.gte is not None:
            es_query["range"][filter_obj.field]["gte"] = filter_obj.gte
        if filter_obj.gt is not None:
            es_query["range"][filter_obj.field]["gt"] = filter_obj.gt
        if filter_obj.lte is not None:
            es_query["range"][filter_obj.field]["lte"] = filter_obj.lte
        if filter_obj.lt is not None:
            es_query["range"][filter_obj.field]["lt"] = filter_obj.lt
        
        return es_query
    
    def _translate_boolean_filter(self, filter_obj: BooleanFilter) -> Dict[str, Any]:
        """Translate a BooleanFilter to Elasticsearch bool query."""
        es_query = {
            "bool": {}
        }
        
        for sub_filter in filter_obj.filters:
            translated = self.translate_filter(sub_filter)
            
            if filter_obj.operator == "AND":
                if "must" not in es_query["bool"]:
                    es_query["bool"]["must"] = []
                es_query["bool"]["must"].append(translated)
            elif filter_obj.operator == "OR":
                if "should" not in es_query["bool"]:
                    es_query["bool"]["should"] = []
                es_query["bool"]["should"].append(translated)
            elif filter_obj.operator == "NOT":
                if "must_not" not in es_query["bool"]:
                    es_query["bool"]["must_not"] = []
                es_query["bool"]["must_not"].append(translated)
        
        return es_query
    
    def translate_sort(self, sort_conditions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Translate sort conditions to Elasticsearch sort DSL.
        
        Args:
            sort_conditions: List of sort condition dictionaries
            
        Returns:
            Elasticsearch sort DSL list
        """
        es_sort = []
        
        for sort_spec in sort_conditions:
            field = sort_spec.get("field")
            direction = sort_spec.get("direction", "asc")
            mode = sort_spec.get("mode")
            missing = sort_spec.get("missing")
            unmapped_type = sort_spec.get("unmapped_type")
            
            sort_entry = {field: {"order": direction}}
            
            if mode is not None:
                sort_entry[field]["mode"] = mode
            if missing is not None:
                missing_value = "_last" if direction == "asc" else "_first"
                sort_entry[field]["missing"] = missing if missing != "auto" else missing_value
            if unmapped_type is not None:
                sort_entry[field]["unmapped_type"] = unmapped_type
            
            es_sort.append(sort_entry)
        
        return es_sort
    
    def translate_aggregation(self, agg_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate aggregation dictionary to Elasticsearch aggregation DSL.
        
        Args:
            agg_dict: Aggregation dictionary from Query Engine
            
        Returns:
            Elasticsearch aggregation DSL
        """
        agg_type = agg_dict.get("type")
        name = agg_dict.get("name")
        
        es_agg = {}
        
        if agg_type == "count":
            if agg_dict.get("field"):
                es_agg[name] = {"value_count": {"field": agg_dict["field"]}}
            else:
                es_agg[name] = {"value_count": {"_index": "_doc"}}
        
        elif agg_type == "terms":
            es_agg[name] = {
                "terms": {
                    "field": agg_dict["field"],
                    "size": agg_dict.get("size", 10),
                    "min_doc_count": agg_dict.get("min_doc_count", 1),
                }
            }
            if agg_dict.get("order"):
                es_agg[name]["terms"]["order"] = agg_dict["order"]
            if agg_dict.get("missing") is not None:
                es_agg[name]["terms"]["missing"] = agg_dict["missing"]
        
        elif agg_type == "range":
            es_agg[name] = {
                "range": {
                    "field": agg_dict["field"],
                    "ranges": agg_dict["ranges"],
                }
            }
        
        elif agg_type == "histogram":
            es_agg[name] = {
                "histogram": {
                    "field": agg_dict["field"],
                    "interval": agg_dict["interval"],
                    "min_doc_count": agg_dict.get("min_doc_count", 1),
                }
            }
        
        elif agg_type == "date_histogram":
            es_agg[name] = {
                "date_histogram": {
                    "field": agg_dict["field"],
                    "calendar_interval": agg_dict["interval"],
                    "min_doc_count": agg_dict.get("min_doc_count", 1),
                }
            }
        
        elif agg_type == "stats":
            es_agg[name] = {"stats": {"field": agg_dict["field"]}}
        
        elif agg_type == "avg":
            es_agg[name] = {"avg": {"field": agg_dict["field"]}}
        
        elif agg_type == "min":
            es_agg[name] = {"min": {"field": agg_dict["field"]}}
        
        elif agg_type == "max":
            es_agg[name] = {"max": {"field": agg_dict["field"]}}
        
        elif agg_type == "sum":
            es_agg[name] = {"sum": {"field": agg_dict["field"]}}
        
        elif agg_type == "percentiles":
            es_agg[name] = {
                "percentiles": {
                    "field": agg_dict["field"],
                    "percents": agg_dict.get("percents", [1.0, 5.0, 25.0, 50.0, 75.0, 95.0, 99.0]),
                }
            }
        
        elif agg_type == "cardinality":
            es_agg[name] = {"cardinality": {"field": agg_dict["field"]}}
        
        return es_agg
    
    def translate_highlight(self, highlight_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate highlight configuration to Elasticsearch highlight DSL.
        
        Args:
            highlight_config: Highlight configuration dictionary
            
        Returns:
            Elasticsearch highlight DSL
        """
        field = highlight_config.get("field")
        
        es_highlight = {
            "fields": {
                field: {
                    "pre_tags": highlight_config.get("pre_tags", ["<em>"]),
                    "post_tags": highlight_config.get("post_tags", ["</em>"]),
                    "fragment_size": highlight_config.get("fragment_size", 150),
                    "number_of_fragments": highlight_config.get("number_of_fragments", 3),
                    "fragment_offset": highlight_config.get("fragment_offset", 0),
                    "type": highlight_config.get("type", "unified"),
                    "order": highlight_config.get("order", "score"),
                }
            }
        }
        
        if highlight_config.get("highlight_query"):
            es_highlight["highlight_query"] = highlight_config["highlight_query"]
        
        return es_highlight
