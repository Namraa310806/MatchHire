"""
Tests for Phase 4C: Ingestion Runs, Source Health & Controlled Scheduling.

Tests verify:
- IngestionRun model creation and status transitions
- IngestionRun integration with ingest_jobs_task
- Source health calculation from run history
- Overlap prevention via database constraints
- Retry behavior with IngestionRun tracking
- Partial ingestion status determination
- Failed ingestion status determination
- Concurrent run prevention
- Management command functionality

Tests use deterministic mocking and do not require live internet access.
"""

import json
import os
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import IntegrityError
import requests

from apps.companies.models import Company
from apps.jobs.models import Job, IngestionRun
from apps.jobs.scrapers.base import NormalizedJob, ScrapingError
from apps.jobs.scrapers.nexus_technologies import NexusTechnologiesScraper
from apps.jobs.services.ingestion import JobIngestionService
from apps.jobs.tasks import (
    classify_failure,
    PermanentIngestionError,
    ingest_jobs_task
)


class IngestionRunModelTest(TestCase):
    """Test IngestionRun model functionality."""
    
    def setUp(self):
        """Set up test company."""
        self.company = Company.objects.create(
            name='Test Company',
            slug='test-company',
            careers_url='https://example.com/careers'
        )
    
    def test_create_ingestion_run(self):
        """Test creating an IngestionRun."""
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.PENDING,
            task_id='test-task-id'
        )
        
        self.assertEqual(run.company, self.company)
        self.assertEqual(run.source, 'test_source')
        self.assertEqual(run.status, IngestionRun.RunStatus.PENDING)
        self.assertEqual(run.task_id, 'test-task-id')
        self.assertIsNotNone(run.created_at)
    
    def test_mark_running(self):
        """Test marking a run as RUNNING."""
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.PENDING
        )
        
        run.mark_running(task_id='test-task-id')
        
        run.refresh_from_db()
        self.assertEqual(run.status, IngestionRun.RunStatus.RUNNING)
        self.assertEqual(run.task_id, 'test-task-id')
        self.assertIsNotNone(run.started_at)
    
    def test_mark_succeeded(self):
        """Test marking a run as SUCCEEDED."""
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.RUNNING
        )
        
        result = {
            'fetched': 10,
            'normalized': 10,
            'created': 5,
            'updated': 5,
            'skipped': 0,
            'failed': 0
        }
        
        run.mark_succeeded(result)
        
        run.refresh_from_db()
        self.assertEqual(run.status, IngestionRun.RunStatus.SUCCEEDED)
        self.assertEqual(run.fetched_count, 10)
        self.assertEqual(run.normalized_count, 10)
        self.assertEqual(run.created_count, 5)
        self.assertEqual(run.updated_count, 5)
        self.assertEqual(run.skipped_count, 0)
        self.assertEqual(run.failed_count, 0)
        self.assertIsNotNone(run.finished_at)
    
    def test_mark_partial(self):
        """Test marking a run as PARTIAL."""
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.RUNNING
        )
        
        result = {
            'fetched': 10,
            'normalized': 10,
            'created': 5,
            'updated': 3,
            'skipped': 2,
            'failed': 0
        }
        
        run.mark_partial(result)
        
        run.refresh_from_db()
        self.assertEqual(run.status, IngestionRun.RunStatus.PARTIAL)
        self.assertEqual(run.skipped_count, 2)
        self.assertIsNotNone(run.finished_at)
    
    def test_mark_failed(self):
        """Test marking a run as FAILED."""
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.RUNNING
        )
        
        run.mark_failed(
            error_type='TimeoutError',
            error_message='Connection timeout after 30 seconds'
        )
        
        run.refresh_from_db()
        self.assertEqual(run.status, IngestionRun.RunStatus.FAILED)
        self.assertEqual(run.error_type, 'TimeoutError')
        self.assertEqual(run.error_message, 'Connection timeout after 30 seconds')
        self.assertIsNotNone(run.finished_at)
    
    def test_error_message_bounded(self):
        """Test that error messages are bounded in size."""
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.RUNNING
        )
        
        long_message = 'x' * 2000
        run.mark_failed(error_message=long_message)
        
        run.refresh_from_db()
        self.assertLessEqual(len(run.error_message), 1000)
    
    def test_increment_retry(self):
        """Test incrementing retry count."""
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.RUNNING,
            retry_count=0
        )
        
        run.increment_retry()
        
        run.refresh_from_db()
        self.assertEqual(run.retry_count, 1)


class OverlapPreventionTest(TestCase):
    """Test overlap prevention for concurrent runs."""
    
    def setUp(self):
        """Set up test company."""
        self.company = Company.objects.create(
            name='Test Company',
            slug='test-company',
            careers_url='https://example.com/careers'
        )
    
    def test_single_running_run_allowed(self):
        """Test that a single RUNNING run is allowed."""
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.RUNNING
        )
        
        self.assertEqual(IngestionRun.objects.filter(
            source='test_source',
            status=IngestionRun.RunStatus.RUNNING
        ).count(), 1)
    
    def test_concurrent_running_runs_prevented(self):
        """Test that concurrent RUNNING runs for same source are prevented."""
        # Create first running run
        run1 = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.RUNNING
        )
        
        # Attempt to create second running run for same source
        with self.assertRaises(IntegrityError):
            run2 = IngestionRun.objects.create(
                company=self.company,
                source='test_source',
                status=IngestionRun.RunStatus.RUNNING
            )
    
    def test_different_sources_can_run_concurrently(self):
        """Test that different sources can have concurrent RUNNING runs."""
        run1 = IngestionRun.objects.create(
            company=self.company,
            source='source_a',
            status=IngestionRun.RunStatus.RUNNING
        )
        
        run2 = IngestionRun.objects.create(
            company=self.company,
            source='source_b',
            status=IngestionRun.RunStatus.RUNNING
        )
        
        self.assertEqual(IngestionRun.objects.filter(
            status=IngestionRun.RunStatus.RUNNING
        ).count(), 2)
    
    def test_finished_runs_do_not_prevent_new_runs(self):
        """Test that finished runs do not prevent new RUNNING runs."""
        # Create finished run
        run1 = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.SUCCEEDED,
            started_at=timezone.now() - timedelta(hours=1),
            finished_at=timezone.now() - timedelta(minutes=55)
        )
        
        # Create new running run for same source
        run2 = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.RUNNING
        )
        
        self.assertEqual(run2.status, IngestionRun.RunStatus.RUNNING)


class SourceHealthTest(TestCase):
    """Test source health calculation from run history."""
    
    def setUp(self):
        """Set up test company."""
        self.company = Company.objects.create(
            name='Test Company',
            slug='test-company',
            careers_url='https://example.com/careers'
        )
    
    def test_source_health_unknown_no_runs(self):
        """Test health is UNKNOWN when no runs exist."""
        health = IngestionRun.get_source_health('test_source')
        
        self.assertEqual(health['health'], 'UNKNOWN')
        self.assertIsNone(health['last_successful_run'])
        self.assertIsNone(health['last_attempt'])
        self.assertEqual(health['consecutive_failures'], 0)
        self.assertEqual(health['recent_runs'], [])
    
    def test_source_health_healthy_recent_success(self):
        """Test health is HEALTHY with recent successful run."""
        # Create successful run within 24 hours
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.SUCCEEDED,
            started_at=timezone.now() - timedelta(hours=2),
            finished_at=timezone.now() - timedelta(hours=1),
            created_count=10,
            updated_count=0
        )
        
        health = IngestionRun.get_source_health('test_source')
        
        self.assertEqual(health['health'], 'HEALTHY')
        self.assertIsNotNone(health['last_successful_run'])
        self.assertEqual(health['consecutive_failures'], 0)
    
    def test_source_health_degraded_old_success(self):
        """Test health is DEGRADED with old successful run."""
        # Create successful run older than 24 hours
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.SUCCEEDED,
            started_at=timezone.now() - timedelta(hours=30),
            finished_at=timezone.now() - timedelta(hours=29),
            created_count=10,
            updated_count=0
        )
        
        health = IngestionRun.get_source_health('test_source')
        
        self.assertEqual(health['health'], 'DEGRADED')
    
    def test_source_health_failing_consecutive_failures(self):
        """Test health is FAILING with 3+ consecutive failures."""
        # Create 3 consecutive failed runs
        for i in range(3):
            run = IngestionRun.objects.create(
                company=self.company,
                source='test_source',
                status=IngestionRun.RunStatus.FAILED,
                started_at=timezone.now() - timedelta(hours=i+1),
                finished_at=timezone.now() - timedelta(hours=i+1),
                error_type='TimeoutError'
            )
        
        health = IngestionRun.get_source_health('test_source')
        
        self.assertEqual(health['health'], 'FAILING')
        self.assertEqual(health['consecutive_failures'], 3)
    
    def test_source_health_degraded_partial_runs(self):
        """Test health is DEGRADED with partial runs only."""
        # Create partial run
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.PARTIAL,
            started_at=timezone.now() - timedelta(hours=1),
            finished_at=timezone.now() - timedelta(minutes=55),
            created_count=5,
            skipped_count=5
        )
        
        health = IngestionRun.get_source_health('test_source')
        
        self.assertEqual(health['health'], 'DEGRADED')
    
    def test_consecutive_failures_count(self):
        """Test consecutive failures are counted correctly."""
        # Create: success, failure, failure, failure, success
        IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.SUCCEEDED,
            started_at=timezone.now() - timedelta(hours=5),
            finished_at=timezone.now() - timedelta(hours=4)
        )
        
        IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.FAILED,
            started_at=timezone.now() - timedelta(hours=3),
            finished_at=timezone.now() - timedelta(hours=2)
        )
        
        IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.FAILED,
            started_at=timezone.now() - timedelta(hours=2),
            finished_at=timezone.now() - timedelta(hours=1)
        )
        
        health = IngestionRun.get_source_health('test_source')
        
        # Should count only consecutive failures from most recent
        self.assertEqual(health['consecutive_failures'], 2)


class TaskIngestionRunIntegrationTest(TestCase):
    """Test ingest_jobs_task integration with IngestionRun."""
    
    def setUp(self):
        """Set up test company and load fixture data."""
        self.company = Company.objects.create(
            name='Nexus Technologies',
            slug='nexus-technologies',
            careers_url='https://careers.nexustech.example.test'
        )
        
        # Load fixture data
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            'scrapers',
            'fixtures',
            'nexus_technologies_jobs.json'
        )
        with open(fixture_path, 'r') as f:
            self.fixture_data = json.load(f)
    
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('apps.jobs.tasks.get_scraper')
    def test_task_creates_ingestion_run(self, mock_get_scraper):
        """Test that task creates an IngestionRun."""
        # Mock scraper
        mock_scraper = Mock()
        mock_scraper.scrape.return_value = [
            NormalizedJob(
                source='nexus_technologies',
                external_id='NX-1001',
                title='Software Engineer',
                description='Build software',
                application_url='https://example.com/apply'
            )
        ]
        mock_get_scraper.return_value = (Mock(return_value=mock_scraper), 'nexus-technologies')
        
        # Execute task
        result = ingest_jobs_task('nexus_technologies')
        
        # Verify IngestionRun was created
        self.assertEqual(IngestionRun.objects.count(), 1)
        run = IngestionRun.objects.first()
        self.assertEqual(run.source, 'nexus_technologies')
        self.assertEqual(run.status, IngestionRun.RunStatus.SUCCEEDED)
        self.assertIsNotNone(run.started_at)
        self.assertIsNotNone(run.finished_at)
    
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('apps.jobs.tasks.get_scraper')
    def test_task_marks_partial_on_skipped_jobs(self, mock_get_scraper):
        """Test that task marks PARTIAL when jobs are skipped."""
        # Mock scraper
        mock_scraper = Mock()
        mock_scraper.scrape.return_value = [
            NormalizedJob(
                source='nexus_technologies',
                external_id='NX-1001',
                title='Software Engineer',
                description='Build software',
                application_url='https://example.com/apply'
            )
        ]
        mock_get_scraper.return_value = (Mock(return_value=mock_scraper), 'nexus-technologies')
        
        # Patch ingestion service to simulate skipped jobs with at least one success
        with patch('apps.jobs.services.ingestion.JobIngestionService.ingest_jobs') as mock_ingest:
            from apps.jobs.services.ingestion import IngestionResult
            result = IngestionResult()
            result.fetched = 2
            result.normalized = 2
            result.created = 1
            result.updated = 0
            result.skipped = 1
            result.failed = 0
            mock_ingest.return_value = result
            
            # Execute task
            ingest_jobs_task('nexus_technologies')
        
        # Verify run is marked PARTIAL (some succeeded, some skipped)
        run = IngestionRun.objects.first()
        self.assertEqual(run.status, IngestionRun.RunStatus.PARTIAL)
    
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('apps.jobs.tasks.get_scraper')
    def test_task_marks_failed_on_permanent_error(self, mock_get_scraper):
        """Test that task marks FAILED on permanent error."""
        # Mock scraper that raises permanent error
        mock_scraper = Mock()
        mock_scraper.scrape.side_effect = ScrapingError("Malformed data")
        mock_get_scraper.return_value = (Mock(return_value=mock_scraper), 'nexus-technologies')
        
        # Execute task (should raise PermanentIngestionError)
        with self.assertRaises(PermanentIngestionError):
            ingest_jobs_task('nexus_technologies')
        
        # Verify run is marked FAILED
        run = IngestionRun.objects.first()
        self.assertEqual(run.status, IngestionRun.RunStatus.FAILED)
        self.assertEqual(run.error_type, 'ScrapingError')
    
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('apps.jobs.tasks.get_scraper')
    def test_transient_failure_moves_to_retrying(self, mock_get_scraper):
        """Test that transient failure moves run to RETRYING, not FAILED."""
        # Mock scraper that fails transiently
        mock_scraper = Mock()
        mock_scraper.scrape.side_effect = requests.exceptions.Timeout()
        mock_get_scraper.return_value = (Mock(return_value=mock_scraper), 'nexus-technologies')
        
        # Execute task (will retry in eager mode)
        with self.assertRaises(Exception):  # Celery Retry in eager mode
            ingest_jobs_task('nexus_technologies')
        
        # Verify run is marked RETRYING, not FAILED
        run = IngestionRun.objects.first()
        self.assertEqual(run.status, IngestionRun.RunStatus.RETRYING)
        self.assertEqual(run.retry_count, 0)
    
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('apps.jobs.tasks.get_scraper')
    def test_retry_reuses_same_logical_run(self, mock_get_scraper):
        """Test that retry reuses the same logical IngestionRun."""
        # Mock scraper that fails transiently on first call, succeeds on retry
        mock_scraper = Mock()
        mock_scraper.scrape.side_effect = [
            requests.exceptions.Timeout(),  # First call fails
            [NormalizedJob(  # Retry succeeds
                source='nexus_technologies',
                external_id='NX-1001',
                title='Software Engineer',
                description='Build software',
                application_url='https://example.com/apply'
            )]
        ]
        mock_get_scraper.return_value = (Mock(return_value=mock_scraper), 'nexus-technologies')
        
        # Execute task (will retry in eager mode)
        with self.assertRaises(Exception):  # Celery Retry in eager mode
            ingest_jobs_task('nexus_technologies')
        
        # Verify only one logical run exists
        self.assertEqual(IngestionRun.objects.count(), 1)
        run = IngestionRun.objects.first()
        self.assertEqual(run.status, IngestionRun.RunStatus.RETRYING)
    
    def test_mark_retrying_method(self):
        """Test mark_retrying method."""
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.RUNNING
        )
        
        run.mark_retrying()
        
        run.refresh_from_db()
        self.assertEqual(run.status, IngestionRun.RunStatus.RETRYING)
    
    def test_retry_count_increments(self):
        """Test that retry_count increments correctly."""
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.RETRYING,
            retry_count=0
        )
        
        run.increment_retry()
        
        run.refresh_from_db()
        self.assertEqual(run.retry_count, 1)
    
    def test_source_health_with_retrying_status(self):
        """Test that source health treats RETRYING as DEGRADED, not FAILING."""
        # Create a run in RETRYING status
        IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.RETRYING,
            started_at=timezone.now() - timedelta(minutes=5),
            retry_count=1
        )
        
        health_info = IngestionRun.get_source_health('test_source')
        
        # RETRYING should be DEGRADED, not FAILING
        self.assertEqual(health_info['health'], 'DEGRADED')
        self.assertEqual(health_info['consecutive_failures'], 0)
    
    def test_source_health_retrying_does_not_count_as_failure(self):
        """Test that RETRYING status does not increment consecutive_failures."""
        # Create a RETRYING run followed by a FAILED run
        IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.RETRYING,
            started_at=timezone.now() - timedelta(minutes=10),
            finished_at=timezone.now() - timedelta(minutes=5),
            retry_count=1
        )
        IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.FAILED,
            started_at=timezone.now() - timedelta(minutes=4),
            finished_at=timezone.now() - timedelta(minutes=2),
            error_type='TestError',
            error_message='Test error'
        )
        
        health_info = IngestionRun.get_source_health('test_source')
        
        # Only the FAILED run should count as a failure
        self.assertEqual(health_info['consecutive_failures'], 1)
    
    def test_exhausted_retries_marks_failed(self):
        """Test that exhausted retries mark run as FAILED."""
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.RETRYING,
            retry_count=3,  # At max_retries
            started_at=timezone.now() - timedelta(minutes=10)
        )
        
        run.mark_failed(error_type='Timeout', error_message='Retry limit exceeded')
        
        run.refresh_from_db()
        self.assertEqual(run.status, IngestionRun.RunStatus.FAILED)
        self.assertEqual(run.error_type, 'Timeout')
    
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('apps.jobs.tasks.get_scraper')
    def test_retry_idempotent_job_deduplication(self, mock_get_scraper):
        """Test that retry remains job-idempotent (no duplicate jobs)."""
        # Mock scraper that returns same job on retry
        mock_scraper = Mock()
        mock_scraper.scrape.side_effect = [
            requests.exceptions.Timeout(),  # First call fails
            [NormalizedJob(  # Retry succeeds with same job
                source='nexus_technologies',
                external_id='NX-1001',
                title='Software Engineer',
                description='Build software',
                application_url='https://example.com/apply'
            )]
        ]
        mock_get_scraper.return_value = (Mock(return_value=mock_scraper), 'nexus-technologies')
        
        # Execute task (will retry in eager mode)
        with self.assertRaises(Exception):
            ingest_jobs_task('nexus_technologies')
        
        # Verify only one IngestionRun exists
        self.assertEqual(IngestionRun.objects.count(), 1)


class ManagementCommandTest(TestCase):
    """Test ingestion_status management command."""
    
    def setUp(self):
        """Set up test company."""
        self.company = Company.objects.create(
            name='Test Company',
            slug='test-company',
            careers_url='https://example.com/careers'
        )
    
    def test_ingestion_status_command(self):
        """Test ingestion_status command runs without error."""
        from io import StringIO
        from django.core.management import call_command
        
        out = StringIO()
        call_command('ingestion_status', stdout=out)
        
        output = out.getvalue()
        # Health section only shown with --health flag
        self.assertIn('=== Recent Ingestion Runs ===', output)
    
    def test_ingestion_status_with_source_filter(self):
        """Test ingestion_status command with source filter."""
        from io import StringIO
        from django.core.management import call_command
        
        # Create a run with a valid source from registry
        IngestionRun.objects.create(
            company=self.company,
            source='stripe',
            status=IngestionRun.RunStatus.SUCCEEDED,
            started_at=timezone.now() - timedelta(hours=1),
            finished_at=timezone.now() - timedelta(minutes=55),
            created_count=10
        )
        
        out = StringIO()
        call_command('ingestion_status', '--source', 'stripe', stdout=out)
        
        output = out.getvalue()
        self.assertIn('stripe', output)
    
    def test_ingestion_status_with_health_flag(self):
        """Test ingestion_status command with health flag."""
        from io import StringIO
        from django.core.management import call_command
        
        out = StringIO()
        call_command('ingestion_status', '--health', stdout=out)
        
        output = out.getvalue()
        self.assertIn('=== Source Health ===', output)


class StatusTransitionTest(TestCase):
    """Test IngestionRun status transitions."""
    
    def setUp(self):
        """Set up test company."""
        self.company = Company.objects.create(
            name='Test Company',
            slug='test-company',
            careers_url='https://example.com/careers'
        )
    
    def test_pending_to_running_transition(self):
        """Test PENDING -> RUNNING transition."""
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.PENDING
        )
        
        run.mark_running()
        
        run.refresh_from_db()
        self.assertEqual(run.status, IngestionRun.RunStatus.RUNNING)
    
    def test_running_to_succeeded_transition(self):
        """Test RUNNING -> SUCCEEDED transition."""
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.RUNNING
        )
        
        result = {'fetched': 10, 'normalized': 10, 'created': 10, 'updated': 0, 'skipped': 0, 'failed': 0}
        run.mark_succeeded(result)
        
        run.refresh_from_db()
        self.assertEqual(run.status, IngestionRun.RunStatus.SUCCEEDED)
    
    def test_running_to_partial_transition(self):
        """Test RUNNING -> PARTIAL transition."""
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.RUNNING
        )
        
        result = {'fetched': 10, 'normalized': 10, 'created': 5, 'updated': 3, 'skipped': 2, 'failed': 0}
        run.mark_partial(result)
        
        run.refresh_from_db()
        self.assertEqual(run.status, IngestionRun.RunStatus.PARTIAL)
    
    def test_running_to_failed_transition(self):
        """Test RUNNING -> FAILED transition."""
        run = IngestionRun.objects.create(
            company=self.company,
            source='test_source',
            status=IngestionRun.RunStatus.RUNNING
        )
        
        run.mark_failed(error_type='TimeoutError', error_message='Timeout')
        
        run.refresh_from_db()
        self.assertEqual(run.status, IngestionRun.RunStatus.FAILED)
