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


class RegistrationTests(TestCase):
	def test_candidate_registration_success(self):
		response = self.client.post(
			"/api/auth/register/candidate/",
			{
				"email": "candidate@example.com",
				"password": "StrongPassword123!",
				"confirm_password": "StrongPassword123!",
				"full_name": "John Doe",
			},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.json()["message"], "Registration successful")
		self.assertEqual(response.json()["user"]["email"], "candidate@example.com")
		self.assertEqual(response.json()["user"]["role"], get_user_model().Roles.CANDIDATE)
		self.assertIn("access_token", response.cookies)
		self.assertIn("refresh_token", response.cookies)
		self.assertNotIn("access", response.json())
		self.assertNotIn("refresh", response.json())

	def test_recruiter_registration_success(self):
		response = self.client.post(
			"/api/auth/register/recruiter/",
			{
				"email": "recruiter@example.com",
				"password": "StrongPassword123!",
				"confirm_password": "StrongPassword123!",
				"full_name": "Jane Smith",
				"company_name": "Acme Inc",
			},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.json()["message"], "Registration successful")
		self.assertEqual(response.json()["user"]["email"], "recruiter@example.com")
		self.assertEqual(response.json()["user"]["role"], get_user_model().Roles.RECRUITER)
		self.assertIn("access_token", response.cookies)
		self.assertIn("refresh_token", response.cookies)

	def test_password_mismatch_rejected(self):
		response = self.client.post(
			"/api/auth/register/candidate/",
			{
				"email": "candidate@example.com",
				"password": "StrongPassword123!",
				"confirm_password": "DifferentPassword123!",
				"full_name": "John Doe",
			},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn("confirm_password", response.json())

	def test_duplicate_email_rejected(self):
		get_user_model().objects.create_user(
			email="duplicate@example.com",
			password="pass12345",
			full_name="Existing User",
		)

		response = self.client.post(
			"/api/auth/register/candidate/",
			{
				"email": "duplicate@example.com",
				"password": "StrongPassword123!",
				"confirm_password": "StrongPassword123!",
				"full_name": "John Doe",
			},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn("email", response.json())

	def test_weak_password_rejected(self):
		response = self.client.post(
			"/api/auth/register/candidate/",
			{
				"email": "candidate@example.com",
				"password": "12345678",
				"confirm_password": "12345678",
				"full_name": "John Doe",
			},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn("password", response.json())

	def test_candidate_profile_auto_created(self):
		response = self.client.post(
			"/api/auth/register/candidate/",
			{
				"email": "candidate-profile@example.com",
				"password": "StrongPassword123!",
				"confirm_password": "StrongPassword123!",
				"full_name": "John Doe",
			},
			content_type="application/json",
		)

		user = get_user_model().objects.get(email="candidate-profile@example.com")
		self.assertEqual(response.status_code, 201)
		self.assertTrue(CandidateProfile.objects.filter(user=user).exists())

	def test_recruiter_profile_created(self):
		response = self.client.post(
			"/api/auth/register/recruiter/",
			{
				"email": "recruiter-profile@example.com",
				"password": "StrongPassword123!",
				"confirm_password": "StrongPassword123!",
				"full_name": "Jane Smith",
				"company_name": "Acme Inc",
			},
			content_type="application/json",
		)

		user = get_user_model().objects.get(email="recruiter-profile@example.com")
		self.assertEqual(response.status_code, 201)
		self.assertTrue(RecruiterProfile.objects.filter(user=user, company_name="Acme Inc").exists())

	def test_jwt_cookies_created_after_registration(self):
		response = self.client.post(
			"/api/auth/register/candidate/",
			{
				"email": "cookie@example.com",
				"password": "StrongPassword123!",
				"confirm_password": "StrongPassword123!",
				"full_name": "Cookie User",
			},
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 201)
		self.assertIn("access_token", response.cookies)
		self.assertIn("refresh_token", response.cookies)
		self.assertEqual(response.cookies["access_token"]["httponly"], True)
		self.assertEqual(response.cookies["refresh_token"]["httponly"], True)
