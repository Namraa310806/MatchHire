from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apps.users.models import User, UserProfile
from apps.companies.models import Company
from apps.jobs.models import Job
from apps.matching.models import MatchScore
from apps.subscriptions.models import Subscription
from apps.analytics.models import ApplyClick


class DomainIntegrationTest(TestCase):
    """Integration test demonstrating core MatchHire domain relationships."""
    
    def test_user_profile_match_score_job_company_relationship(self):
        """Test User -> UserProfile -> MatchScore -> Job -> Company relationship."""
        # Create Company
        company = Company.objects.create(
            name='Test Company',
            slug='test-company',
            careers_url='https://test.example.test/careers'
        )
        
        # Create Job
        job = Job.objects.create(
            company=company,
            external_job_id='TEST-001',
            title='Software Engineer',
            description='Build software',
            application_url='https://test.example.test/jobs/1',
            deduplication_hash='test-hash-001'
        )
        
        # Create User
        user = User.objects.create_user(
            email='test@example.test',
            username='testuser',
            password='testpass123'
        )
        
        # Create UserProfile
        profile = UserProfile.objects.create(
            user=user,
            title='Engineer',
            years_of_experience=5.0,
            skills=['python', 'django'],
            keywords=['backend', 'api']
        )
        
        # Create MatchScore
        match_score = MatchScore.objects.create(
            user_profile=profile,
            job=job,
            final_score=Decimal('0.8500'),
            skill_similarity_score=Decimal('0.9000'),
            experience_match_score=Decimal('0.8000'),
            keyword_overlap_score=Decimal('0.7500'),
            version=1
        )
        
        # Verify the complete relationship chain
        self.assertEqual(match_score.user_profile.user, user)
        self.assertEqual(match_score.user_profile, profile)
        self.assertEqual(match_score.job, job)
        self.assertEqual(match_score.job.company, company)
        
        # Verify reverse relationships
        self.assertEqual(user.profile, profile)
        self.assertIn(match_score, profile.match_scores.all())
        self.assertIn(match_score, job.match_scores.all())
        self.assertIn(job, company.jobs.all())
    
    def test_user_subscription_relationship(self):
        """Test User -> Subscription relationship."""
        # Create User
        user = User.objects.create_user(
            email='test@example.test',
            username='testuser',
            password='testpass123'
        )
        
        # Create Subscription
        now = timezone.now()
        subscription = Subscription.objects.create(
            user=user,
            plan=Subscription.Plan.PRO,
            status=Subscription.Status.ACTIVE,
            start_time=now,
            expiration_time=now + timedelta(days=30),
            provider_subscription_id='test-sub-001'
        )
        
        # Verify relationship
        self.assertEqual(subscription.user, user)
        self.assertEqual(user.subscription, subscription)
    
    def test_user_apply_click_job_relationship(self):
        """Test User -> ApplyClick -> Job relationship."""
        # Create Company and Job
        company = Company.objects.create(
            name='Test Company',
            slug='test-company',
            careers_url='https://test.example.test/careers'
        )
        job = Job.objects.create(
            company=company,
            external_job_id='TEST-001',
            title='Software Engineer',
            description='Build software',
            application_url='https://test.example.test/jobs/1',
            deduplication_hash='test-hash-001'
        )
        
        # Create User
        user = User.objects.create_user(
            email='test@example.test',
            username='testuser',
            password='testpass123'
        )
        
        # Create ApplyClick
        apply_click = ApplyClick.objects.create(
            user=user,
            job=job
        )
        
        # Verify relationship
        self.assertEqual(apply_click.user, user)
        self.assertEqual(apply_click.job, job)
        self.assertIn(apply_click, user.apply_clicks.all())
        self.assertIn(apply_click, job.apply_clicks.all())
    
    def test_complete_domain_integration(self):
        """Test complete domain integration with all relationships."""
        # Create Company
        company = Company.objects.create(
            name='Integration Test Company',
            slug='integration-test-company',
            careers_url='https://integration.example.test/careers'
        )
        
        # Create Job
        job = Job.objects.create(
            company=company,
            external_job_id='INT-001',
            title='Backend Developer',
            description='Develop backend systems',
            location='Remote',
            employment_type=Job.EmploymentType.REMOTE,
            experience_required='3-5 years',
            minimum_experience_years=3.0,
            maximum_experience_years=5.0,
            skills=['python', 'django', 'postgresql'],
            keywords=['backend', 'api', 'distributed systems'],
            application_url='https://integration.example.test/jobs/1',
            source_url='https://integration.example.test/jobs/1',
            deduplication_hash='integration-hash-001'
        )
        
        # Create User
        user = User.objects.create_user(
            email='integration@example.test',
            username='integrationuser',
            password='testpass123'
        )
        
        # Create UserProfile
        profile = UserProfile.objects.create(
            user=user,
            title='Backend Developer',
            years_of_experience=4.0,
            location='San Francisco, CA',
            skills=['python', 'django', 'postgresql', 'redis'],
            keywords=['backend', 'api', 'distributed systems']
        )
        
        # Create MatchScore
        match_score = MatchScore.objects.create(
            user_profile=profile,
            job=job,
            final_score=Decimal('0.8800'),
            skill_similarity_score=Decimal('0.9200'),
            experience_match_score=Decimal('0.8500'),
            keyword_overlap_score=Decimal('0.8000'),
            version=1
        )
        
        # Create Subscription
        now = timezone.now()
        subscription = Subscription.objects.create(
            user=user,
            plan=Subscription.Plan.PREMIUM,
            status=Subscription.Status.ACTIVE,
            start_time=now,
            expiration_time=now + timedelta(days=30),
            provider_subscription_id='integration-sub-001'
        )
        
        # Create ApplyClick
        apply_click = ApplyClick.objects.create(
            user=user,
            job=job
        )
        
        # Verify all relationships work together
        # User relationships
        self.assertEqual(user.profile, profile)
        self.assertEqual(user.subscription, subscription)
        self.assertIn(apply_click, user.apply_clicks.all())
        
        # Profile relationships
        self.assertEqual(profile.user, user)
        self.assertIn(match_score, profile.match_scores.all())
        
        # Job relationships
        self.assertEqual(job.company, company)
        self.assertIn(match_score, job.match_scores.all())
        self.assertIn(apply_click, job.apply_clicks.all())
        
        # Company relationships
        self.assertIn(job, company.jobs.all())
        
        # MatchScore relationships
        self.assertEqual(match_score.user_profile, profile)
        self.assertEqual(match_score.job, job)
        
        # Subscription relationships
        self.assertEqual(subscription.user, user)
        
        # ApplyClick relationships
        self.assertEqual(apply_click.user, user)
        self.assertEqual(apply_click.job, job)
        
        # Verify data integrity
        self.assertEqual(company.name, 'Integration Test Company')
        self.assertEqual(job.title, 'Backend Developer')
        self.assertEqual(user.email, 'integration@example.test')
        self.assertEqual(profile.years_of_experience, Decimal('4.0'))
        self.assertEqual(match_score.final_score, Decimal('0.8800'))
        self.assertEqual(subscription.plan, Subscription.Plan.PREMIUM)
        self.assertIsNotNone(apply_click.clicked_at)
