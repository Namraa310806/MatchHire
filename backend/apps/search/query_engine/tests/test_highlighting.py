"""
Tests for the Highlighting system.
"""

import unittest
from apps.search.query_engine.highlighting import (
    HighlightConfig,
    HighlightBuilder,
    HighlightFragment,
    FieldHighlight,
    HighlightResult,
    HighlighterType,
    FragmentOrder,
    PredefinedHighlights,
)


class TestHighlightConfig(unittest.TestCase):
    """Test cases for HighlightConfig."""
    
    def test_basic_highlight_config(self):
        """Test basic highlight configuration."""
        config = HighlightConfig(field="title")
        self.assertEqual(config.field, "title")
        self.assertEqual(config.pre_tags, ["<em>"])
        self.assertEqual(config.post_tags, ["</em>"])
        self.assertEqual(config.fragment_size, 150)
        self.assertTrue(config.validate())
    
    def test_highlight_config_with_custom_tags(self):
        """Test highlight configuration with custom tags."""
        config = HighlightConfig(
            field="title",
            pre_tags=["<strong>"],
            post_tags=["</strong>"]
        )
        self.assertEqual(config.pre_tags, ["<strong>"])
        self.assertEqual(config.post_tags, ["</strong>"])
    
    def test_highlight_config_with_fragment_size(self):
        """Test highlight configuration with custom fragment size."""
        config = HighlightConfig(field="title", fragment_size=200)
        self.assertEqual(config.fragment_size, 200)
    
    def test_highlight_config_to_dict(self):
        """Test highlight configuration serialization."""
        config = HighlightConfig(field="title", fragment_size=200)
        config_dict = config.to_dict()
        self.assertEqual(config_dict["field"], "title")
        self.assertEqual(config_dict["fragment_size"], 200)
    
    def test_highlight_config_validation(self):
        """Test highlight configuration validation."""
        valid_config = HighlightConfig(field="title")
        self.assertTrue(valid_config.validate())
        
        invalid_config = HighlightConfig(field="", fragment_size=0)
        self.assertFalse(invalid_config.validate())
    
    def test_highlight_config_with_type(self):
        """Test highlight configuration with type."""
        config = HighlightConfig(field="title", type=HighlighterType.PLAIN)
        self.assertEqual(config.type, HighlighterType.PLAIN)


class TestHighlightFragment(unittest.TestCase):
    """Test cases for HighlightFragment."""
    
    def test_basic_highlight_fragment(self):
        """Test basic highlight fragment."""
        fragment = HighlightFragment(text="<em>software</em> engineer")
        self.assertEqual(fragment.text, "<em>software</em> engineer")
        self.assertIsNone(fragment.score)
    
    def test_highlight_fragment_with_score(self):
        """Test highlight fragment with score."""
        fragment = HighlightFragment(text="<em>software</em> engineer", score=0.8)
        self.assertEqual(fragment.score, 0.8)
    
    def test_highlight_fragment_to_dict(self):
        """Test highlight fragment serialization."""
        fragment = HighlightFragment(text="<em>software</em> engineer", score=0.8)
        fragment_dict = fragment.to_dict()
        self.assertEqual(fragment_dict["text"], "<em>software</em> engineer")
        self.assertEqual(fragment_dict["score"], 0.8)


class TestFieldHighlight(unittest.TestCase):
    """Test cases for FieldHighlight."""
    
    def test_basic_field_highlight(self):
        """Test basic field highlight."""
        fragments = [
            HighlightFragment(text="<em>software</em> engineer"),
            HighlightFragment(text="Senior <em>developer</em>"),
        ]
        highlight = FieldHighlight(field="title", fragments=fragments)
        self.assertEqual(highlight.field, "title")
        self.assertEqual(len(highlight.fragments), 2)
    
    def test_field_highlight_to_dict(self):
        """Test field highlight serialization."""
        fragments = [HighlightFragment(text="<em>software</em> engineer")]
        highlight = FieldHighlight(field="title", fragments=fragments)
        highlight_dict = highlight.to_dict()
        self.assertEqual(highlight_dict["field"], "title")
        self.assertEqual(len(highlight_dict["fragments"]), 1)
    
    def test_get_best_fragment(self):
        """Test getting best fragment."""
        fragments = [
            HighlightFragment(text="<em>software</em> engineer", score=0.5),
            HighlightFragment(text="Senior <em>developer</em>", score=0.9),
        ]
        highlight = FieldHighlight(field="title", fragments=fragments)
        best = highlight.get_best_fragment()
        self.assertEqual(best.score, 0.9)
    
    def test_get_best_fragment_no_fragments(self):
        """Test getting best fragment with no fragments."""
        highlight = FieldHighlight(field="title", fragments=[])
        best = highlight.get_best_fragment()
        self.assertIsNone(best)
    
    def test_get_all_text(self):
        """Test getting all text from fragments."""
        fragments = [
            HighlightFragment(text="<em>software</em> engineer"),
            HighlightFragment(text="Senior <em>developer</em>"),
        ]
        highlight = FieldHighlight(field="title", fragments=fragments)
        all_text = highlight.get_all_text()
        self.assertIn("<em>software</em> engineer", all_text)
        self.assertIn("Senior <em>developer</em>", all_text)


class TestHighlightResult(unittest.TestCase):
    """Test cases for HighlightResult."""
    
    def test_basic_highlight_result(self):
        """Test basic highlight result."""
        field_highlight = FieldHighlight(
            field="title",
            fragments=[HighlightFragment(text="<em>software</em> engineer")]
        )
        result = HighlightResult(highlights={"title": field_highlight})
        self.assertEqual(len(result.highlights), 1)
    
    def test_highlight_result_to_dict(self):
        """Test highlight result serialization."""
        field_highlight = FieldHighlight(
            field="title",
            fragments=[HighlightFragment(text="<em>software</em> engineer")]
        )
        result = HighlightResult(highlights={"title": field_highlight})
        result_dict = result.to_dict()
        self.assertIn("title", result_dict)
    
    def test_get_field_highlight(self):
        """Test getting highlight for specific field."""
        field_highlight = FieldHighlight(
            field="title",
            fragments=[HighlightFragment(text="<em>software</em> engineer")]
        )
        result = HighlightResult(highlights={"title": field_highlight})
        title_highlight = result.get_field_highlight("title")
        self.assertIsNotNone(title_highlight)
        self.assertEqual(title_highlight.field, "title")
    
    def test_has_highlights(self):
        """Test checking if highlights exist."""
        field_highlight = FieldHighlight(
            field="title",
            fragments=[HighlightFragment(text="<em>software</em> engineer")]
        )
        result = HighlightResult(highlights={"title": field_highlight})
        self.assertTrue(result.has_highlights())
    
    def test_get_all_fields(self):
        """Test getting all fields with highlights."""
        field_highlight1 = FieldHighlight(
            field="title",
            fragments=[HighlightFragment(text="<em>software</em> engineer")]
        )
        field_highlight2 = FieldHighlight(
            field="description",
            fragments=[HighlightFragment(text="Senior <em>developer</em>")]
        )
        result = HighlightResult(highlights={"title": field_highlight1, "description": field_highlight2})
        fields = result.get_all_fields()
        self.assertEqual(len(fields), 2)
        self.assertIn("title", fields)
        self.assertIn("description", fields)


class TestHighlightBuilder(unittest.TestCase):
    """Test cases for HighlightBuilder."""
    
    def test_basic_highlight_builder(self):
        """Test basic highlight builder."""
        builder = HighlightBuilder()
        configs = builder.add_field(field="title").build()
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].field, "title")
    
    def test_highlight_builder_with_custom_tags(self):
        """Test highlight builder with custom tags."""
        builder = HighlightBuilder()
        configs = builder.add_field(
            field="title",
            pre_tags=["<strong>"],
            post_tags=["</strong>"]
        ).build()
        self.assertEqual(configs[0].pre_tags, ["<strong>"])
    
    def test_highlight_builder_chaining(self):
        """Test highlight builder chaining."""
        builder = HighlightBuilder()
        configs = (
            builder
            .add_field(field="title")
            .add_field(field="description")
            .build()
        )
        self.assertEqual(len(configs), 2)
    
    def test_highlight_builder_title(self):
        """Test title highlight preset."""
        builder = HighlightBuilder()
        configs = builder.title(field="title").build()
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].fragment_size, 50)
    
    def test_highlight_builder_description(self):
        """Test description highlight preset."""
        builder = HighlightBuilder()
        configs = builder.description(field="description").build()
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].fragment_size, 150)
    
    def test_highlight_builder_content(self):
        """Test content highlight preset."""
        builder = HighlightBuilder()
        configs = builder.content(field="content").build()
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].fragment_size, 200)
    
    def test_highlight_builder_skills(self):
        """Test skills highlight preset."""
        builder = HighlightBuilder()
        configs = builder.skills(field="skills").build()
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].fragment_size, 100)
    
    def test_highlight_builder_set_global_tags(self):
        """Test setting global tags."""
        builder = HighlightBuilder()
        builder.set_global_tags(["<strong>"], ["</strong>"])
        configs = builder.add_field(field="title").build()
        self.assertEqual(configs[0].pre_tags, ["<strong>"])
    
    def test_highlight_builder_reset(self):
        """Test highlight builder reset."""
        builder = HighlightBuilder()
        builder.add_field(field="title")
        builder.reset()
        self.assertEqual(len(builder._configs), 0)


class TestPredefinedHighlights(unittest.TestCase):
    """Test cases for PredefinedHighlights."""
    
    def test_job_search(self):
        """Test job search highlights."""
        highlights = PredefinedHighlights.job_search()
        self.assertGreater(len(highlights), 0)
        fields = [h.field for h in highlights]
        self.assertIn("title", fields)
        self.assertIn("description", fields)
    
    def test_candidate_search(self):
        """Test candidate search highlights."""
        highlights = PredefinedHighlights.candidate_search()
        self.assertGreater(len(highlights), 0)
        fields = [h.field for h in highlights]
        self.assertIn("full_name", fields)
    
    def test_resume_search(self):
        """Test resume search highlights."""
        highlights = PredefinedHighlights.resume_search()
        self.assertGreater(len(highlights), 0)
        fields = [h.field for h in highlights]
        self.assertIn("summary", fields)
    
    def test_company_search(self):
        """Test company search highlights."""
        highlights = PredefinedHighlights.company_search()
        self.assertGreater(len(highlights), 0)
        fields = [h.field for h in highlights]
        self.assertIn("company_name", fields)


if __name__ == "__main__":
    unittest.main()
