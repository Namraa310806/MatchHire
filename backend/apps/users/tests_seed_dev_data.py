from django.test import TestCase
from django.core.management import call_command
from django.db import transaction
from decimal import Decimal
from apps.users.models import User, UserProfile
from apps.companies.models import Company
from apps.jobs.models import Job
from apps.matching.models import MatchScore
from apps.subscriptions.models import Subscription
from apps.analytics.models import ApplyClick


class SeedDevDataCommandTest(TestCase):
    """Test seed_dev_data management command."""
    
    def setUp(self):
        """Clean up database before each test to ensure isolation."""
        # Clear all relevant tables to ensure each test starts with a clean state
        # This prevents interference from other test modules that create real companies
        ApplyClick.objects.all().delete()
        MatchScore.objects.all().delete()
        Subscription.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.all().delete()
        Job.objects.all().delete()
        Company.objects.all().delete()
    
    def test_first_execution_creates_expected_dataset(self):
        """Test that first execution creates the expected dataset."""
        # Verify database is empty
        self.assertEqual(Company.objects.count(), 0)
        self.assertEqual(Job.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(UserProfile.objects.count(), 0)
        self.assertEqual(MatchScore.objects.count(), 0)
        self.assertEqual(Subscription.objects.count(), 0)
        self.assertEqual(ApplyClick.objects.count(), 0)
        
        # Run seed command
        call_command('seed_dev_data')
        
        # Verify expected counts
        self.assertEqual(Company.objects.count(), 4)
        self.assertEqual(Job.objects.count(), 11)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(UserProfile.objects.count(), 2)
        self.assertEqual(MatchScore.objects.count(), 8)
        self.assertEqual(Subscription.objects.count(), 2)
        self.assertEqual(ApplyClick.objects.count(), 4)
    
    def test_second_execution_does_not_duplicate_records(self):
        """Test that second execution does not duplicate records."""
        # First run
        call_command('seed_dev_data')
        counts_after_first = {
            'companies': Company.objects.count(),
            'jobs': Job.objects.count(),
            'users': User.objects.count(),
            'profiles': UserProfile.objects.count(),
            'match_scores': MatchScore.objects.count(),
            'subscriptions': Subscription.objects.count(),
            'apply_clicks': ApplyClick.objects.count()
        }
        
        # Second run
        call_command('seed_dev_data')
        counts_after_second = {
            'companies': Company.objects.count(),
            'jobs': Job.objects.count(),
            'users': User.objects.count(),
            'profiles': UserProfile.objects.count(),
            'match_scores': MatchScore.objects.count(),
            'subscriptions': Subscription.objects.count(),
            'apply_clicks': ApplyClick.objects.count()
        }
        
        # Verify counts are unchanged
        self.assertEqual(counts_after_first, counts_after_second)
    
    def test_relationships_are_correct(self):
        """Test that seeded data has correct relationships."""
        call_command('seed_dev_data')
        
        # Test Company -> Job relationship
        nexus = Company.objects.get(slug='nexus-technologies')
        nexus_jobs = nexus.jobs.all()
        self.assertEqual(nexus_jobs.count(), 3)
        
        # Test User -> UserProfile relationship
        user1 = User.objects.get(email='dev.user1@example.test')
        self.assertIsNotNone(user1.profile)
        self.assertEqual(user1.profile.title, 'Senior Software Engineer')
        
        # Test User -> Subscription relationship
        self.assertIsNotNone(user1.subscription)
        self.assertEqual(user1.subscription.plan, Subscription.Plan.PRO)
        
        # Test UserProfile -> MatchScore relationship
        profile1 = user1.profile
        match_scores = profile1.match_scores.all()
        self.assertGreater(match_scores.count(), 0)
        
        # Test Job -> MatchScore relationship
        job = Job.objects.get(external_job_id='NX-1001')
        job_match_scores = job.match_scores.all()
        self.assertGreater(job_match_scores.count(), 0)
        
        # Test User -> ApplyClick relationship
        user_clicks = user1.apply_clicks.all()
        self.assertGreater(user_clicks.count(), 0)
        
        # Test Job -> ApplyClick relationship
        job_clicks = job.apply_clicks.all()
        self.assertGreater(job_clicks.count(), 0)
    
    def test_seeded_jobs_satisfy_database_constraints(self):
        """Test that seeded jobs satisfy current database constraints."""
        call_command('seed_dev_data')
        
        # Verify all jobs have valid experience ranges
        jobs = Job.objects.all()
        for job in jobs:
            if job.minimum_experience_years is not None and job.maximum_experience_years is not None:
                self.assertLessEqual(job.minimum_experience_years, job.maximum_experience_years)
        
        # Verify external_job_id is unique per company
        for company in Company.objects.all():
            external_ids = company.jobs.values_list('external_job_id', flat=True)
            self.assertEqual(len(external_ids), len(set(external_ids)))
        
        # Verify deduplication_hash is globally unique
        hashes = Job.objects.values_list('deduplication_hash', flat=True)
        self.assertEqual(len(hashes), len(set(hashes)))
    
    def test_match_scores_satisfy_score_constraints(self):
        """Test that seeded match scores satisfy score constraints."""
        call_command('seed_dev_data')
        
        match_scores = MatchScore.objects.all()
        for score in match_scores:
            # Verify all scores are in valid range
            self.assertGreaterEqual(score.final_score, Decimal('0.0'))
            self.assertLessEqual(score.final_score, Decimal('1.0'))
            self.assertGreaterEqual(score.skill_similarity_score, Decimal('0.0'))
            self.assertLessEqual(score.skill_similarity_score, Decimal('1.0'))
            self.assertGreaterEqual(score.experience_match_score, Decimal('0.0'))
            self.assertLessEqual(score.experience_match_score, Decimal('1.0'))
            self.assertGreaterEqual(score.keyword_overlap_score, Decimal('0.0'))
            self.assertLessEqual(score.keyword_overlap_score, Decimal('1.0'))
    
    def test_seed_operation_transaction_safety(self):
        """Test that seed operation is transaction-safe."""
        # Start with empty database
        self.assertEqual(Company.objects.count(), 0)
        
        # Manually create a company that will conflict with seed data
        Company.objects.create(
            name='Nexus Technologies',
            slug='nexus-technologies',
            careers_url='https://different-url.example.test'
        )
        
        # The seed command should handle this gracefully without partial creation
        # Since we use get_or_create, it should reuse the existing company
        call_command('seed_dev_data')
        
        # Verify the company was reused, not duplicated
        self.assertEqual(Company.objects.filter(slug='nexus-technologies').count(), 1)
        
        # Verify other data was still created
        self.assertGreater(Job.objects.count(), 0)
    
    def test_seed_data_uses_fictional_development_identities(self):
        """Test that seed data uses clearly fictional development identities."""
        call_command('seed_dev_data')
        
        # Verify emails use .example.test domain
        users = User.objects.all()
        for user in users:
            self.assertTrue('@example.test' in user.email)
        
        # Verify company URLs use example.test domain
        companies = Company.objects.all()
        for company in companies:
            self.assertTrue('example.test' in company.careers_url)
        
        # Verify job URLs use example.test domain
        jobs = Job.objects.all()
        for job in jobs:
            self.assertTrue('example.test' in job.application_url)
    
    def test_seed_data_respects_source_only_invariant(self):
        """Test that seed data respects the source-only job invariant."""
        call_command('seed_dev_data')
        
        # All jobs must belong to a company
        jobs = Job.objects.all()
        for job in jobs:
            self.assertIsNotNone(job.company)
        
        # All jobs must have external_job_id
        for job in jobs:
            self.assertTrue(job.external_job_id)
        
        # All jobs must have deduplication_hash
        for job in jobs:
            self.assertTrue(job.deduplication_hash)
    
    def test_seed_data_match_scores_are_precomputed_demonstration_values(self):
        """Test that match scores are precomputed demonstration values."""
        call_command('seed_dev_data')
        
        # Verify match scores have reasonable demonstration values
        match_scores = MatchScore.objects.all()
        for score in match_scores:
            # These should be static demonstration values, not computed
            self.assertIsNotNone(score.final_score)
            self.assertIsNotNone(score.skill_similarity_score)
            self.assertIsNotNone(score.experience_match_score)
            self.assertIsNotNone(score.keyword_overlap_score)
            self.assertEqual(score.version, 1)
    
    def test_seed_data_subscriptions_use_controlled_plans(self):
        """Test that subscriptions use controlled plans."""
        call_command('seed_dev_data')
        
        subscriptions = Subscription.objects.all()
        valid_plans = [Subscription.Plan.FREE, Subscription.Plan.PRO, Subscription.Plan.PREMIUM]
        
        for sub in subscriptions:
            self.assertIn(sub.plan, valid_plans)
            self.assertIn(sub.status, [Subscription.Status.ACTIVE, Subscription.Status.CANCELLED, 
                                        Subscription.Status.EXPIRED, Subscription.Status.PENDING])
    
    def test_seed_data_apply_clicks_have_required_relationships(self):
        """Test that apply clicks have required relationships."""
        call_command('seed_dev_data')
        
        clicks = ApplyClick.objects.all()
        for click in clicks:
            # All clicks should reference a job
            self.assertIsNotNone(click.job)
            # All clicks should have a user (seed data doesn't create anonymous clicks)
            self.assertIsNotNone(click.user)
            # All clicks should have a timestamp
            self.assertIsNotNone(click.clicked_at)
