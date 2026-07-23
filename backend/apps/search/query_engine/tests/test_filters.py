"""
Tests for the Filter system.
"""

import unittest
from apps.search.query_engine.filters import (
    Filter,
    RangeFilter,
    BooleanFilter,
    FilterBuilder,
    FilterOperator,
    JobFilters,
    CandidateFilters,
    CompanyFilters,
)


class TestFilter(unittest.TestCase):
    """Test cases for Filter."""
    
    def test_basic_filter(self):
        """Test basic filter creation."""
        filter_obj = Filter(field="status", operator=FilterOperator.EQ, value="active")
        self.assertEqual(filter_obj.field, "status")
        self.assertEqual(filter_obj.operator, FilterOperator.EQ)
        self.assertEqual(filter_obj.value, "active")
        self.assertTrue(filter_obj.validate())
    
    def test_filter_to_dict(self):
        """Test filter serialization."""
        filter_obj = Filter(field="status", operator=FilterOperator.EQ, value="active")
        filter_dict = filter_obj.to_dict()
        self.assertEqual(filter_dict["field"], "status")
        self.assertEqual(filter_dict["operator"], "eq")
        self.assertEqual(filter_dict["value"], "active")
    
    def test_filter_validation(self):
        """Test filter validation."""
        valid_filter = Filter(field="status", operator=FilterOperator.EQ, value="active")
        self.assertTrue(valid_filter.validate())
        
        invalid_filter = Filter(field="", operator=FilterOperator.EQ, value="active")
        self.assertFalse(invalid_filter.validate())
    
    def test_filter_with_nested_path(self):
        """Test filter with nested path."""
        filter_obj = Filter(
            field="name",
            operator=FilterOperator.EQ,
            value="python",
            nested_path="skills"
        )
        self.assertEqual(filter_obj.nested_path, "skills")


class TestRangeFilter(unittest.TestCase):
    """Test cases for RangeFilter."""
    
    def test_basic_range_filter(self):
        """Test basic range filter creation."""
        filter_obj = RangeFilter(field="salary", gte=50000, lte=100000)
        self.assertEqual(filter_obj.field, "salary")
        self.assertEqual(filter_obj.gte, 50000)
        self.assertEqual(filter_obj.lte, 100000)
        self.assertTrue(filter_obj.validate())
    
    def test_range_filter_to_dict(self):
        """Test range filter serialization."""
        filter_obj = RangeFilter(field="salary", gte=50000, lte=100000)
        filter_dict = filter_obj.to_dict()
        self.assertEqual(filter_dict["field"], "salary")
        self.assertEqual(filter_dict["operator"], "range")
        self.assertEqual(filter_dict["value"]["gte"], 50000)
        self.assertEqual(filter_dict["value"]["lte"], 100000)
    
    def test_range_filter_validation(self):
        """Test range filter validation."""
        valid_filter = RangeFilter(field="salary", gte=50000)
        self.assertTrue(valid_filter.validate())
        
        invalid_filter = RangeFilter(field="salary")
        self.assertFalse(invalid_filter.validate())


class TestBooleanFilter(unittest.TestCase):
    """Test cases for BooleanFilter."""
    
    def test_basic_boolean_filter(self):
        """Test basic boolean filter creation."""
        filter_obj = BooleanFilter(operator="AND")
        self.assertEqual(filter_obj.operator, "AND")
        self.assertFalse(filter_obj.validate())  # Empty is invalid
    
    def test_boolean_filter_with_conditions(self):
        """Test boolean filter with conditions."""
        condition1 = Filter(field="status", operator=FilterOperator.EQ, value="active")
        condition2 = Filter(field="type", operator=FilterOperator.EQ, value="full-time")
        filter_obj = BooleanFilter(operator="AND", filters=[condition1, condition2])
        self.assertEqual(len(filter_obj.filters), 2)
        self.assertTrue(filter_obj.validate())
    
    def test_boolean_filter_add_condition(self):
        """Test adding condition to boolean filter."""
        filter_obj = BooleanFilter(operator="AND")
        condition = Filter(field="status", operator=FilterOperator.EQ, value="active")
        filter_obj.add_condition(condition)
        self.assertEqual(len(filter_obj.filters), 1)
    
    def test_boolean_filter_to_dict(self):
        """Test boolean filter serialization."""
        condition = Filter(field="status", operator=FilterOperator.EQ, value="active")
        filter_obj = BooleanFilter(operator="AND", filters=[condition])
        filter_dict = filter_obj.to_dict()
        self.assertEqual(filter_dict["operator"], "AND")
        self.assertEqual(len(filter_dict["filters"]), 1)


class TestFilterBuilder(unittest.TestCase):
    """Test cases for FilterBuilder."""
    
    def test_builder_eq(self):
        """Test builder equality filter."""
        builder = FilterBuilder()
        filters = builder.eq(field="status", value="active").build()
        self.assertEqual(len(filters), 1)
        self.assertEqual(filters[0].operator, FilterOperator.EQ)
    
    def test_builder_range(self):
        """Test builder range filter."""
        builder = FilterBuilder()
        filters = builder.range(field="salary", gte=50000, lte=100000).build()
        self.assertEqual(len(filters), 1)
        self.assertIsInstance(filters[0], RangeFilter)
    
    def test_builder_in(self):
        """Test builder IN filter."""
        builder = FilterBuilder()
        filters = builder.in_(field="status", values=["active", "pending"]).build()
        self.assertEqual(len(filters), 1)
        self.assertEqual(filters[0].operator, FilterOperator.IN)
    
    def test_builder_chaining(self):
        """Test builder method chaining."""
        builder = FilterBuilder()
        filters = (
            builder
            .eq(field="status", value="active")
            .range(field="salary", gte=50000)
            .build()
        )
        self.assertEqual(len(filters), 2)
    
    def test_builder_and(self):
        """Test builder AND boolean filter."""
        builder = FilterBuilder()
        condition1 = Filter(field="status", operator=FilterOperator.EQ, value="active")
        condition2 = Filter(field="type", operator=FilterOperator.EQ, value="full-time")
        filters = builder.and_(condition1, condition2).build()
        self.assertEqual(len(filters), 1)
        self.assertIsInstance(filters[0], BooleanFilter)
    
    def test_builder_reset(self):
        """Test builder reset."""
        builder = FilterBuilder()
        builder.eq(field="status", value="active")
        builder.reset()
        self.assertEqual(len(builder._filters), 0)


class TestJobFilters(unittest.TestCase):
    """Test cases for JobFilters."""
    
    def test_by_status(self):
        """Test job status filter."""
        filter_obj = JobFilters.by_status("active")
        self.assertEqual(filter_obj.field, "status")
        self.assertEqual(filter_obj.value, "active")
    
    def test_by_employment_type(self):
        """Test job employment type filter."""
        filter_obj = JobFilters.by_employment_type("full-time")
        self.assertEqual(filter_obj.field, "employment_type")
        self.assertEqual(filter_obj.value, "full-time")
    
    def test_by_salary_range(self):
        """Test job salary range filter."""
        filter_obj = JobFilters.by_salary_range(min_salary=50000, max_salary=100000)
        self.assertEqual(filter_obj.field, "salary")
        self.assertEqual(filter_obj.gte, 50000)
        self.assertEqual(filter_obj.lte, 100000)
    
    def test_by_location(self):
        """Test job location filter."""
        filter_obj = JobFilters.by_location("San Francisco")
        self.assertEqual(filter_obj.field, "location")
        self.assertEqual(filter_obj.operator, FilterOperator.CONTAINS)
    
    def test_active(self):
        """Test active jobs filter."""
        filter_obj = JobFilters.active()
        self.assertEqual(filter_obj.value, "active")


class TestCandidateFilters(unittest.TestCase):
    """Test cases for CandidateFilters."""
    
    def test_by_status(self):
        """Test candidate status filter."""
        filter_obj = CandidateFilters.by_status("available")
        self.assertEqual(filter_obj.field, "status")
        self.assertEqual(filter_obj.value, "available")
    
    def test_by_experience_years(self):
        """Test candidate experience years filter."""
        filter_obj = CandidateFilters.by_experience_years(min_years=3, max_years=10)
        self.assertEqual(filter_obj.field, "years_of_experience")
        self.assertEqual(filter_obj.gte, 3)
        self.assertEqual(filter_obj.lte, 10)
    
    def test_by_skill(self):
        """Test candidate skill filter."""
        filter_obj = CandidateFilters.by_skill("python")
        self.assertEqual(filter_obj.field, "skills")
        self.assertEqual(filter_obj.nested_path, "skills")
    
    def test_active(self):
        """Test active candidates filter."""
        filter_obj = CandidateFilters.active()
        self.assertEqual(filter_obj.value, True)


class TestCompanyFilters(unittest.TestCase):
    """Test cases for CompanyFilters."""
    
    def test_by_industry(self):
        """Test company industry filter."""
        filter_obj = CompanyFilters.by_industry("Technology")
        self.assertEqual(filter_obj.field, "industry")
        self.assertEqual(filter_obj.operator, FilterOperator.CONTAINS)
    
    def test_by_size(self):
        """Test company size filter."""
        filter_obj = CompanyFilters.by_size("medium")
        self.assertEqual(filter_obj.field, "company_size")
        self.assertEqual(filter_obj.value, "medium")
    
    def test_by_employee_count(self):
        """Test company employee count filter."""
        filter_obj = CompanyFilters.by_employee_count(min_employees=50, max_employees=500)
        self.assertEqual(filter_obj.field, "employee_count")
        self.assertEqual(filter_obj.gte, 50)
        self.assertEqual(filter_obj.lte, 500)
    
    def test_verified(self):
        """Test verified companies filter."""
        filter_obj = CompanyFilters.verified()
        self.assertEqual(filter_obj.value, True)


if __name__ == "__main__":
    unittest.main()
