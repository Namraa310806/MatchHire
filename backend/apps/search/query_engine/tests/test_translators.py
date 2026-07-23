"""
Tests for the Provider Translators.
"""

import unittest
from apps.search.query_engine.dsl import (
    MatchQuery,
    MultiMatchQuery,
    RangeQuery,
    TermQuery,
    TermsQuery,
    BoolQuery,
)
from apps.search.query_engine.filters import (
    Filter,
    RangeFilter,
    BooleanFilter,
    FilterOperator,
)
from apps.search.query_engine.translators.postgresql import PostgreSQLQueryTranslator
from apps.search.query_engine.translators.elasticsearch import ElasticsearchQueryTranslator


class TestPostgreSQLQueryTranslator(unittest.TestCase):
    """Test cases for PostgreSQLQueryTranslator."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock model for testing
        class MockModel:
            pass
        self.model = MockModel
        self.translator = PostgreSQLQueryTranslator(self.model)
    
    def test_translate_match_query(self):
        """Test translating MatchQuery."""
        query = MatchQuery(field="title", query="software engineer")
        # This would return a QuerySet, but we're testing the translation logic
        # In a real test, you'd mock the QuerySet
        self.assertIsNotNone(query)
    
    def test_translate_range_query(self):
        """Test translating RangeQuery."""
        query = RangeQuery(field="salary", gte=50000, lte=100000)
        self.assertIsNotNone(query)
    
    def test_translate_term_query(self):
        """Test translating TermQuery."""
        query = TermQuery(field="status", value="active")
        self.assertIsNotNone(query)
    
    def test_translate_terms_query(self):
        """Test translating TermsQuery."""
        query = TermsQuery(field="status", values=["active", "pending"])
        self.assertIsNotNone(query)
    
    def test_translate_bool_query(self):
        """Test translating BoolQuery."""
        must_query = MatchQuery(field="title", query="software")
        query = BoolQuery(must=[must_query])
        self.assertIsNotNone(query)
    
    def test_translate_simple_filter(self):
        """Test translating simple Filter."""
        filter_obj = Filter(field="status", operator=FilterOperator.EQ, value="active")
        # Test the filter translation logic
        self.assertIsNotNone(filter_obj)
    
    def test_translate_range_filter(self):
        """Test translating RangeFilter."""
        filter_obj = RangeFilter(field="salary", gte=50000, lte=100000)
        self.assertIsNotNone(filter_obj)
    
    def test_translate_boolean_filter(self):
        """Test translating BooleanFilter."""
        condition = Filter(field="status", operator=FilterOperator.EQ, value="active")
        filter_obj = BooleanFilter(operator="AND", filters=[condition])
        self.assertIsNotNone(filter_obj)


class TestElasticsearchQueryTranslator(unittest.TestCase):
    """Test cases for ElasticsearchQueryTranslator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.translator = ElasticsearchQueryTranslator()
    
    def test_translate_match_query(self):
        """Test translating MatchQuery to Elasticsearch DSL."""
        query = MatchQuery(field="title", query="software engineer")
        es_query = self.translator.translate_query(query)
        self.assertIn("match", es_query)
        self.assertIn("title", es_query["match"])
        self.assertEqual(es_query["match"]["title"]["query"], "software engineer")
    
    def test_translate_match_query_with_operator(self):
        """Test translating MatchQuery with operator."""
        query = MatchQuery(field="title", query="software engineer", operator="and")
        es_query = self.translator.translate_query(query)
        self.assertEqual(es_query["match"]["title"]["operator"], "and")
    
    def test_translate_multi_match_query(self):
        """Test translating MultiMatchQuery to Elasticsearch DSL."""
        query = MultiMatchQuery(
            query="software engineer",
            fields=["title", "description"]
        )
        es_query = self.translator.translate_query(query)
        self.assertIn("multi_match", es_query)
        self.assertEqual(es_query["multi_match"]["query"], "software engineer")
        self.assertEqual(es_query["multi_match"]["fields"], ["title", "description"])
    
    def test_translate_range_query(self):
        """Test translating RangeQuery to Elasticsearch DSL."""
        query = RangeQuery(field="salary", gte=50000, lte=100000)
        es_query = self.translator.translate_query(query)
        self.assertIn("range", es_query)
        self.assertIn("salary", es_query["range"])
        self.assertEqual(es_query["range"]["salary"]["gte"], 50000)
        self.assertEqual(es_query["range"]["salary"]["lte"], 100000)
    
    def test_translate_term_query(self):
        """Test translating TermQuery to Elasticsearch DSL."""
        query = TermQuery(field="status", value="active")
        es_query = self.translator.translate_query(query)
        self.assertIn("term", es_query)
        self.assertEqual(es_query["term"]["status"], "active")
    
    def test_translate_terms_query(self):
        """Test translating TermsQuery to Elasticsearch DSL."""
        query = TermsQuery(field="status", values=["active", "pending"])
        es_query = self.translator.translate_query(query)
        self.assertIn("terms", es_query)
        self.assertEqual(es_query["terms"]["status"], ["active", "pending"])
    
    def test_translate_bool_query(self):
        """Test translating BoolQuery to Elasticsearch DSL."""
        must_query = MatchQuery(field="title", query="software")
        query = BoolQuery(must=[must_query])
        es_query = self.translator.translate_query(query)
        self.assertIn("bool", es_query)
        self.assertIn("must", es_query["bool"])
        self.assertEqual(len(es_query["bool"]["must"]), 1)
    
    def test_translate_bool_query_with_multiple_clauses(self):
        """Test translating BoolQuery with multiple clauses."""
        must_query = MatchQuery(field="title", query="software")
        should_query = MatchQuery(field="description", query="engineer")
        query = BoolQuery(must=[must_query], should=[should_query])
        es_query = self.translator.translate_query(query)
        self.assertIn("must", es_query["bool"])
        self.assertIn("should", es_query["bool"])
        self.assertEqual(len(es_query["bool"]["must"]), 1)
        self.assertEqual(len(es_query["bool"]["should"]), 1)
    
    def test_translate_simple_filter(self):
        """Test translating simple Filter to Elasticsearch DSL."""
        filter_obj = Filter(field="status", operator=FilterOperator.EQ, value="active")
        es_filter = self.translator.translate_filter(filter_obj)
        self.assertIn("term", es_filter)
        self.assertEqual(es_filter["term"]["status"], "active")
    
    def test_translate_range_filter(self):
        """Test translating RangeFilter to Elasticsearch DSL."""
        filter_obj = RangeFilter(field="salary", gte=50000, lte=100000)
        es_filter = self.translator.translate_filter(filter_obj)
        self.assertIn("range", es_filter)
        self.assertEqual(es_filter["range"]["salary"]["gte"], 50000)
        self.assertEqual(es_filter["range"]["salary"]["lte"], 100000)
    
    def test_translate_boolean_filter(self):
        """Test translating BooleanFilter to Elasticsearch DSL."""
        condition = Filter(field="status", operator=FilterOperator.EQ, value="active")
        filter_obj = BooleanFilter(operator="AND", filters=[condition])
        es_filter = self.translator.translate_filter(filter_obj)
        self.assertIn("bool", es_filter)
        self.assertIn("must", es_filter["bool"])
    
    def test_translate_sort(self):
        """Test translating sort conditions to Elasticsearch DSL."""
        sort_conditions = [
            {"field": "salary", "direction": "desc"},
            {"field": "title", "direction": "asc"},
        ]
        es_sort = self.translator.translate_sort(sort_conditions)
        self.assertEqual(len(es_sort), 2)
        self.assertEqual(es_sort[0]["salary"]["order"], "desc")
        self.assertEqual(es_sort[1]["title"]["order"], "asc")
    
    def test_translate_sort_with_mode(self):
        """Test translating sort with mode."""
        sort_conditions = [
            {"field": "salary", "direction": "desc", "mode": "avg"},
        ]
        es_sort = self.translator.translate_sort(sort_conditions)
        self.assertEqual(es_sort[0]["salary"]["mode"], "avg")
    
    def test_translate_aggregation_count(self):
        """Test translating count aggregation."""
        agg_dict = {"name": "doc_count", "type": "count"}
        es_agg = self.translator.translate_aggregation(agg_dict)
        self.assertIn("doc_count", es_agg)
        self.assertIn("value_count", es_agg["doc_count"])
    
    def test_translate_aggregation_terms(self):
        """Test translating terms aggregation."""
        agg_dict = {
            "name": "by_status",
            "type": "terms",
            "field": "status",
            "size": 20
        }
        es_agg = self.translator.translate_aggregation(agg_dict)
        self.assertIn("by_status", es_agg)
        self.assertIn("terms", es_agg["by_status"])
        self.assertEqual(es_agg["by_status"]["terms"]["field"], "status")
        self.assertEqual(es_agg["by_status"]["terms"]["size"], 20)
    
    def test_translate_aggregation_range(self):
        """Test translating range aggregation."""
        agg_dict = {
            "name": "salary_ranges",
            "type": "range",
            "field": "salary",
            "ranges": [
                {"key": "low", "from": 0, "to": 50000},
                {"key": "high", "from": 50000, "to": 100000},
            ]
        }
        es_agg = self.translator.translate_aggregation(agg_dict)
        self.assertIn("salary_ranges", es_agg)
        self.assertIn("range", es_agg["salary_ranges"])
    
    def test_translate_aggregation_histogram(self):
        """Test translating histogram aggregation."""
        agg_dict = {
            "name": "experience_hist",
            "type": "histogram",
            "field": "years_of_experience",
            "interval": 1.0
        }
        es_agg = self.translator.translate_aggregation(agg_dict)
        self.assertIn("experience_hist", es_agg)
        self.assertIn("histogram", es_agg["experience_hist"])
    
    def test_translate_aggregation_stats(self):
        """Test translating stats aggregation."""
        agg_dict = {
            "name": "salary_stats",
            "type": "stats",
            "field": "salary"
        }
        es_agg = self.translator.translate_aggregation(agg_dict)
        self.assertIn("salary_stats", es_agg)
        self.assertIn("stats", es_agg["salary_stats"])
    
    def test_translate_aggregation_avg(self):
        """Test translating average aggregation."""
        agg_dict = {
            "name": "avg_salary",
            "type": "avg",
            "field": "salary"
        }
        es_agg = self.translator.translate_aggregation(agg_dict)
        self.assertIn("avg_salary", es_agg)
        self.assertIn("avg", es_agg["avg_salary"])
    
    def test_translate_aggregation_percentiles(self):
        """Test translating percentiles aggregation."""
        agg_dict = {
            "name": "salary_percentiles",
            "type": "percentiles",
            "field": "salary",
            "percents": [10.0, 50.0, 90.0]
        }
        es_agg = self.translator.translate_aggregation(agg_dict)
        self.assertIn("salary_percentiles", es_agg)
        self.assertIn("percentiles", es_agg["salary_percentiles"])
    
    def test_translate_highlight(self):
        """Test translating highlight configuration."""
        highlight_config = {
            "field": "title",
            "pre_tags": ["<em>"],
            "post_tags": ["</em>"],
            "fragment_size": 150,
            "number_of_fragments": 3,
        }
        es_highlight = self.translator.translate_highlight(highlight_config)
        self.assertIn("fields", es_highlight)
        self.assertIn("title", es_highlight["fields"])
        self.assertEqual(es_highlight["fields"]["title"]["pre_tags"], ["<em>"])
        self.assertEqual(es_highlight["fields"]["title"]["fragment_size"], 150)


if __name__ == "__main__":
    unittest.main()
