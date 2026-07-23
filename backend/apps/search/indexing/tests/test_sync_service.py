"""
Tests for synchronization service.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from django.test import TestCase

from apps.search.indexing.sync_service import SyncService, SyncStatus, SyncProgress
from apps.search.indexing.documents import CandidateDocument, EntityType
from apps.search.exceptions import SearchError


class TestSyncService(TestCase):
    """Test SyncService class."""
    
    def setUp(self):
        """Set up test data."""
        self.provider = Mock()
        self.sync_service = SyncService(self.provider)
    
    def test_sync_single_document_success(self):
        """Test successful single document sync."""
        document = CandidateDocument(
            id="user-123",
            user_id="user-123",
            email="test@example.com",
            full_name="John Doe",
        )
        
        result = self.sync_service.sync_single_document(document)
        
        self.assertEqual(result.document_id, "user-123")
        self.assertEqual(result.status, SyncStatus.COMPLETED)
        self.assertEqual(result.error, None)
    
    def test_sync_single_document_with_retry(self):
        """Test single document sync with retry."""
        document = CandidateDocument(
            id="user-123",
            user_id="user-123",
            email="test@example.com",
            full_name="John Doe",
        )
        
        # Mock provider to fail once then succeed
        self.provider.index_document = Mock(side_effect=[Exception("Error"), None])
        
        result = self.sync_service.sync_single_document(document)
        
        # Should succeed after retry
        self.assertEqual(result.status, SyncStatus.COMPLETED)
    
    def test_sync_single_document_failure(self):
        """Test single document sync failure after max retries."""
        document = CandidateDocument(
            id="user-123",
            user_id="user-123",
            email="test@example.com",
            full_name="John Doe",
        )
        
        # Mock provider to always fail
        self.provider.index_document = Mock(side_effect=Exception("Error"))
        
        result = self.sync_service.sync_single_document(document)
        
        self.assertEqual(result.status, SyncStatus.FAILED)
        self.assertIsNotNone(result.error)
    
    def test_sync_bulk_documents(self):
        """Test bulk document sync."""
        documents = [
            CandidateDocument(
                id=f"user-{i}",
                user_id=f"user-{i}",
                email=f"test{i}@example.com",
                full_name=f"User {i}",
            )
            for i in range(5)
        ]
        
        results = self.sync_service.sync_bulk_documents(documents)
        
        self.assertEqual(len(results), 5)
        self.assertTrue(all(r.status == SyncStatus.COMPLETED for r in results))
    
    def test_delete_document(self):
        """Test document deletion."""
        result = self.sync_service.delete_document(
            document_id="user-123",
            entity_type=EntityType.CANDIDATE,
        )
        
        self.assertEqual(result.document_id, "user-123")
        self.assertEqual(result.status, SyncStatus.COMPLETED)
    
    def test_dead_letter_queue(self):
        """Test dead letter queue functionality."""
        # Add a failed sync to dead letter queue
        document = CandidateDocument(
            id="user-123",
            user_id="user-123",
            email="test@example.com",
            full_name="John Doe",
        )
        
        self.provider.index_document = Mock(side_effect=Exception("Error"))
        self.sync_service.max_retries = 0  # Disable retries for this test
        
        result = self.sync_service.sync_single_document(document)
        
        # Check dead letter queue
        dead_letter = self.sync_service.get_dead_letter_queue()
        self.assertEqual(len(dead_letter), 1)
        self.assertEqual(dead_letter[0].document_id, "user-123")
    
    def test_clear_dead_letter_queue(self):
        """Test clearing dead letter queue."""
        self.sync_service._dead_letter_queue.append(
            Mock(document_id="test", entity_type="candidate", status="failed")
        )
        
        self.sync_service.clear_dead_letter_queue()
        
        dead_letter = self.sync_service.get_dead_letter_queue()
        self.assertEqual(len(dead_letter), 0)


class TestSyncProgress(TestCase):
    """Test SyncProgress class."""
    
    def test_sync_progress_percentage(self):
        """Test progress percentage calculation."""
        progress = SyncProgress(total=100, completed=50)
        
        self.assertEqual(progress.percentage, 50.0)
    
    def test_sync_progress_zero_total(self):
        """Test progress with zero total."""
        progress = SyncProgress(total=0, completed=0)
        
        self.assertEqual(progress.percentage, 100.0)
    
    def test_sync_progress_duration(self):
        """Test duration calculation."""
        start = datetime.utcnow()
        end = start + timedelta(seconds=10)
        
        progress = SyncProgress(total=100, start_time=start, end_time=end)
        
        self.assertEqual(progress.duration, 10.0)
    
    def test_sync_progress_documents_per_second(self):
        """Test documents per second calculation."""
        start = datetime.utcnow()
        end = start + timedelta(seconds=10)
        
        progress = SyncProgress(total=100, completed=50, start_time=start, end_time=end)
        
        self.assertEqual(progress.documents_per_second, 5.0)
