from django.test import TestCase
from django.core.exceptions import ValidationError
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
