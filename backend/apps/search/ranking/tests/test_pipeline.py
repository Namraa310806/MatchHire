"""
Tests for the ranking pipeline.
"""

import unittest
from datetime import datetime
from apps.search.ranking.pipeline import (
    RankingPipeline,
    PipelineConfig,
    PipelineStage,
    ScoreNormalizer,
    NormalizationMethod,
    PipelineDiagnostics,
)
from apps.search.ranking.signals import (
    LexicalSignal,
    MetadataSignal,
    FreshnessSignal,
)


class TestScoreNormalizer(unittest.TestCase):
    """Test cases for ScoreNormalizer."""
    
    def test_min_max_normalization(self):
        """Test min-max normalization."""
        scores = [1.0, 2.0, 3.0, 4.0, 5.0]
        normalized = ScoreNormalizer.min_max(scores)
        
        self.assertEqual(len(normalized), len(scores))
        self.assertAlmostEqual(normalized[0], 0.0)
        self.assertAlmostEqual(normalized[-1], 1.0)
    
    def test_min_max_with_custom_bounds(self):
        """Test min-max normalization with custom bounds."""
        scores = [1.0, 2.0, 3.0]
        normalized = ScoreNormalizer.min_max(scores, min_val=0.0, max_val=10.0)
        
        self.assertAlmostEqual(normalized[0], 0.1)
        self.assertAlmostEqual(normalized[-1], 0.3)
    
    def test_z_score_normalization(self):
        """Test z-score normalization."""
        scores = [1.0, 2.0, 3.0, 4.0, 5.0]
        normalized = ScoreNormalizer.z_score(scores)
        
        self.assertEqual(len(normalized), len(scores))
        # Mean should be close to 0
        self.assertAlmostEqual(sum(normalized) / len(normalized), 0.0, places=10)
    
    def test_logistic_normalization(self):
        """Test logistic normalization."""
        scores = [0.0, 1.0, 2.0, 3.0]
        normalized = ScoreNormalizer.logistic(scores)
        
        self.assertEqual(len(normalized), len(scores))
        # All values should be in (0, 1)
        for val in normalized:
            self.assertGreater(val, 0.0)
            self.assertLess(val, 1.0)
    
    def test_softmax_normalization(self):
        """Test softmax normalization."""
        scores = [1.0, 2.0, 3.0]
        normalized = ScoreNormalizer.softmax(scores)
        
        self.assertEqual(len(normalized), len(scores))
        # Should sum to 1
        self.assertAlmostEqual(sum(normalized), 1.0, places=10)
    
    def test_binary_normalization(self):
        """Test binary normalization."""
        scores = [0.2, 0.5, 0.7, 0.9]
        normalized = ScoreNormalizer.binary(scores, threshold=0.5)
        
        self.assertEqual(len(normalized), len(scores))
        self.assertEqual(normalized[0], 0.0)
        self.assertEqual(normalized[1], 1.0)
        self.assertEqual(normalized[2], 1.0)
        self.assertEqual(normalized[3], 1.0)
    
    def test_normalize_method_dispatcher(self):
        """Test normalize method dispatcher."""
        scores = [1.0, 2.0, 3.0]
        
        # Test each method
        for method in NormalizationMethod:
            normalized = ScoreNormalizer.normalize(scores, method)
            self.assertEqual(len(normalized), len(scores))


class TestPipelineStage(unittest.TestCase):
    """Test cases for PipelineStage."""
    
    def test_stage_creation(self):
        """Test creating a pipeline stage."""
        stage = PipelineStage(
            name="test_stage",
            signals=["lexical", "metadata"],
            weights={"lexical": 1.0, "metadata": 0.5},
        )
        
        self.assertEqual(stage.name, "test_stage")
        self.assertEqual(len(stage.signals), 2)
        self.assertTrue(stage.enabled)
    
    def test_stage_to_dict(self):
        """Test converting stage to dictionary."""
        stage = PipelineStage(
            name="test_stage",
            signals=["lexical"],
            weights={"lexical": 1.0},
        )
        
        stage_dict = stage.to_dict()
        self.assertEqual(stage_dict["name"], "test_stage")
        self.assertEqual(stage_dict["signals"], ["lexical"])
    
    def test_stage_should_execute(self):
        """Test stage execution condition."""
        stage = PipelineStage(
            name="test_stage",
            signals=["lexical"],
        )
        
        # Should execute by default
        self.assertTrue(stage.should_execute({}))
        
        # Should not execute if disabled
        stage.enabled = False
        self.assertFalse(stage.should_execute({}))
        
        # Should execute with condition
        stage.enabled = True
        stage.condition = lambda ctx: ctx.get("test", False)
        self.assertFalse(stage.should_execute({}))
        self.assertTrue(stage.should_execute({"test": True}))


class TestRankingPipeline(unittest.TestCase):
    """Test cases for RankingPipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = PipelineConfig(
            enable_parallel_scoring=False,  # Disable for simpler testing
            cache_enabled=False,
        )
        self.pipeline = RankingPipeline(config=self.config)
        
        # Register test signals
        self.pipeline.register_signal("lexical", LexicalSignal())
        self.pipeline.register_signal("metadata", MetadataSignal())
        self.pipeline.register_signal("freshness", FreshnessSignal())
    
    def test_pipeline_creation(self):
        """Test creating a ranking pipeline."""
        pipeline = RankingPipeline()
        self.assertIsNotNone(pipeline)
        self.assertEqual(len(pipeline._stages), 0)
    
    def test_add_stage(self):
        """Test adding a stage to the pipeline."""
        stage = PipelineStage(
            name="test_stage",
            signals=["lexical"],
            weights={"lexical": 1.0},
        )
        
        result = self.pipeline.add_stage(stage)
        self.assertEqual(result, self.pipeline)
        self.assertEqual(len(self.pipeline._stages), 1)
    
    def test_register_signal(self):
        """Test registering a signal."""
        signal = LexicalSignal()
        self.pipeline.register_signal("test_lexical", signal)
        
        retrieved = self.pipeline.get_signal("test_lexical")
        self.assertEqual(retrieved, signal)
    
    def test_execute_empty_results(self):
        """Test executing pipeline with empty results."""
        results = []
        context = {"query": "test"}
        
        ranked_results, diagnostics = self.pipeline.execute(results, context)
        
        self.assertEqual(len(ranked_results), 0)
        self.assertIsNotNone(diagnostics)
    
    def test_execute_with_results(self):
        """Test executing pipeline with results."""
        # Add a stage
        stage = PipelineStage(
            name="lexical_stage",
            signals=["lexical"],
            weights={"lexical": 1.0},
        )
        self.pipeline.add_stage(stage)
        
        # Create test results
        results = [
            {"id": "1", "title": "Software Engineer", "_score": 1.0},
            {"id": "2", "title": "Data Scientist", "_score": 0.5},
        ]
        context = {"query": "engineer"}
        
        ranked_results, diagnostics = self.pipeline.execute(results, context)
        
        self.assertEqual(len(ranked_results), 2)
        self.assertIn("_ranking_score", ranked_results[0])
        self.assertIn("_ranking_signals", ranked_results[0])
        self.assertIsNotNone(diagnostics)
    
    def test_execute_max_scoring_depth(self):
        """Test max scoring depth limit."""
        self.config.max_scoring_depth = 1
        
        results = [
            {"id": "1", "title": "Job 1"},
            {"id": "2", "title": "Job 2"},
            {"id": "3", "title": "Job 3"},
        ]
        context = {"query": "test"}
        
        ranked_results, _ = self.pipeline.execute(results, context)
        
        self.assertEqual(len(ranked_results), 1)
    
    def test_pipeline_diagnostics(self):
        """Test pipeline diagnostics."""
        stage = PipelineStage(
            name="test_stage",
            signals=["lexical"],
            weights={"lexical": 1.0},
        )
        self.pipeline.add_stage(stage)
        
        results = [{"id": "1", "title": "Test", "_score": 1.0}]
        context = {"query": "test"}
        
        _, diagnostics = self.pipeline.execute(results, context)
        
        self.assertIsInstance(diagnostics, PipelineDiagnostics)
        self.assertGreater(diagnostics.total_time_ms, 0)
    
    def test_clear_cache(self):
        """Test clearing the cache."""
        self.pipeline._cache["test_key"] = "test_value"
        self.pipeline.clear_cache()
        
        self.assertEqual(len(self.pipeline._cache), 0)


class TestPipelineConfig(unittest.TestCase):
    """Test cases for PipelineConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = PipelineConfig()
        
        self.assertTrue(config.enable_parallel_scoring)
        self.assertTrue(config.cache_enabled)
        self.assertTrue(config.enable_diagnostics)
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = PipelineConfig(
            enable_parallel_scoring=False,
            max_parallel_workers=2,
            cache_enabled=False,
        )
        
        self.assertFalse(config.enable_parallel_scoring)
        self.assertEqual(config.max_parallel_workers, 2)
        self.assertFalse(config.cache_enabled)
    
    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = PipelineConfig()
        config_dict = config.to_dict()
        
        self.assertIn("enable_parallel_scoring", config_dict)
        self.assertIn("max_parallel_workers", config_dict)
        self.assertIn("cache_enabled", config_dict)


if __name__ == "__main__":
    unittest.main()
