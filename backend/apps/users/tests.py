from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from .models import User, UserProfile


class UserModelTest(TestCase):
    """Test User model functionality."""
    
    def test_create_user(self):
        """Test creating a user with email."""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
    
    def test_user_email_unique(self):
        """Test that email is unique."""
        User.objects.create_user(
            email='test@example.com',
            username='testuser1',
            password='testpass123'
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='test@example.com',
                username='testuser2',
                password='testpass123'
            )


class UserProfileModelTest(TestCase):
    """Test UserProfile model functionality."""
    
    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
    
    def test_create_user_profile(self):
        """Test creating a user profile."""
        profile = UserProfile.objects.create(
            user=self.user,
            title='Software Engineer',
            years_of_experience=5.0,
            location='San Francisco, CA'
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.title, 'Software Engineer')
        self.assertEqual(profile.years_of_experience, 5.0)
    
    def test_user_profile_one_to_one(self):
        """Test one-to-one relationship between User and UserProfile."""
        profile1 = UserProfile.objects.create(user=self.user)
        # Creating another profile for the same user should fail
        with self.assertRaises(Exception):
            UserProfile.objects.create(user=self.user)
    
    def test_user_profile_json_fields(self):
        """Test JSONField for skills and keywords."""
        profile = UserProfile.objects.create(
            user=self.user,
            skills=['Python', 'Django', 'PostgreSQL'],
            keywords=['backend', 'web development']
        )
        self.assertEqual(profile.skills, ['Python', 'Django', 'PostgreSQL'])
        self.assertEqual(profile.keywords, ['backend', 'web development'])
    
    def test_user_profile_related_name(self):
        """Test related_name from User to UserProfile."""
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(self.user.profile, profile)


class UserProfileDeletionBehaviorTest(TestCase):
    """Test deletion behavior for User and UserProfile relationships."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            title='Software Engineer',
            years_of_experience=5.0
        )
    
    def test_user_deletion_cascades_to_profile(self):
        """Test that deleting a user cascades to their profile (CASCADE)."""
        profile_id = self.profile.id
        self.user.delete()
        # Profile should be deleted due to CASCADE
        self.assertFalse(UserProfile.objects.filter(id=profile_id).exists())
    
    def test_profile_deletion_does_not_delete_user(self):
        """Test that deleting a profile does NOT delete the user (CASCADE is one-way)."""
        user_id = self.user.id
        self.profile.delete()
        # User should still exist
        self.assertTrue(User.objects.filter(id=user_id).exists())
        # Profile should be deleted
        self.assertFalse(UserProfile.objects.filter(user=self.user).exists())


class UserProfileDatabaseConstraintTest(TestCase):
    """Test database-level constraints for UserProfile."""
    
    def test_duplicate_profile_for_same_user_rejected_at_database_level(self):
        """Test that duplicate profile for same user is rejected at database level."""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        UserProfile.objects.create(user=user, title='Engineer')
        # Attempt to create second profile should fail at database level
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UserProfile.objects.create(user=user, title='Senior Engineer')
