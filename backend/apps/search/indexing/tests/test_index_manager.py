"""
Tests for index manager.
"""

from unittest.mock import Mock, MagicMock

from django.test import TestCase

from apps.search.indexing.index_manager import IndexManager
from apps.search.indexing.documents import EntityType
from apps.search.exceptions import SearchError


class TestIndexManager(TestCase):
    """Test IndexManager class."""
    
    def setUp(self):
        """Set up test data."""
        self.provider = Mock()
        self.index_manager = IndexManager(self.provider)
    
    def test_create_index(self):
        """Test index creation."""
        result = self.index_manager.create_index(EntityType.CANDIDATE)
        
        self.assertTrue(result)
    
    def test_create_index_with_custom_name(self):
        """Test index creation with custom name."""
        result = self.index_manager.create_index(
            EntityType.CANDIDATE,
            index_name="custom_index",
        )
        
        self.assertTrue(result)
    
    def test_delete_index(self):
        """Test index deletion."""
        result = self.index_manager.delete_index(EntityType.CANDIDATE)
        
        self.assertTrue(result)
    
    def test_rebuild_index(self):
        """Test index rebuild."""
        result = self.index_manager.rebuild_index(EntityType.CANDIDATE)
        
        self.assertTrue(result)
    
    def test_refresh_index(self):
        """Test index refresh."""
        result = self.index_manager.refresh_index(EntityType.CANDIDATE)
        
        self.assertTrue(result)
    
    def test_optimize_index(self):
        """Test index optimization."""
        result = self.index_manager.optimize_index(EntityType.CANDIDATE)
        
        self.assertTrue(result)
    
    def test_health_check(self):
        """Test health check."""
        health = self.index_manager.health_check(EntityType.CANDIDATE)
        
        self.assertIn("status", health)
    
    def test_get_statistics(self):
        """Test getting statistics."""
        stats = self.index_manager.get_statistics(EntityType.CANDIDATE)
        
        self.assertIsInstance(stats, dict)
    
    def test_create_alias(self):
        """Test alias creation."""
        result = self.index_manager.create_alias(
            alias_name="candidate_alias",
            index_name="candidate_index",
            entity_type=EntityType.CANDIDATE,
        )
        
        self.assertTrue(result)
    
    def test_delete_alias(self):
        """Test alias deletion."""
        result = self.index_manager.delete_alias(
            alias_name="candidate_alias",
            entity_type=EntityType.CANDIDATE,
        )
        
        self.assertTrue(result)
    
    def test_get_aliases(self):
        """Test getting aliases."""
        aliases = self.index_manager.get_aliases(EntityType.CANDIDATE)
        
        self.assertIsInstance(aliases, list)
