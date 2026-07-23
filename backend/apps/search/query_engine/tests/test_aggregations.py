"""
Tests for the Aggregations framework.
"""

import unittest
from apps.search.query_engine.aggregations import (
    Aggregation,
    CountAggregation,
    TermsAggregation,
    RangeAggregation,
    HistogramAggregation,
    DateHistogramAggregation,
    StatsAggregation,
    AverageAggregation,
    MinAggregation,
    MaxAggregation,
    SumAggregation,
    PercentilesAggregation,
    CardinalityAggregation,
    AggregationBuilder,
    RangeBucket,
    PredefinedAggregations,
    HistogramInterval,
)


class TestCountAggregation(unittest.TestCase):
    """Test cases for CountAggregation."""
    
    def test_basic_count_aggregation(self):
        """Test basic count aggregation."""
        agg = CountAggregation(name="doc_count")
        self.assertEqual(agg.name, "doc_count")
        self.assertIsNone(agg.field)
        self.assertTrue(agg.validate())
    
    def test_count_aggregation_with_field(self):
        """Test count aggregation with field."""
        agg = CountAggregation(name="field_count", field="status")
        self.assertEqual(agg.field, "status")
    
    def test_count_aggregation_to_dict(self):
        """Test count aggregation serialization."""
        agg = CountAggregation(name="doc_count")
        agg_dict = agg.to_dict()
        self.assertEqual(agg_dict["name"], "doc_count")
        self.assertEqual(agg_dict["type"], "count")


class TestTermsAggregation(unittest.TestCase):
    """Test cases for TermsAggregation."""
    
    def test_basic_terms_aggregation(self):
        """Test basic terms aggregation."""
        agg = TermsAggregation(name="by_status", field="status")
        self.assertEqual(agg.name, "by_status")
        self.assertEqual(agg.field, "status")
        self.assertEqual(agg.size, 10)
        self.assertTrue(agg.validate())
    
    def test_terms_aggregation_with_size(self):
        """Test terms aggregation with custom size."""
        agg = TermsAggregation(name="by_status", field="status", size=20)
        self.assertEqual(agg.size, 20)
    
    def test_terms_aggregation_to_dict(self):
        """Test terms aggregation serialization."""
        agg = TermsAggregation(name="by_status", field="status", size=20)
        agg_dict = agg.to_dict()
        self.assertEqual(agg_dict["name"], "by_status")
        self.assertEqual(agg_dict["field"], "status")
        self.assertEqual(agg_dict["size"], 20)
    
    def test_terms_aggregation_validation(self):
        """Test terms aggregation validation."""
        valid_agg = TermsAggregation(name="by_status", field="status")
        self.assertTrue(valid_agg.validate())
        
        invalid_agg = TermsAggregation(name="by_status", field="", size=0)
        self.assertFalse(invalid_agg.validate())


class TestRangeBucket(unittest.TestCase):
    """Test cases for RangeBucket."""
    
    def test_basic_range_bucket(self):
        """Test basic range bucket."""
        bucket = RangeBucket(key="low", from_value=0, to_value=50000)
        self.assertEqual(bucket.key, "low")
        self.assertEqual(bucket.from_value, 0)
        self.assertEqual(bucket.to_value, 50000)
    
    def test_range_bucket_to_dict(self):
        """Test range bucket serialization."""
        bucket = RangeBucket(key="low", from_value=0, to_value=50000)
        bucket_dict = bucket.to_dict()
        self.assertEqual(bucket_dict["key"], "low")
        self.assertEqual(bucket_dict["from"], 0)
        self.assertEqual(bucket_dict["to"], 50000)


class TestRangeAggregation(unittest.TestCase):
    """Test cases for RangeAggregation."""
    
    def test_basic_range_aggregation(self):
        """Test basic range aggregation."""
        ranges = [
            RangeBucket(key="low", from_value=0, to_value=50000),
            RangeBucket(key="high", from_value=50000, to_value=100000),
        ]
        agg = RangeAggregation(name="salary_ranges", field="salary", ranges=ranges)
        self.assertEqual(agg.name, "salary_ranges")
        self.assertEqual(agg.field, "salary")
        self.assertEqual(len(agg.ranges), 2)
        self.assertTrue(agg.validate())
    
    def test_range_aggregation_to_dict(self):
        """Test range aggregation serialization."""
        ranges = [RangeBucket(key="low", from_value=0, to_value=50000)]
        agg = RangeAggregation(name="salary_ranges", field="salary", ranges=ranges)
        agg_dict = agg.to_dict()
        self.assertEqual(agg_dict["name"], "salary_ranges")
        self.assertEqual(agg_dict["field"], "salary")
        self.assertEqual(len(agg_dict["ranges"]), 1)


class TestHistogramAggregation(unittest.TestCase):
    """Test cases for HistogramAggregation."""
    
    def test_basic_histogram_aggregation(self):
        """Test basic histogram aggregation."""
        agg = HistogramAggregation(name="experience_hist", field="years_of_experience", interval=1.0)
        self.assertEqual(agg.name, "experience_hist")
        self.assertEqual(agg.field, "years_of_experience")
        self.assertEqual(agg.interval, 1.0)
        self.assertTrue(agg.validate())
    
    def test_histogram_aggregation_to_dict(self):
        """Test histogram aggregation serialization."""
        agg = HistogramAggregation(name="experience_hist", field="years_of_experience", interval=1.0)
        agg_dict = agg.to_dict()
        self.assertEqual(agg_dict["name"], "experience_hist")
        self.assertEqual(agg_dict["field"], "years_of_experience")
        self.assertEqual(agg_dict["interval"], 1.0)


class TestDateHistogramAggregation(unittest.TestCase):
    """Test cases for DateHistogramAggregation."""
    
    def test_basic_date_histogram_aggregation(self):
        """Test basic date histogram aggregation."""
        agg = DateHistogramAggregation(
            name="posted_over_time",
            field="posted_date",
            interval=HistogramInterval.MONTH
        )
        self.assertEqual(agg.name, "posted_over_time")
        self.assertEqual(agg.field, "posted_date")
        self.assertTrue(agg.validate())
    
    def test_date_histogram_with_string_interval(self):
        """Test date histogram with string interval."""
        agg = DateHistogramAggregation(
            name="posted_over_time",
            field="posted_date",
            interval="1M"
        )
        self.assertEqual(agg.interval, "1M")
    
    def test_date_histogram_to_dict(self):
        """Test date histogram serialization."""
        agg = DateHistogramAggregation(
            name="posted_over_time",
            field="posted_date",
            interval=HistogramInterval.MONTH
        )
        agg_dict = agg.to_dict()
        self.assertEqual(agg_dict["name"], "posted_over_time")
        self.assertEqual(agg_dict["field"], "posted_date")
        self.assertEqual(agg_dict["interval"], "1M")


class TestStatsAggregation(unittest.TestCase):
    """Test cases for StatsAggregation."""
    
    def test_basic_stats_aggregation(self):
        """Test basic stats aggregation."""
        agg = StatsAggregation(name="salary_stats", field="salary")
        self.assertEqual(agg.name, "salary_stats")
        self.assertEqual(agg.field, "salary")
        self.assertTrue(agg.validate())
    
    def test_stats_aggregation_to_dict(self):
        """Test stats aggregation serialization."""
        agg = StatsAggregation(name="salary_stats", field="salary")
        agg_dict = agg.to_dict()
        self.assertEqual(agg_dict["name"], "salary_stats")
        self.assertEqual(agg_dict["type"], "stats")
        self.assertEqual(agg_dict["field"], "salary")


class TestAverageAggregation(unittest.TestCase):
    """Test cases for AverageAggregation."""
    
    def test_basic_average_aggregation(self):
        """Test basic average aggregation."""
        agg = AverageAggregation(name="avg_salary", field="salary")
        self.assertEqual(agg.name, "avg_salary")
        self.assertEqual(agg.field, "salary")
        self.assertTrue(agg.validate())
    
    def test_average_aggregation_to_dict(self):
        """Test average aggregation serialization."""
        agg = AverageAggregation(name="avg_salary", field="salary")
        agg_dict = agg.to_dict()
        self.assertEqual(agg_dict["name"], "avg_salary")
        self.assertEqual(agg_dict["type"], "avg")


class TestPercentilesAggregation(unittest.TestCase):
    """Test cases for PercentilesAggregation."""
    
    def test_basic_percentiles_aggregation(self):
        """Test basic percentiles aggregation."""
        agg = PercentilesAggregation(name="salary_percentiles", field="salary")
        self.assertEqual(agg.name, "salary_percentiles")
        self.assertEqual(agg.field, "salary")
        self.assertEqual(len(agg.percents), 7)
        self.assertTrue(agg.validate())
    
    def test_percentiles_aggregation_custom_percents(self):
        """Test percentiles aggregation with custom percents."""
        agg = PercentilesAggregation(
            name="salary_percentiles",
            field="salary",
            percents=[10.0, 50.0, 90.0]
        )
        self.assertEqual(agg.percents, [10.0, 50.0, 90.0])
    
    def test_percentiles_aggregation_to_dict(self):
        """Test percentiles aggregation serialization."""
        agg = PercentilesAggregation(name="salary_percentiles", field="salary")
        agg_dict = agg.to_dict()
        self.assertEqual(agg_dict["name"], "salary_percentiles")
        self.assertEqual(agg_dict["type"], "percentiles")
        self.assertEqual(len(agg_dict["percents"]), 7)


class TestAggregationBuilder(unittest.TestCase):
    """Test cases for AggregationBuilder."""
    
    def test_builder_count(self):
        """Test builder count aggregation."""
        builder = AggregationBuilder()
        aggs = builder.count(name="doc_count").build()
        self.assertEqual(len(aggs), 1)
        self.assertIsInstance(aggs[0], CountAggregation)
    
    def test_builder_terms(self):
        """Test builder terms aggregation."""
        builder = AggregationBuilder()
        aggs = builder.terms(name="by_status", field="status", size=20).build()
        self.assertEqual(len(aggs), 1)
        self.assertIsInstance(aggs[0], TermsAggregation)
    
    def test_builder_range(self):
        """Test builder range aggregation."""
        builder = AggregationBuilder()
        ranges = [RangeBucket(key="low", from_value=0, to_value=50000)]
        aggs = builder.range(name="salary_ranges", field="salary", ranges=ranges).build()
        self.assertEqual(len(aggs), 1)
        self.assertIsInstance(aggs[0], RangeAggregation)
    
    def test_builder_histogram(self):
        """Test builder histogram aggregation."""
        builder = AggregationBuilder()
        aggs = builder.histogram(name="experience_hist", field="years_of_experience", interval=1.0).build()
        self.assertEqual(len(aggs), 1)
        self.assertIsInstance(aggs[0], HistogramAggregation)
    
    def test_builder_stats(self):
        """Test builder stats aggregation."""
        builder = AggregationBuilder()
        aggs = builder.stats(name="salary_stats", field="salary").build()
        self.assertEqual(len(aggs), 1)
        self.assertIsInstance(aggs[0], StatsAggregation)
    
    def test_builder_chaining(self):
        """Test builder chaining."""
        builder = AggregationBuilder()
        aggs = (
            builder
            .count(name="doc_count")
            .terms(name="by_status", field="status")
            .stats(name="salary_stats", field="salary")
            .build()
        )
        self.assertEqual(len(aggs), 3)
    
    def test_builder_reset(self):
        """Test builder reset."""
        builder = AggregationBuilder()
        builder.count(name="doc_count")
        builder.reset()
        self.assertEqual(len(builder._aggregations), 0)


class TestPredefinedAggregations(unittest.TestCase):
    """Test cases for PredefinedAggregations."""
    
    def test_job_salary_stats(self):
        """Test job salary stats."""
        aggs = PredefinedAggregations.job_salary_stats()
        self.assertGreater(len(aggs), 0)
        names = [a.name for a in aggs]
        self.assertIn("salary_stats", names)
    
    def test_job_location_distribution(self):
        """Test job location distribution."""
        aggs = PredefinedAggregations.job_location_distribution()
        self.assertGreater(len(aggs), 0)
        names = [a.name for a in aggs]
        self.assertIn("by_location", names)
    
    def test_job_posting_timeline(self):
        """Test job posting timeline."""
        aggs = PredefinedAggregations.job_posting_timeline()
        self.assertGreater(len(aggs), 0)
        names = [a.name for a in aggs]
        self.assertIn("posted_over_time", names)
    
    def test_candidate_experience_stats(self):
        """Test candidate experience stats."""
        aggs = PredefinedAggregations.candidate_experience_stats()
        self.assertGreater(len(aggs), 0)
        names = [a.name for a in aggs]
        self.assertIn("experience_stats", names)
    
    def test_skill_popularity(self):
        """Test skill popularity."""
        aggs = PredefinedAggregations.skill_popularity()
        self.assertGreater(len(aggs), 0)
        names = [a.name for a in aggs]
        self.assertIn("skill_ranking", names)
    
    def test_application_status_breakdown(self):
        """Test application status breakdown."""
        aggs = PredefinedAggregations.application_status_breakdown()
        self.assertGreater(len(aggs), 0)
        names = [a.name for a in aggs]
        self.assertIn("by_status", names)


if __name__ == "__main__":
    unittest.main()
