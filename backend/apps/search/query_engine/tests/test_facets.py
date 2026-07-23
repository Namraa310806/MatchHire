"""
Tests for the Faceted search system.
"""

import unittest
from apps.search.query_engine.facets import (
    FacetConfig,
    FacetBuilder,
    FacetState,
    FacetResponse,
    FacetValue,
    FacetSort,
    PredefinedFacets,
)


class TestFacetConfig(unittest.TestCase):
    """Test cases for FacetConfig."""
    
    def test_basic_facet_config(self):
        """Test basic facet configuration."""
        config = FacetConfig(field="location", name="Location")
        self.assertEqual(config.field, "location")
        self.assertEqual(config.name, "Location")
        self.assertEqual(config.size, 10)
        self.assertTrue(config.validate())
    
    def test_facet_config_with_size(self):
        """Test facet configuration with custom size."""
        config = FacetConfig(field="location", name="Location", size=20)
        self.assertEqual(config.size, 20)
    
    def test_facet_config_to_dict(self):
        """Test facet configuration serialization."""
        config = FacetConfig(field="location", name="Location", size=20)
        config_dict = config.to_dict()
        self.assertEqual(config_dict["field"], "location")
        self.assertEqual(config_dict["name"], "Location")
        self.assertEqual(config_dict["size"], 20)
    
    def test_facet_config_validation(self):
        """Test facet configuration validation."""
        valid_config = FacetConfig(field="location", name="Location")
        self.assertTrue(valid_config.validate())
        
        invalid_config = FacetConfig(field="", name="Location")
        self.assertFalse(invalid_config.validate())
    
    def test_facet_config_with_nested_path(self):
        """Test facet configuration with nested path."""
        config = FacetConfig(
            field="name",
            name="Skills",
            nested_path="skills"
        )
        self.assertEqual(config.nested_path, "skills")


class TestFacetValue(unittest.TestCase):
    """Test cases for FacetValue."""
    
    def test_basic_facet_value(self):
        """Test basic facet value."""
        value = FacetValue(value="San Francisco", count=100)
        self.assertEqual(value.value, "San Francisco")
        self.assertEqual(value.count, 100)
        self.assertFalse(value.selected)
    
    def test_facet_value_to_dict(self):
        """Test facet value serialization."""
        value = FacetValue(value="San Francisco", count=100)
        value_dict = value.to_dict()
        self.assertEqual(value_dict["value"], "San Francisco")
        self.assertEqual(value_dict["count"], 100)
        self.assertEqual(value_dict["selected"], False)


class TestFacetResponse(unittest.TestCase):
    """Test cases for FacetResponse."""
    
    def test_basic_facet_response(self):
        """Test basic facet response."""
        values = [
            FacetValue(value="San Francisco", count=100),
            FacetValue(value="New York", count=80),
        ]
        response = FacetResponse(field="location", name="Location", values=values, total=180)
        self.assertEqual(response.field, "location")
        self.assertEqual(response.total, 180)
        self.assertEqual(len(response.values), 2)
    
    def test_facet_response_to_dict(self):
        """Test facet response serialization."""
        values = [FacetValue(value="San Francisco", count=100)]
        response = FacetResponse(field="location", name="Location", values=values, total=100)
        response_dict = response.to_dict()
        self.assertEqual(response_dict["field"], "location")
        self.assertEqual(response_dict["total"], 100)
        self.assertEqual(len(response_dict["values"]), 1)
    
    def test_get_selected_values(self):
        """Test getting selected facet values."""
        values = [
            FacetValue(value="San Francisco", count=100, selected=True),
            FacetValue(value="New York", count=80, selected=False),
        ]
        response = FacetResponse(field="location", name="Location", values=values, total=180)
        selected = response.get_selected_values()
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0], "San Francisco")
    
    def test_get_selected_count(self):
        """Test getting selected count."""
        values = [
            FacetValue(value="San Francisco", count=100, selected=True),
            FacetValue(value="New York", count=80, selected=True),
        ]
        response = FacetResponse(field="location", name="Location", values=values, total=180)
        self.assertEqual(response.get_selected_count(), 2)


class TestFacetState(unittest.TestCase):
    """Test cases for FacetState."""
    
    def test_basic_facet_state(self):
        """Test basic facet state."""
        state = FacetState()
        self.assertFalse(state.has_selections())
    
    def test_add_selection(self):
        """Test adding facet selection."""
        state = FacetState()
        state.add_selection("location", "San Francisco")
        self.assertTrue(state.is_selected("location", "San Francisco"))
        self.assertTrue(state.has_selections())
    
    def test_remove_selection(self):
        """Test removing facet selection."""
        state = FacetState()
        state.add_selection("location", "San Francisco")
        state.remove_selection("location", "San Francisco")
        self.assertFalse(state.is_selected("location", "San Francisco"))
    
    def test_clear_field(self):
        """Test clearing field selections."""
        state = FacetState()
        state.add_selection("location", "San Francisco")
        state.add_selection("location", "New York")
        state.clear_field("location")
        self.assertEqual(len(state.get_selections("location")), 0)
    
    def test_clear_all(self):
        """Test clearing all selections."""
        state = FacetState()
        state.add_selection("location", "San Francisco")
        state.add_selection("industry", "Technology")
        state.clear_all()
        self.assertFalse(state.has_selections())
    
    def test_get_selections(self):
        """Test getting selections for a field."""
        state = FacetState()
        state.add_selection("location", "San Francisco")
        state.add_selection("location", "New York")
        selections = state.get_selections("location")
        self.assertEqual(len(selections), 2)
    
    def test_to_dict(self):
        """Test facet state serialization."""
        state = FacetState()
        state.add_selection("location", "San Francisco")
        state_dict = state.to_dict()
        self.assertIn("location", state_dict)
        self.assertEqual(state_dict["location"], ["San Francisco"])
    
    def test_from_dict(self):
        """Test creating facet state from dictionary."""
        data = {"location": ["San Francisco", "New York"]}
        state = FacetState.from_dict(data)
        self.assertEqual(len(state.get_selections("location")), 2)


class TestFacetBuilder(unittest.TestCase):
    """Test cases for FacetBuilder."""
    
    def test_basic_facet_builder(self):
        """Test basic facet builder."""
        builder = FacetBuilder()
        configs = builder.add_facet(field="location", name="Location").build()
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].field, "location")
    
    def test_facet_builder_chaining(self):
        """Test facet builder chaining."""
        builder = FacetBuilder()
        configs = (
            builder
            .add_facet(field="location", name="Location")
            .add_facet(field="industry", name="Industry")
            .build()
        )
        self.assertEqual(len(configs), 2)
    
    def test_facet_builder_location_facet(self):
        """Test location facet preset."""
        builder = FacetBuilder()
        configs = builder.location_facet(size=20).build()
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].field, "location")
    
    def test_facet_builder_company_facet(self):
        """Test company facet preset."""
        builder = FacetBuilder()
        configs = builder.company_facet(size=15).build()
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].field, "company_name")
    
    def test_facet_builder_skills_facet(self):
        """Test skills facet preset."""
        builder = FacetBuilder()
        configs = builder.skills_facet(size=30).build()
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].nested_path, "skills")
    
    def test_facet_builder_salary_facet(self):
        """Test salary facet preset."""
        builder = FacetBuilder()
        configs = builder.salary_facet(size=10).build()
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].field, "salary_range")
    
    def test_facet_builder_reset(self):
        """Test facet builder reset."""
        builder = FacetBuilder()
        builder.add_facet(field="location", name="Location")
        builder.reset()
        self.assertEqual(len(builder._facets), 0)


class TestPredefinedFacets(unittest.TestCase):
    """Test cases for PredefinedFacets."""
    
    def test_job_search_facets(self):
        """Test job search facets."""
        facets = PredefinedFacets.job_search_facets()
        self.assertGreater(len(facets), 0)
        fields = [f.field for f in facets]
        self.assertIn("location", fields)
        self.assertIn("company_name", fields)
    
    def test_candidate_search_facets(self):
        """Test candidate search facets."""
        facets = PredefinedFacets.candidate_search_facets()
        self.assertGreater(len(facets), 0)
        fields = [f.field for f in facets]
        self.assertIn("location", fields)
    
    def test_company_search_facets(self):
        """Test company search facets."""
        facets = PredefinedFacets.company_search_facets()
        self.assertGreater(len(facets), 0)
        fields = [f.field for f in facets]
        self.assertIn("industry", fields)
    
    def test_application_search_facets(self):
        """Test application search facets."""
        facets = PredefinedFacets.application_search_facets()
        self.assertGreater(len(facets), 0)
        fields = [f.field for f in facets]
        self.assertIn("status", fields)
    
    def test_interview_search_facets(self):
        """Test interview search facets."""
        facets = PredefinedFacets.interview_search_facets()
        self.assertGreater(len(facets), 0)
        fields = [f.field for f in facets]
        self.assertIn("status", fields)


if __name__ == "__main__":
    unittest.main()
