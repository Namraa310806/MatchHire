"""
Tests for the Sorting and Ranking system.
"""

import unittest
from apps.search.query_engine.sorting import (
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


class TestSortDirection(unittest.TestCase):
    """Test cases for SortDirection enum."""
    
    def test_sort_direction_values(self):
        """Test sort direction enum values."""
        self.assertEqual(SortDirection.ASC.value, "asc")
        self.assertEqual(SortDirection.DESC.value, "desc")


class TestScoreMode(unittest.TestCase):
    """Test cases for ScoreMode enum."""
    
    def test_score_mode_values(self):
        """Test score mode enum values."""
        self.assertEqual(ScoreMode.SUM.value, "sum")
        self.assertEqual(ScoreMode.AVG.value, "avg")
        self.assertEqual(ScoreMode.MAX.value, "max")


class TestSortCondition(unittest.TestCase):
    """Test cases for SortCondition."""
    
    def test_basic_sort_condition(self):
        """Test basic sort condition."""
        condition = SortCondition(field="salary", direction=SortDirection.DESC)
        self.assertEqual(condition.field, "salary")
        self.assertEqual(condition.direction, SortDirection.DESC)
    
    def test_sort_condition_with_mode(self):
        """Test sort condition with mode."""
        condition = SortCondition(
            field="salary",
            direction=SortDirection.DESC,
            mode="avg"
        )
        self.assertEqual(condition.mode, "avg")
    
    def test_sort_condition_with_missing(self):
        """Test sort condition with missing value."""
        condition = SortCondition(
            field="salary",
            direction=SortDirection.DESC,
            missing=0
        )
        self.assertEqual(condition.missing, 0)
    
    def test_sort_condition_to_dict(self):
        """Test sort condition serialization."""
        condition = SortCondition(field="salary", direction=SortDirection.DESC)
        condition_dict = condition.to_dict()
        self.assertEqual(condition_dict["field"], "salary")
        self.assertEqual(condition_dict["direction"], "desc")
    
    def test_sort_condition_validation(self):
        """Test sort condition validation."""
        valid_condition = SortCondition(field="salary", direction=SortDirection.DESC)
        self.assertTrue(valid_condition.validate())
        
        invalid_condition = SortCondition(field="", direction=SortDirection.DESC)
        self.assertFalse(invalid_condition.validate())


class TestFieldBoost(unittest.TestCase):
    """Test cases for FieldBoost."""
    
    def test_basic_field_boost(self):
        """Test basic field boost."""
        boost = FieldBoost(field="title", boost=2.0)
        self.assertEqual(boost.field, "title")
        self.assertEqual(boost.boost, 2.0)
    
    def test_field_boost_with_factor(self):
        """Test field boost with factor."""
        boost = FieldBoost(field="title", boost=2.0, factor=1.5)
        self.assertEqual(boost.factor, 1.5)
    
    def test_field_boost_to_dict(self):
        """Test field boost serialization."""
        boost = FieldBoost(field="title", boost=2.0)
        boost_dict = boost.to_dict()
        self.assertEqual(boost_dict["field"], "title")
        self.assertEqual(boost_dict["boost"], 2.0)


class TestFreshnessBoost(unittest.TestCase):
    """Test cases for FreshnessBoost."""
    
    def test_basic_freshness_boost(self):
        """Test basic freshness boost."""
        boost = FreshnessBoost(field="created_at", scale="30d")
        self.assertEqual(boost.field, "created_at")
        self.assertEqual(boost.scale, "30d")
        self.assertEqual(boost.decay, 0.5)
    
    def test_freshness_boost_with_offset(self):
        """Test freshness boost with offset."""
        boost = FreshnessBoost(field="created_at", scale="30d", offset="7d")
        self.assertEqual(boost.offset, "7d")
    
    def test_freshness_boost_to_dict(self):
        """Test freshness boost serialization."""
        boost = FreshnessBoost(field="created_at", scale="30d")
        boost_dict = boost.to_dict()
        self.assertEqual(boost_dict["field"], "created_at")
        self.assertEqual(boost_dict["scale"], "30d")


class TestPopularityBoost(unittest.TestCase):
    """Test cases for PopularityBoost."""
    
    def test_basic_popularity_boost(self):
        """Test basic popularity boost."""
        boost = PopularityBoost(field="view_count")
        self.assertEqual(boost.field, "view_count")
        self.assertEqual(boost.factor, 1.0)
    
    def test_popularity_boost_with_factor(self):
        """Test popularity boost with custom factor."""
        boost = PopularityBoost(field="view_count", factor=2.0)
        self.assertEqual(boost.factor, 2.0)
    
    def test_popularity_boost_to_dict(self):
        """Test popularity boost serialization."""
        boost = PopularityBoost(field="view_count")
        boost_dict = boost.to_dict()
        self.assertEqual(boost_dict["field"], "view_count")


class TestBusinessRuleBoost(unittest.TestCase):
    """Test cases for BusinessRuleBoost."""
    
    def test_basic_business_rule_boost(self):
        """Test basic business rule boost."""
        boost = BusinessRuleBoost(
            name="premium_company",
            condition="company.is_premium == true",
            boost=1.5
        )
        self.assertEqual(boost.name, "premium_company")
        self.assertEqual(boost.boost, 1.5)
    
    def test_business_rule_boost_with_filter(self):
        """Test business rule boost with filter query."""
        boost = BusinessRuleBoost(
            name="premium_company",
            condition="company.is_premium == true",
            boost=1.5,
            filter_query={"term": {"is_premium": True}}
        )
        self.assertIsNotNone(boost.filter_query)
    
    def test_business_rule_boost_to_dict(self):
        """Test business rule boost serialization."""
        boost = BusinessRuleBoost(
            name="premium_company",
            condition="company.is_premium == true",
            boost=1.5
        )
        boost_dict = boost.to_dict()
        self.assertEqual(boost_dict["name"], "premium_company")


class TestRankingHooks(unittest.TestCase):
    """Test cases for RankingHooks."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.hooks = RankingHooks()
    
    def test_add_pre_rank_hook(self):
        """Test adding pre-rank hook."""
        def hook(context):
            pass
        
        self.hooks.add_pre_rank_hook(hook)
        self.assertEqual(len(self.hooks._pre_rank_hooks), 1)
    
    def test_add_post_rank_hook(self):
        """Test adding post-rank hook."""
        def hook(results, context):
            pass
        
        self.hooks.add_post_rank_hook(hook)
        self.assertEqual(len(self.hooks._post_rank_hooks), 1)
    
    def test_add_score_modifier(self):
        """Test adding score modifier."""
        def modifier(results, context):
            pass
        
        self.hooks.add_score_modifier(modifier)
        self.assertEqual(len(self.hooks._score_modifiers), 1)
    
    def test_apply_pre_rank_hooks(self):
        """Test applying pre-rank hooks."""
        executed = []
        
        def hook1(context):
            executed.append("hook1")
        
        def hook2(context):
            executed.append("hook2")
        
        self.hooks.add_pre_rank_hook(hook1)
        self.hooks.add_pre_rank_hook(hook2)
        
        self.hooks.apply_pre_rank_hooks({})
        self.assertEqual(len(executed), 2)
    
    def test_apply_post_rank_hooks(self):
        """Test applying post-rank hooks."""
        executed = []
        
        def hook(results, context):
            executed.append("hook")
        
        self.hooks.add_post_rank_hook(hook)
        self.hooks.apply_post_rank_hooks([], {})
        self.assertEqual(len(executed), 1)
    
    def test_apply_score_modifiers(self):
        """Test applying score modifiers."""
        executed = []
        
        def modifier(results, context):
            executed.append("modifier")
        
        self.hooks.add_score_modifier(modifier)
        self.hooks.apply_score_modifiers([], {})
        self.assertEqual(len(executed), 1)


class TestSortBuilder(unittest.TestCase):
    """Test cases for SortBuilder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.builder = SortBuilder()
    
    def test_add_sort(self):
        """Test adding sort condition."""
        self.builder.add_sort(field="salary", direction=SortDirection.DESC)
        conditions = self.builder.build_sort()
        self.assertEqual(len(conditions), 1)
        self.assertEqual(conditions[0].field, "salary")
    
    def test_add_field_boost(self):
        """Test adding field boost."""
        self.builder.add_field_boost(field="title", boost=2.0)
        boosts = self.builder.build_boosts()
        self.assertEqual(len(boosts["field_boosts"]), 1)
    
    def test_add_freshness_boost(self):
        """Test adding freshness boost."""
        self.builder.add_freshness_boost(field="created_at", scale="30d")
        boosts = self.builder.build_boosts()
        self.assertEqual(len(boosts["freshness_boosts"]), 1)
    
    def test_add_popularity_boost(self):
        """Test adding popularity boost."""
        self.builder.add_popularity_boost(field="view_count", factor=1.0)
        boosts = self.builder.build_boosts()
        self.assertEqual(len(boosts["popularity_boosts"]), 1)
    
    def test_add_business_rule_boost(self):
        """Test adding business rule boost."""
        self.builder.add_business_rule_boost(
            name="premium",
            condition="is_premium",
            boost=1.5
        )
        boosts = self.builder.build_boosts()
        self.assertEqual(len(boosts["business_rule_boosts"]), 1)
    
    def test_by_relevance(self):
        """Test by_relevance convenience method."""
        self.builder.by_relevance(direction=SortDirection.DESC)
        conditions = self.builder.build_sort()
        self.assertEqual(conditions[0].field, "_score")
    
    def test_by_date(self):
        """Test by_date convenience method."""
        self.builder.by_date(field="created_at", direction=SortDirection.DESC)
        conditions = self.builder.build_sort()
        self.assertEqual(conditions[0].field, "created_at")
    
    def test_by_field(self):
        """Test by_field convenience method."""
        self.builder.by_field(field="salary", direction=SortDirection.DESC)
        conditions = self.builder.build_sort()
        self.assertEqual(conditions[0].field, "salary")
    
    def test_by_salary(self):
        """Test by_salary convenience method."""
        self.builder.by_salary()
        conditions = self.builder.build_sort()
        self.assertEqual(conditions[0].field, "salary")
    
    def test_by_experience(self):
        """Test by_experience convenience method."""
        self.builder.by_experience()
        conditions = self.builder.build_sort()
        self.assertEqual(conditions[0].field, "experience_level")
    
    def test_by_location(self):
        """Test by_location convenience method."""
        self.builder.by_location()
        conditions = self.builder.build_sort()
        self.assertEqual(conditions[0].field, "location")
    
    def test_by_company(self):
        """Test by_company convenience method."""
        self.builder.by_company()
        conditions = self.builder.build_sort()
        self.assertEqual(conditions[0].field, "company_name")
    
    def test_boost_title(self):
        """Test boost_title convenience method."""
        self.builder.boost_title(boost=2.0)
        boosts = self.builder.build_boosts()
        self.assertEqual(boosts["field_boosts"][0]["field"], "title")
    
    def test_boost_description(self):
        """Test boost_description convenience method."""
        self.builder.boost_description(boost=1.5)
        boosts = self.builder.build_boosts()
        self.assertEqual(boosts["field_boosts"][0]["field"], "description")
    
    def test_boost_skills(self):
        """Test boost_skills convenience method."""
        self.builder.boost_skills(boost=2.0)
        boosts = self.builder.build_boosts()
        self.assertEqual(boosts["field_boosts"][0]["field"], "skills")
    
    def test_boost_freshness(self):
        """Test boost_freshness convenience method."""
        self.builder.boost_freshness(field="created_at", scale="30d")
        boosts = self.builder.build_boosts()
        self.assertEqual(boosts["freshness_boosts"][0]["field"], "created_at")
    
    def test_boost_popularity(self):
        """Test boost_popularity convenience method."""
        self.builder.boost_popularity(field="view_count", factor=1.0)
        boosts = self.builder.build_boosts()
        self.assertEqual(boosts["popularity_boosts"][0]["field"], "view_count")
    
    def test_chaining(self):
        """Test method chaining."""
        conditions = (
            self.builder
            .by_relevance(direction=SortDirection.DESC)
            .by_date(direction=SortDirection.DESC)
            .build_sort()
        )
        self.assertEqual(len(conditions), 2)
    
    def test_reset(self):
        """Test reset."""
        self.builder.add_sort(field="salary", direction=SortDirection.DESC)
        self.builder.reset()
        self.assertEqual(len(self.builder._sort_conditions), 0)
    
    def test_create(self):
        """Test create class method."""
        builder = SortBuilder.create()
        self.assertIsInstance(builder, SortBuilder)


class TestPredefinedSorts(unittest.TestCase):
    """Test cases for PredefinedSorts."""
    
    def test_relevance_first(self):
        """Test relevance_first predefined sort."""
        builder = PredefinedSorts.relevance_first()
        conditions = builder.build_sort()
        self.assertGreater(len(conditions), 0)
    
    def test_most_recent(self):
        """Test most_recent predefined sort."""
        builder = PredefinedSorts.most_recent()
        conditions = builder.build_sort()
        self.assertEqual(len(conditions), 1)
    
    def test_highest_salary(self):
        """Test highest_salary predefined sort."""
        builder = PredefinedSorts.highest_salary()
        conditions = builder.build_sort()
        self.assertEqual(conditions[0].field, "salary")
    
    def test_most_experienced(self):
        """Test most_experienced predefined sort."""
        builder = PredefinedSorts.most_experienced()
        conditions = builder.build_sort()
        self.assertEqual(conditions[0].field, "experience_level")
    
    def test_location_alpha(self):
        """Test location_alpha predefined sort."""
        builder = PredefinedSorts.location_alpha()
        conditions = builder.build_sort()
        self.assertEqual(conditions[0].field, "location")
    
    def test_company_alpha(self):
        """Test company_alpha predefined sort."""
        builder = PredefinedSorts.company_alpha()
        conditions = builder.build_sort()
        self.assertEqual(conditions[0].field, "company_name")
    
    def test_boosted_relevance(self):
        """Test boosted_relevance predefined sort."""
        builder = PredefinedSorts.boosted_relevance()
        boosts = builder.build_boosts()
        self.assertGreater(len(boosts["field_boosts"]), 0)
    
    def test_fresh_and_relevant(self):
        """Test fresh_and_relevant predefined sort."""
        builder = PredefinedSorts.fresh_and_relevant()
        boosts = builder.build_boosts()
        self.assertGreater(len(boosts["freshness_boosts"]), 0)
    
    def test_popular_and_relevant(self):
        """Test popular_and_relevant predefined sort."""
        builder = PredefinedSorts.popular_and_relevant()
        boosts = builder.build_boosts()
        self.assertGreater(len(boosts["popularity_boosts"]), 0)


if __name__ == "__main__":
    unittest.main()
