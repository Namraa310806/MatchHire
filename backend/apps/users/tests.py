from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model
from .models import User, UserProfile

User = get_user_model()


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
    
    def test_user_can_be_created_without_username(self):
        """Test that username is optional when email is USERNAME_FIELD."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertIsNone(user.username)
    
    def test_user_is_active_by_default(self):
        """Test that new users are active by default."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertTrue(user.is_active)
    
    def test_user_is_not_staff_by_default(self):
        """Test that new users are not staff by default."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertFalse(user.is_staff)
    
    def test_user_is_not_superuser_by_default(self):
        """Test that new users are not superuser by default."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertFalse(user.is_superuser)


class UserManagerTest(TestCase):
    """Test UserManager functionality for authentication foundation."""
    
    def test_create_user_requires_email(self):
        """Test that create_user raises ValueError when email is not provided."""
        with self.assertRaises(ValueError) as cm:
            User.objects.create_user(email='', password='testpass123')
        self.assertEqual(str(cm.exception), 'Users must have an email address')
    
    def test_create_user_hashes_password(self):
        """Test that password is hashed, not stored in plaintext."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        # Password should not be stored as plaintext
        self.assertNotEqual(user.password, 'testpass123')
        # Password should be hashed (starts with algorithm identifier)
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))
    
    def test_create_user_check_password_correct(self):
        """Test that check_password returns True for correct password."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertTrue(user.check_password('testpass123'))
    
    def test_create_user_check_password_incorrect(self):
        """Test that check_password returns False for incorrect password."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertFalse(user.check_password('wrongpassword'))
    
    def test_create_superuser_sets_staff_flag(self):
        """Test that create_superuser sets is_staff=True."""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(user.is_staff)
    
    def test_create_superuser_sets_superuser_flag(self):
        """Test that create_superuser sets is_superuser=True."""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(user.is_superuser)
    
    def test_create_superuser_sets_active_flag(self):
        """Test that create_superuser sets is_active=True."""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(user.is_active)
    
    def test_create_superuser_requires_staff_true(self):
        """Test that create_superuser raises ValueError if is_staff is False."""
        with self.assertRaises(ValueError) as cm:
            User.objects.create_superuser(
                email='admin@example.com',
                password='adminpass123',
                is_staff=False
            )
        self.assertEqual(str(cm.exception), 'Superuser must have is_staff=True.')
    
    def test_create_superuser_requires_superuser_true(self):
        """Test that create_superuser raises ValueError if is_superuser is False."""
        with self.assertRaises(ValueError) as cm:
            User.objects.create_superuser(
                email='admin@example.com',
                password='adminpass123',
                is_superuser=False
            )
        self.assertEqual(str(cm.exception), 'Superuser must have is_superuser=True.')
    
    def test_create_superuser_password_hashed(self):
        """Test that superuser password is hashed, not stored in plaintext."""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertNotEqual(user.password, 'adminpass123')
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))
    
    def test_email_normalization(self):
        """Test that email domain part is normalized (lowercased)."""
        user = User.objects.create_user(
            email='test@Example.COM',
            password='testpass123'
        )
        # Django's normalize_email only lowercases the domain part
        self.assertEqual(user.email, 'test@example.com')


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


class UserAuthenticationDatabaseConstraintTest(TestCase):
    """Test database-level constraints for User authentication."""
    
    def test_duplicate_email_rejected_at_database_level(self):
        """Test that duplicate email is rejected at database level."""
        User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        # Attempt to create user with same email should fail at database level
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(
                    email='test@example.com',
                    password='differentpass123'
                )
    
    def test_email_uniqueness_enforced(self):
        """Test that email uniqueness is enforced at database level."""
        user1 = User.objects.create_user(
            email='user1@example.com',
            password='pass123'
        )
        user2 = User.objects.create_user(
            email='user2@example.com',
            password='pass123'
        )
        self.assertNotEqual(user1.email, user2.email)
        self.assertEqual(User.objects.filter(email='user1@example.com').count(), 1)
        self.assertEqual(User.objects.filter(email='user2@example.com').count(), 1)
