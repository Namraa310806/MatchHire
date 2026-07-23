"""
Tests for the Query DSL.
"""

import unittest
from apps.search.query_engine.dsl import (
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
    BoolQuery,
    DisMaxQuery,
    FunctionScoreQuery,
    DSLQueryBuilder,
    BooleanOperator,
    MatchType,
    ZeroTermsQuery,
    WeightFunction,
    FieldValueFactorFunction,
)


class TestMatchQuery(unittest.TestCase):
    """Test cases for MatchQuery."""
    
    def test_basic_match_query(self):
        """Test basic match query creation."""
        query = MatchQuery(field="title", query="software engineer")
        self.assertEqual(query.field, "title")
        self.assertEqual(query.query, "software engineer")
        self.assertTrue(query.validate())
    
    def test_match_query_with_operator(self):
        """Test match query with operator."""
        query = MatchQuery(field="title", query="software engineer", operator="and")
        self.assertEqual(query.operator, "and")
    
    def test_match_query_to_dict(self):
        """Test match query serialization."""
        query = MatchQuery(field="title", query="software engineer")
        query_dict = query.to_dict()
        self.assertEqual(query_dict["type"], "match")
        self.assertEqual(query_dict["field"], "title")
        self.assertEqual(query_dict["query"], "software engineer")
    
    def test_match_query_validation(self):
        """Test match query validation."""
        valid_query = MatchQuery(field="title", query="test")
        self.assertTrue(valid_query.validate())
        
        invalid_query = MatchQuery(field="", query="test")
        self.assertFalse(invalid_query.validate())


class TestMultiMatchQuery(unittest.TestCase):
    """Test cases for MultiMatchQuery."""
    
    def test_basic_multi_match_query(self):
        """Test basic multi-match query creation."""
        query = MultiMatchQuery(
            query="software engineer",
            fields=["title", "description"]
        )
        self.assertEqual(query.query, "software engineer")
        self.assertEqual(query.fields, ["title", "description"])
        self.assertTrue(query.validate())
    
    def test_multi_match_query_type(self):
        """Test multi-match query with type."""
        query = MultiMatchQuery(
            query="software engineer",
            fields=["title", "description"],
            type=MatchType.BEST_FIELDS
        )
        self.assertEqual(query.type, MatchType.BEST_FIELDS)
    
    def test_multi_match_query_to_dict(self):
        """Test multi-match query serialization."""
        query = MultiMatchQuery(
            query="software engineer",
            fields=["title", "description"]
        )
        query_dict = query.to_dict()
        self.assertEqual(query_dict["type"], "multi_match")
        self.assertEqual(query_dict["fields"], ["title", "description"])


class TestPhraseQuery(unittest.TestCase):
    """Test cases for PhraseQuery."""
    
    def test_basic_phrase_query(self):
        """Test basic phrase query creation."""
        query = PhraseQuery(field="title", query="software engineer")
        self.assertEqual(query.field, "title")
        self.assertEqual(query.query, "software engineer")
        self.assertTrue(query.validate())
    
    def test_phrase_query_with_slop(self):
        """Test phrase query with slop."""
        query = PhraseQuery(field="title", query="software engineer", slop=2)
        self.assertEqual(query.slop, 2)


class TestRangeQuery(unittest.TestCase):
    """Test cases for RangeQuery."""
    
    def test_basic_range_query(self):
        """Test basic range query creation."""
        query = RangeQuery(field="salary", gte=50000, lte=100000)
        self.assertEqual(query.field, "salary")
        self.assertEqual(query.gte, 50000)
        self.assertEqual(query.lte, 100000)
        self.assertTrue(query.validate())
    
    def test_range_query_to_dict(self):
        """Test range query serialization."""
        query = RangeQuery(field="salary", gte=50000, lte=100000)
        query_dict = query.to_dict()
        self.assertEqual(query_dict["type"], "range")
        self.assertEqual(query_dict["field"], "salary")
        self.assertEqual(query_dict["range"]["gte"], 50000)
        self.assertEqual(query_dict["range"]["lte"], 100000)
    
    def test_range_query_validation(self):
        """Test range query validation."""
        valid_query = RangeQuery(field="salary", gte=50000)
        self.assertTrue(valid_query.validate())
        
        invalid_query = RangeQuery(field="salary")
        self.assertFalse(invalid_query.validate())


class TestBoolQuery(unittest.TestCase):
    """Test cases for BoolQuery."""
    
    def test_basic_bool_query(self):
        """Test basic bool query creation."""
        query = BoolQuery()
        self.assertTrue(query.validate())  # Empty bool query is valid
    
    def test_bool_query_with_must(self):
        """Test bool query with must clauses."""
        must_query = MatchQuery(field="title", query="software")
        query = BoolQuery(must=[must_query])
        self.assertEqual(len(query.must), 1)
        self.assertTrue(query.validate())
    
    def test_bool_query_add_must(self):
        """Test adding must clause."""
        query = BoolQuery()
        must_query = MatchQuery(field="title", query="software")
        query.add_must(must_query)
        self.assertEqual(len(query.must), 1)
    
    def test_bool_query_to_dict(self):
        """Test bool query serialization."""
        must_query = MatchQuery(field="title", query="software")
        query = BoolQuery(must=[must_query])
        query_dict = query.to_dict()
        self.assertEqual(query_dict["type"], "bool")
        self.assertIn("must", query_dict)
        self.assertEqual(len(query_dict["must"]), 1)
    
    def test_bool_query_validation(self):
        """Test bool query validation."""
        valid_query = BoolQuery(must=[MatchQuery(field="title", query="test")])
        self.assertTrue(valid_query.validate())
        
        # Invalid sub-query
        invalid_query = BoolQuery(must=[MatchQuery(field="", query="test")])
        self.assertFalse(invalid_query.validate())


class TestDSLQueryBuilder(unittest.TestCase):
    """Test cases for DSLQueryBuilder."""
    
    def test_builder_match(self):
        """Test builder match query."""
        builder = DSLQueryBuilder()
        query = builder.match(field="title", query="software engineer").build()
        self.assertIsInstance(query, MatchQuery)
        self.assertEqual(query.field, "title")
    
    def test_builder_multi_match(self):
        """Test builder multi-match query."""
        builder = DSLQueryBuilder()
        query = builder.multi_match(
            query="software engineer",
            fields=["title", "description"]
        ).build()
        self.assertIsInstance(query, MultiMatchQuery)
    
    def test_builder_bool(self):
        """Test builder bool query."""
        builder = DSLQueryBuilder()
        builder.bool()
        builder.must(MatchQuery(field="title", query="software"))
        query = builder.build()
        self.assertIsInstance(query, BoolQuery)
    
    def test_builder_chaining(self):
        """Test builder method chaining."""
        builder = DSLQueryBuilder()
        query = builder.match(field="title", query="software").build()
        self.assertIsInstance(query, MatchQuery)
    
    def test_builder_reset(self):
        """Test builder reset."""
        builder = DSLQueryBuilder()
        builder.match(field="title", query="software")
        builder.reset()
        self.assertIsNone(builder._query)
    
    def test_builder_validation(self):
        """Test builder validation."""
        builder = DSLQueryBuilder()
        with self.assertRaises(ValueError):
            builder.build()  # No query built


class TestQueryComposition(unittest.TestCase):
    """Test cases for query composition."""
    
    def test_and_composition(self):
        """Test AND composition."""
        query1 = MatchQuery(field="title", query="software")
        query2 = MatchQuery(field="description", query="engineer")
        bool_query = query1.and_(query2)
        self.assertIsInstance(bool_query, BoolQuery)
        self.assertEqual(len(bool_query.must), 2)
    
    def test_or_composition(self):
        """Test OR composition."""
        query1 = MatchQuery(field="title", query="software")
        query2 = MatchQuery(field="description", query="engineer")
        bool_query = query1.or_(query2)
        self.assertIsInstance(bool_query, BoolQuery)
        self.assertEqual(len(bool_query.should), 2)
    
    def test_not_composition(self):
        """Test NOT composition."""
        query = MatchQuery(field="title", query="software")
        bool_query = query.not_()
        self.assertIsInstance(bool_query, BoolQuery)
        self.assertEqual(len(bool_query.must_not), 1)


class TestFunctionScoreQuery(unittest.TestCase):
    """Test cases for FunctionScoreQuery."""
    
    def test_basic_function_score(self):
        """Test basic function score query."""
        base_query = MatchQuery(field="title", query="software")
        query = FunctionScoreQuery(query=base_query)
        self.assertEqual(query.query, base_query)
        self.assertTrue(query.validate())
    
    def test_function_score_with_weight(self):
        """Test function score with weight function."""
        base_query = MatchQuery(field="title", query="software")
        query = FunctionScoreQuery(query=base_query)
        weight_func = WeightFunction(weight=2.0)
        query.add_function(weight_func)
        self.assertEqual(len(query.functions), 1)
    
    def test_function_score_with_field_value_factor(self):
        """Test function score with field value factor."""
        base_query = MatchQuery(field="title", query="software")
        query = FunctionScoreQuery(query=base_query)
        fv_func = FieldValueFactorFunction(field="popularity")
        query.add_function(fv_func)
        self.assertEqual(len(query.functions), 1)


if __name__ == "__main__":
    unittest.main()
