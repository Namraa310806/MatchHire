"""
Tests for query builder.
"""

import pytest

from apps.search.query_builder.builder import (
    QueryBuilder,
    QueryBuilderFactory,
    FilterCondition,
    BooleanFilter,
    SortCondition,
    FieldBoost,
    BooleanOperator,
    ComparisonOperator,
)


class TestFilterCondition:
    """Test FilterCondition model."""

    def test_exact_condition(self):
        """Test exact filter condition."""
        condition = FilterCondition(field="status", operator=ComparisonOperator.EXACT, value="active")
        result = condition.to_dict()
        assert result == {"field": "status", "operator": "exact", "value": "active"}

    def test_gte_condition(self):
        """Test gte filter condition."""
        condition = FilterCondition(field="salary", operator=ComparisonOperator.GTE, value=50000)
        result = condition.to_dict()
        assert result == {"field": "salary", "operator": "gte", "value": 50000}


class TestBooleanFilter:
    """Test BooleanFilter model."""

    def test_and_filter(self):
        """Test AND boolean filter."""
        filter_obj = BooleanFilter(
            operator=BooleanOperator.AND,
            conditions=[
                FilterCondition(field="status", operator=ComparisonOperator.EXACT, value="active"),
                FilterCondition(field="salary", operator=ComparisonOperator.GTE, value=50000),
            ],
        )
        result = filter_obj.to_dict()
        assert result["operator"] == "and"
        assert len(result["conditions"]) == 2

    def test_add_condition(self):
        """Test adding a condition to boolean filter."""
        filter_obj = BooleanFilter(operator=BooleanOperator.AND)
        condition = FilterCondition(field="status", operator=ComparisonOperator.EXACT, value="active")
        filter_obj.add_condition(condition)
        assert len(filter_obj.conditions) == 1


class TestSortCondition:
    """Test SortCondition model."""

    def test_asc_sort(self):
        """Test ascending sort condition."""
        sort = SortCondition(field="created_at", direction="asc")
        result = sort.to_dict()
        assert result == {"field": "created_at", "direction": "asc"}

    def test_desc_sort(self):
        """Test descending sort condition."""
        sort = SortCondition(field="created_at", direction="desc")
        result = sort.to_dict()
        assert result == {"field": "created_at", "direction": "desc"}


class TestFieldBoost:
    """Test FieldBoost model."""

    def test_field_boost(self):
        """Test field boost."""
        boost = FieldBoost(field="title", boost=2.0)
        result = boost.to_dict()
        assert result == {"field": "title", "boost": 2.0}


class TestQueryBuilder:
    """Test QueryBuilder functionality."""

    def test_initialization(self):
        """Test query builder initialization."""
        builder = QueryBuilder(entity_type="job")
        assert builder.entity_type == "job"
        assert builder.query_string is None
        assert builder.filters == []

    def test_set_query(self):
        """Test setting query string."""
        builder = QueryBuilder(entity_type="job")
        builder.set_query("engineer")
        assert builder.query_string == "engineer"

    def test_add_filter(self):
        """Test adding a filter."""
        builder = QueryBuilder(entity_type="job")
        builder.add_filter("status", ComparisonOperator.EXACT, "active")
        assert len(builder.filters) == 1

    def test_add_filter_with_string_operator(self):
        """Test adding a filter with string operator."""
        builder = QueryBuilder(entity_type="job")
        builder.add_filter("status", "exact", "active")
        assert len(builder.filters) == 1

    def test_add_boolean_filter(self):
        """Test adding a boolean filter."""
        builder = QueryBuilder(entity_type="job")
        conditions = [
            FilterCondition(field="status", operator=ComparisonOperator.EXACT, value="active"),
            FilterCondition(field="salary", operator=ComparisonOperator.GTE, value=50000),
        ]
        builder.add_boolean_filter(BooleanOperator.AND, conditions)
        assert len(builder.filters) == 1

    def test_add_sort(self):
        """Test adding a sort condition."""
        builder = QueryBuilder(entity_type="job")
        builder.add_sort("created_at", "asc")
        assert len(builder.sort_conditions) == 1

    def test_set_fields(self):
        """Test setting field selection."""
        builder = QueryBuilder(entity_type="job")
        builder.set_fields(["title", "company"])
        assert builder.field_selection == ["title", "company"]

    def test_add_boost(self):
        """Test adding a field boost."""
        builder = QueryBuilder(entity_type="job")
        builder.add_boost("title", 2.0)
        assert len(builder.field_boosts) == 1

    def test_set_pagination(self):
        """Test setting pagination parameters."""
        builder = QueryBuilder(entity_type="job")
        builder.set_pagination(page=2, page_size=10)
        assert builder.pagination == {"page": 2, "page_size": 10}

    def test_set_offset_limit(self):
        """Test setting offset/limit parameters."""
        builder = QueryBuilder(entity_type="job")
        builder.set_offset_limit(offset=10, limit=20)
        assert builder.pagination == {"offset": 10, "limit": 20}

    def test_build(self):
        """Test building query dictionary."""
        builder = QueryBuilder(entity_type="job")
        builder.set_query("engineer")
        builder.add_filter("status", ComparisonOperator.EXACT, "active")
        builder.add_sort("created_at", "desc")
        builder.set_pagination(page=1, page_size=20)

        result = builder.build()
        assert result["entity_type"] == "job"
        assert result["query"] == "engineer"
        assert len(result["filters"]) == 1
        assert len(result["sort"]) == 1
        assert result["pagination"] == {"page": 1, "page_size": 20}

    def test_build_minimal(self):
        """Test building minimal query."""
        builder = QueryBuilder(entity_type="job")
        result = builder.build()
        assert result == {"entity_type": "job"}

    def test_method_chaining(self):
        """Test method chaining."""
        builder = (
            QueryBuilder(entity_type="job")
            .set_query("engineer")
            .add_filter("status", ComparisonOperator.EXACT, "active")
            .add_sort("created_at", "desc")
            .set_pagination(page=1, page_size=20)
        )
        assert builder.query_string == "engineer"
        assert len(builder.filters) == 1
        assert len(builder.sort_conditions) == 1

    def test_reset(self):
        """Test resetting the builder."""
        builder = QueryBuilder(entity_type="job")
        builder.set_query("engineer")
        builder.add_filter("status", ComparisonOperator.EXACT, "active")
        builder.reset()
        assert builder.query_string is None
        assert builder.filters == []

    @classmethod
    def test_for_entity(cls):
        """Test QueryBuilderFactory.for_entity."""
        builder = QueryBuilder.for_entity("job")
        assert builder.entity_type == "job"


class TestQueryBuilderFactory:
    """Test QueryBuilderFactory."""

    def test_job_search(self):
        """Test creating job search builder."""
        builder = QueryBuilderFactory.job_search()
        assert builder.entity_type == "job"

    def test_candidate_search(self):
        """Test creating candidate search builder."""
        builder = QueryBuilderFactory.candidate_search()
        assert builder.entity_type == "candidate"

    def test_resume_search(self):
        """Test creating resume search builder."""
        builder = QueryBuilderFactory.resume_search()
        assert builder.entity_type == "resume"

    def test_company_search(self):
        """Test creating company search builder."""
        builder = QueryBuilderFactory.company_search()
        assert builder.entity_type == "company"

    def test_recruiter_search(self):
        """Test creating recruiter search builder."""
        builder = QueryBuilderFactory.recruiter_search()
        assert builder.entity_type == "recruiter"

    def test_skill_search(self):
        """Test creating skill search builder."""
        builder = QueryBuilderFactory.skill_search()
        assert builder.entity_type == "skill"
