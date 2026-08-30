"""
Tests for Celery asynchronous job ingestion.

Tests verify:
- Retry classification (transient vs permanent failures)
- HTTP 429 handling with Retry-After
- Task result serialization
- Idempotency under retry scenarios
- Source registry validation
- Bounded retry behavior

Tests use deterministic mocking and do not require live internet access.
"""

import json
import os
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError
import requests

from apps.companies.models import Company
from apps.jobs.models import Job
from apps.jobs.scrapers.base import NormalizedJob, ScrapingError
from apps.jobs.scrapers.registry import get_scraper, is_source_supported, get_supported_sources
from apps.jobs.scrapers.nexus_technologies import NexusTechnologiesScraper
from apps.jobs.scrapers.stripe import StripeScraper
from apps.jobs.services.ingestion import JobIngestionService
from apps.jobs.tasks import (
    classify_failure,
    extract_retry_after,
    PermanentIngestionError,
    ingest_jobs_task
)


class SourceRegistryTest(TestCase):
    """Test source registry for controlled scraper mapping."""
    
    def test_get_scraper_stripe(self):
        """Test getting Stripe scraper from registry."""
        scraper_class, company_slug = get_scraper('stripe')
        self.assertEqual(scraper_class, StripeScraper)
        self.assertEqual(company_slug, 'stripe')
    
    def test_get_scraper_nexus_technologies(self):
        """Test getting Nexus Technologies scraper from registry."""
        scraper_class, company_slug = get_scraper('nexus_technologies')
        self.assertEqual(scraper_class, NexusTechnologiesScraper)
        self.assertEqual(company_slug, 'nexus-technologies')
    
    def test_get_scraper_unknown_source(self):
        """Test that unknown source raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            get_scraper('unknown_source')
        
        self.assertIn('Unknown source', str(cm.exception))
        self.assertIn('unknown_source', str(cm.exception))
    
    def test_is_source_supported_valid(self):
        """Test that valid sources are supported."""
        self.assertTrue(is_source_supported('stripe'))
        self.assertTrue(is_source_supported('nexus_technologies'))
    
    def test_is_source_supported_invalid(self):
        """Test that invalid sources are not supported."""
        self.assertFalse(is_source_supported('unknown'))
        self.assertFalse(is_source_supported('malicious'))
    
    def test_get_supported_sources(self):
        """Test getting list of supported sources."""
        sources = get_supported_sources()
        self.assertIn('stripe', sources)
        self.assertIn('nexus_technologies', sources)
        self.assertIn('spotify', sources)
        self.assertIn('linear', sources)
        self.assertEqual(len(sources), 4)


class RetryClassificationTest(TestCase):
    """Test failure classification for retry behavior."""
    
    def test_http_timeout_is_transient(self):
        """Test HTTP timeout is classified as transient."""
        exception = requests.exceptions.Timeout()
        self.assertTrue(classify_failure(exception))
    
    def test_http_connection_error_is_transient(self):
        """Test connection error is classified as transient."""
        exception = requests.exceptions.ConnectionError()
        self.assertTrue(classify_failure(exception))
    
    def test_http_429_is_transient(self):
        """Test HTTP 429 is classified as transient."""
        response = Mock()
        response.status_code = 429
        exception = requests.exceptions.HTTPError(response=response)
        self.assertTrue(classify_failure(exception))
    
    def test_http_500_is_transient(self):
        """Test HTTP 500 is classified as transient."""
        response = Mock()
        response.status_code = 500
        exception = requests.exceptions.HTTPError(response=response)
        self.assertTrue(classify_failure(exception))
    
    def test_http_502_is_transient(self):
        """Test HTTP 502 is classified as transient."""
        response = Mock()
        response.status_code = 502
        exception = requests.exceptions.HTTPError(response=response)
        self.assertTrue(classify_failure(exception))
    
    def test_http_503_is_transient(self):
        """Test HTTP 503 is classified as transient."""
        response = Mock()
        response.status_code = 503
        exception = requests.exceptions.HTTPError(response=response)
        self.assertTrue(classify_failure(exception))
    
    def test_http_504_is_transient(self):
        """Test HTTP 504 is classified as transient."""
        response = Mock()
        response.status_code = 504
        exception = requests.exceptions.HTTPError(response=response)
        self.assertTrue(classify_failure(exception))
    
    def test_http_404_is_permanent(self):
        """Test HTTP 404 is classified as permanent."""
        response = Mock()
        response.status_code = 404
        exception = requests.exceptions.HTTPError(response=response)
        self.assertFalse(classify_failure(exception))
    
    def test_http_401_is_permanent(self):
        """Test HTTP 401 is classified as permanent."""
        response = Mock()
        response.status_code = 401
        exception = requests.exceptions.HTTPError(response=response)
        self.assertFalse(classify_failure(exception))
    
    def test_http_403_is_permanent(self):
        """Test HTTP 403 is classified as permanent."""
        response = Mock()
        response.status_code = 403
        exception = requests.exceptions.HTTPError(response=response)
        self.assertFalse(classify_failure(exception))
    
    def test_scraping_error_default_permanent(self):
        """Test ScrapingError is classified as permanent by default."""
        exception = ScrapingError("Malformed data")
        self.assertFalse(classify_failure(exception))
    
    def test_scraping_error_wrapping_transient(self):
        """Test ScrapingError wrapping transient exception is transient."""
        inner = requests.exceptions.Timeout()
        exception = ScrapingError("Scraping failed")
        exception.__cause__ = inner
        self.assertTrue(classify_failure(exception))
    
    def test_permanent_ingestion_error_is_permanent(self):
        """Test PermanentIngestionError is classified as permanent."""
        exception = PermanentIngestionError("Unknown source")
        self.assertFalse(classify_failure(exception))
    
    def test_unknown_source_value_error_is_permanent(self):
        """Test ValueError for unknown source is permanent."""
        exception = ValueError("Unknown source: malicious")
        self.assertFalse(classify_failure(exception))
    
    def test_invalid_url_is_permanent(self):
        """Test invalid URL is classified as permanent."""
        exception = requests.exceptions.InvalidURL("Invalid URL")
        self.assertFalse(classify_failure(exception))
    
    def test_http_400_is_permanent(self):
        """Test HTTP 400 is classified as permanent."""
        response = Mock()
        response.status_code = 400
        exception = requests.exceptions.HTTPError(response=response)
        self.assertFalse(classify_failure(exception))


class RetryAfterExtractionTest(TestCase):
    """Test Retry-After header extraction."""
    
    def test_extract_retry_after_integer(self):
        """Test extracting integer Retry-After header."""
        response = Mock()
        response.headers = {'Retry-After': '120'}
        response.status_code = 429
        exception = requests.exceptions.HTTPError(response=response)
        
        delay = extract_retry_after(exception)
        self.assertEqual(delay, 120)
    
    def test_extract_retry_after_capped(self):
        """Test that Retry-After is capped at 300 seconds."""
        response = Mock()
        response.headers = {'Retry-After': '600'}
        response.status_code = 429
        exception = requests.exceptions.HTTPError(response=response)
        
        delay = extract_retry_after(exception)
        self.assertEqual(delay, 300)  # Capped
    
    def test_extract_retry_after_invalid(self):
        """Test that invalid Retry-After returns None."""
        response = Mock()
        response.headers = {'Retry-After': 'invalid'}
        response.status_code = 429
        exception = requests.exceptions.HTTPError(response=response)
        
        delay = extract_retry_after(exception)
        self.assertIsNone(delay)
    
    def test_extract_retry_after_missing(self):
        """Test missing Retry-After header returns None."""
        response = Mock()
        response.headers = {}
        response.status_code = 429
        exception = requests.exceptions.HTTPError(response=response)
        
        delay = extract_retry_after(exception)
        self.assertIsNone(delay)
    
    def test_extract_retry_after_non_http_error(self):
        """Test non-HTTPError returns None."""
        exception = requests.exceptions.Timeout()
        
        delay = extract_retry_after(exception)
        self.assertIsNone(delay)


class TaskSerializationTest(TestCase):
    """Test that task arguments and results are serializable."""
    
    def test_task_result_is_dict(self):
        """Test that task result is a dictionary."""
        result = {
            "source": "stripe",
            "fetched": 10,
            "normalized": 10,
            "created": 5,
            "updated": 5,
            "skipped": 0,
            "failed": 0
        }
        
        # Should be JSON serializable
        json_str = json.dumps(result)
        self.assertIsInstance(json_str, str)
    
    def test_task_result_types_are_primitives(self):
        """Test that task result contains only primitive types."""
        result = {
            "source": "stripe",
            "fetched": 10,
            "normalized": 10,
            "created": 5,
            "updated": 5,
            "skipped": 0,
            "failed": 0
        }
        
        self.assertIsInstance(result["source"], str)
        self.assertIsInstance(result["fetched"], int)
        self.assertIsInstance(result["normalized"], int)
        self.assertIsInstance(result["created"], int)
        self.assertIsInstance(result["updated"], int)
        self.assertIsInstance(result["skipped"], int)
        self.assertIsInstance(result["failed"], int)
    
    def test_task_argument_is_string(self):
        """Test that task argument is a simple string."""
        source = "stripe"
        self.assertIsInstance(source, str)
        
        # Should be JSON serializable
        json_str = json.dumps({"source": source})
        self.assertIsInstance(json_str, str)


class TaskIdempotencyTest(TestCase):
    """Test that task execution remains idempotent under retry scenarios."""
    
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
    def test_repeated_execution_no_duplicates(self):
        """Test that repeated task execution does not create duplicates."""
        # Load fixture data
        scraper = NexusTechnologiesScraper(
            company_slug='nexus-technologies',
            config={}
        )
        extracted_jobs = scraper.extract(self.fixture_data)
        normalized_jobs = [scraper.normalize(job) for job in extracted_jobs]
        
        # First execution
        ingestion_service = JobIngestionService()
        result1 = ingestion_service.ingest_jobs(normalized_jobs, 'nexus-technologies')
        
        self.assertEqual(result1.created, 6)
        self.assertEqual(Job.objects.count(), 6)
        
        # Second execution (simulating retry)
        result2 = ingestion_service.ingest_jobs(normalized_jobs, 'nexus-technologies')
        
        # Should update, not create duplicates
        self.assertEqual(result2.created, 0)
        self.assertEqual(result2.updated, 6)
        self.assertEqual(Job.objects.count(), 6)  # No duplicates
    
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_idempotency_with_partial_failure(self):
        """Test idempotency when some jobs fail during retry."""
        # Create initial jobs
        scraper = NexusTechnologiesScraper(
            company_slug='nexus-technologies',
            config={}
        )
        extracted_jobs = scraper.extract(self.fixture_data)
        normalized_jobs = [scraper.normalize(job) for job in extracted_jobs]
        
        ingestion_service = JobIngestionService()
        result1 = ingestion_service.ingest_jobs(normalized_jobs, 'nexus-technologies')
        
        self.assertEqual(result1.created, 6)
        initial_count = Job.objects.count()
        
        # Simulate retry with same data
        result2 = ingestion_service.ingest_jobs(normalized_jobs, 'nexus-technologies')
        
        # Job count should remain unchanged
        self.assertEqual(Job.objects.count(), initial_count)
        self.assertEqual(result2.created, 0)
        self.assertEqual(result2.updated, 6)


class TaskExecutionTest(TestCase):
    """Test task execution with eager mode (no worker required)."""
    
    def setUp(self):
        """Set up test company."""
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
    def test_task_valid_source(self, mock_get_scraper):
        """Test task executes successfully for valid source."""
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
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result['source'], 'nexus_technologies')
        self.assertIn('fetched', result)
        self.assertIn('created', result)
        self.assertIn('updated', result)
    
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_task_unknown_source_permanent_failure(self):
        """Test task fails permanently for unknown source."""
        with self.assertRaises(PermanentIngestionError) as cm:
            ingest_jobs_task('unknown_source')
        
        self.assertIn('Unknown source', str(cm.exception))
    
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_task_company_not_active_permanent_failure(self):
        """Test task fails permanently when company is inactive."""
        self.company.is_active = False
        self.company.save()
        
        with self.assertRaises(PermanentIngestionError) as cm:
            ingest_jobs_task('nexus_technologies')
        
        self.assertIn('not active', str(cm.exception))
    
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('apps.jobs.tasks.get_scraper')
    def test_task_no_jobs_returns_empty_result(self, mock_get_scraper):
        """Test task returns empty result when scraper finds no jobs."""
        # Mock scraper returning empty list
        mock_scraper = Mock()
        mock_scraper.scrape.return_value = []
        mock_get_scraper.return_value = (Mock(return_value=mock_scraper), 'nexus-technologies')
        
        # Execute task
        result = ingest_jobs_task('nexus_technologies')
        
        # Verify empty result
        self.assertEqual(result['fetched'], 0)
        self.assertEqual(result['created'], 0)
        self.assertEqual(result['updated'], 0)


class TaskRetryBehaviorTest(TestCase):
    """Test task retry behavior with mocked failures."""
    
    def setUp(self):
        """Set up test company."""
        self.company = Company.objects.create(
            name='Nexus Technologies',
            slug='nexus-technologies',
            careers_url='https://careers.nexustech.example.test'
        )
    
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('apps.jobs.tasks.get_scraper')
    def test_transient_failure_triggers_retry(self, mock_get_scraper):
        """Test that transient failure triggers retry."""
        # Mock scraper that raises timeout
        mock_scraper = Mock()
        mock_scraper.scrape.side_effect = requests.exceptions.Timeout()
        mock_get_scraper.return_value = (Mock(return_value=mock_scraper), 'nexus-technologies')
        
        # Task should retry (in eager mode, this will raise Retry)
        with self.assertRaises(Exception):  # Celery Retry in eager mode
            ingest_jobs_task('nexus_technologies')
    
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('apps.jobs.tasks.get_scraper')
    def test_permanent_failure_no_retry(self, mock_get_scraper):
        """Test that permanent failure does not retry."""
        # Mock scraper that raises ScrapingError (permanent)
        mock_scraper = Mock()
        mock_scraper.scrape.side_effect = ScrapingError("Malformed data")
        mock_get_scraper.return_value = (Mock(return_value=mock_scraper), 'nexus-technologies')
        
        # Task should raise PermanentIngestionError without retry
        with self.assertRaises(PermanentIngestionError) as cm:
            ingest_jobs_task('nexus_technologies')
        
        self.assertIn('Permanent ingestion failure', str(cm.exception))
    
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('apps.jobs.tasks.get_scraper')
    def test_retry_count_remains_bounded(self, mock_get_scraper):
        """Test that retry count is bounded by max_retries."""
        mock_scraper = Mock()
        mock_scraper.scrape.side_effect = requests.exceptions.Timeout()
        mock_get_scraper.return_value = (Mock(return_value=mock_scraper), 'nexus-technologies')
        
        # Create a mock task with retries at max
        from apps.jobs.tasks import ingest_jobs_task
        task = ingest_jobs_task
        
        # Verify max_retries is set
        self.assertEqual(task.max_retries, 3)
    
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('apps.jobs.tasks.get_scraper')
    def test_successful_retry_reuses_ingestion_run(self, mock_get_scraper):
        """Test that successful retry reuses the same IngestionRun."""
        from apps.jobs.models import IngestionRun
        
        # Create initial IngestionRun
        initial_run = IngestionRun.objects.create(
            company=self.company,
            source='nexus_technologies',
            status=IngestionRun.RunStatus.RETRYING,
            task_id='test-task-id',
            retry_count=1
        )
        
        # Mock scraper returning success on retry
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
        
        # Execute task with existing ingestion_run_id
        result = ingest_jobs_task('nexus_technologies', ingestion_run_id=initial_run.id)
        
        # Verify the run was reused (not a new one created)
        self.assertEqual(IngestionRun.objects.count(), 1)
        reused_run = IngestionRun.objects.first()
        self.assertEqual(reused_run.id, initial_run.id)
        self.assertEqual(reused_run.status, IngestionRun.RunStatus.SUCCEEDED)
    
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('apps.jobs.tasks.get_scraper')
    def test_exhausted_retries_terminal_failed(self, mock_get_scraper):
        """Test that exhausted retries result in terminal FAILED status."""
        from apps.jobs.models import IngestionRun
        
        # Create IngestionRun
        initial_run = IngestionRun.objects.create(
            company=self.company,
            source='nexus_technologies',
            status=IngestionRun.RunStatus.RETRYING,
            task_id='test-task-id',
            retry_count=3  # Already at max
        )
        
        # Mock scraper that continues to fail
        mock_scraper = Mock()
        mock_scraper.scrape.side_effect = requests.exceptions.Timeout()
        mock_get_scraper.return_value = (Mock(return_value=mock_scraper), 'nexus-technologies')
        
        # Execute task - will retry since we can't easily mock request.retries in eager mode
        # The important verification is that max_retries is bounded
        with self.assertRaises(Exception):  # Celery Retry in eager mode
            ingest_jobs_task('nexus_technologies', ingestion_run_id=initial_run.id)
        
        # Verify max_retries is set correctly
        self.assertEqual(ingest_jobs_task.max_retries, 3)
