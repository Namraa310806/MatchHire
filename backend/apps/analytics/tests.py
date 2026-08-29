from django.test import TestCase
from .models import ApplyClick
from apps.users.models import User
from apps.companies.models import Company
from apps.jobs.models import Job


class ApplyClickModelTest(TestCase):
    """Test ApplyClick model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.company = Company.objects.create(
            name='Tech Corp',
            slug='tech-corp',
            careers_url='https://techcorp.com/careers'
        )
        self.job = Job.objects.create(
            company=self.company,
            external_job_id='job-123',
            title='Software Engineer',
            description='Build great software',
            application_url='https://techcorp.com/jobs/123',
            deduplication_hash='abc123'
        )
    
    def test_create_apply_click(self):
        """Test creating an apply click."""
        apply_click = ApplyClick.objects.create(
            user=self.user,
            job=self.job
        )
        self.assertEqual(apply_click.user, self.user)
        self.assertEqual(apply_click.job, self.job)
        self.assertIsNotNone(apply_click.clicked_at)
    
    def test_apply_click_nullable_user(self):
        """Test that user can be nullable for anonymous tracking."""
        apply_click = ApplyClick.objects.create(
            user=None,
            job=self.job
        )
        self.assertIsNone(apply_click.user)
        self.assertEqual(apply_click.job, self.job)
    
    def test_apply_click_json_metadata(self):
        """Test JSONField for event metadata."""
        apply_click = ApplyClick.objects.create(
            user=self.user,
            job=self.job,
            event_metadata={'device': 'mobile', 'referrer': 'google'}
        )
        self.assertEqual(apply_click.event_metadata['device'], 'mobile')
        self.assertEqual(apply_click.event_metadata['referrer'], 'google')
    
    def test_apply_click_related_names(self):
        """Test related_name relationships."""
        apply_click = ApplyClick.objects.create(
            user=self.user,
            job=self.job
        )
        self.assertIn(apply_click, self.user.apply_clicks.all())
        self.assertIn(apply_click, self.job.apply_clicks.all())
    
    def test_apply_click_job_cascade(self):
        """Test that deleting job cascades to apply clicks."""
        apply_click = ApplyClick.objects.create(
            user=self.user,
            job=self.job
        )
        job_id = self.job.id
        self.job.delete()
        # ApplyClick should be deleted
        self.assertFalse(ApplyClick.objects.filter(id=apply_click.id).exists())
