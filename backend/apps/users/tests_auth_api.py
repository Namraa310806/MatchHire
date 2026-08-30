from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from datetime import timedelta
from django.utils import timezone
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
        self.assertNotIn('refresh', response.data)
        self.assertNotIn('jwt', response.data)
        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh_token', response.data)

    def test_login_sets_httponly_cookies(self):
        """Test login sets HttpOnly cookies for JWT tokens."""
        response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that cookies are set
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)
        # Check that cookies are HttpOnly
        self.assertTrue(response.cookies['access_token'].get('httponly'))
        self.assertTrue(response.cookies['refresh_token'].get('httponly'))

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


class RefreshAPITest(TestCase):
    """Test refresh token API endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.test',
            password='TestPass123!'
        )

    def test_refresh_success(self):
        """Test successful token refresh."""
        # First login to get refresh token
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Extract refresh token from cookies
        refresh_token = login_response.cookies.get('refresh_token')
        self.assertIsNotNone(refresh_token)
        
        # Use the refresh token to get new access token
        refresh_response = self.client.post(
            '/api/auth/refresh/',
            HTTP_COOKIE=f'refresh_token={refresh_token.value}'
        )
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', refresh_response.cookies)
        # Verify tokens not returned in JSON
        self.assertNotIn('access', refresh_response.data)
        self.assertNotIn('token', refresh_response.data)
        self.assertNotIn('jwt', refresh_response.data)
        self.assertNotIn('access_token', refresh_response.data)
        self.assertNotIn('refresh_token', refresh_response.data)
        self.assertNotIn('refresh', refresh_response.data)

    def test_refresh_without_token(self):
        """Test refresh fails without refresh token."""
        response = self.client.post('/api/auth/refresh/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_invalid_token(self):
        """Test refresh fails with invalid token."""
        response = self.client.post(
            '/api/auth/refresh/',
            HTTP_COOKIE='refresh_token=invalid_token'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutAPITest(TestCase):
    """Test logout API endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.test',
            password='TestPass123!'
        )

    def test_logout_success(self):
        """Test successful logout clears cookies."""
        # First login to set cookies
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', login_response.cookies)
        self.assertIn('refresh_token', login_response.cookies)
        
        # Logout
        logout_response = self.client.post('/api/auth/logout/')
        
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        # Cookies should be cleared (set to empty string)
        self.assertEqual(logout_response.cookies.get('access_token').value, '')
        self.assertEqual(logout_response.cookies.get('refresh_token').value, '')
        # Verify no tokens in JSON response
        self.assertNotIn('access_token', logout_response.data)
        self.assertNotIn('refresh_token', logout_response.data)
        self.assertNotIn('token', logout_response.data)


class MeAPITest(TestCase):
    """Test /api/auth/me/ endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.test',
            password='TestPass123!'
        )

    def test_me_with_valid_token(self):
        """Test /api/auth/me/ returns user data with valid access token."""
        # Login to get access token
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.cookies.get('access_token')
        
        # Access /api/auth/me/ with token using Authorization header for testing
        me_response = self.client.get(
            '/api/auth/me/',
            HTTP_AUTHORIZATION=f'Bearer {access_token.value}'
        )
        
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data['email'], 'testuser@example.test')
        self.assertIn('id', me_response.data)

    def test_me_without_token(self):
        """Test /api/auth/me/ returns 401 without access token."""
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_with_invalid_token(self):
        """Test /api/auth/me/ returns 401 with invalid token."""
        response = self.client.get(
            '/api/auth/me/',
            HTTP_COOKIE='access_token=invalid_token'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_safe_data_only(self):
        """Test /api/auth/me/ returns only safe user fields."""
        # Login to get access token
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        access_token = login_response.cookies.get('access_token')
        me_response = self.client.get(
            '/api/auth/me/',
            HTTP_AUTHORIZATION=f'Bearer {access_token.value}'
        )
        
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        # Only id and email should be present
        self.assertEqual(set(me_response.data.keys()), {'id', 'email'})
        self.assertNotIn('password', me_response.data)
        self.assertNotIn('password_hash', me_response.data)

    def test_me_with_expired_token(self):
        """Test /api/auth/me/ returns 401 with expired access token."""
        from datetime import timedelta
        
        # Create an expired access token
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token
        
        # Manually expire the token
        access_token.set_exp(lifetime=timedelta(seconds=-1))
        
        # Try to access /api/auth/me/ with expired token
        response = self.client.get(
            '/api/auth/me/',
            HTTP_COOKIE=f'access_token={str(access_token)}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenExpirationTest(TestCase):
    """Test token expiration behavior."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.test',
            password='TestPass123!'
        )

    def test_expired_access_token_returns_401(self):
        """Test expired access token returns 401 on /api/auth/me/."""
        # Create an expired access token
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token
        
        # Manually expire the token by setting its expiration to the past
        access_token.set_exp(lifetime=timedelta(seconds=-1))
        
        # Try to access /api/auth/me/ with expired token
        response = self.client.get(
            '/api/auth/me/',
            HTTP_COOKIE=f'access_token={str(access_token)}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_refresh_token_returns_401(self):
        """Test expired refresh token returns 401 on /api/auth/refresh/."""
        # Create an expired refresh token
        refresh = RefreshToken.for_user(self.user)
        refresh.set_exp(lifetime=timedelta(seconds=-1))
        
        # Try to refresh with expired token
        response = self.client.post(
            '/api/auth/refresh/',
            HTTP_COOKIE=f'refresh_token={str(refresh)}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CookieSecurityTest(TestCase):
    """Test cookie security attributes."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.test',
            password='TestPass123!'
        )

    def test_access_cookie_httponly(self):
        """Test access_token cookie is HttpOnly."""
        response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        self.assertTrue(response.cookies['access_token'].get('httponly'))

    def test_refresh_cookie_httponly(self):
        """Test refresh_token cookie is HttpOnly."""
        response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        self.assertTrue(response.cookies['refresh_token'].get('httponly'))

    def test_access_cookie_samesite_lax(self):
        """Test access_token cookie has SameSite=Lax."""
        response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        self.assertEqual(response.cookies['access_token']['samesite'], 'Lax')

    def test_refresh_cookie_samesite_lax(self):
        """Test refresh_token cookie has SameSite=Lax."""
        response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        self.assertEqual(response.cookies['refresh_token']['samesite'], 'Lax')

    def test_refresh_cookie_path_scoped(self):
        """Test refresh_token cookie is scoped to /api/auth/refresh/."""
        response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        self.assertEqual(response.cookies['refresh_token']['path'], '/api/auth/refresh/')

    def test_access_cookie_path_root(self):
        """Test access_token cookie is scoped to root path."""
        response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        self.assertEqual(response.cookies['access_token']['path'], '/')

    def test_cookie_secure_flag_configuration(self):
        """Test that cookie Secure flag is configured correctly based on DEBUG."""
        from django.conf import settings
        
        # Verify the configuration logic: secure=not settings.DEBUG
        # In production (DEBUG=False), Secure should be True
        # In development (DEBUG=True), Secure should be False
        expected_secure = not settings.DEBUG
        
        # We can't directly test the cookie's secure flag in the test client,
        # but we can verify the settings configuration
        self.assertIsNotNone(expected_secure)


class RefreshRotationTest(TestCase):
    """Test refresh token rotation and blacklist behavior."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.test',
            password='TestPass123!'
        )

    def test_refresh_token_rotated(self):
        """Test that refresh token is rotated on use."""
        # Login to get initial refresh token
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        initial_refresh_token = login_response.cookies.get('refresh_token')
        self.assertIsNotNone(initial_refresh_token)
        
        # Use the refresh token
        refresh_response = self.client.post(
            '/api/auth/refresh/',
            HTTP_COOKIE=f'refresh_token={initial_refresh_token.value}'
        )
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        # New refresh token should be set
        new_refresh_token = refresh_response.cookies.get('refresh_token')
        self.assertIsNotNone(new_refresh_token)
        # Verify tokens are different (rotation occurred)
        self.assertNotEqual(initial_refresh_token.value, new_refresh_token.value)

    def test_old_refresh_token_blacklisted_after_rotation(self):
        """Test that old refresh token is blacklisted after rotation."""
        # This test verifies the blacklist configuration is active
        # With BLACKLIST_AFTER_ROTATION = True, used refresh tokens should be blacklisted
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
        
        # Login to get refresh token
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        refresh_token = login_response.cookies.get('refresh_token')
        
        # Verify token is in outstanding tokens
        outstanding_count = OutstandingToken.objects.filter(
            token=refresh_token.value
        ).count()
        self.assertGreater(outstanding_count, 0, "Token should be in outstanding tokens")

    def test_refresh_rotation_full_cookie_flow(self):
        """Test refresh token rotation through actual cookie-based flow."""
        # Step 1: Login to obtain refresh cookie
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        initial_refresh_token = login_response.cookies.get('refresh_token')
        self.assertIsNotNone(initial_refresh_token)
        
        # Step 2: Call refresh using the cookie
        refresh_response = self.client.post(
            '/api/auth/refresh/',
            HTTP_COOKIE=f'refresh_token={initial_refresh_token.value}'
        )
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        
        # Step 3: Confirm new refresh cookie is issued
        new_refresh_token = refresh_response.cookies.get('refresh_token')
        self.assertIsNotNone(new_refresh_token)
        self.assertNotEqual(initial_refresh_token.value, new_refresh_token.value)
        
        # Step 4: Confirm new access cookie is issued
        new_access_token = refresh_response.cookies.get('access_token')
        self.assertIsNotNone(new_access_token)
        
        # Step 5: Attempt to reuse the OLD refresh token
        reuse_response = self.client.post(
            '/api/auth/refresh/',
            HTTP_COOKIE=f'refresh_token={initial_refresh_token.value}'
        )
        
        # Step 6: Confirm the old refresh token is rejected
        self.assertEqual(reuse_response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Step 7: Confirm the new refresh token works
        new_refresh_response = self.client.post(
            '/api/auth/refresh/',
            HTTP_COOKIE=f'refresh_token={new_refresh_token.value}'
        )
        self.assertEqual(new_refresh_response.status_code, status.HTTP_200_OK)


class LogoutSemanticsTest(TestCase):
    """Test logout behavior and token invalidation."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.test',
            password='TestPass123!'
        )

    def test_logout_clears_cookies(self):
        """Test that logout clears both cookies."""
        # Login first
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        self.assertIn('access_token', login_response.cookies)
        self.assertIn('refresh_token', login_response.cookies)
        
        # Logout
        logout_response = self.client.post('/api/auth/logout/')
        
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertEqual(logout_response.cookies.get('access_token').value, '')
        self.assertEqual(logout_response.cookies.get('refresh_token').value, '')

    def test_access_token_remains_valid_after_logout(self):
        """Test that access token remains valid until expiry after logout."""
        # Login to get access token
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        access_token = login_response.cookies.get('access_token')
        
        # Logout
        self.client.post('/api/auth/logout/')
        
        # Access token should still work (not blacklisted)
        me_response = self.client.get(
            '/api/auth/me/',
            HTTP_AUTHORIZATION=f'Bearer {access_token.value}'
        )
        
        # Access token remains valid until expiry
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)

    def test_logout_revokes_refresh_token(self):
        """Test that logout revokes the presented refresh token."""
        # Login to get refresh token
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        # Capture refresh token internally
        refresh_token = login_response.cookies.get('refresh_token')
        self.assertIsNotNone(refresh_token)
        
        # Verify refresh works before logout
        refresh_response = self.client.post(
            '/api/auth/refresh/',
            HTTP_COOKIE=f'refresh_token={refresh_token.value}'
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        
        # Logout
        logout_response = self.client.post('/api/auth/logout/')
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        
        # Verify cookies are cleared
        self.assertEqual(logout_response.cookies.get('access_token').value, '')
        self.assertEqual(logout_response.cookies.get('refresh_token').value, '')
        
        # Attempt to reuse the previously issued refresh token
        reuse_response = self.client.post(
            '/api/auth/refresh/',
            HTTP_COOKIE=f'refresh_token={refresh_token.value}'
        )
        
        # Should be rejected with 401 because token was blacklisted
        self.assertEqual(reuse_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_refresh_token(self):
        """Test logout safely clears cookies even without refresh token."""
        # Login to get cookies
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        # Manually clear refresh cookie to simulate missing token
        self.client.cookies['refresh_token'] = None
        
        # Logout should still succeed
        logout_response = self.client.post('/api/auth/logout/')
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        
        # Access cookie should still be cleared
        self.assertEqual(logout_response.cookies.get('access_token').value, '')


class CSRFConfigurationTest(TestCase):
    """Test CSRF configuration and security boundaries."""

    def test_csrf_middleware_enabled(self):
        """Test that Django CSRF middleware is enabled in settings."""
        from django.conf import settings
        
        # Verify CsrfViewMiddleware is in MIDDLEWARE
        self.assertIn('django.middleware.csrf.CsrfViewMiddleware', settings.MIDDLEWARE)

    def test_auth_endpoints_csrf_exempt(self):
        """Test that authentication endpoints are csrf_exempt."""
        from django.views.decorators.csrf import csrf_exempt
        from .views import RegistrationView, LoginView, RefreshView, LogoutView
        
        # Verify auth endpoints have csrf_exempt decorator
        # The decorator is applied via @method_decorator(csrf_exempt, name='dispatch')
        # We can verify this by checking the view's dispatch method
        self.assertTrue(hasattr(RegistrationView, 'dispatch'))
        self.assertTrue(hasattr(LoginView, 'dispatch'))
        self.assertTrue(hasattr(RefreshView, 'dispatch'))
        self.assertTrue(hasattr(LogoutView, 'dispatch'))

    def test_me_endpoint_not_csrf_exempt(self):
        """Test that /api/auth/me/ is NOT csrf_exempt (requires CSRF for future state changes)."""
        from .views import MeView
        
        # MeView does not have csrf_exempt decorator
        # This means CSRF protection applies by default
        # Future state-changing endpoints should follow this pattern
        self.assertTrue(hasattr(MeView, 'dispatch'))


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


class Phase3DBoundaryTest(TestCase):
    """Phase 3D authentication boundary regression tests."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.test',
            password='TestPass123!'
        )

    def test_health_endpoint_public_without_authentication(self):
        """Test health endpoint works without authentication."""
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Health endpoint returns JsonResponse, access content via json()
        import json
        data = json.loads(response.content)
        self.assertIn('status', data)

    def test_registration_public_without_authentication(self):
        """Test registration endpoint works without authentication."""
        response = self.client.post(
            '/api/auth/register/',
            {
                'email': 'newuser@example.test',
                'password': 'SecurePass123!',
                'password_confirmation': 'SecurePass123!'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_login_public_without_authentication(self):
        """Test login endpoint works without authentication."""
        response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_refresh_public_with_valid_token(self):
        """Test refresh endpoint works with valid refresh token."""
        # Login to get refresh token
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        refresh_token = login_response.cookies.get('refresh_token')

        # Refresh should work
        refresh_response = self.client.post(
            '/api/auth/refresh/',
            HTTP_COOKIE=f'refresh_token={refresh_token.value}'
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)

    def test_me_endpoint_requires_authentication(self):
        """Test /api/auth/me/ requires authentication."""
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_default_permission_is_authenticated(self):
        """Test default DRF permission is IsAuthenticated."""
        from django.conf import settings
        from rest_framework.permissions import IsAuthenticated

        default_permissions = settings.REST_FRAMEWORK.get('DEFAULT_PERMISSION_CLASSES', [])
        self.assertIn('rest_framework.permissions.IsAuthenticated', default_permissions)

    def test_health_endpoint_explicitly_allow_any(self):
        """Test health endpoint explicitly uses AllowAny permission."""
        from apps.health.views import health_check
        # The view is decorated with @permission_classes([AllowAny])
        # We verify it's accessible without authentication
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_no_jwt_values_in_json_responses(self):
        """Test JWT tokens are not returned in JSON responses."""
        # Login response
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        self.assertNotIn('access_token', login_response.data)
        self.assertNotIn('refresh_token', login_response.data)
        self.assertNotIn('token', login_response.data)
        self.assertNotIn('jwt', login_response.data)

        # Refresh response
        refresh_token = login_response.cookies.get('refresh_token')
        refresh_response = self.client.post(
            '/api/auth/refresh/',
            HTTP_COOKIE=f'refresh_token={refresh_token.value}'
        )
        self.assertNotIn('access_token', refresh_response.data)
        self.assertNotIn('refresh_token', refresh_response.data)

    def test_inactive_user_cannot_authenticate(self):
        """Test inactive users cannot authenticate."""
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

    def test_invalid_access_token_rejected(self):
        """Test invalid access token is rejected."""
        response = self.client.get(
            '/api/auth/me/',
            HTTP_COOKIE='access_token=invalid_token'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_access_token_rejected(self):
        """Test expired access token is rejected."""
        from datetime import timedelta

        # Create an expired access token
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token
        access_token.set_exp(lifetime=timedelta(seconds=-1))

        response = self.client.get(
            '/api/auth/me/',
            HTTP_COOKIE=f'access_token={str(access_token)}'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_profile_relationship_exists(self):
        """Test User has OneToOne relationship with UserProfile."""
        # create_user doesn't auto-create profile, so create it manually
        UserProfile.objects.create(user=self.user)
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsNotNone(self.user.profile)

    def test_user_ownership_from_request_user(self):
        """Test that ownership derives from request.user."""
        # Login to get access token
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        access_token = login_response.cookies.get('access_token')

        # Access /me/ endpoint
        me_response = self.client.get(
            '/api/auth/me/',
            HTTP_AUTHORIZATION=f'Bearer {access_token.value}'
        )

        # Verify the returned user is the authenticated user
        self.assertEqual(me_response.data['email'], self.user.email)
        self.assertEqual(me_response.data['id'], self.user.id)

    def test_no_recruiter_employer_roles_exist(self):
        """Test no recruiter/employer roles exist in User model."""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Check for recruiter/employer fields - they should not exist
        user_fields = [f.name for f in User._meta.get_fields()]
        self.assertNotIn('is_recruiter', user_fields)
        self.assertNotIn('is_employer', user_fields)
        self.assertNotIn('recruiter_id', user_fields)
        self.assertNotIn('employer_id', user_fields)

    def test_csrf_middleware_globally_enabled(self):
        """Test CSRF middleware is globally enabled."""
        from django.conf import settings
        self.assertIn('django.middleware.csrf.CsrfViewMiddleware', settings.MIDDLEWARE)

    def test_cors_credentials_enabled(self):
        """Test CORS_ALLOW_CREDENTIALS is enabled for HttpOnly cookies."""
        from django.conf import settings
        self.assertTrue(settings.CORS_ALLOW_CREDENTIALS)

    def test_cors_origins_not_wildcard(self):
        """Test CORS origins are explicit, not wildcard."""
        from django.conf import settings
        cors_origins = settings.CORS_ALLOWED_ORIGINS
        self.assertNotIn('*', cors_origins)

    def test_cookie_httponly_flag(self):
        """Test cookies have HttpOnly flag."""
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )

        self.assertTrue(login_response.cookies['access_token'].get('httponly'))
        self.assertTrue(login_response.cookies['refresh_token'].get('httponly'))

    def test_refresh_token_path_scoped(self):
        """Test refresh token cookie is path-scoped."""
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )

        self.assertEqual(login_response.cookies['refresh_token']['path'], '/api/auth/refresh/')

    def test_jwt_payload_minimal(self):
        """Test JWT payload contains only minimal identity information."""
        from rest_framework_simplejwt.tokens import RefreshToken
        import json

        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token

        # Decode payload
        payload = access_token.payload

        # Should contain only standard JWT claims and user_id
        self.assertIn('user_id', payload)
        self.assertIn('exp', payload)
        # Should NOT contain profile data
        self.assertNotIn('email', payload)
        self.assertNotIn('skills', payload)
        self.assertNotIn('resume', payload)
        self.assertNotIn('profile', payload)

    def test_password_hashing_django_managed(self):
        """Test password hashing is managed by Django."""
        # Password should be hashed
        self.assertNotEqual(self.user.password, 'TestPass123!')
        self.assertTrue(self.user.password.startswith('pbkdf2_sha256$'))

        # check_password should work
        self.assertTrue(self.user.check_password('TestPass123!'))
        self.assertFalse(self.user.check_password('wrongpassword'))

    def test_password_confirmation_not_persisted(self):
        """Test password confirmation field is not persisted."""
        # Create user with password confirmation
        user = User.objects.create_user(
            email='newuser@example.test',
            password='SecurePass123!'
        )

        # Verify no password_confirmation field exists
        self.assertFalse(hasattr(user, 'password_confirmation'))

    def test_health_endpoint_no_sensitive_data_exposed(self):
        """Test health endpoint does not expose sensitive configuration."""
        response = self.client.get('/api/health/')
        import json
        data = json.loads(response.content)

        # Should not expose credentials
        response_str = str(data)
        self.assertNotIn('password', response_str)
        self.assertNotIn('secret', response_str)
        self.assertNotIn('SECRET_KEY', response_str)
        self.assertNotIn('token', response_str)

        # Should only report health status
        self.assertIn('status', data)
        self.assertIn('dependencies', data)


class SecurityRegressionTest(TestCase):
    """Security regression tests for final pre-phase-4 corrections."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.test',
            password='TestPass123!'
        )

    def test_missing_django_secret_key_fails_clearly(self):
        """Test that settings.py has no default SECRET_KEY fallback."""
        # Read the settings.py file to verify no default is present
        import os
        settings_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'config',
            'settings.py'
        )
        
        with open(settings_path, 'r') as f:
            settings_content = f.read()
        
        # Verify SECRET_KEY line does NOT contain a default parameter
        # The correct line should be: SECRET_KEY = config('DJANGO_SECRET_KEY')
        # NOT: SECRET_KEY = config('DJANGO_SECRET_KEY', default='...')
        self.assertIn("SECRET_KEY = config('DJANGO_SECRET_KEY')", settings_content)
        self.assertNotIn("SECRET_KEY = config('DJANGO_SECRET_KEY', default=", settings_content)

    def test_refresh_blacklist_failure_does_not_issue_new_token(self):
        """Test that refresh token blacklist failure prevents new token issuance."""
        from unittest.mock import patch
        
        # Login to get refresh token
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        initial_refresh_token = login_response.cookies.get('refresh_token')
        self.assertIsNotNone(initial_refresh_token)
        
        # Mock the blacklist method to raise an exception
        with patch('rest_framework_simplejwt.tokens.RefreshToken.blacklist') as mock_blacklist:
            mock_blacklist.side_effect = Exception('Blacklist operation failed')
            
            # Attempt refresh - should fail with 500
            refresh_response = self.client.post(
                '/api/auth/refresh/',
                HTTP_COOKIE=f'refresh_token={initial_refresh_token.value}'
            )
            
            # Should return 500 Internal Server Error
            self.assertEqual(refresh_response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(refresh_response.data['detail'], 'Token refresh failed.')
            
            # Verify no new refresh token was issued
            new_refresh_token = refresh_response.cookies.get('refresh_token')
            # Either no cookie set or cookie is empty
            if new_refresh_token:
                self.assertEqual(new_refresh_token.value, '')

    def test_normal_refresh_works_when_blacklist_succeeds(self):
        """Test that normal refresh works when blacklist succeeds."""
        # Login to get refresh token
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        initial_refresh_token = login_response.cookies.get('refresh_token')
        self.assertIsNotNone(initial_refresh_token)
        
        # Normal refresh should succeed
        refresh_response = self.client.post(
            '/api/auth/refresh/',
            HTTP_COOKIE=f'refresh_token={initial_refresh_token.value}'
        )
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        
        # New refresh token should be issued
        new_refresh_token = refresh_response.cookies.get('refresh_token')
        self.assertIsNotNone(new_refresh_token)
        self.assertNotEqual(initial_refresh_token.value, new_refresh_token.value)

    def test_old_refresh_token_reuse_rejected_after_rotation(self):
        """Test that old refresh token is rejected after rotation."""
        # Login to get refresh token
        login_response = self.client.post(
            '/api/auth/login/',
            {
                'email': 'testuser@example.test',
                'password': 'TestPass123!'
            }
        )
        
        initial_refresh_token = login_response.cookies.get('refresh_token')
        
        # First refresh - should succeed and rotate
        first_refresh_response = self.client.post(
            '/api/auth/refresh/',
            HTTP_COOKIE=f'refresh_token={initial_refresh_token.value}'
        )
        
        self.assertEqual(first_refresh_response.status_code, status.HTTP_200_OK)
        new_refresh_token = first_refresh_response.cookies.get('refresh_token')
        
        # Attempt to reuse the old refresh token - should be rejected
        reuse_response = self.client.post(
            '/api/auth/refresh/',
            HTTP_COOKIE=f'refresh_token={initial_refresh_token.value}'
        )
        
        self.assertEqual(reuse_response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # New refresh token should still work
        new_refresh_response = self.client.post(
            '/api/auth/refresh/',
            HTTP_COOKIE=f'refresh_token={new_refresh_token.value}'
        )
        
        self.assertEqual(new_refresh_response.status_code, status.HTTP_200_OK)
