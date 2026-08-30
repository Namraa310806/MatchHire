"""
Integration tests for the full job ingestion pipeline.

Tests the complete flow: fixture -> scraper -> normalize -> validation -> persistence -> PostgreSQL.
"""

import json
import os
from django.test import TestCase
from decimal import Decimal

from apps.companies.models import Company
from apps.jobs.models import Job
from apps.jobs.scrapers.nexus_technologies import NexusTechnologiesScraper
from apps.jobs.services.ingestion import JobIngestionService


class FullIngestionPipelineTest(TestCase):
    """Test the complete ingestion pipeline from fixture to database."""
    
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
        
        self.scraper = NexusTechnologiesScraper(
            company_slug='nexus-technologies',
            config={}
        )
        self.ingestion_service = JobIngestionService()
    
    def test_full_pipeline_first_ingestion(self):
        """Test complete pipeline for first ingestion (creates jobs)."""
        # Extract from fixture
        extracted_jobs = self.scraper.extract(self.fixture_data)
        self.assertEqual(len(extracted_jobs), 6)
        
        # Normalize all jobs
        normalized_jobs = []
        for extracted_job in extracted_jobs:
            normalized = self.scraper.normalize(extracted_job)
            normalized_jobs.append(normalized)
        
        self.assertEqual(len(normalized_jobs), 6)
        
        # Ingest to database
        result = self.ingestion_service.ingest_jobs(
            normalized_jobs,
            'nexus-technologies'
        )
        
        # Verify results
        self.assertEqual(result.created, 6)
        self.assertEqual(result.updated, 0)
        self.assertEqual(result.skipped, 0)
        self.assertEqual(result.failed, 0)
        
        # Verify database state
        self.assertEqual(Job.objects.count(), 6)
        
        # Verify job details
        job = Job.objects.get(external_job_id='NX-1001')
        self.assertEqual(job.title, 'Senior Backend Engineer')
        self.assertEqual(job.company, self.company)
        self.assertEqual(job.employment_type, 'FULL_TIME')
        self.assertEqual(job.minimum_experience_years, Decimal('5.0'))
        self.assertEqual(job.maximum_experience_years, Decimal('7.0'))
        self.assertEqual(job.skills, ['python', 'django', 'postgresql', 'redis', 'docker'])
        self.assertEqual(job.status, Job.JobStatus.ACTIVE)
    
    def test_full_pipeline_repeated_ingestion_updates(self):
        """Test that repeated ingestion updates existing jobs without creating duplicates."""
        # First ingestion
        extracted_jobs = self.scraper.extract(self.fixture_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        result1 = self.ingestion_service.ingest_jobs(
            normalized_jobs,
            'nexus-technologies'
        )
        
        self.assertEqual(result1.created, 6)
        self.assertEqual(Job.objects.count(), 6)
        
        # Second ingestion with same data
        result2 = self.ingestion_service.ingest_jobs(
            normalized_jobs,
            'nexus-technologies'
        )
        
        # Should update, not create
        self.assertEqual(result2.created, 0)
        self.assertEqual(result2.updated, 6)
        self.assertEqual(Job.objects.count(), 6)  # No duplicates
    
    def test_full_pipeline_partial_update(self):
        """Test ingestion with some new and some existing jobs."""
        # First ingestion with 2 jobs
        partial_data = {'jobs': self.fixture_data['jobs'][:2]}
        extracted_jobs = self.scraper.extract(partial_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        
        result1 = self.ingestion_service.ingest_jobs(
            normalized_jobs,
            'nexus-technologies'
        )
        
        self.assertEqual(result1.created, 2)
        self.assertEqual(Job.objects.count(), 2)
        
        # Second ingestion with all 6 jobs
        extracted_jobs = self.scraper.extract(self.fixture_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        
        result2 = self.ingestion_service.ingest_jobs(
            normalized_jobs,
            'nexus-technologies'
        )
        
        # Should update 2 existing, create 4 new
        self.assertEqual(result2.updated, 2)
        self.assertEqual(result2.created, 4)
        self.assertEqual(Job.objects.count(), 6)
    
    def test_deduplication_hash_consistency(self):
        """Test that deduplication hashes are consistent across ingestions."""
        # First ingestion
        extracted_jobs = self.scraper.extract(self.fixture_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        self.ingestion_service.ingest_jobs(normalized_jobs, 'nexus-technologies')
        
        job1 = Job.objects.get(external_job_id='NX-1001')
        hash1 = job1.deduplication_hash
        
        # Second ingestion
        self.ingestion_service.ingest_jobs(normalized_jobs, 'nexus-technologies')
        
        job2 = Job.objects.get(external_job_id='NX-1001')
        hash2 = job2.deduplication_hash
        
        # Hash should remain the same
        self.assertEqual(hash1, hash2)
    
    def test_company_association(self):
        """Test that jobs are correctly associated with the company."""
        extracted_jobs = self.scraper.extract(self.fixture_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        self.ingestion_service.ingest_jobs(normalized_jobs, 'nexus-technologies')
        
        # All jobs should belong to the correct company
        for job in Job.objects.all():
            self.assertEqual(job.company, self.company)
        
        # Company should have correct related jobs count
        self.assertEqual(self.company.jobs.count(), 6)
    
    def test_unrelated_jobs_untouched(self):
        """Test that ingestion doesn't affect jobs from other companies."""
        # Create a job for a different company
        other_company = Company.objects.create(
            name='Other Company',
            slug='other-company',
            careers_url='https://other.com/careers'
        )
        other_job = Job.objects.create(
            company=other_company,
            external_job_id='OTHER-1',
            title='Other Job',
            description='Other description',
            application_url='https://other.com/apply',
            deduplication_hash='other-hash'
        )
        
        # Ingest Nexus jobs
        extracted_jobs = self.scraper.extract(self.fixture_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        self.ingestion_service.ingest_jobs(normalized_jobs, 'nexus-technologies')
        
        # Other company job should be untouched
        other_job.refresh_from_db()
        self.assertEqual(other_job.title, 'Other Job')
        self.assertEqual(other_job.company, other_company)
        
        # Should have 6 Nexus jobs + 1 other job
        self.assertEqual(Job.objects.count(), 7)
    
    def test_external_id_uniqueness_per_company(self):
        """Test that external_id uniqueness is enforced per company."""
        # Create a job with external_id NX-1001
        Job.objects.create(
            company=self.company,
            external_job_id='NX-1001',
            title='Existing Job',
            description='Existing description',
            application_url='https://example.com/apply',
            deduplication_hash='existing-hash'
        )
        
        # Ingest fixture with same external_id
        extracted_jobs = self.scraper.extract(self.fixture_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        result = self.ingestion_service.ingest_jobs(normalized_jobs, 'nexus-technologies')
        
        # Should update the existing job, not create duplicate
        self.assertEqual(result.updated, 1)  # NX-1001 updated
        self.assertEqual(result.created, 5)  # Other 5 created
        self.assertEqual(Job.objects.filter(company=self.company).count(), 6)
        
        # Verify the job was updated
        job = Job.objects.get(external_job_id='NX-1001')
        self.assertEqual(job.title, 'Senior Backend Engineer')  # Updated from fixture
    
    def test_experience_range_normalization(self):
        """Test that experience ranges are correctly normalized and persisted."""
        extracted_jobs = self.scraper.extract(self.fixture_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        self.ingestion_service.ingest_jobs(normalized_jobs, 'nexus-technologies')
        
        # Check specific jobs
        job1 = Job.objects.get(external_job_id='NX-1001')  # "5-7 years"
        self.assertEqual(job1.minimum_experience_years, Decimal('5.0'))
        self.assertEqual(job1.maximum_experience_years, Decimal('7.0'))
        
        job2 = Job.objects.get(external_job_id='NX-1004')  # "4+ years"
        self.assertEqual(job2.minimum_experience_years, Decimal('4.0'))
        self.assertIsNone(job2.maximum_experience_years)
        
        job3 = Job.objects.get(external_job_id='NX-1005')  # "3 years"
        self.assertEqual(job3.minimum_experience_years, Decimal('3.0'))
        self.assertEqual(job3.maximum_experience_years, Decimal('3.0'))
        
        job4 = Job.objects.get(external_job_id='NX-1006')  # "Senior"
        self.assertIsNone(job4.minimum_experience_years)
        self.assertIsNone(job4.maximum_experience_years)
    
    def test_skills_keywords_normalization(self):
        """Test that skills and keywords are correctly normalized."""
        extracted_jobs = self.scraper.extract(self.fixture_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        self.ingestion_service.ingest_jobs(normalized_jobs, 'nexus-technologies')
        
        job = Job.objects.get(external_job_id='NX-1001')
        
        # Skills should be lowercase
        self.assertEqual(job.skills, ['python', 'django', 'postgresql', 'redis', 'docker'])
        
        # Keywords should be lowercase
        self.assertEqual(job.keywords, ['backend', 'distributed systems', 'api', 'scalability'])
    
    def test_employment_type_normalization(self):
        """Test that employment types are correctly normalized."""
        extracted_jobs = self.scraper.extract(self.fixture_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        self.ingestion_service.ingest_jobs(normalized_jobs, 'nexus-technologies')
        
        # Check various employment types
        full_time_jobs = Job.objects.filter(employment_type='FULL_TIME')
        remote_jobs = Job.objects.filter(employment_type='REMOTE')
        
        self.assertGreaterEqual(full_time_jobs.count(), 3)
        self.assertGreaterEqual(remote_jobs.count(), 2)
    
    def test_application_url_preservation(self):
        """Test that official application URLs are preserved."""
        extracted_jobs = self.scraper.extract(self.fixture_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        self.ingestion_service.ingest_jobs(normalized_jobs, 'nexus-technologies')
        
        job = Job.objects.get(external_job_id='NX-1001')
        self.assertEqual(
            job.application_url,
            'https://careers.nexustech.example.test/jobs/NX-1001'
        )
    
    def test_raw_data_preservation(self):
        """Test that raw source data is preserved in job_metadata."""
        extracted_jobs = self.scraper.extract(self.fixture_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        self.ingestion_service.ingest_jobs(normalized_jobs, 'nexus-technologies')
        
        job = Job.objects.get(external_job_id='NX-1001')
        
        # Raw data should be preserved
        self.assertIsNotNone(job.job_metadata)
        self.assertIn('id', job.job_metadata)
        self.assertEqual(job.job_metadata['id'], 'NX-1001')
    
    def test_transaction_rollback_on_error(self):
        """Test that transaction rolls back on error."""
        # Create a job with invalid data that will fail validation
        invalid_job_data = {
            'jobs': [
                {
                    'id': 'INVALID-1',
                    'title': '',  # Invalid: empty title
                    'description': 'Test',
                    'application_url': 'https://example.com/apply'
                }
            ]
        }
        
        initial_count = Job.objects.count()
        
        # Try to extract and normalize invalid job - should raise ScrapingError
        extracted_jobs = self.scraper.extract(invalid_job_data)
        with self.assertRaises(Exception):  # ScrapingError from normalize
            normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        
        # No jobs should be created
        self.assertEqual(Job.objects.count(), initial_count)


class StripeIngestionPipelineTest(TestCase):
    """Test the complete ingestion pipeline for Stripe from fixture to database."""
    
    def setUp(self):
        """Set up test company and load fixture data."""
        self.company = Company.objects.create(
            name='Stripe',
            slug='stripe',
            careers_url='https://stripe.com/careers'
        )
        
        # Load fixture data
        fixture_path = os.path.join(
            os.path.dirname(__file__),
            'scrapers',
            'fixtures',
            'stripe_jobs.json'
        )
        with open(fixture_path, 'r') as f:
            self.fixture_data = json.load(f)
        
        from apps.jobs.scrapers.stripe import StripeScraper
        self.scraper = StripeScraper(
            company_slug='stripe',
            config={}
        )
        self.ingestion_service = JobIngestionService()
    
    def test_stripe_full_pipeline_first_ingestion(self):
        """Test complete pipeline for first Stripe ingestion (creates jobs)."""
        # Extract from fixture
        extracted_jobs = self.scraper.extract(self.fixture_data)
        self.assertEqual(len(extracted_jobs), 4)
        
        # Normalize all jobs
        normalized_jobs = []
        for extracted_job in extracted_jobs:
            normalized = self.scraper.normalize(extracted_job)
            normalized_jobs.append(normalized)
        
        self.assertEqual(len(normalized_jobs), 4)
        
        # Ingest to database
        result = self.ingestion_service.ingest_jobs(
            normalized_jobs,
            'stripe'
        )
        
        # Verify results
        self.assertEqual(result.created, 4)
        self.assertEqual(result.updated, 0)
        self.assertEqual(result.skipped, 0)
        self.assertEqual(result.failed, 0)
        
        # Verify database state
        self.assertEqual(Job.objects.count(), 4)
        
        # Verify job details
        job = Job.objects.get(external_job_id='7532733')
        self.assertEqual(job.title, 'Account Executive, AI Sales')
        self.assertEqual(job.company, self.company)
        self.assertEqual(job.location, 'San Francisco, CA')
        self.assertEqual(job.status, Job.JobStatus.ACTIVE)
    
    def test_stripe_repeated_ingestion_updates(self):
        """Test that repeated Stripe ingestion updates existing jobs without creating duplicates."""
        # First ingestion
        extracted_jobs = self.scraper.extract(self.fixture_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        result1 = self.ingestion_service.ingest_jobs(
            normalized_jobs,
            'stripe'
        )
        
        self.assertEqual(result1.created, 4)
        self.assertEqual(Job.objects.count(), 4)
        
        # Second ingestion with same data
        result2 = self.ingestion_service.ingest_jobs(
            normalized_jobs,
            'stripe'
        )
        
        # Should update, not create
        self.assertEqual(result2.created, 0)
        self.assertEqual(result2.updated, 4)
        self.assertEqual(Job.objects.count(), 4)  # No duplicates
    
    def test_stripe_deduplication_hash_consistency(self):
        """Test that deduplication hashes are consistent across Stripe ingestions."""
        # First ingestion
        extracted_jobs = self.scraper.extract(self.fixture_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        self.ingestion_service.ingest_jobs(normalized_jobs, 'stripe')
        
        job1 = Job.objects.get(external_job_id='7532733')
        hash1 = job1.deduplication_hash
        
        # Second ingestion
        self.ingestion_service.ingest_jobs(normalized_jobs, 'stripe')
        
        job2 = Job.objects.get(external_job_id='7532733')
        hash2 = job2.deduplication_hash
        
        # Hash should remain the same
        self.assertEqual(hash1, hash2)
    
    def test_stripe_company_association(self):
        """Test that Stripe jobs are correctly associated with the company."""
        extracted_jobs = self.scraper.extract(self.fixture_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        self.ingestion_service.ingest_jobs(normalized_jobs, 'stripe')
        
        # All jobs should belong to the correct company
        for job in Job.objects.all():
            self.assertEqual(job.company, self.company)
        
        # Company should have correct related jobs count
        self.assertEqual(self.company.jobs.count(), 4)
    
    def test_stripe_external_id_uniqueness_per_company(self):
        """Test that external_id uniqueness is enforced per company for Stripe."""
        # Create a job with external_id 7532733
        Job.objects.create(
            company=self.company,
            external_job_id='7532733',
            title='Existing Job',
            description='Existing description',
            application_url='https://example.com/apply',
            deduplication_hash='existing-hash'
        )
        
        # Ingest fixture with same external_id
        extracted_jobs = self.scraper.extract(self.fixture_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        result = self.ingestion_service.ingest_jobs(normalized_jobs, 'stripe')
        
        # Should update the existing job, not create duplicate
        self.assertEqual(result.updated, 1)  # 7532733 updated
        self.assertEqual(result.created, 3)  # Other 3 created
        self.assertEqual(Job.objects.filter(company=self.company).count(), 4)
        
        # Verify the job was updated
        job = Job.objects.get(external_job_id='7532733')
        self.assertEqual(job.title, 'Account Executive, AI Sales')  # Updated from fixture
    
    def test_stripe_application_url_preservation(self):
        """Test that official application URLs are preserved for Stripe."""
        extracted_jobs = self.scraper.extract(self.fixture_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        self.ingestion_service.ingest_jobs(normalized_jobs, 'stripe')
        
        job = Job.objects.get(external_job_id='7532733')
        self.assertEqual(
            job.application_url,
            'https://stripe.com/jobs/search?gh_jid=7532733'
        )
    
    def test_stripe_raw_data_preservation(self):
        """Test that raw source data is preserved in job_metadata for Stripe."""
        extracted_jobs = self.scraper.extract(self.fixture_data)
        normalized_jobs = [self.scraper.normalize(job) for job in extracted_jobs]
        self.ingestion_service.ingest_jobs(normalized_jobs, 'stripe')
        
        job = Job.objects.get(external_job_id='7532733')
        
        # Raw data should be preserved
        self.assertIsNotNone(job.job_metadata)
        self.assertIn('id', job.job_metadata)
        self.assertEqual(job.job_metadata['id'], 7532733)
