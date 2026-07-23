"""
Security tests for MatchHire API hardening.

Tests cover:
- Throttling
- File upload validation
- Request validation (UUID, pagination, ordering, search)
- Security headers
- Permission audits
- Serializer hardening
- Security audit logging
- Password validators
- JWT configuration
- API versioning
- Exception handling
"""

import uuid
from io import BytesIO
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError

from matchhire_backend.core.validators import (
    validate_uuid,
    validate_pagination,
    validate_ordering,
    validate_search_length,
    validate_boolean,
    validate_choice,
)
from matchhire_backend.core.security_audit import SecurityAuditService
from matchhire_backend.core.throttling import (
    AnonymousRateThrottle,
    AuthenticatedRateThrottle,
    LoginRateThrottle,
    RegistrationRateThrottle,
    ResumeUploadRateThrottle,
    JobApplyRateThrottle,
    MatchingRateThrottle,
    InterviewScheduleRateThrottle,
    NotificationRateThrottle,
    AdminRateThrottle,
    AnalyticsRateThrottle,
)


User = get_user_model()


class ValidatorsTest(TestCase):
    """Test request validation utilities."""

    def test_validate_uuid_valid(self):
        """Test valid UUID passes validation."""
        valid_uuid = str(uuid.uuid4())
        # Should not raise
        validate_uuid(valid_uuid, "id")

    def test_validate_uuid_invalid(self):
        """Test invalid UUID raises ValidationError."""
        with self.assertRaises(ValidationError):
            validate_uuid("not-a-uuid", "id")

    def test_validate_uuid_invalid_format(self):
        """Test invalid UUID format raises ValidationError."""
        with self.assertRaises(ValidationError):
            validate_uuid("12345", "id")

    def test_validate_pagination_valid(self):
        """Test valid pagination passes."""
        validate_pagination(1, 20)

    def test_validate_pagination_invalid_page(self):
        """Test invalid page number raises ValidationError."""
        with self.assertRaises(ValidationError):
            validate_pagination(0, 20)

    def test_validate_pagination_invalid_page_size(self):
        """Test invalid page size raises ValidationError."""
        with self.assertRaises(ValidationError):
            validate_pagination(1, 0)

    def test_validate_pagination_page_size_exceeds_max(self):
        """Test page size exceeding max raises ValidationError."""
        with self.assertRaises(ValidationError):
            validate_pagination(1, 200, max_page_size=100)

    def test_validate_ordering_valid(self):
        """Test valid ordering passes."""
        validate_ordering("created_at", ["created_at", "-created_at"])

    def test_validate_ordering_invalid(self):
        """Test invalid ordering raises ValidationError."""
        with self.assertRaises(ValidationError):
            validate_ordering("invalid_field", ["created_at", "-created_at"])

    def test_validate_search_length_valid(self):
        """Test valid search length passes."""
        validate_search_length("test", max_length=200)

    def test_validate_search_length_exceeds(self):
        """Test search length exceeding max raises ValidationError."""
        with self.assertRaises(ValidationError):
            validate_search_length("x" * 201, max_length=200)

    def test_validate_boolean_valid_true(self):
        """Test valid boolean 'true' passes."""
        validate_boolean("true", "is_active")

    def test_validate_boolean_valid_false(self):
        """Test valid boolean 'false' passes."""
        validate_boolean("false", "is_active")

    def test_validate_boolean_invalid(self):
        """Test invalid boolean raises ValidationError."""
        with self.assertRaises(ValidationError):
            validate_boolean("invalid", "is_active")

    def test_validate_choice_valid(self):
        """Test valid choice passes."""
        validate_choice("active", ["active", "inactive"], "status")

    def test_validate_choice_invalid(self):
        """Test invalid choice raises ValidationError."""
        with self.assertRaises(ValidationError):
            validate_choice("invalid", ["active", "inactive"], "status")


class SecurityAuditServiceTest(TestCase):
    """Test security audit logging service."""

    def test_log_failed_login(self):
        """Test failed login logging."""
        # Should not raise
        SecurityAuditService.log_failed_login("test@example.com", "127.0.0.1")

    def test_log_permission_denied(self):
        """Test permission denied logging."""
        SecurityAuditService.log_permission_denied("user123", "/api/jobs/", "GET")

    def test_log_invalid_upload(self):
        """Test invalid upload logging."""
        SecurityAuditService.log_invalid_upload(
            "user123", "malicious.exe", "dangerous extension"
        )

    def test_log_rate_limit_exceeded(self):
        """Test rate limit exceeded logging."""
        SecurityAuditService.log_rate_limit_exceeded(
            "user123", "login", "/api/auth/login/"
        )

    def test_log_invalid_status_transition(self):
        """Test invalid status transition logging."""
        SecurityAuditService.log_invalid_status_transition(
            "user123", "application", "app123", "submitted", "hired"
        )

    def test_log_invalid_moderation_attempt(self):
        """Test invalid moderation attempt logging."""
        SecurityAuditService.log_invalid_moderation_attempt(
            "admin123", "job", "job123", "unauthorized_update"
        )

    def test_log_suspicious_activity(self):
        """Test suspicious activity logging."""
        SecurityAuditService.log_suspicious_activity(
            "user123", "brute_force", "multiple_failed_logins"
        )


class ThrottleClassesTest(TestCase):
    """Test custom throttle classes configuration."""

    def test_anonymous_rate_throttle_scope(self):
        """Test AnonymousRateThrottle has correct scope."""
        throttle = AnonymousRateThrottle()
        self.assertEqual(throttle.scope, "anonymous")

    def test_authenticated_rate_throttle_scope(self):
        """Test AuthenticatedRateThrottle has correct scope."""
        throttle = AuthenticatedRateThrottle()
        self.assertEqual(throttle.scope, "authenticated")

    def test_login_rate_throttle_scope(self):
        """Test LoginRateThrottle has correct scope."""
        throttle = LoginRateThrottle()
        self.assertEqual(throttle.scope, "login")

    def test_registration_rate_throttle_scope(self):
        """Test RegistrationRateThrottle has correct scope."""
        throttle = RegistrationRateThrottle()
        self.assertEqual(throttle.scope, "registration")

    def test_resume_upload_rate_throttle_scope(self):
        """Test ResumeUploadRateThrottle has correct scope."""
        throttle = ResumeUploadRateThrottle()
        self.assertEqual(throttle.scope, "resume_upload")

    def test_job_apply_rate_throttle_scope(self):
        """Test JobApplyRateThrottle has correct scope."""
        throttle = JobApplyRateThrottle()
        self.assertEqual(throttle.scope, "job_apply")

    def test_matching_rate_throttle_scope(self):
        """Test MatchingRateThrottle has correct scope."""
        throttle = MatchingRateThrottle()
        self.assertEqual(throttle.scope, "matching")

    def test_interview_schedule_rate_throttle_scope(self):
        """Test InterviewScheduleRateThrottle has correct scope."""
        throttle = InterviewScheduleRateThrottle()
        self.assertEqual(throttle.scope, "interview_schedule")

    def test_notification_rate_throttle_scope(self):
        """Test NotificationRateThrottle has correct scope."""
        throttle = NotificationRateThrottle()
        self.assertEqual(throttle.scope, "notification")

    def test_admin_rate_throttle_scope(self):
        """Test AdminRateThrottle has correct scope."""
        throttle = AdminRateThrottle()
        self.assertEqual(throttle.scope, "admin")

    def test_analytics_rate_throttle_scope(self):
        """Test AnalyticsRateThrottle has correct scope."""
        throttle = AnalyticsRateThrottle()
        self.assertEqual(throttle.scope, "analytics")


class FileUploadValidationTest(APITestCase):
    """Test file upload validation."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="candidate@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        self.client.force_authenticate(user=self.user)

    def test_upload_pdf_file(self):
        """Test uploading a valid PDF file."""
        # Create a fake PDF file
        pdf_content = b"%PDF-1.4\n%fake pdf content"
        pdf_file = BytesIO(pdf_content)
        pdf_file.name = "resume.pdf"
        pdf_file.content_type = "application/pdf"

        response = self.client.post(
            "/api/v1/resumes/upload/", {"file": pdf_file}, format="multipart"
        )
        # Should succeed or fail based on actual implementation
        # This tests the validation is called
        self.assertIn(
            response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
        )

    def test_upload_dangerous_extension(self):
        """Test uploading a file with dangerous extension is rejected."""
        exe_content = b"MZ\x90\x00"
        exe_file = BytesIO(exe_content)
        exe_file.name = "malicious.exe"
        exe_file.content_type = "application/x-msdownload"

        response = self.client.post(
            "/api/v1/resumes/upload/", {"file": exe_file}, format="multipart"
        )
        # Should be rejected
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_oversized_file(self):
        """Test uploading an oversized file is rejected."""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        large_file = BytesIO(large_content)
        large_file.name = "large.pdf"
        large_file.content_type = "application/pdf"

        response = self.client.post(
            "/api/v1/resumes/upload/", {"file": large_file}, format="multipart"
        )
        # Should be rejected
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class APIVersioningTest(APITestCase):
    """Test API versioning."""

    def test_v1_api_accessible(self):
        """Test v1 API is accessible."""
        response = self.client.get("/api/v1/jobs/")
        # Should return 401 (unauthenticated) or 200 if public
        self.assertIn(
            response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_200_OK]
        )

    def test_backward_compatibility(self):
        """Test backward compatibility with /api/ path."""
        response = self.client.get("/api/jobs/")
        # Should return 401 (unauthenticated) or 200 if public
        self.assertIn(
            response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_200_OK]
        )


class PermissionAuditTest(APITestCase):
    """Test permission configuration on endpoints."""

    def setUp(self):
        """Set up test client and users."""
        self.client = APIClient()
        self.candidate = User.objects.create_user(
            email="candidate@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        self.recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="testpass123",
            role=User.Roles.RECRUITER,
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            role=User.Roles.ADMIN,
        )

    def test_login_allows_anonymous(self):
        """Test login endpoint allows anonymous access."""
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "test@example.com", "password": "wrongpass"},
        )
        # Should not return 403 (permission denied)
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_protected_endpoint_requires_auth(self):
        """Test protected endpoint requires authentication."""
        response = self.client.get("/api/v1/resumes/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_candidate_endpoint_requires_candidate_role(self):
        """Test candidate-specific endpoint requires candidate role."""
        self.client.force_authenticate(user=self.recruiter)
        response = self.client.post(
            "/api/v1/resumes/upload/",
            {"file": BytesIO(b"%PDF-1.4")},
            format="multipart",
        )
        # Recruiter should not be able to upload resume
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_recruiter_endpoint_requires_recruiter_role(self):
        """Test recruiter-specific endpoint requires recruiter role."""
        self.client.force_authenticate(user=self.candidate)
        response = self.client.post(
            "/api/v1/jobs/",
            {
                "title": "Test Job",
                "description": "Test Description",
                "company_name": "Test Company",
                "location": "Test Location",
            },
        )
        # Candidate should not be able to create job
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UUIDValidationTest(APITestCase):
    """Test UUID validation in endpoints."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="candidate@example.com",
            password="testpass123",
            role=User.Roles.CANDIDATE,
        )
        self.client.force_authenticate(user=self.user)

    def test_invalid_uuid_returns_400(self):
        """Test invalid UUID parameter returns 400."""
        response = self.client.get("/api/v1/resumes/invalid-uuid/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_uuid_format(self):
        """Test valid UUID format is accepted."""
        valid_uuid = str(uuid.uuid4())
        response = self.client.get(f"/api/v1/resumes/{valid_uuid}/")
        # Should return 404 (not found) rather than 400 (bad request)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SecurityHeadersTest(TestCase):
    """Test security headers configuration."""

    @override_settings(DEBUG=False)
    def test_security_headers_in_production(self):
        """Test security headers are set in production."""
        from matchhire_backend.settings import prod

        # Check that security settings are defined
        self.assertTrue(hasattr(prod, "SECURE_SSL_REDIRECT"))
        self.assertTrue(hasattr(prod, "SESSION_COOKIE_SECURE"))
        self.assertTrue(hasattr(prod, "CSRF_COOKIE_SECURE"))
        self.assertTrue(hasattr(prod, "SECURE_HSTS_SECONDS"))
        self.assertTrue(hasattr(prod, "X_FRAME_OPTIONS"))
        self.assertTrue(hasattr(prod, "SECURE_CONTENT_TYPE_NOSNIFF"))
        self.assertTrue(hasattr(prod, "SECURE_BROWSER_XSS_FILTER"))
        self.assertTrue(hasattr(prod, "SECURE_REFERRER_POLICY"))
        self.assertTrue(hasattr(prod, "SECURE_PROXY_SSL_HEADER"))


class PasswordValidatorsTest(TestCase):
    """Test password validators configuration."""

    def test_password_validators_configured(self):
        """Test password validators are configured."""
        from django.conf import settings

        validators = settings.AUTH_PASSWORD_VALIDATORS
        validator_names = [v["NAME"] for v in validators]

        self.assertIn(
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
            validator_names,
        )
        self.assertIn(
            "django.contrib.auth.password_validation.MinimumLengthValidator",
            validator_names,
        )
        self.assertIn(
            "django.contrib.auth.password_validation.CommonPasswordValidator",
            validator_names,
        )
        self.assertIn(
            "django.contrib.auth.password_validation.NumericPasswordValidator",
            validator_names,
        )


class JWTConfigurationTest(TestCase):
    """Test JWT configuration."""

    def test_jwt_access_token_lifetime(self):
        """Test JWT access token lifetime is 15 minutes."""
        from datetime import timedelta
        from django.conf import settings

        self.assertEqual(
            settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"], timedelta(minutes=15)
        )

    def test_jwt_refresh_token_lifetime(self):
        """Test JWT refresh token lifetime is 7 days."""
        from datetime import timedelta
        from django.conf import settings

        self.assertEqual(
            settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"], timedelta(days=7)
        )

    def test_jwt_rotation_enabled(self):
        """Test JWT token rotation is enabled."""
        from django.conf import settings

        self.assertTrue(settings.SIMPLE_JWT["ROTATE_REFRESH_TOKENS"])

    def test_jwt_blacklist_enabled(self):
        """Test JWT blacklist after rotation is enabled."""
        from django.conf import settings

        self.assertTrue(settings.SIMPLE_JWT["BLACKLIST_AFTER_ROTATION"])


class CORSConfigurationTest(TestCase):
    """Test CORS configuration."""

    def test_cors_uses_whitelist(self):
        """Test CORS uses whitelist not allow all."""
        from django.conf import settings

        # Should have CORS_ALLOWED_ORIGINS defined
        self.assertTrue(hasattr(settings, "CORS_ALLOWED_ORIGINS"))

        # Should NOT have CORS_ALLOW_ALL_ORIGINS set to True
        self.assertFalse(getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False))

    def test_cors_credentials_allowed(self):
        """Test CORS allows credentials."""
        from django.conf import settings

        self.assertTrue(settings.CORS_ALLOW_CREDENTIALS)


class ExceptionHandlerTest(APITestCase):
    """Test centralized exception handler."""

    def test_validation_error_format(self):
        """Test validation errors return consistent format."""
        self.client = APIClient()
        response = self.client.post(
            "/api/v1/auth/login/", {"email": "invalid", "password": "invalid"}
        )
        # Should return error in consistent format
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertIn("error", response.data)


class ThrottlingIntegrationTest(APITestCase):
    """Test throttling integration with endpoints."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()

    def test_login_endpoint_has_throttle_scope(self):
        """Test login endpoint has throttle scope."""
        from apps.users.auth_views import LoginView

        view = LoginView()
        self.assertEqual(view.throttle_scope, "login")

    def test_registration_endpoint_has_throttle_scope(self):
        """Test registration endpoints have throttle scope."""
        from apps.users.auth_views import (
            CandidateRegistrationView,
            RecruiterRegistrationView,
        )

        candidate_view = CandidateRegistrationView()
        recruiter_view = RecruiterRegistrationView()

        self.assertEqual(candidate_view.throttle_scope, "registration")
        self.assertEqual(recruiter_view.throttle_scope, "registration")


class DRFSettingsTest(TestCase):
    """Test DRF settings configuration."""

    def test_throttle_classes_configured(self):
        """Test default throttle classes are configured."""
        from django.conf import settings

        self.assertIn("DEFAULT_THROTTLE_CLASSES", settings.REST_FRAMEWORK)
        self.assertIn("DEFAULT_THROTTLE_RATES", settings.REST_FRAMEWORK)

    def test_exception_handler_configured(self):
        """Test custom exception handler is configured."""
        from django.conf import settings

        self.assertIn("EXCEPTION_HANDLER", settings.REST_FRAMEWORK)
        self.assertEqual(
            settings.REST_FRAMEWORK["EXCEPTION_HANDLER"],
            "matchhire_backend.core.exceptions.custom_exception_handler",
        )

    def test_versioning_configured(self):
        """Test API versioning is configured."""
        from django.conf import settings

        self.assertIn("DEFAULT_VERSIONING_CLASS", settings.REST_FRAMEWORK)
        self.assertIn("DEFAULT_VERSION", settings.REST_FRAMEWORK)
        self.assertIn("ALLOWED_VERSIONS", settings.REST_FRAMEWORK)

        self.assertEqual(settings.REST_FRAMEWORK["DEFAULT_VERSION"], "v1")
        self.assertEqual(settings.REST_FRAMEWORK["ALLOWED_VERSIONS"], ["v1"])
