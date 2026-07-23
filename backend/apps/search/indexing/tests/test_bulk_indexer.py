"""
Tests for bulk indexer.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from django.test import TestCase

from apps.search.indexing.bulk_indexer import BulkIndexer, BulkIndexJob, BulkIndexStatus
from apps.search.indexing.sync_service import SyncService
from apps.search.indexing.documents import EntityType


class TestBulkIndexJob(TestCase):
    """Test BulkIndexJob class."""
    
    def test_bulk_index_job_creation(self):
        """Test creating a bulk index job."""
        job = BulkIndexJob(
            job_id="job-123",
            entity_type=EntityType.CANDIDATE,
        )
        
        self.assertEqual(job.job_id, "job-123")
        self.assertEqual(job.entity_type, EntityType.CANDIDATE)
        self.assertEqual(job.status, BulkIndexStatus.PENDING)
    
    def test_bulk_index_job_progress_percentage(self):
        """Test progress percentage calculation."""
        job = BulkIndexJob(
            job_id="job-123",
            entity_type=EntityType.CANDIDATE,
            total_count=100,
            processed_count=50,
        )
        
        self.assertEqual(job.progress_percentage, 50.0)
    
    def test_bulk_index_job_zero_total(self):
        """Test progress with zero total."""
        job = BulkIndexJob(
            job_id="job-123",
            entity_type=EntityType.CANDIDATE,
            total_count=0,
        )
        
        self.assertEqual(job.progress_percentage, 100.0)
    
    def test_bulk_index_job_duration(self):
        """Test duration calculation."""
        start = datetime.utcnow()
        end = start + timedelta(seconds=10)
        
        job = BulkIndexJob(
            job_id="job-123",
            entity_type=EntityType.CANDIDATE,
            start_time=start,
            end_time=end,
        )
        
        self.assertEqual(job.duration, 10.0)
    
    def test_bulk_index_job_to_dict(self):
        """Test converting job to dictionary."""
        job = BulkIndexJob(
            job_id="job-123",
            entity_type=EntityType.CANDIDATE,
            total_count=100,
            processed_count=50,
        )
        
        result = job.to_dict()
        
        self.assertEqual(result["job_id"], "job-123")
        self.assertEqual(result["entity_type"], "candidate")
        self.assertEqual(result["total_count"], 100)
        self.assertEqual(result["processed_count"], 50)


class TestBulkIndexer(TestCase):
    """Test BulkIndexer class."""
    
    def setUp(self):
        """Set up test data."""
        self.provider = Mock()
        self.sync_service = SyncService(self.provider)
        self.bulk_indexer = BulkIndexer(self.sync_service, chunk_size=10)
    
    def test_create_job(self):
        """Test creating a bulk index job."""
        job = self.bulk_indexer.create_job(EntityType.CANDIDATE)
        
        self.assertIsNotNone(job.job_id)
        self.assertEqual(job.entity_type, EntityType.CANDIDATE)
        self.assertEqual(job.status, BulkIndexStatus.PENDING)
    
    def test_get_job(self):
        """Test getting a job by ID."""
        job = self.bulk_indexer.create_job(EntityType.CANDIDATE)
        
        retrieved_job = self.bulk_indexer.get_job(job.job_id)
        
        self.assertEqual(retrieved_job.job_id, job.job_id)
    
    def test_get_nonexistent_job(self):
        """Test getting a nonexistent job."""
        job = self.bulk_indexer.get_job("nonexistent-id")
        
        self.assertIsNone(job)
    
    def test_list_jobs(self):
        """Test listing jobs."""
        job1 = self.bulk_indexer.create_job(EntityType.CANDIDATE)
        job2 = self.bulk_indexer.create_job(EntityType.JOB)
        
        jobs = self.bulk_indexer.list_jobs()
        
        self.assertEqual(len(jobs), 2)
    
    def test_list_jobs_with_filter(self):
        """Test listing jobs with entity type filter."""
        job1 = self.bulk_indexer.create_job(EntityType.CANDIDATE)
        job2 = self.bulk_indexer.create_job(EntityType.JOB)
        
        jobs = self.bulk_indexer.list_jobs(entity_type=EntityType.CANDIDATE)
        
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].entity_type, EntityType.CANDIDATE)
    
    def test_pause_job(self):
        """Test pausing a job."""
        job = self.bulk_indexer.create_job(EntityType.CANDIDATE)
        job.status = BulkIndexStatus.IN_PROGRESS
        
        paused_job = self.bulk_indexer.pause_job(job.job_id)
        
        self.assertEqual(paused_job.status, BulkIndexStatus.PAUSED)
    
    def test_cancel_job(self):
        """Test canceling a job."""
        job = self.bulk_indexer.create_job(EntityType.CANDIDATE)
        
        cancelled_job = self.bulk_indexer.cancel_job(job.job_id)
        
        self.assertEqual(cancelled_job.status, BulkIndexStatus.CANCELLED)
        self.assertIsNotNone(cancelled_job.end_time)
    
    def test_pause_nonexistent_job(self):
        """Test pausing a nonexistent job."""
        with self.assertRaises(ValueError):
            self.bulk_indexer.pause_job("nonexistent-id")
    
    def test_cancel_nonexistent_job(self):
        """Test canceling a nonexistent job."""
        with self.assertRaises(ValueError):
            self.bulk_indexer.cancel_job("nonexistent-id")
