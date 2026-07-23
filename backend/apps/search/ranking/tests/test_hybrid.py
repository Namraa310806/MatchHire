"""
Tests for hybrid search framework.
"""

import unittest
from apps.search.ranking.hybrid import (
    HybridSearchEngine,
    FusionStrategy,
    WeightedFusion,
    RankFusion,
    ReciprocalRankFusion,
    CondorcetFusion,
    LexicalStrategy,
    MetadataStrategy,
    SearchResult,
    StrategyResult,
)


class TestSearchResult(unittest.TestCase):
    """Test cases for SearchResult."""
    
    def test_result_creation(self):
        """Test creating a search result."""
        result = SearchResult(
            document_id="doc1",
            score=1.0,
            rank=1,
            source="lexical",
        )
        
        self.assertEqual(result.document_id, "doc1")
        self.assertEqual(result.score, 1.0)
        self.assertEqual(result.rank, 1)
        self.assertEqual(result.source, "lexical")
    
    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = SearchResult(
            document_id="doc1",
            score=1.0,
            rank=1,
            source="lexical",
        )
        
        result_dict = result.to_dict()
        self.assertEqual(result_dict["document_id"], "doc1")
        self.assertEqual(result_dict["score"], 1.0)


class TestStrategyResult(unittest.TestCase):
    """Test cases for StrategyResult."""
    
    def test_result_creation(self):
        """Test creating a strategy result."""
        results = [
            SearchResult(document_id="doc1", score=1.0, rank=1, source="lexical"),
        ]
        
        result = StrategyResult(
            strategy_name="lexical",
            results=results,
            total=1,
            took_ms=10.0,
        )
        
        self.assertEqual(result.strategy_name, "lexical")
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.total, 1)
        self.assertEqual(result.took_ms, 10.0)


class TestLexicalStrategy(unittest.TestCase):
    """Test cases for LexicalStrategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = LexicalStrategy()
    
    def test_strategy_creation(self):
        """Test creating a lexical strategy."""
        self.assertEqual(self.strategy.name, "lexical")
        self.assertEqual(self.strategy.weight, 1.0)
    
    def test_get_weight(self):
        """Test getting strategy weight."""
        self.assertEqual(self.strategy.get_weight(), 1.0)
    
    def test_set_weight(self):
        """Test setting strategy weight."""
        self.strategy.set_weight(2.0)
        self.assertEqual(self.strategy.get_weight(), 2.0)


class TestMetadataStrategy(unittest.TestCase):
    """Test cases for MetadataStrategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = MetadataStrategy()
    
    def test_strategy_creation(self):
        """Test creating a metadata strategy."""
        self.assertEqual(self.strategy.name, "metadata")
        self.assertEqual(self.strategy.weight, 0.5)


class TestWeightedFusion(unittest.TestCase):
    """Test cases for WeightedFusion."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fusion = WeightedFusion()
    
    def test_fusion_single_strategy(self):
        """Test fusion with single strategy."""
        results = [
            SearchResult(document_id="doc1", score=1.0, rank=1, source="lexical"),
            SearchResult(document_id="doc2", score=0.5, rank=2, source="lexical"),
        ]
        
        strategy_result = StrategyResult(
            strategy_name="lexical",
            results=results,
            total=2,
            took_ms=10.0,
        )
        
        fused = self.fusion.fuse([strategy_result])
        
        self.assertEqual(len(fused), 2)
        self.assertEqual(fused[0].document_id, "doc1")
        self.assertGreater(fused[0].score, fused[1].score)
    
    def test_fusion_multiple_strategies(self):
        """Test fusion with multiple strategies."""
        results1 = [
            SearchResult(document_id="doc1", score=1.0, rank=1, source="lexical"),
            SearchResult(document_id="doc2", score=0.5, rank=2, source="lexical"),
        ]
        
        results2 = [
            SearchResult(document_id="doc2", score=1.0, rank=1, source="metadata"),
            SearchResult(document_id="doc1", score=0.5, rank=2, source="metadata"),
        ]
        
        strategy_result1 = StrategyResult(
            strategy_name="lexical",
            results=results1,
            total=2,
            took_ms=10.0,
        )
        
        strategy_result2 = StrategyResult(
            strategy_name="metadata",
            results=results2,
            total=2,
            took_ms=10.0,
        )
        
        fused = self.fusion.fuse([strategy_result1, strategy_result2])
        
        self.assertEqual(len(fused), 2)
        # Both documents should appear in fused results
        doc_ids = [r.document_id for r in fused]
        self.assertIn("doc1", doc_ids)
        self.assertIn("doc2", doc_ids)


class TestRankFusion(unittest.TestCase):
    """Test cases for RankFusion."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fusion = RankFusion()
    
    def test_fusion_by_rank(self):
        """Test fusion based on rank."""
        results = [
            SearchResult(document_id="doc1", score=1.0, rank=1, source="lexical"),
            SearchResult(document_id="doc2", score=0.5, rank=2, source="lexical"),
        ]
        
        strategy_result = StrategyResult(
            strategy_name="lexical",
            results=results,
            total=2,
            took_ms=10.0,
        )
        
        fused = self.fusion.fuse([strategy_result])
        
        self.assertEqual(len(fused), 2)
        # Lower rank should get higher score
        self.assertGreater(fused[0].score, fused[1].score)


class TestReciprocalRankFusion(unittest.TestCase):
    """Test cases for ReciprocalRankFusion."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fusion = ReciprocalRankFusion(k=60)
    
    def test_fusion_rrf(self):
        """Test reciprocal rank fusion."""
        results = [
            SearchResult(document_id="doc1", score=1.0, rank=1, source="lexical"),
            SearchResult(document_id="doc2", score=0.5, rank=2, source="lexical"),
        ]
        
        strategy_result = StrategyResult(
            strategy_name="lexical",
            results=results,
            total=2,
            took_ms=10.0,
        )
        
        fused = self.fusion.fuse([strategy_result])
        
        self.assertEqual(len(fused), 2)
        # Rank 1 should get higher RRF score
        self.assertGreater(fused[0].score, fused[1].score)
    
    def test_custom_k_parameter(self):
        """Test custom k parameter."""
        fusion = ReciprocalRankFusion(k=100)
        self.assertEqual(fusion.k, 100)


class TestCondorcetFusion(unittest.TestCase):
    """Test cases for CondorcetFusion."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fusion = CondorcetFusion()
    
    def test_fusion_condorcet(self):
        """Test Condorcet fusion."""
        results = [
            SearchResult(document_id="doc1", score=1.0, rank=1, source="lexical"),
            SearchResult(document_id="doc2", score=0.5, rank=2, source="lexical"),
        ]
        
        strategy_result = StrategyResult(
            strategy_name="lexical",
            results=results,
            total=2,
            took_ms=10.0,
        )
        
        fused = self.fusion.fuse([strategy_result])
        
        self.assertEqual(len(fused), 2)
        # Document with rank 1 should win pairwise comparison
        self.assertGreater(fused[0].score, fused[1].score)


class TestHybridSearchEngine(unittest.TestCase):
    """Test cases for HybridSearchEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock provider registry
        class MockProvider:
            def get_current_provider(self):
                return "postgresql"
            
            def get_provider(self, name):
                return MockProviderInstance()
        
        class MockProviderInstance:
            def search(self, entity_type, query, filters, sort, pagination, fields):
                return {
                    "results": [
                        {"id": "doc1", "_score": 1.0},
                        {"id": "doc2", "_score": 0.5},
                    ],
                    "total": 2,
                }
        
        self.registry = MockProvider()
        self.engine = HybridSearchEngine(self.registry)
    
    def test_engine_creation(self):
        """Test creating a hybrid search engine."""
        self.assertIsNotNone(self.engine)
        self.assertGreater(len(self.engine._strategies), 0)
    
    def test_register_strategy(self):
        """Test registering a strategy."""
        strategy = LexicalStrategy(weight=1.5)
        self.engine.register_strategy(strategy)
        
        self.assertGreater(len(self.engine._strategies), 1)
    
    def test_set_fusion_algorithm(self):
        """Test setting fusion algorithm."""
        fusion = RankFusion()
        self.engine.set_fusion_algorithm(fusion)
        
        self.assertEqual(self.engine._fusion_algorithm, fusion)
    
    def test_get_strategies(self):
        """Test getting registered strategies."""
        strategies = self.engine.get_strategies()
        
        self.assertIsInstance(strategies, list)
        self.assertGreater(len(strategies), 0)


if __name__ == "__main__":
    unittest.main()
