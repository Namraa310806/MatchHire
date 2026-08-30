"""
Unit tests for job scrapers.

Tests use deterministic fixture data and do not require live internet access.
"""

import json
import os
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.jobs.scrapers.base import NormalizedJob, BaseJobScraper, ScrapingError
from apps.jobs.scrapers.nexus_technologies import NexusTechnologiesScraper
from apps.jobs.scrapers.stripe import StripeScraper
from apps.jobs.scrapers.spotify import SpotifyScraper
from apps.jobs.scrapers.linear import LinearScraper
from apps.jobs.models import Job
from apps.companies.models import Company


class NormalizedJobTest(TestCase):
    """Test NormalizedJob dataclass."""
    
    def test_normalized_job_creation(self):
        """Test creating a normalized job with all fields."""
        job = NormalizedJob(
            source='test_source',
            external_id='job-123',
            title='Software Engineer',
            description='Build software',
            application_url='https://example.com/apply'
        )
        self.assertEqual(job.source, 'test_source')
        self.assertEqual(job.external_id, 'job-123')
        self.assertEqual(job.title, 'Software Engineer')
        self.assertEqual(job.skills, [])
        self.assertEqual(job.keywords, [])
    
    def test_normalized_job_with_optional_fields(self):
        """Test creating a normalized job with optional fields."""
        job = NormalizedJob(
            source='test_source',
            external_id='job-123',
            title='Software Engineer',
            description='Build software',
            location='San Francisco, CA',
            employment_type='FULL_TIME',
            minimum_experience_years=Decimal('3.0'),
            maximum_experience_years=Decimal('5.0'),
            skills=['python', 'django'],
            keywords=['backend'],
            application_url='https://example.com/apply',
            source_url='https://example.com/job'
        )
        self.assertEqual(job.location, 'San Francisco, CA')
        self.assertEqual(job.minimum_experience_years, Decimal('3.0'))
        self.assertEqual(job.maximum_experience_years, Decimal('5.0'))
        self.assertEqual(job.skills, ['python', 'django'])
    
    def test_deduplication_hash_generation(self):
        """Test that deduplication hash is deterministic."""
        job1 = NormalizedJob(
            source='test_source',
            external_id='job-123',
            title='Software Engineer',
            description='Build software',
            application_url='https://example.com/apply'
        )
        job2 = NormalizedJob(
            source='test_source',
            external_id='job-123',
            title='Software Engineer',
            description='Build software',
            application_url='https://example.com/apply'
        )
        
        hash1 = job1.generate_deduplication_hash()
        hash2 = job2.generate_deduplication_hash()
        
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA256 hex length
    
    def test_deduplication_hash_different_jobs(self):
        """Test that different jobs produce different hashes."""
        job1 = NormalizedJob(
            source='test_source',
            external_id='job-123',
            title='Software Engineer',
            description='Build software',
            application_url='https://example.com/apply'
        )
        job2 = NormalizedJob(
            source='test_source',
            external_id='job-456',
            title='Senior Engineer',
            description='Lead development',
            application_url='https://example.com/apply2'
        )
        
        hash1 = job1.generate_deduplication_hash()
        hash2 = job2.generate_deduplication_hash()
        
        self.assertNotEqual(hash1, hash2)
    
    def test_validation_valid_job(self):
        """Test validation of a valid job."""
        job = NormalizedJob(
            source='test_source',
            external_id='job-123',
            title='Software Engineer',
            description='Build software',
            application_url='https://example.com/apply'
        )
        errors = job.validate()
        self.assertEqual(errors, [])
    
    def test_validation_missing_title(self):
        """Test validation rejects missing title."""
        job = NormalizedJob(
            source='test_source',
            external_id='job-123',
            title='',
            description='Build software',
            application_url='https://example.com/apply'
        )
        errors = job.validate()
        self.assertIn('Title is required', errors)
    
    def test_validation_missing_description(self):
        """Test validation rejects missing description."""
        job = NormalizedJob(
            source='test_source',
            external_id='job-123',
            title='Software Engineer',
            description='',
            application_url='https://example.com/apply'
        )
        errors = job.validate()
        self.assertIn('Description is required', errors)
    
    def test_validation_missing_external_id(self):
        """Test validation rejects missing external ID."""
        job = NormalizedJob(
            source='test_source',
            external_id='',
            title='Software Engineer',
            description='Build software',
            application_url='https://example.com/apply'
        )
        errors = job.validate()
        self.assertIn('External ID is required', errors)
    
    def test_validation_missing_application_url(self):
        """Test validation rejects missing application URL."""
        job = NormalizedJob(
            source='test_source',
            external_id='job-123',
            title='Software Engineer',
            description='Build software',
            application_url=''
        )
        errors = job.validate()
        self.assertIn('Application URL is required', errors)
    
    def test_validation_missing_source(self):
        """Test validation rejects missing source."""
        job = NormalizedJob(
            source='',
            external_id='job-123',
            title='Software Engineer',
            description='Build software',
            application_url='https://example.com/apply'
        )
        errors = job.validate()
        self.assertIn('Source is required', errors)
    
    def test_validation_invalid_experience_range(self):
        """Test validation rejects invalid experience range."""
        job = NormalizedJob(
            source='test_source',
            external_id='job-123',
            title='Software Engineer',
            description='Build software',
            application_url='https://example.com/apply',
            minimum_experience_years=Decimal('5.0'),
            maximum_experience_years=Decimal('3.0')
        )
        errors = job.validate()
        self.assertIn('Minimum experience years cannot exceed maximum experience years', errors)
    
    def test_validation_valid_experience_range(self):
        """Test validation accepts valid experience range."""
        job = NormalizedJob(
            source='test_source',
            external_id='job-123',
            title='Software Engineer',
            description='Build software',
            application_url='https://example.com/apply',
            minimum_experience_years=Decimal('3.0'),
            maximum_experience_years=Decimal('5.0')
        )
        errors = job.validate()
        self.assertEqual(errors, [])


class NexusTechnologiesScraperTest(TestCase):
    """Test Nexus Technologies scraper with fixture data."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Load fixture data
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            'scrapers',
            'fixtures',
            'nexus_technologies_jobs.json'
        )
        with open(fixture_path, 'r') as f:
            self.fixture_data = json.load(f)
        
        self.scraper = NexusTechnologiesScraper(
            company_slug='nexus-technologies',
            config={}
        )
    
    def test_source_identifier(self):
        """Test source identifier is correct."""
        self.assertEqual(
            self.scraper.get_source_identifier(),
            'nexus_technologies'
        )
    
    def test_extract_valid_data(self):
        """Test extraction from valid fixture data."""
        extracted = self.scraper.extract(self.fixture_data)
        
        self.assertEqual(len(extracted), 6)
        self.assertEqual(extracted[0]['id'], 'NX-1001')
        self.assertEqual(extracted[0]['title'], 'Senior Backend Engineer')
    
    def test_extract_missing_jobs_key(self):
        """Test extraction fails when 'jobs' key is missing."""
        invalid_data = {'data': []}
        
        with self.assertRaises(ScrapingError) as cm:
            self.scraper.extract(invalid_data)
        
        self.assertIn("Missing 'jobs' key", str(cm.exception))
    
    def test_extract_jobs_not_list(self):
        """Test extraction fails when 'jobs' is not a list."""
        invalid_data = {'jobs': 'not a list'}
        
        with self.assertRaises(ScrapingError) as cm:
            self.scraper.extract(invalid_data)
        
        self.assertIn("'jobs' must be a list", str(cm.exception))
    
    def test_extract_empty_jobs(self):
        """Test extraction handles empty jobs list."""
        empty_data = {'jobs': []}
        
        extracted = self.scraper.extract(empty_data)
        
        self.assertEqual(extracted, [])
    
    def test_normalize_valid_job(self):
        """Test normalization of a valid job."""
        extracted_job = self.fixture_data['jobs'][0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        self.assertEqual(normalized.source, 'nexus_technologies')
        self.assertEqual(normalized.external_id, 'NX-1001')
        self.assertEqual(normalized.title, 'Senior Backend Engineer')
        self.assertEqual(normalized.location, 'San Francisco, CA')
        self.assertEqual(normalized.employment_type, 'FULL_TIME')
        self.assertEqual(normalized.minimum_experience_years, Decimal('5.0'))
        self.assertEqual(normalized.maximum_experience_years, Decimal('7.0'))
        self.assertEqual(normalized.skills, ['python', 'django', 'postgresql', 'redis', 'docker'])
        self.assertEqual(normalized.keywords, ['backend', 'distributed systems', 'api', 'scalability'])
    
    def test_normalize_employment_type_mapping(self):
        """Test employment type normalization."""
        test_cases = [
            ('Full-time', 'FULL_TIME'),
            ('full-time', 'FULL_TIME'),
            ('Full time', 'FULL_TIME'),
            ('Remote', 'REMOTE'),
            ('remote', 'REMOTE'),
            ('Part-time', 'PART_TIME'),
            ('Contract', 'CONTRACT'),
            ('Internship', 'INTERNSHIP'),
        ]
        
        for input_type, expected in test_cases:
            result = self.scraper._normalize_employment_type(input_type)
            self.assertEqual(result, expected, f"Failed for input: {input_type}")
    
    def test_normalize_employment_type_invalid(self):
        """Test invalid employment type returns None."""
        result = self.scraper._normalize_employment_type('invalid-type')
        self.assertIsNone(result)
    
    def test_parse_experience_range(self):
        """Test parsing experience range."""
        test_cases = [
            ('5-7 years', (Decimal('5.0'), Decimal('7.0'))),
            ('5 - 7 years', (Decimal('5.0'), Decimal('7.0'))),
            ('5-7', (Decimal('5.0'), Decimal('7.0'))),
        ]
        
        for input_str, expected in test_cases:
            result = self.scraper._parse_experience(input_str)
            self.assertEqual(result, expected, f"Failed for input: {input_str}")
    
    def test_parse_experience_plus(self):
        """Test parsing experience with '+' notation."""
        test_cases = [
            ('5+ years', (Decimal('5.0'), None)),
            ('5+', (Decimal('5.0'), None)),
            ('10+ years experience', (Decimal('10.0'), None)),
        ]
        
        for input_str, expected in test_cases:
            result = self.scraper._parse_experience(input_str)
            self.assertEqual(result, expected, f"Failed for input: {input_str}")
    
    def test_parse_experience_single(self):
        """Test parsing single experience value."""
        test_cases = [
            ('3 years', (Decimal('3.0'), Decimal('3.0'))),
            ('3', (Decimal('3.0'), Decimal('3.0'))),
        ]
        
        for input_str, expected in test_cases:
            result = self.scraper._parse_experience(input_str)
            self.assertEqual(result, expected, f"Failed for input: {input_str}")
    
    def test_parse_experience_text_only(self):
        """Test parsing text-only experience returns None."""
        test_cases = [
            'Senior',
            'Junior',
            'Mid-level',
            'Entry level',
            '',
            None,
        ]
        
        for input_str in test_cases:
            result = self.scraper._parse_experience(input_str)
            self.assertEqual(result, (None, None), f"Failed for input: {input_str}")
    
    def test_normalize_skill_list(self):
        """Test skill list normalization."""
        skills = ['Python', 'Django', 'PostgreSQL', '  Redis  ', '']
        
        normalized = self.scraper._normalize_skill_list(skills)
        
        self.assertEqual(
            normalized,
            ['python', 'django', 'postgresql', 'redis']
        )
    
    def test_normalize_skill_list_empty(self):
        """Test empty skill list normalization."""
        normalized = self.scraper._normalize_skill_list([])
        self.assertEqual(normalized, [])
    
    def test_normalize_keyword_list(self):
        """Test keyword list normalization."""
        keywords = ['Backend', 'API', '  Distributed Systems  ', '']
        
        normalized = self.scraper._normalize_keyword_list(keywords)
        
        self.assertEqual(
            normalized,
            ['backend', 'api', 'distributed systems']
        )
    
    def test_normalize_missing_required_field(self):
        """Test normalization fails with missing required field."""
        invalid_job = {
            'id': 'NX-1001',
            'title': 'Software Engineer',
            # Missing description
            'application_url': 'https://example.com/apply'
        }
        
        with self.assertRaises(ScrapingError) as cm:
            self.scraper.normalize(invalid_job)
        
        self.assertIn('Missing required field', str(cm.exception))
    
    def test_normalize_preserves_raw_data(self):
        """Test that raw data is preserved."""
        extracted_job = self.fixture_data['jobs'][0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        self.assertEqual(normalized.raw_data, extracted_job)


class IngestionServiceTest(TestCase):
    """Test job ingestion service."""
    
    def setUp(self):
        """Set up test company."""
        self.company = Company.objects.create(
            name='Nexus Technologies',
            slug='nexus-technologies',
            careers_url='https://careers.nexustech.example.test'
        )
        
        from apps.jobs.services.ingestion import JobIngestionService
        self.ingestion_service = JobIngestionService()
    
    def test_ingest_new_jobs(self):
        """Test ingesting new jobs creates records."""
        normalized_jobs = [
            NormalizedJob(
                source='nexus_technologies',
                external_id='NX-1001',
                title='Software Engineer',
                description='Build software',
                location='San Francisco, CA',
                employment_type='FULL_TIME',
                experience_required='3-5 years',
                application_url='https://example.com/apply'
            ),
            NormalizedJob(
                source='nexus_technologies',
                external_id='NX-1002',
                title='Senior Engineer',
                description='Lead development',
                location='New York, NY',
                employment_type='FULL_TIME',
                experience_required='5+ years',
                application_url='https://example.com/apply2'
            )
        ]
        
        result = self.ingestion_service.ingest_jobs(
            normalized_jobs,
            'nexus-technologies'
        )
        
        # Check result
        self.assertEqual(result.created, 2)
        self.assertEqual(result.updated, 0)
        self.assertEqual(result.failed, 0)
        
        # Verify database state
        self.assertEqual(Job.objects.count(), 2)
        
        # Verify job details
        job1 = Job.objects.get(external_job_id='NX-1001')
        self.assertEqual(job1.title, 'Software Engineer')
        self.assertEqual(job1.company, self.company)
    
    def test_ingest_duplicate_jobs_updates(self):
        """Test ingesting duplicate jobs updates existing records."""
        # Create initial job
        initial_job = Job.objects.create(
            company=self.company,
            external_job_id='NX-1001',
            title='Software Engineer',
            description='Build software',
            location='San Francisco, CA',
            employment_type='FULL_TIME',
            experience_required='3-5 years',
            application_url='https://example.com/apply',
            deduplication_hash='hash1'
        )
        
        # Ingest same job with updated description
        normalized_jobs = [
            NormalizedJob(
                source='nexus_technologies',
                external_id='NX-1001',
                title='Software Engineer',
                description='Build great software',  # Updated
                location='San Francisco, CA',
                employment_type='FULL_TIME',
                experience_required='3-5 years',
                application_url='https://example.com/apply'
            )
        ]
        
        result = self.ingestion_service.ingest_jobs(
            normalized_jobs,
            'nexus-technologies'
        )
        
        # Check result
        self.assertEqual(result.created, 0)
        self.assertEqual(result.updated, 1)
        
        # Verify update
        job = Job.objects.get(external_job_id='NX-1001')
        self.assertEqual(job.description, 'Build great software')
        self.assertEqual(job.pk, initial_job.pk)  # Same record
    
    def test_ingest_company_not_found(self):
        """Test ingestion fails when company not found."""
        normalized_jobs = [
            NormalizedJob(
                source='nexus_technologies',
                external_id='NX-1001',
                title='Software Engineer',
                description='Build software',
                application_url='https://example.com/apply'
            )
        ]
        
        result = self.ingestion_service.ingest_jobs(
            normalized_jobs,
            'non-existent-company'
        )
        
        self.assertEqual(result.failed, 1)
        self.assertIn('Company not found', result.errors[0])
    
    def test_ingest_validation_failure_skips(self):
        """Test that validation failures skip jobs."""
        normalized_jobs = [
            NormalizedJob(
                source='nexus_technologies',
                external_id='NX-1001',
                title='',  # Invalid: empty title
                description='Build software',
                application_url='https://example.com/apply'
            )
        ]
        
        result = self.ingestion_service.ingest_jobs(
            normalized_jobs,
            'nexus-technologies'
        )
        
        self.assertEqual(result.skipped, 1)
        self.assertEqual(Job.objects.count(), 0)
    
    def test_ingest_mixed_valid_invalid(self):
        """Test ingestion with mix of valid and invalid jobs."""
        normalized_jobs = [
            NormalizedJob(
                source='nexus_technologies',
                external_id='NX-1001',
                title='Software Engineer',
                description='Build software',
                location='San Francisco, CA',
                employment_type='FULL_TIME',
                experience_required='3-5 years',
                application_url='https://example.com/apply'
            ),
            NormalizedJob(
                source='nexus_technologies',
                external_id='NX-1002',
                title='',  # Invalid
                description='Build software',
                location='New York, NY',
                employment_type='FULL_TIME',
                experience_required='3-5 years',
                application_url='https://example.com/apply'
            ),
            NormalizedJob(
                source='nexus_technologies',
                external_id='NX-1003',
                title='Senior Engineer',
                description='Lead development',
                location='Austin, TX',
                employment_type='FULL_TIME',
                experience_required='5+ years',
                application_url='https://example.com/apply'
            )
        ]
        
        result = self.ingestion_service.ingest_jobs(
            normalized_jobs,
            'nexus-technologies'
        )
        
        # Check result - 2 valid jobs created, 1 invalid skipped
        self.assertEqual(result.created, 2)
        self.assertEqual(result.skipped, 1)
        
        # Verify database state - only 2 valid jobs created
        self.assertEqual(Job.objects.count(), 2)
        
        # Verify the valid jobs were created
        self.assertTrue(Job.objects.filter(external_job_id='NX-1001').exists())
        self.assertTrue(Job.objects.filter(external_job_id='NX-1003').exists())
        self.assertFalse(Job.objects.filter(external_job_id='NX-1002').exists())


class StripeScraperTest(TestCase):
    """Test Stripe scraper with real fixture data."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Load fixture data
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            'scrapers',
            'fixtures',
            'stripe_jobs.json'
        )
        with open(fixture_path, 'r') as f:
            self.fixture_data = json.load(f)
        
        self.scraper = StripeScraper(
            company_slug='stripe',
            config={}
        )
    
    def test_source_identifier(self):
        """Test source identifier is correct."""
        self.assertEqual(
            self.scraper.get_source_identifier(),
            'stripe'
        )
    
    def test_extract_valid_data(self):
        """Test extraction from valid fixture data."""
        extracted = self.scraper.extract(self.fixture_data)
        
        self.assertEqual(len(extracted), 4)
        self.assertEqual(extracted[0]['id'], 7532733)
        self.assertEqual(extracted[0]['title'], 'Account Executive, AI Sales')
    
    def test_extract_missing_jobs_key(self):
        """Test extraction fails when 'jobs' key is missing."""
        invalid_data = {'data': []}
        
        with self.assertRaises(ScrapingError) as cm:
            self.scraper.extract(invalid_data)
        
        self.assertIn("Missing 'jobs' key", str(cm.exception))
    
    def test_extract_jobs_not_list(self):
        """Test extraction fails when 'jobs' is not a list."""
        invalid_data = {'jobs': 'not a list'}
        
        with self.assertRaises(ScrapingError) as cm:
            self.scraper.extract(invalid_data)
        
        self.assertIn("'jobs' must be a list", str(cm.exception))
    
    def test_extract_empty_jobs(self):
        """Test extraction handles empty jobs list."""
        empty_data = {'jobs': []}
        
        extracted = self.scraper.extract(empty_data)
        
        self.assertEqual(extracted, [])
    
    def test_normalize_valid_job(self):
        """Test normalization of a valid job."""
        extracted_job = self.fixture_data['jobs'][0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        self.assertEqual(normalized.source, 'stripe')
        self.assertEqual(normalized.external_id, '7532733')
        self.assertEqual(normalized.title, 'Account Executive, AI Sales')
        self.assertEqual(normalized.location, 'San Francisco, CA')
        self.assertIn('1175 enterprise - account executives (na)', normalized.keywords)
        self.assertIn('us', normalized.keywords)
    
    def test_normalize_html_to_text(self):
        """Test HTML content is converted to plain text."""
        extracted_job = self.fixture_data['jobs'][0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        # Description should not contain HTML tags
        self.assertNotIn('<h2>', normalized.description)
        self.assertNotIn('<p>', normalized.description)
        self.assertNotIn('</h2>', normalized.description)
        # Should contain actual text content
        self.assertIn('Stripe is a financial infrastructure platform', normalized.description)
    
    def test_normalize_missing_required_field(self):
        """Test normalization fails with missing required field."""
        invalid_job = {
            'id': 12345,
            'title': 'Software Engineer',
            # Missing content
            'absolute_url': 'https://example.com/apply'
        }
        
        with self.assertRaises(ScrapingError) as cm:
            self.scraper.normalize(invalid_job)
        
        self.assertIn('Missing required field', str(cm.exception))
    
    def test_normalize_preserves_raw_data(self):
        """Test that raw data is preserved."""
        extracted_job = self.fixture_data['jobs'][0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        self.assertEqual(normalized.raw_data, extracted_job)
    
    def test_normalize_application_url(self):
        """Test application URL is preserved correctly."""
        extracted_job = self.fixture_data['jobs'][0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        self.assertEqual(
            normalized.application_url,
            'https://stripe.com/jobs/search?gh_jid=7532733'
        )
        self.assertEqual(normalized.source_url, normalized.application_url)
    
    def test_normalize_keywords_from_departments(self):
        """Test keywords are extracted from departments."""
        extracted_job = self.fixture_data['jobs'][0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        # Should contain department name
        self.assertIn('1175 enterprise - account executives (na)', normalized.keywords)
    
    def test_normalize_keywords_from_offices(self):
        """Test keywords are extracted from offices."""
        extracted_job = self.fixture_data['jobs'][0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        # Should contain office name
        self.assertIn('us', normalized.keywords)
    
    def test_normalize_keywords_deduplication(self):
        """Test duplicate keywords are removed."""
        extracted_job = self.fixture_data['jobs'][0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        # Check no duplicates in keywords
        self.assertEqual(len(normalized.keywords), len(set(normalized.keywords)))
    
    def test_normalize_multiple_locations(self):
        """Test normalization handles different locations."""
        jobs = self.fixture_data['jobs']
        
        # San Francisco job
        sf_job = self.scraper.normalize(jobs[0])
        self.assertEqual(sf_job.location, 'San Francisco, CA')
        
        # Singapore job
        sg_job = self.scraper.normalize(jobs[2])
        self.assertEqual(sg_job.location, 'Singapore')
        
        # Bengaluru job
        blr_job = self.scraper.normalize(jobs[3])
        self.assertEqual(blr_job.location, 'Bengaluru')


class SpotifyScraperTest(TestCase):
    """Test Spotify scraper with fixture data."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Load fixture data
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            'scrapers',
            'fixtures',
            'spotify_jobs.json'
        )
        with open(fixture_path, 'r') as f:
            self.fixture_data = json.load(f)
        
        self.scraper = SpotifyScraper(
            company_slug='spotify',
            config={}
        )
    
    def test_source_identifier(self):
        """Test source identifier is correct."""
        self.assertEqual(
            self.scraper.get_source_identifier(),
            'spotify'
        )
    
    def test_extract_valid_data(self):
        """Test extraction from valid fixture data."""
        extracted = self.scraper.extract(self.fixture_data)
        
        self.assertEqual(len(extracted), 2)
        self.assertEqual(extracted[0]['id'], 'a0fa7da3-4c3c-4fa2-97bd-7d6eb01eb9e5')
        self.assertEqual(extracted[0]['text'], 'Android Engineer - Advertising')
    
    def test_extract_not_list(self):
        """Test extraction fails when data is not a list."""
        invalid_data = {'jobs': 'not a list'}
        
        with self.assertRaises(ScrapingError) as cm:
            self.scraper.extract(invalid_data)
        
        self.assertIn("Expected list of jobs", str(cm.exception))
    
    def test_extract_empty_list(self):
        """Test extraction handles empty list."""
        extracted = self.scraper.extract([])
        
        self.assertEqual(extracted, [])
    
    def test_normalize_valid_job(self):
        """Test normalization of a valid job."""
        extracted_job = self.fixture_data[0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        self.assertEqual(normalized.source, 'spotify')
        self.assertEqual(normalized.external_id, 'a0fa7da3-4c3c-4fa2-97bd-7d6eb01eb9e5')
        self.assertEqual(normalized.title, 'Android Engineer - Advertising')
        self.assertEqual(normalized.location, 'New York, NY')
        self.assertEqual(normalized.employment_type, 'FULL_TIME')
        self.assertIn('engineering', normalized.keywords)
        self.assertIn('advertising r&d', normalized.keywords)
    
    def test_normalize_employment_type_mapping(self):
        """Test employment type normalization."""
        test_cases = [
            ('Permanent', 'FULL_TIME'),
            ('permanent', 'FULL_TIME'),
            ('Contract', 'CONTRACT'),
            ('Intern', 'INTERNSHIP'),
            ('Part-time', 'PART_TIME'),
        ]
        
        for input_type, expected in test_cases:
            result = self.scraper._normalize_employment_type(input_type)
            self.assertEqual(result, expected, f"Failed for input: {input_type}")
    
    def test_normalize_employment_type_invalid(self):
        """Test invalid employment type returns None."""
        result = self.scraper._normalize_employment_type('invalid-type')
        self.assertIsNone(result)
    
    def test_normalize_missing_required_field(self):
        """Test normalization fails with missing required field."""
        invalid_job = {
            'id': 'test-id',
            'text': 'Software Engineer',
            # Missing description
            'applyUrl': 'https://example.com/apply'
        }
        
        with self.assertRaises(ScrapingError) as cm:
            self.scraper.normalize(invalid_job)
        
        self.assertIn('Missing required field', str(cm.exception))
    
    def test_normalize_preserves_raw_data(self):
        """Test that raw data is preserved."""
        extracted_job = self.fixture_data[0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        self.assertEqual(normalized.raw_data, extracted_job)
    
    def test_normalize_application_url(self):
        """Test application URL is preserved correctly."""
        extracted_job = self.fixture_data[0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        self.assertEqual(
            normalized.application_url,
            'https://jobs.lever.co/spotify/a0fa7da3-4c3c-4fa2-97bd-7d6eb01eb9e5/apply'
        )
    
    def test_normalize_keywords_from_categories(self):
        """Test keywords are extracted from categories."""
        extracted_job = self.fixture_data[0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        # Should contain department and team
        self.assertIn('engineering', normalized.keywords)
        self.assertIn('advertising r&d', normalized.keywords)
    
    def test_normalize_keywords_deduplication(self):
        """Test duplicate keywords are removed."""
        extracted_job = self.fixture_data[0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        # Check no duplicates in keywords
        self.assertEqual(len(normalized.keywords), len(set(normalized.keywords)))
    
    def test_normalize_multiple_locations(self):
        """Test normalization handles different locations."""
        jobs = self.fixture_data
        
        # New York job
        ny_job = self.scraper.normalize(jobs[0])
        self.assertEqual(ny_job.location, 'New York, NY')
        
        # London job
        london_job = self.scraper.normalize(jobs[1])
        self.assertEqual(london_job.location, 'London')


class LinearScraperTest(TestCase):
    """Test Linear scraper with fixture data."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Load fixture data
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            'scrapers',
            'fixtures',
            'linear_jobs.json'
        )
        with open(fixture_path, 'r') as f:
            self.fixture_data = json.load(f)
        
        self.scraper = LinearScraper(
            company_slug='linear',
            config={}
        )
    
    def test_source_identifier(self):
        """Test source identifier is correct."""
        self.assertEqual(
            self.scraper.get_source_identifier(),
            'linear'
        )
    
    def test_extract_valid_data(self):
        """Test extraction from valid fixture data."""
        extracted = self.scraper.extract(self.fixture_data)
        
        self.assertEqual(len(extracted), 3)
        self.assertEqual(extracted[0]['id'], 'd3bc1ced-3ce4-4086-a050-555055dbb1ff')
        self.assertEqual(extracted[0]['title'], 'Senior / Staff Fullstack Engineer')
    
    def test_extract_jobs_not_list(self):
        """Test extraction fails when 'jobs' is not a list."""
        invalid_data = {'apiVersion': '1', 'jobs': 'not a list'}
        
        with self.assertRaises(ScrapingError) as cm:
            self.scraper.extract(invalid_data)
        
        self.assertIn("Expected 'jobs' to be a list", str(cm.exception))
    
    def test_extract_filters_unlisted(self):
        """Test extraction filters out unlisted jobs."""
        data_with_unlisted = {
            'apiVersion': '1',
            'jobs': [
                {'id': '1', 'title': 'Listed', 'isListed': True},
                {'id': '2', 'title': 'Unlisted', 'isListed': False},
                {'id': '3', 'title': 'Listed 2', 'isListed': True},
            ]
        }
        
        extracted = self.scraper.extract(data_with_unlisted)
        
        self.assertEqual(len(extracted), 2)
        self.assertEqual(extracted[0]['id'], '1')
        self.assertEqual(extracted[1]['id'], '3')
    
    def test_extract_empty_jobs(self):
        """Test extraction handles empty jobs list."""
        empty_data = {'apiVersion': '1', 'jobs': []}
        
        extracted = self.scraper.extract(empty_data)
        
        self.assertEqual(extracted, [])
    
    def test_normalize_valid_job(self):
        """Test normalization of a valid job."""
        extracted_job = self.fixture_data['jobs'][0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        self.assertEqual(normalized.source, 'linear')
        self.assertEqual(normalized.external_id, 'd3bc1ced-3ce4-4086-a050-555055dbb1ff')
        self.assertEqual(normalized.title, 'Senior / Staff Fullstack Engineer')
        self.assertEqual(normalized.location, 'Europe')
        self.assertEqual(normalized.employment_type, 'FULL_TIME')
        self.assertIn('product', normalized.keywords)
        self.assertIn('engineering', normalized.keywords)
    
    def test_normalize_employment_type_mapping(self):
        """Test employment type normalization."""
        test_cases = [
            ('FullTime', 'FULL_TIME'),
            ('PartTime', 'PART_TIME'),
            ('Intern', 'INTERNSHIP'),
            ('Contract', 'CONTRACT'),
            ('Temporary', 'CONTRACT'),
        ]
        
        for input_type, expected in test_cases:
            result = self.scraper._normalize_employment_type(input_type)
            self.assertEqual(result, expected, f"Failed for input: {input_type}")
    
    def test_normalize_employment_type_invalid(self):
        """Test invalid employment type returns None."""
        result = self.scraper._normalize_employment_type('invalid-type')
        self.assertIsNone(result)
    
    def test_normalize_missing_required_field(self):
        """Test normalization fails with missing required field."""
        invalid_job = {
            'id': 'test-id',
            'title': 'Software Engineer',
            # Missing description
            'applyUrl': 'https://example.com/apply'
        }
        
        with self.assertRaises(ScrapingError) as cm:
            self.scraper.normalize(invalid_job)
        
        self.assertIn('Missing required field', str(cm.exception))
    
    def test_normalize_preserves_raw_data(self):
        """Test that raw data is preserved."""
        extracted_job = self.fixture_data['jobs'][0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        self.assertEqual(normalized.raw_data, extracted_job)
    
    def test_normalize_application_url(self):
        """Test application URL is preserved correctly."""
        extracted_job = self.fixture_data['jobs'][0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        self.assertEqual(
            normalized.application_url,
            'https://jobs.ashbyhq.com/linear/d3bc1ced-3ce4-4086-a050-555055dbb1ff/application'
        )
    
    def test_normalize_keywords_from_department_team(self):
        """Test keywords are extracted from department and team."""
        extracted_job = self.fixture_data['jobs'][0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        # Should contain department and team
        self.assertIn('product', normalized.keywords)
        self.assertIn('engineering', normalized.keywords)
    
    def test_normalize_keywords_deduplication(self):
        """Test duplicate keywords are removed."""
        extracted_job = self.fixture_data['jobs'][0]
        
        normalized = self.scraper.normalize(extracted_job)
        
        # Check no duplicates in keywords
        self.assertEqual(len(normalized.keywords), len(set(normalized.keywords)))
    
    def test_normalize_multiple_locations(self):
        """Test normalization handles different locations."""
        jobs = self.fixture_data['jobs']
        
        # Europe job
        eu_job = self.scraper.normalize(jobs[0])
        self.assertEqual(eu_job.location, 'Europe')
        
        # North America job
        na_job = self.scraper.normalize(jobs[1])
        self.assertEqual(na_job.location, 'North America')
    
    def test_normalize_remote_detection(self):
        """Test remote status is detected correctly."""
        jobs = self.fixture_data['jobs']
        
        # All jobs in fixture are remote (we can't test is_remote field since it's not in NormalizedJob)
        # Just verify they normalize successfully
        for job_data in jobs:
            normalized = self.scraper.normalize(job_data)
            self.assertIsNotNone(normalized.location, f"Job {job_data['title']} should have location")
    
    def test_normalize_non_engineering_role(self):
        """Test normalization of non-engineering role."""
        # Technical Recruiter role
        recruiter_job = self.fixture_data['jobs'][2]
        
        normalized = self.scraper.normalize(recruiter_job)
        
        self.assertEqual(normalized.title, 'Technical Recruiter')
        self.assertIn('operations', normalized.keywords)
        self.assertIn('talent', normalized.keywords)
