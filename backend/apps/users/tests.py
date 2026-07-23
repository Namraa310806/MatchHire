from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from .models import CandidateProfile, RecruiterProfile
from .permissions import (
    CandidateAndVerified,
    IsProfileOwner,
    ReadOnly,
    RecruiterAndVerified,
)


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
        self.assertTrue(
            self.client.login(username="admin@example.com", password="pass12345")
        )


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
        self.client.cookies["refresh_token"] = login_response.cookies[
            "refresh_token"
        ].value

        response = self.client.post(
            "/api/auth/refresh/", {}, content_type="application/json"
        )

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

        response = self.client.post(
            "/api/auth/logout/", {}, content_type="application/json"
        )

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
        self.assertEqual(
            response.json()["user"]["role"], get_user_model().Roles.CANDIDATE
        )
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
        self.assertEqual(
            response.json()["user"]["role"], get_user_model().Roles.RECRUITER
        )
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
        self.assertTrue(
            RecruiterProfile.objects.filter(user=user, company_name="Acme Inc").exists()
        )

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


class CurrentUserViewTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.candidate = self.user_model.objects.create_user(
            email="candidate@example.com",
            password="pass12345",
            full_name="Candidate User",
        )
        self.recruiter = self.user_model.objects.create_user(
            email="recruiter@example.com",
            password="pass12345",
            full_name="Recruiter User",
            role=self.user_model.Roles.RECRUITER,
        )
        self.recruiter.recruiter_profile.company_name = "Acme Inc"
        self.recruiter.recruiter_profile.save()

    def _authenticate_user(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.cookies["access_token"] = str(refresh.access_token)
        self.client.cookies["refresh_token"] = str(refresh)

    def test_candidate_can_access_me_endpoint(self):
        self._authenticate_user(self.candidate)
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("user", response.json())
        self.assertIn("profile", response.json())

    def test_recruiter_can_access_me_endpoint(self):
        self._authenticate_user(self.recruiter)
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("user", response.json())
        self.assertIn("profile", response.json())

    def test_anonymous_request_rejected(self):
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 401)

    def test_candidate_profile_returned(self):
        self._authenticate_user(self.candidate)
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("profile", data)
        self.assertIn("headline", data["profile"])
        self.assertIn("bio", data["profile"])

    def test_recruiter_profile_returned(self):
        self._authenticate_user(self.recruiter)
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("profile", data)
        self.assertIn("company_name", data["profile"])
        self.assertEqual(data["profile"]["company_name"], "Acme Inc")

    def test_correct_role_returned(self):
        self._authenticate_user(self.candidate)
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user"]["role"], self.user_model.Roles.CANDIDATE)

        self.client.cookies.clear()
        self._authenticate_user(self.recruiter)
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user"]["role"], self.user_model.Roles.RECRUITER)

    def test_no_sensitive_fields_exposed(self):
        self._authenticate_user(self.candidate)
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        user_data = data["user"]

        self.assertNotIn("password", user_data)
        self.assertNotIn("groups", user_data)
        self.assertNotIn("permissions", user_data)
        self.assertNotIn("is_superuser", user_data)
        self.assertNotIn("is_active", user_data)
        self.assertNotIn("is_staff", user_data)
        self.assertNotIn("updated_at", user_data)

    def test_required_user_fields_returned(self):
        self._authenticate_user(self.candidate)
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        user_data = data["user"]

        self.assertIn("id", user_data)
        self.assertIn("email", user_data)
        self.assertIn("full_name", user_data)
        self.assertIn("role", user_data)
        self.assertIn("is_verified", user_data)
        self.assertIn("date_joined", user_data)

    def test_missing_candidate_profile_raises_error(self):
        self.candidate.candidate_profile.delete()
        self._authenticate_user(self.candidate)
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 500)

    def test_missing_recruiter_profile_raises_error(self):
        self.recruiter.recruiter_profile.delete()
        self._authenticate_user(self.recruiter)
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 500)


class ProfileManagementTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.candidate = self.user_model.objects.create_user(
            email="candidate@example.com",
            password="pass12345",
            full_name="Candidate User",
        )
        self.recruiter = self.user_model.objects.create_user(
            email="recruiter@example.com",
            password="pass12345",
            full_name="Recruiter User",
            role=self.user_model.Roles.RECRUITER,
        )
        self.recruiter.recruiter_profile.company_name = "Acme Inc"
        self.recruiter.recruiter_profile.save()

    def _authenticate_user(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.cookies["access_token"] = str(refresh.access_token)
        self.client.cookies["refresh_token"] = str(refresh)

    def test_candidate_get_profile(self):
        self._authenticate_user(self.candidate)
        response = self.client.get("/api/profile/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("user", response.json())
        self.assertIn("profile", response.json())

    def test_candidate_update_profile(self):
        self._authenticate_user(self.candidate)
        response = self.client.patch(
            "/api/profile/",
            {"full_name": "Updated Name"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["full_name"], "Updated Name")
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.full_name, "Updated Name")

    def test_recruiter_get_profile(self):
        self._authenticate_user(self.recruiter)
        response = self.client.get("/api/profile/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("user", response.json())
        self.assertIn("profile", response.json())

    def test_recruiter_update_profile(self):
        self._authenticate_user(self.recruiter)
        response = self.client.patch(
            "/api/profile/",
            {"full_name": "Updated Recruiter Name"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["full_name"], "Updated Recruiter Name")
        self.recruiter.refresh_from_db()
        self.assertEqual(self.recruiter.full_name, "Updated Recruiter Name")

    def test_candidate_blocked_from_recruiter_endpoints(self):
        self._authenticate_user(self.candidate)
        response = self.client.get("/api/profile/recruiter/")

        self.assertEqual(response.status_code, 403)

    def test_recruiter_blocked_from_candidate_endpoints(self):
        self._authenticate_user(self.recruiter)
        response = self.client.get("/api/profile/candidate/")

        self.assertEqual(response.status_code, 403)

    def test_authentication_required(self):
        response = self.client.get("/api/profile/")

        self.assertEqual(response.status_code, 401)

    def test_email_cannot_be_changed(self):
        self._authenticate_user(self.candidate)
        response = self.client.patch(
            "/api/profile/",
            {"email": "newemail@example.com"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.email, "candidate@example.com")

    def test_role_cannot_be_changed(self):
        self._authenticate_user(self.candidate)
        response = self.client.patch(
            "/api/profile/",
            {"role": self.user_model.Roles.RECRUITER},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.role, self.user_model.Roles.CANDIDATE)


class CandidateProfileTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.candidate = self.user_model.objects.create_user(
            email="candidate@example.com",
            password="pass12345",
            full_name="Candidate User",
        )

    def _authenticate_user(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.cookies["access_token"] = str(refresh.access_token)
        self.client.cookies["refresh_token"] = str(refresh)

    def test_candidate_get_candidate_profile(self):
        self._authenticate_user(self.candidate)
        response = self.client.get("/api/profile/candidate/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("headline", data)
        self.assertIn("bio", data)
        self.assertIn("current_location", data)
        self.assertIn("years_of_experience", data)
        self.assertIn("skills_text", data)
        self.assertIn("linkedin_url", data)
        self.assertIn("github_url", data)
        self.assertIn("portfolio_url", data)
        self.assertIn("resume_uploaded", data)

    def test_candidate_update_candidate_profile(self):
        self._authenticate_user(self.candidate)
        update_data = {
            "headline": "Software Engineer",
            "bio": "Experienced developer",
            "current_location": "San Francisco",
            "years_of_experience": 5,
            "skills_text": "Python, Django, JavaScript",
            "linkedin_url": "https://linkedin.com/in/test",
            "github_url": "https://github.com/test",
            "portfolio_url": "https://portfolio.com",
        }
        response = self.client.patch(
            "/api/profile/candidate/",
            update_data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["headline"], "Software Engineer")
        self.assertEqual(data["bio"], "Experienced developer")
        self.assertEqual(data["current_location"], "San Francisco")
        self.assertEqual(data["years_of_experience"], 5)
        self.assertEqual(data["skills_text"], "Python, Django, JavaScript")
        self.assertEqual(data["linkedin_url"], "https://linkedin.com/in/test")
        self.assertEqual(data["github_url"], "https://github.com/test")
        self.assertEqual(data["portfolio_url"], "https://portfolio.com")

    def test_invalid_years_of_experience_rejected(self):
        self._authenticate_user(self.candidate)
        response = self.client.patch(
            "/api/profile/candidate/",
            {"years_of_experience": -1},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("years_of_experience", response.json())

    def test_invalid_linkedin_url_rejected(self):
        self._authenticate_user(self.candidate)
        response = self.client.patch(
            "/api/profile/candidate/",
            {"linkedin_url": "not-a-valid-url"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("linkedin_url", response.json())

    def test_invalid_github_url_rejected(self):
        self._authenticate_user(self.candidate)
        response = self.client.patch(
            "/api/profile/candidate/",
            {"github_url": "not-a-valid-url"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("github_url", response.json())

    def test_invalid_portfolio_url_rejected(self):
        self._authenticate_user(self.candidate)
        response = self.client.patch(
            "/api/profile/candidate/",
            {"portfolio_url": "not-a-valid-url"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("portfolio_url", response.json())


class RecruiterProfileTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.recruiter = self.user_model.objects.create_user(
            email="recruiter@example.com",
            password="pass12345",
            full_name="Recruiter User",
            role=self.user_model.Roles.RECRUITER,
        )
        self.recruiter.recruiter_profile.company_name = "Acme Inc"
        self.recruiter.recruiter_profile.save()

    def _authenticate_user(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.cookies["access_token"] = str(refresh.access_token)
        self.client.cookies["refresh_token"] = str(refresh)

    def test_recruiter_get_recruiter_profile(self):
        self._authenticate_user(self.recruiter)
        response = self.client.get("/api/profile/recruiter/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("company_name", data)
        self.assertIn("company_website", data)
        self.assertIn("job_title", data)
        self.assertIn("verified_company", data)

    def test_recruiter_update_recruiter_profile(self):
        self._authenticate_user(self.recruiter)
        update_data = {
            "company_name": "New Company Inc",
            "company_website": "https://newcompany.com",
            "job_title": "Senior Recruiter",
        }
        response = self.client.patch(
            "/api/profile/recruiter/",
            update_data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["company_name"], "New Company Inc")
        self.assertEqual(data["company_website"], "https://newcompany.com")
        self.assertEqual(data["job_title"], "Senior Recruiter")

    def test_verified_company_cannot_be_changed(self):
        self._authenticate_user(self.recruiter)
        response = self.client.patch(
            "/api/profile/recruiter/",
            {"verified_company": True},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.recruiter.recruiter_profile.refresh_from_db()
        self.assertEqual(self.recruiter.recruiter_profile.verified_company, False)


class RBACPermissionTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.candidate = self.user_model.objects.create_user(
            email="candidate@example.com",
            password="pass12345",
            full_name="Candidate User",
        )
        self.verified_candidate = self.user_model.objects.create_user(
            email="verified_candidate@example.com",
            password="pass12345",
            full_name="Verified Candidate",
        )
        self.verified_candidate.is_verified = True
        self.verified_candidate.save()
        self.recruiter = self.user_model.objects.create_user(
            email="recruiter@example.com",
            password="pass12345",
            full_name="Recruiter User",
            role=self.user_model.Roles.RECRUITER,
        )
        self.verified_recruiter = self.user_model.objects.create_user(
            email="verified_recruiter@example.com",
            password="pass12345",
            full_name="Verified Recruiter",
            role=self.user_model.Roles.RECRUITER,
        )
        self.verified_recruiter.is_verified = True
        self.verified_recruiter.save()

    def _authenticate_user(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.cookies["access_token"] = str(refresh.access_token)
        self.client.cookies["refresh_token"] = str(refresh)

    def _create_mock_request(self, user, method="GET"):
        class MockRequest:
            def __init__(self, user, method):
                self.user = user
                self.method = method

        return MockRequest(user, method)

    def test_candidate_accesses_candidate_only_endpoint(self):
        self._authenticate_user(self.candidate)
        response = self.client.get("/api/users/rbac/candidate-only/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Access granted")

    def test_recruiter_denied_candidate_only_endpoint(self):
        self._authenticate_user(self.recruiter)
        response = self.client.get("/api/users/rbac/candidate-only/")
        self.assertEqual(response.status_code, 403)

    def test_recruiter_accesses_recruiter_only_endpoint(self):
        self._authenticate_user(self.recruiter)
        response = self.client.get("/api/users/rbac/recruiter-only/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Access granted")

    def test_candidate_denied_recruiter_only_endpoint(self):
        self._authenticate_user(self.candidate)
        response = self.client.get("/api/users/rbac/recruiter-only/")
        self.assertEqual(response.status_code, 403)

    def test_verified_user_accesses_verified_endpoint(self):
        self._authenticate_user(self.verified_candidate)
        response = self.client.get("/api/users/rbac/verified-only/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Access granted")

    def test_unverified_user_denied_verified_endpoint(self):
        self._authenticate_user(self.candidate)
        response = self.client.get("/api/users/rbac/verified-only/")
        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_denied_all_endpoints(self):
        response = self.client.get("/api/users/rbac/candidate-only/")
        self.assertEqual(response.status_code, 401)
        response = self.client.get("/api/users/rbac/recruiter-only/")
        self.assertEqual(response.status_code, 401)
        response = self.client.get("/api/users/rbac/verified-only/")
        self.assertEqual(response.status_code, 401)

    def test_readonly_allows_get(self):
        request = self._create_mock_request(self.candidate, "GET")
        permission = ReadOnly()
        self.assertTrue(permission.has_permission(request, None))

    def test_readonly_blocks_patch(self):
        request = self._create_mock_request(self.candidate, "PATCH")
        permission = ReadOnly()
        self.assertFalse(permission.has_permission(request, None))

    def test_isprofileowner_allows_owner(self):
        permission = IsProfileOwner()
        profile = self.candidate.candidate_profile
        request = self._create_mock_request(self.candidate)
        self.assertTrue(permission.has_object_permission(request, None, profile))

    def test_isprofileowner_denies_non_owner(self):
        permission = IsProfileOwner()
        profile = self.candidate.candidate_profile
        request = self._create_mock_request(self.recruiter)
        self.assertFalse(permission.has_object_permission(request, None, profile))

    def test_candidate_and_verified_works(self):
        request = self._create_mock_request(self.verified_candidate)
        permission = CandidateAndVerified()
        self.assertTrue(permission.has_permission(request, None))

    def test_recruiter_and_verified_works(self):
        request = self._create_mock_request(self.verified_recruiter)
        permission = RecruiterAndVerified()
        self.assertTrue(permission.has_permission(request, None))
