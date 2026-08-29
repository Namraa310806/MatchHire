from django.test import TestCase
from .models import Job
from apps.companies.models import Company


class JobModelTest(TestCase):
    """Test Job model functionality."""
    
    def setUp(self):
        """Set up test company."""
        self.company = Company.objects.create(
            name='Tech Corp',
            slug='tech-corp',
            careers_url='https://techcorp.com/careers'
        )
    
    def test_create_job(self):
        """Test creating a job."""
        job = Job.objects.create(
            company=self.company,
            external_job_id='job-123',
            title='Software Engineer',
            description='Build great software',
            application_url='https://techcorp.com/jobs/123',
            deduplication_hash='abc123'
        )
        self.assertEqual(job.company, self.company)
        self.assertEqual(job.external_job_id, 'job-123')
        self.assertEqual(job.status, Job.JobStatus.ACTIVE)
    
    def test_job_employment_type_choices(self):
        """Test employment type choices."""
        job = Job.objects.create(
            company=self.company,
            external_job_id='job-123',
            title='Software Engineer',
            description='Build great software',
            employment_type=Job.EmploymentType.FULL_TIME,
            application_url='https://techcorp.com/jobs/123',
            deduplication_hash='abc123'
        )
        self.assertEqual(job.employment_type, Job.EmploymentType.FULL_TIME)
    
    def test_job_status_choices(self):
        """Test job status choices."""
        job = Job.objects.create(
            company=self.company,
            external_job_id='job-123',
            title='Software Engineer',
            description='Build great software',
            status=Job.JobStatus.INACTIVE,
            application_url='https://techcorp.com/jobs/123',
            deduplication_hash='abc123'
        )
        self.assertEqual(job.status, Job.JobStatus.INACTIVE)
    
    def test_job_company_foreign_key_protect(self):
        """Test that company relationship uses PROTECT."""
        job = Job.objects.create(
            company=self.company,
            external_job_id='job-123',
            title='Software Engineer',
            description='Build great software',
            application_url='https://techcorp.com/jobs/123',
            deduplication_hash='abc123'
        )
        # Attempting to delete company should be prevented
        with self.assertRaises(Exception):
            self.company.delete()
    
    def test_job_external_id_unique_per_company(self):
        """Test that external_job_id is unique per company."""
        Job.objects.create(
            company=self.company,
            external_job_id='job-123',
            title='Software Engineer',
            description='Build great software',
            application_url='https://techcorp.com/jobs/123',
            deduplication_hash='abc123'
        )
        # Same external ID for same company should fail
        with self.assertRaises(Exception):
            Job.objects.create(
                company=self.company,
                external_job_id='job-123',
                title='Senior Engineer',
                description='Lead software development',
                application_url='https://techcorp.com/jobs/124',
                deduplication_hash='def456'
            )
    
    def test_job_json_fields(self):
        """Test JSONField for skills and keywords."""
        job = Job.objects.create(
            company=self.company,
            external_job_id='job-123',
            title='Software Engineer',
            description='Build great software',
            skills=['Python', 'Django'],
            keywords=['backend', 'API'],
            application_url='https://techcorp.com/jobs/123',
            deduplication_hash='abc123'
        )
        self.assertEqual(job.skills, ['Python', 'Django'])
        self.assertEqual(job.keywords, ['backend', 'API'])
    
    def test_job_deduplication_hash_unique(self):
        """Test that deduplication_hash is unique."""
        Job.objects.create(
            company=self.company,
            external_job_id='job-123',
            title='Software Engineer',
            description='Build great software',
            application_url='https://techcorp.com/jobs/123',
            deduplication_hash='abc123'
        )
        # Same hash should fail
        with self.assertRaises(Exception):
            Job.objects.create(
                company=self.company,
                external_job_id='job-456',
                title='Senior Engineer',
                description='Lead software development',
                application_url='https://techcorp.com/jobs/456',
                deduplication_hash='abc123'
            )
    
    def test_job_company_related_name(self):
        """Test related_name from Company to Job."""
        job = Job.objects.create(
            company=self.company,
            external_job_id='job-123',
            title='Software Engineer',
            description='Build great software',
            application_url='https://techcorp.com/jobs/123',
            deduplication_hash='abc123'
        )
        self.assertIn(job, self.company.jobs.all())
    
    def test_job_experience_numeric_fields(self):
        """Test numeric experience fields for structured matching."""
        job = Job.objects.create(
            company=self.company,
            external_job_id='job-123',
            title='Software Engineer',
            description='Build great software',
            experience_required='3-5 years',
            minimum_experience_years=3.0,
            maximum_experience_years=5.0,
            application_url='https://techcorp.com/jobs/123',
            deduplication_hash='abc123'
        )
        self.assertEqual(job.minimum_experience_years, 3.0)
        self.assertEqual(job.maximum_experience_years, 5.0)
    
    def test_job_experience_nullable_fields(self):
        """Test that experience numeric fields can be NULL."""
        job = Job.objects.create(
            company=self.company,
            external_job_id='job-123',
            title='Software Engineer',
            description='Build great software',
            experience_required='Senior',
            application_url='https://techcorp.com/jobs/123',
            deduplication_hash='abc123'
        )
        self.assertIsNone(job.minimum_experience_years)
        self.assertIsNone(job.maximum_experience_years)
    
    def test_job_creation_with_all_fields(self):
        """Test normal Job creation with all fields populated."""
        job = Job.objects.create(
            company=self.company,
            external_job_id='job-123',
            title='Software Engineer',
            description='Build great software',
            location='San Francisco, CA',
            employment_type=Job.EmploymentType.FULL_TIME,
            experience_required='3-5 years',
            minimum_experience_years=3.0,
            maximum_experience_years=5.0,
            skills=['python', 'django', 'postgresql'],
            keywords=['backend', 'api'],
            application_url='https://techcorp.com/jobs/123',
            source_url='https://techcorp.com/careers/123',
            status=Job.JobStatus.ACTIVE,
            deduplication_hash='abc123'
        )
        self.assertEqual(job.minimum_experience_years, 3.0)
        self.assertEqual(job.maximum_experience_years, 5.0)
        self.assertEqual(job.skills, ['python', 'django', 'postgresql'])
        self.assertEqual(job.keywords, ['backend', 'api'])
