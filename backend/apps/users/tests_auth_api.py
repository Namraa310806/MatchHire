from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import UserProfile

User = get_user_model()


class RegistrationAPITest(TestCase):
    """Test registration API endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()

    def test_registration_success(self):
        """Test successful registration creates user and profile."""
        response = self.client.post(
            '/api/auth/register/',
            {
                'email': 'newuser@example.test',
                'password': 'SecurePass123!',
                'password_confirmation': 'SecurePass123!'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'newuser@example.test')
        self.assertIn('id', response.data)
        
        # Verify user was created
        user = User.objects.get(email='newuser@example.test')
        self.assertIsNotNone(user)
        
        # Verify password is hashed
        self.assertNotEqual(user.password, 'SecurePass123!')
        self.assertTrue(user.password.startswith('pbkdf2_sha256$'))
        
        # Verify check_password works
        self.assertTrue(user.check_password('SecurePass123!'))
        self.assertFalse(user.check_password('wrongpassword'))
        
        # Verify UserProfile was created
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsNotNone(user.profile)
        
        # Verify profile is empty (no fake data)
        self.assertEqual(user.profile.title, '')
        self.assertEqual(user.profile.skills, [])
        self.assertEqual(user.profile.keywords, [])

    def test_registration_response_no_password(self):
        """Test registration response does not expose password or hash."""
        response = self.client.post(
            '/api/auth/register/',
            {
                'email': 'newuser@example.test',
                'password': 'SecurePass123!',
                'password_confirmation': 'SecurePass123!'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', response.data)
        self.assertNotIn('password_confirmation', response.data)
        self.assertNotIn('password_hash', response.data)

    def test_registration_missing_email(self):
        """Test registration fails with missing email."""
        response = self.client.post(
            '/api/auth/register/',
            {
                'password': 'SecurePass123!',
                'password_confirmation': 'SecurePass123!'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_registration_invalid_email(self):
        """Test registration fails with invalid email format."""
        response = self.client.post(
            '/api/auth/register/',
            {
                'email': 'not-an-email',
                'password': 'SecurePass123!',
                'password_confirmation': 'SecurePass123!'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_registration_missing_password(self):
        """Test registration fails with missing password."""
        response = self.client.post(
            '/api/auth/register/',
            {
                'email': 'newuser@example.test',
                'password_confirmation': 'SecurePass123!'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_registration_missing_password_confirmation(self):
        """Test registration fails with missing password confirmation."""
        response = self.client.post(
            '/api/auth/register/',
            {
                'email': 'newuser@example.test',
                'password': 'SecurePass123!'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirmation', response.data)

    def test_registration_password_mismatch(self):
        """Test registration fails when passwords don't match."""
        response = self.client.post(
            '/api/auth/register/',
            {
                'email': 'newuser@example.test',
                'password': 'SecurePass123!',
                'password_confirmation': 'DifferentPass123!'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_registration_duplicate_email(self):
        """Test registration fails with duplicate email."""
        # Create first user
        User.objects.create_user(
            email='existing@example.test',
            password='ExistingPass123!'
        )
        
        # Attempt to register with same email
        response = self.client.post(
            '/api/auth/register/',
            {
                'email': 'existing@example.test',
                'password': 'SecurePass123!',
                'password_confirmation': 'SecurePass123!'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_registration_weak_password(self):
        """Test registration fails with weak password (Django validators)."""
        response = self.client.post(
            '/api/auth/register/',
            {
                'email': 'newuser@example.test',
                'password': '123',  # Too short
                'password_confirmation': '123'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Django password validation returns non_field_errors
        self.assertIn('non_field_errors', response.data)

    def test_registration_password_not_persisted(self):
        """Test password confirmation field is never persisted."""
        self.client.post(
            '/api/auth/register/',
            {
                'email': 'newuser@example.test',
                'password': 'SecurePass123!',
                'password_confirmation': 'SecurePass123!'
            }
        )
        
        user = User.objects.get(email='newuser@example.test')
        # Verify no password_confirmation field exists on model
        self.assertFalse(hasattr(user, 'password_confirmation'))

    def test_registration_transaction_rollback(self):
        """Test registration transaction rolls back on profile creation failure."""
        # This test verifies the atomic transaction behavior
        # We'll simulate a failure by patching UserProfile.create
        from unittest.mock import patch
        
        with patch('apps.users.serializers.UserProfile.objects.create') as mock_create:
            mock_create.side_effect = Exception('Profile creation failed')
            
            # The exception will propagate, so we expect it to be raised
            with self.assertRaises(Exception):
                self.client.post(
                    '/api/auth/register/',
                    {
                        'email': 'newuser@example.test',
                        'password': 'SecurePass123!',
                        'password_confirmation': 'SecurePass123!'
                    }
                )
            
            # User should not exist (transaction rolled back)
            self.assertFalse(User.objects.filter(email='newuser@example.test').exists())


class LoginAPITest(TestCase):
    """Test login API endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.test',
            password='TestPass123!'
        )

    def test_login_success(self):
        """Test successful login with valid credentials."""
        response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'testuser@example.test')
        self.assertIn('id', response.data['user'])

    def test_login_response_no_password(self):
        """Test login response does not expose password or hash."""
        response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('password', response.data['user'])
        self.assertNotIn('password_hash', response.data['user'])
        self.assertNotIn('token', response.data)
        self.assertNotIn('access_token', response.data)

    def test_login_nonexistent_email(self):
        """Test login fails with nonexistent email."""
        response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'nonexistent@example.test',
                'password': 'SomePass123!'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Generic error, doesn't reveal email doesn't exist
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(response.data['non_field_errors'], ['Invalid email or password.'])

    def test_login_incorrect_password(self):
        """Test login fails with incorrect password."""
        response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'WrongPass123!'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Generic error, doesn't reveal password is wrong
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(response.data['non_field_errors'], ['Invalid email or password.'])

    def test_login_inactive_user(self):
        """Test login fails for inactive user."""
        self.user.is_active = False
        self.user.save()
        
        response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Generic error, doesn't reveal user is inactive
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(response.data['non_field_errors'], ['Invalid email or password.'])

    def test_login_missing_email(self):
        """Test login fails with missing email."""
        response = self.client.post(
            '/api/auth/login/',
            {
                'password': 'TestPass123!'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_login_missing_password(self):
        """Test login fails with missing password."""
        response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_login_invalid_email_format(self):
        """Test login fails with invalid email format."""
        response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'not-an-email',
                'password': 'TestPass123!'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)


class SafeUserSerializerTest(TestCase):
    """Test SafeUserSerializer exposes only safe fields."""

    def test_safe_user_serializer_fields(self):
        """Test SafeUserSerializer only exposes id and email."""
        user = User.objects.create_user(
            email='test@example.test',
            password='TestPass123!'
        )
        
        from .serializers import SafeUserSerializer
        serializer = SafeUserSerializer(user)
        data = serializer.data
        
        self.assertEqual(set(data.keys()), {'id', 'email'})
        self.assertNotIn('password', data)
        self.assertNotIn('username', data)
        self.assertNotIn('is_staff', data)
        self.assertNotIn('is_superuser', data)
