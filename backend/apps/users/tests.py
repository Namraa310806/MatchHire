from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from .models import CandidateProfile, RecruiterProfile


class UserModelTests(TestCase):
	def test_candidate_profile_is_created_automatically(self):
		user = get_user_model().objects.create_user(
			email="candidate@example.com",
			password="pass12345",
			full_name="Candidate One",
		)

		self.assertEqual(user.role, get_user_model().Roles.CANDIDATE)
		self.assertTrue(CandidateProfile.objects.filter(user=user).exists())

	def test_recruiter_profile_is_created_automatically(self):
		user = get_user_model().objects.create_user(
			email="recruiter@example.com",
			password="pass12345",
			full_name="Recruiter One",
			role=get_user_model().Roles.RECRUITER,
		)

		self.assertTrue(RecruiterProfile.objects.filter(user=user).exists())

	def test_create_superuser_enables_admin_login(self):
		user = get_user_model().objects.create_superuser(
			email="admin@example.com",
			password="pass12345",
			full_name="Admin User",
		)

		self.assertTrue(user.is_staff)
		self.assertTrue(user.is_superuser)
		self.assertTrue(self.client.login(username="admin@example.com", password="pass12345"))


class JwtAuthenticationTests(TestCase):
	def setUp(self):
		self.user_model = get_user_model()
		self.active_user = self.user_model.objects.create_user(
			email="active@example.com",
			password="pass12345",
			full_name="Active User",
		)
		self.inactive_user = self.user_model.objects.create_user(
			email="inactive@example.com",
			password="pass12345",
			full_name="Inactive User",
		)
		self.inactive_user.is_active = False
		self.inactive_user.save(update_fields=["is_active"])

	def test_successful_login_sets_cookies(self):
		response = self.client.post(
			"/api/auth/login/",
			{"email": "active@example.com", "password": "pass12345"},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["message"], "Login successful")
		self.assertIn("access_token", response.cookies)
		self.assertIn("refresh_token", response.cookies)
		self.assertEqual(response.cookies["access_token"]["httponly"], True)
		self.assertEqual(response.cookies["refresh_token"]["httponly"], True)
		self.assertEqual(response.cookies["access_token"]["samesite"], "Lax")

	def test_invalid_password_rejected(self):
		response = self.client.post(
			"/api/auth/login/",
			{"email": "active@example.com", "password": "wrong-pass"},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 401)
		self.assertEqual(response.json()["message"], "Invalid email or password")

	def test_inactive_user_rejected(self):
		response = self.client.post(
			"/api/auth/login/",
			{"email": "inactive@example.com", "password": "pass12345"},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 401)
		self.assertEqual(response.json()["message"], "User account is inactive")

	def test_refresh_token_rotates_cookies(self):
		login_response = self.client.post(
			"/api/auth/login/",
			{"email": "active@example.com", "password": "pass12345"},
			content_type="application/json",
		)
		self.client.cookies["refresh_token"] = login_response.cookies["refresh_token"].value

		response = self.client.post("/api/auth/refresh/", {}, content_type="application/json")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["message"], "Token refreshed")
		self.assertIn("access_token", response.cookies)
		self.assertIn("refresh_token", response.cookies)

	def test_logout_blacklists_refresh_and_clears_cookies(self):
		login_response = self.client.post(
			"/api/auth/login/",
			{"email": "active@example.com", "password": "pass12345"},
			content_type="application/json",
		)
		refresh_value = login_response.cookies["refresh_token"].value
		refresh_token = RefreshToken(refresh_value)
		token_jti = refresh_token["jti"]
		self.client.cookies["refresh_token"] = refresh_value

		response = self.client.post("/api/auth/logout/", {}, content_type="application/json")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["message"], "Logged out")
		self.assertIn("access_token", response.cookies)
		self.assertIn("refresh_token", response.cookies)
		self.assertEqual(response.cookies["access_token"]["max-age"], 0)
		self.assertEqual(response.cookies["refresh_token"]["max-age"], 0)

		self.assertTrue(OutstandingToken.objects.filter(jti=token_jti).exists())
		self.assertTrue(BlacklistedToken.objects.filter(token__jti=token_jti).exists())
