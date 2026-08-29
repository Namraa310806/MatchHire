from django.test import TestCase
from django.db import IntegrityError, transaction
from .models import Company
from apps.jobs.models import Job


class CompanyModelTest(TestCase):
    """Test Company model functionality."""
    
    def test_create_company(self):
        """Test creating a company."""
        company = Company.objects.create(
            name='Tech Corp',
            slug='tech-corp',
            careers_url='https://techcorp.com/careers'
        )
        self.assertEqual(company.name, 'Tech Corp')
        self.assertEqual(company.slug, 'tech-corp')
        self.assertTrue(company.is_active)
    
    def test_company_name_unique(self):
        """Test that company name is unique."""
        Company.objects.create(
            name='Tech Corp',
            slug='tech-corp',
            careers_url='https://techcorp.com/careers'
        )
        with self.assertRaises(Exception):
            Company.objects.create(
                name='Tech Corp',
                slug='tech-corp-2',
                careers_url='https://techcorp.com/careers2'
            )
    
    def test_company_slug_unique(self):
        """Test that company slug is unique."""
        Company.objects.create(
            name='Tech Corp',
            slug='tech-corp',
            careers_url='https://techcorp.com/careers'
        )
        with self.assertRaises(Exception):
            Company.objects.create(
                name='Tech Corp 2',
                slug='tech-corp',
                careers_url='https://techcorp.com/careers2'
            )
    
    def test_company_scraper_config_json(self):
        """Test JSONField for scraper configuration."""
        company = Company.objects.create(
            name='Tech Corp',
            slug='tech-corp',
            careers_url='https://techcorp.com/careers',
            scraper_config={'scraper_type': 'custom', 'rate_limit': 10}
        )
        self.assertEqual(company.scraper_config['scraper_type'], 'custom')
        self.assertEqual(company.scraper_config['rate_limit'], 10)


class CompanyDeletionBehaviorTest(TestCase):
    """Test deletion behavior for Company relationships."""
    
    def setUp(self):
        """Set up test company."""
        self.company = Company.objects.create(
            name='Tech Corp',
            slug='tech-corp',
            careers_url='https://techcorp.com/careers'
        )
    
    def test_company_deletion_protected_when_jobs_exist(self):
        """Test that company deletion is PROTECTED when jobs exist."""
        Job.objects.create(
            company=self.company,
            external_job_id='job-1',
            title='Software Engineer',
            description='Build great software',
            application_url='https://techcorp.com/jobs/1',
            deduplication_hash='abc123'
        )
        # Attempting to delete company should be prevented
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.company.delete()
