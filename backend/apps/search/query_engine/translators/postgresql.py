"""
PostgreSQL query translator for the Query DSL.

This module translates the provider-independent Query DSL into
PostgreSQL-specific queries using Django ORM and PostgreSQL features
like full-text search (tsvector) and trigram matching (pg_trgm).
"""

from typing import Any, Dict, List, Optional, Union
from django.db.models import Q, QuerySet
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

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
)
from ..filters import Filter, RangeFilter, BooleanFilter, FilterOperator


class PostgreSQLQueryTranslator:
    """
    Translator for converting Query DSL to PostgreSQL queries.
    
    This translator converts the provider-independent Query DSL into
    Django ORM queries with PostgreSQL-specific features.
    """
    
    def __init__(self, model):
        """
        Initialize the translator.
        
        Args:
            model: Django model class for the entity type
        """
        self.model = model
        self._searchable_fields = self._get_searchable_fields()
    
    def _get_searchable_fields(self) -> List[str]:
        """
        Get searchable fields for the model.
        
        Returns:
            List of searchable field names
        """
        # Default searchable fields - can be overridden per model
        return ["title", "description", "name"]
    
    def translate_query(
        self,
        query: Query,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a Query DSL object to a Django QuerySet.
        
        Args:
            query: Query DSL object
            queryset: Base QuerySet to build upon
            
        Returns:
            Modified QuerySet with query applied
        """
        if isinstance(query, MatchQuery):
            return self._translate_match_query(query, queryset)
        elif isinstance(query, MultiMatchQuery):
            return self._translate_multi_match_query(query, queryset)
        elif isinstance(query, PhraseQuery):
            return self._translate_phrase_query(query, queryset)
        elif isinstance(query, PrefixQuery):
            return self._translate_prefix_query(query, queryset)
        elif isinstance(query, WildcardQuery):
            return self._translate_wildcard_query(query, queryset)
        elif isinstance(query, FuzzyQuery):
            return self._translate_fuzzy_query(query, queryset)
        elif isinstance(query, RangeQuery):
            return self._translate_range_query(query, queryset)
        elif isinstance(query, ExistsQuery):
            return self._translate_exists_query(query, queryset)
        elif isinstance(query, TermQuery):
            return self._translate_term_query(query, queryset)
        elif isinstance(query, TermsQuery):
            return self._translate_terms_query(query, queryset)
        elif isinstance(query, NestedQuery):
            return self._translate_nested_query(query, queryset)
        elif isinstance(query, BoolQuery):
            return self._translate_bool_query(query, queryset)
        elif isinstance(query, DisMaxQuery):
            return self._translate_dis_max_query(query, queryset)
        elif isinstance(query, FunctionScoreQuery):
            return self._translate_function_score_query(query, queryset)
        else:
            raise ValueError(f"Unsupported query type: {type(query)}")
    
    def _translate_match_query(
        self,
        query: MatchQuery,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a MatchQuery to PostgreSQL full-text search.
        
        Args:
            query: MatchQuery object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        # Use PostgreSQL full-text search
        search_vector = SearchVector(*self._searchable_fields)
        search_query = SearchQuery(query.query)
        
        queryset = queryset.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query)
        
        return queryset
    
    def _translate_multi_match_query(
        self,
        query: MultiMatchQuery,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a MultiMatchQuery to PostgreSQL full-text search.
        
        Args:
            query: MultiMatchQuery object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        # Map DSL fields to model fields
        model_fields = self._map_fields(query.fields)
        
        search_vector = SearchVector(*model_fields)
        search_query = SearchQuery(query.query)
        
        queryset = queryset.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query)
        
        return queryset
    
    def _translate_phrase_query(
        self,
        query: PhraseQuery,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a PhraseQuery to PostgreSQL phrase search.
        
        Args:
            query: PhraseQuery object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        # PostgreSQL phrase search using tsquery with phrase operator
        phrase_query = query.query.replace(" ", " <-> ")
        
        search_vector = SearchVector(*self._searchable_fields)
        search_query = SearchQuery(phrase_query)
        
        queryset = queryset.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query)
        
        return queryset
    
    def _translate_prefix_query(
        self,
        query: PrefixQuery,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a PrefixQuery to PostgreSQL icontains.
        
        Args:
            query: PrefixQuery object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        # Use icontains for prefix matching
        # In production, consider using pg_trgm for better performance
        return queryset.filter(**{f"{query.field}__icontains": query.value})
    
    def _translate_wildcard_query(
        self,
        query: WildcardQuery,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a WildcardQuery to PostgreSQL LIKE/ILIKE.
        
        Args:
            query: WildcardQuery object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        # Convert wildcard pattern to SQL LIKE pattern
        pattern = query.value.replace("*", "%").replace("?", "_")
        return queryset.filter(**{f"{query.field}__icontains": pattern})
    
    def _translate_fuzzy_query(
        self,
        query: FuzzyQuery,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a FuzzyQuery to PostgreSQL trigram similarity.
        
        Args:
            query: FuzzyQuery object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        # Use pg_trgm for fuzzy matching
        # This requires the pg_trgm extension
        from django.contrib.postgres.search import TrigramSimilarity
        
        return queryset.annotate(
            similarity=TrigramSimilarity(query.field, query.value)
        ).filter(similarity__gt=0.3).order_by("-similarity")
    
    def _translate_range_query(
        self,
        query: RangeQuery,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a RangeQuery to PostgreSQL range filters.
        
        Args:
            query: RangeQuery object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        filter_kwargs = {}
        
        if query.gte is not None:
            filter_kwargs[f"{query.field}__gte"] = query.gte
        if query.gt is not None:
            filter_kwargs[f"{query.field}__gt"] = query.gt
        if query.lte is not None:
            filter_kwargs[f"{query.field}__lte"] = query.lte
        if query.lt is not None:
            filter_kwargs[f"{query.field}__lt"] = query.lt
        
        return queryset.filter(**filter_kwargs)
    
    def _translate_exists_query(
        self,
        query: ExistsQuery,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate an ExistsQuery to PostgreSQL isnull check.
        
        Args:
            query: ExistsQuery object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        return queryset.filter(**{f"{query.field}__isnull": False})
    
    def _translate_term_query(
        self,
        query: TermQuery,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a TermQuery to PostgreSQL exact match.
        
        Args:
            query: TermQuery object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        return queryset.filter(**{query.field: query.value})
    
    def _translate_terms_query(
        self,
        query: TermsQuery,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a TermsQuery to PostgreSQL IN clause.
        
        Args:
            query: TermsQuery object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        return queryset.filter(**{f"{query.field}__in": query.values})
    
    def _translate_nested_query(
        self,
        query: NestedQuery,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a NestedQuery to PostgreSQL related object query.
        
        Args:
            query: NestedQuery object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        # For nested queries, use Django's related object filtering
        # This is a simplified implementation
        related_field = query.path
        return queryset.filter(**{f"{related_field}__isnull": False})
    
    def _translate_bool_query(
        self,
        query: BoolQuery,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a BoolQuery to Django Q objects.
        
        Args:
            query: BoolQuery object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        q_objects = Q()
        
        for must_query in query.must:
            q_objects &= self._query_to_q(must_query)
        
        for should_query in query.should:
            q_objects |= self._query_to_q(should_query)
        
        for must_not_query in query.must_not:
            q_objects &= ~self._query_to_q(must_not_query)
        
        for filter_query in query.filter:
            q_objects &= self._query_to_q(filter_query)
        
        return queryset.filter(q_objects)
    
    def _translate_dis_max_query(
        self,
        query: DisMaxQuery,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a DisMaxQuery to PostgreSQL OR with ranking.
        
        Args:
            query: DisMaxQuery object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        # DisMax is approximated by OR with ranking
        q_objects = Q()
        
        for sub_query in query.queries:
            q_objects |= self._query_to_q(sub_query)
        
        return queryset.filter(q_objects)
    
    def _translate_function_score_query(
        self,
        query: FunctionScoreQuery,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a FunctionScoreQuery to PostgreSQL with custom scoring.
        
        Args:
            query: FunctionScoreQuery object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        # First apply the base query
        if query.query:
            queryset = self.translate_query(query.query, queryset)
        
        # Apply score functions using annotations
        # This is a simplified implementation
        # In production, you'd implement proper function score translation
        return queryset
    
    def _query_to_q(self, query: Query) -> Q:
        """
        Convert a Query to a Django Q object.
        
        Args:
            query: Query object
            
        Returns:
            Django Q object
        """
        if isinstance(query, TermQuery):
            return Q(**{query.field: query.value})
        elif isinstance(query, TermsQuery):
            return Q(**{f"{query.field}__in": query.values})
        elif isinstance(query, RangeQuery):
            q = Q()
            if query.gte is not None:
                q &= Q(**{f"{query.field}__gte": query.gte})
            if query.gt is not None:
                q &= Q(**{f"{query.field}__gt": query.gt})
            if query.lte is not None:
                q &= Q(**{f"{query.field}__lte": query.lte})
            if query.lt is not None:
                q &= Q(**{f"{query.field}__lt": query.lt})
            return q
        elif isinstance(query, ExistsQuery):
            return Q(**{f"{query.field}__isnull": False})
        elif isinstance(query, PrefixQuery):
            return Q(**{f"{query.field}__icontains": query.value})
        else:
            # For complex queries, use a placeholder
            # In production, implement full translation
            return Q()
    
    def translate_filter(
        self,
        filter_obj: Union[Filter, RangeFilter, BooleanFilter],
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a Filter to a Django QuerySet filter.
        
        Args:
            filter_obj: Filter object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        if isinstance(filter_obj, RangeFilter):
            return self._translate_range_filter(filter_obj, queryset)
        elif isinstance(filter_obj, BooleanFilter):
            return self._translate_boolean_filter(filter_obj, queryset)
        else:
            return self._translate_simple_filter(filter_obj, queryset)
    
    def _translate_simple_filter(
        self,
        filter_obj: Filter,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a simple Filter to Django QuerySet filter.
        
        Args:
            filter_obj: Filter object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        field = filter_obj.field
        operator = filter_obj.operator
        value = filter_obj.value
        
        # Map operator to Django lookup
        operator_map = {
            FilterOperator.EQ: "",
            FilterOperator.NE: "",
            FilterOperator.GT: "__gt",
            FilterOperator.GTE: "__gte",
            FilterOperator.LT: "__lt",
            FilterOperator.LTE: "__lte",
            FilterOperator.IN: "__in",
            FilterOperator.NOT_IN: "__in",
            FilterOperator.CONTAINS: "__icontains",
            FilterOperator.NOT_CONTAINS: "__icontains",
            FilterOperator.STARTS_WITH: "__istartswith",
            FilterOperator.ENDS_WITH: "__iendswith",
            FilterOperator.IS_NULL: "__isnull",
            FilterOperator.IS_NOT_NULL: "__isnull",
        }
        
        lookup = operator_map.get(operator, "")
        
        if operator == FilterOperator.NE:
            return queryset.exclude(**{field: value})
        elif operator == FilterOperator.NOT_IN:
            return queryset.exclude(**{f"{field}__in": value})
        elif operator == FilterOperator.NOT_CONTAINS:
            return queryset.exclude(**{f"{field}__icontains": value})
        elif operator == FilterOperator.IS_NULL:
            return queryset.filter(**{f"{field}__isnull": True})
        elif operator == FilterOperator.IS_NOT_NULL:
            return queryset.filter(**{f"{field}__isnull": False})
        else:
            return queryset.filter(**{f"{field}{lookup}": value})
    
    def _translate_range_filter(
        self,
        filter_obj: RangeFilter,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a RangeFilter to Django QuerySet filter.
        
        Args:
            filter_obj: RangeFilter object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        filter_kwargs = {}
        
        if filter_obj.gte is not None:
            filter_kwargs[f"{filter_obj.field}__gte"] = filter_obj.gte
        if filter_obj.gt is not None:
            filter_kwargs[f"{filter_obj.field}__gt"] = filter_obj.gt
        if filter_obj.lte is not None:
            filter_kwargs[f"{filter_obj.field}__lte"] = filter_obj.lte
        if filter_obj.lt is not None:
            filter_kwargs[f"{filter_obj.field}__lt"] = filter_obj.lt
        
        return queryset.filter(**filter_kwargs)
    
    def _translate_boolean_filter(
        self,
        filter_obj: BooleanFilter,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate a BooleanFilter to Django Q objects.
        
        Args:
            filter_obj: BooleanFilter object
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        q_objects = Q()
        
        for sub_filter in filter_obj.filters:
            if filter_obj.operator == "AND":
                q_objects &= self._filter_to_q(sub_filter)
            elif filter_obj.operator == "OR":
                q_objects |= self._filter_to_q(sub_filter)
            elif filter_obj.operator == "NOT":
                q_objects &= ~self._filter_to_q(sub_filter)
        
        return queryset.filter(q_objects)
    
    def _filter_to_q(self, filter_obj: Union[Filter, RangeFilter, BooleanFilter]) -> Q:
        """
        Convert a Filter to a Django Q object.
        
        Args:
            filter_obj: Filter object
            
        Returns:
            Django Q object
        """
        if isinstance(filter_obj, BooleanFilter):
            q = Q()
            for sub_filter in filter_obj.filters:
                if filter_obj.operator == "AND":
                    q &= self._filter_to_q(sub_filter)
                elif filter_obj.operator == "OR":
                    q |= self._filter_to_q(sub_filter)
                elif filter_obj.operator == "NOT":
                    q &= ~self._filter_to_q(sub_filter)
            return q
        elif isinstance(filter_obj, RangeFilter):
            q = Q()
            if filter_obj.gte is not None:
                q &= Q(**{f"{filter_obj.field}__gte": filter_obj.gte})
            if filter_obj.gt is not None:
                q &= Q(**{f"{filter_obj.field}__gt": filter_obj.gt})
            if filter_obj.lte is not None:
                q &= Q(**{f"{filter_obj.field}__lte": filter_obj.lte})
            if filter_obj.lt is not None:
                q &= Q(**{f"{filter_obj.field}__lt": filter_obj.lt})
            return q
        else:
            # Simple filter
            field = filter_obj.field
            operator = filter_obj.operator
            value = filter_obj.value
            
            if operator == FilterOperator.EQ:
                return Q(**{field: value})
            elif operator == FilterOperator.NE:
                return ~Q(**{field: value})
            elif operator == FilterOperator.IN:
                return Q(**{f"{field}__in": value})
            elif operator == FilterOperator.CONTAINS:
                return Q(**{f"{field}__icontains": value})
            elif operator == FilterOperator.GT:
                return Q(**{f"{field}__gt": value})
            elif operator == FilterOperator.GTE:
                return Q(**{f"{field}__gte": value})
            elif operator == FilterOperator.LT:
                return Q(**{f"{field}__lt": value})
            elif operator == FilterOperator.LTE:
                return Q(**{f"{field}__lte": value})
            else:
                return Q(**{field: value})
    
    def translate_sort(
        self,
        sort_conditions: List[Dict[str, Any]],
        queryset: QuerySet,
    ) -> QuerySet:
        """
        Translate sort conditions to Django QuerySet ordering.
        
        Args:
            sort_conditions: List of sort condition dictionaries
            queryset: Base QuerySet
            
        Returns:
            Modified QuerySet
        """
        order_fields = []
        
        for sort_spec in sort_conditions:
            field = sort_spec.get("field")
            direction = sort_spec.get("direction", "asc")
            
            if direction == "desc":
                order_fields.append(f"-{field}")
            else:
                order_fields.append(field)
        
        if order_fields:
            queryset = queryset.order_by(*order_fields)
        
        return queryset
    
    def _map_fields(self, fields: List[str]) -> List[str]:
        """
        Map DSL field names to model field names.
        
        Args:
            fields: List of DSL field names
            
        Returns:
            List of model field names
        """
        # This is a simplified implementation
        # In production, you'd have a proper field mapping
        return fields
