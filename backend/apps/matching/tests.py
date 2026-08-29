from django.test import TestCase
from decimal import Decimal
from .models import MatchScore
from apps.users.models import User, UserProfile
from apps.companies.models import Company
from apps.jobs.models import Job


class MatchScoreModelTest(TestCase):
    """Test MatchScore model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(user=self.user)
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
    
    def test_create_match_score(self):
        """Test creating a match score."""
        match_score = MatchScore.objects.create(
            user_profile=self.profile,
            job=self.job,
            final_score=Decimal('0.8500'),
            skill_similarity_score=Decimal('0.9000'),
            experience_match_score=Decimal('0.8000'),
            keyword_overlap_score=Decimal('0.7500')
        )
        self.assertEqual(match_score.user_profile, self.profile)
        self.assertEqual(match_score.job, self.job)
        self.assertEqual(match_score.final_score, Decimal('0.8500'))
        self.assertEqual(match_score.version, 1)
    
    def test_match_score_component_fields(self):
        """Test that component scores are stored correctly."""
        match_score = MatchScore.objects.create(
            user_profile=self.profile,
            job=self.job,
            final_score=Decimal('0.8500'),
            skill_similarity_score=Decimal('0.9000'),
            experience_match_score=Decimal('0.8000'),
            keyword_overlap_score=Decimal('0.7500')
        )
        self.assertEqual(match_score.skill_similarity_score, Decimal('0.9000'))
        self.assertEqual(match_score.experience_match_score, Decimal('0.8000'))
        self.assertEqual(match_score.keyword_overlap_score, Decimal('0.7500'))
    
    def test_match_score_versioning(self):
        """Test version tracking for match scores."""
        match_score1 = MatchScore.objects.create(
            user_profile=self.profile,
            job=self.job,
            final_score=Decimal('0.8500'),
            skill_similarity_score=Decimal('0.9000'),
            experience_match_score=Decimal('0.8000'),
            keyword_overlap_score=Decimal('0.7500'),
            version=1
        )
        # Creating a new version should be allowed
        match_score2 = MatchScore.objects.create(
            user_profile=self.profile,
            job=self.job,
            final_score=Decimal('0.9000'),
            skill_similarity_score=Decimal('0.9500'),
            experience_match_score=Decimal('0.8500'),
            keyword_overlap_score=Decimal('0.8000'),
            version=2
        )
        self.assertEqual(match_score1.version, 1)
        self.assertEqual(match_score2.version, 2)
    
    def test_match_score_unique_constraint(self):
        """Test that user_profile + job + version is unique."""
        MatchScore.objects.create(
            user_profile=self.profile,
            job=self.job,
            final_score=Decimal('0.8500'),
            skill_similarity_score=Decimal('0.9000'),
            experience_match_score=Decimal('0.8000'),
            keyword_overlap_score=Decimal('0.7500'),
            version=1
        )
        # Same combination should fail
        with self.assertRaises(Exception):
            MatchScore.objects.create(
                user_profile=self.profile,
                job=self.job,
                final_score=Decimal('0.9000'),
                skill_similarity_score=Decimal('0.9500'),
                experience_match_score=Decimal('0.8500'),
                keyword_overlap_score=Decimal('0.8000'),
                version=1
            )
    
    def test_match_score_related_names(self):
        """Test related_name relationships."""
        match_score = MatchScore.objects.create(
            user_profile=self.profile,
            job=self.job,
            final_score=Decimal('0.8500'),
            skill_similarity_score=Decimal('0.9000'),
            experience_match_score=Decimal('0.8000'),
            keyword_overlap_score=Decimal('0.7500')
        )
        self.assertIn(match_score, self.profile.match_scores.all())
        self.assertIn(match_score, self.job.match_scores.all())
    
    def test_match_score_valid_minimum(self):
        """Test that 0.0 is a valid score."""
        match_score = MatchScore.objects.create(
            user_profile=self.profile,
            job=self.job,
            final_score=Decimal('0.0000'),
            skill_similarity_score=Decimal('0.0000'),
            experience_match_score=Decimal('0.0000'),
            keyword_overlap_score=Decimal('0.0000')
        )
        self.assertEqual(match_score.final_score, Decimal('0.0000'))
    
    def test_match_score_valid_maximum(self):
        """Test that 1.0 is a valid score."""
        match_score = MatchScore.objects.create(
            user_profile=self.profile,
            job=self.job,
            final_score=Decimal('1.0000'),
            skill_similarity_score=Decimal('1.0000'),
            experience_match_score=Decimal('1.0000'),
            keyword_overlap_score=Decimal('1.0000')
        )
        self.assertEqual(match_score.final_score, Decimal('1.0000'))
    
    def test_match_score_rejects_below_zero(self):
        """Test that scores below 0.0 are rejected."""
        match_score = MatchScore(
            user_profile=self.profile,
            job=self.job,
            final_score=Decimal('-0.1000'),
            skill_similarity_score=Decimal('0.5000'),
            experience_match_score=Decimal('0.5000'),
            keyword_overlap_score=Decimal('0.5000')
        )
        with self.assertRaises(Exception):
            match_score.full_clean()
    
    def test_match_score_rejects_above_one(self):
        """Test that scores above 1.0 are rejected."""
        match_score = MatchScore(
            user_profile=self.profile,
            job=self.job,
            final_score=Decimal('1.1000'),
            skill_similarity_score=Decimal('0.5000'),
            experience_match_score=Decimal('0.5000'),
            keyword_overlap_score=Decimal('0.5000')
        )
        with self.assertRaises(Exception):
            match_score.full_clean()
    
    def test_match_score_component_validation(self):
        """Test that component scores also validate range."""
        match_score = MatchScore(
            user_profile=self.profile,
            job=self.job,
            final_score=Decimal('0.5000'),
            skill_similarity_score=Decimal('1.5000'),
            experience_match_score=Decimal('0.5000'),
            keyword_overlap_score=Decimal('0.5000')
        )
        with self.assertRaises(Exception):
            match_score.full_clean()
