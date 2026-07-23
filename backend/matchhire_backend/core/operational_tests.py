"""
Operational tests for production readiness infrastructure.

Tests health endpoints, middleware, logging, and startup validation.
"""

import uuid
from unittest.mock import patch, MagicMock

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status

from matchhire_backend.core.middleware import RequestIDMiddleware, RequestIDFilter
from matchhire_backend.core.startup_checks import (
    validate_startup_configuration,
    check_database_connection,
    check_redis_connection,
)


class HealthEndpointTests(TestCase):
    """Test health check endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_health_endpoint_returns_healthy(self):
        """Test /health/ endpoint returns healthy status."""
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "healthy")

    def test_health_live_endpoint_returns_healthy(self):
        """Test /health/live/ endpoint returns healthy status."""
        response = self.client.get("/health/live/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "healthy")

    def test_health_ready_endpoint_returns_healthy(self):
        """Test /health/ready/ endpoint returns healthy status when database and Redis are connected."""
        response = self.client.get("/health/ready/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "healthy")
        self.assertTrue(response.data["database"])
        self.assertTrue(response.data["redis"])

    def test_health_ready_endpoint_returns_unhealthy_on_db_failure(self):
        """Test /health/ready/ endpoint returns 503 when database fails."""
        with patch("matchhire_backend.api.views.connections") as mock_connections:
            mock_connections.__getitem__.return_value.cursor.side_effect = Exception(
                "DB error"
            )
            response = self.client.get("/health/ready/")
            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            self.assertEqual(response.data["status"], "unhealthy")
            self.assertFalse(response.data["database"])

    def test_health_ready_endpoint_returns_unhealthy_on_redis_failure(self):
        """Test /health/ready/ endpoint returns 503 when Redis fails."""
        with patch("matchhire_backend.api.views.redis") as mock_redis:
            mock_redis.Redis.from_url.side_effect = Exception("Redis error")
            response = self.client.get("/health/ready/")
            self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
            self.assertEqual(response.data["status"], "unhealthy")
            self.assertFalse(response.data["redis"])

    def test_health_endpoint_allows_anonymous_access(self):
        """Test health endpoints allow anonymous access without authentication."""
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_endpoint_returns_json(self):
        """Test health endpoints return JSON responses."""
        response = self.client.get("/health/")
        self.assertEqual(response["Content-Type"], "application/json")

    def test_version_endpoint_returns_version_info(self):
        """Test /version/ endpoint returns version information."""
        response = self.client.get("/version/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("version", response.data)
        self.assertIn("commit", response.data)
        self.assertIn("environment", response.data)


class RequestIDMiddlewareTests(TestCase):
    """Test Request ID middleware."""

    def setUp(self):
        self.client = APIClient()
        self.middleware = RequestIDMiddleware(get_response=lambda r: r)

    def test_request_id_generated_when_not_provided(self):
        """Test request ID is generated when not provided by client."""
        request = MagicMock()
        request.META = {}
        request.id = None

        self.middleware.process_request(request)

        self.assertIsNotNone(request.id)
        # Verify it's a valid UUID
        uuid.UUID(request.id)

    def test_request_id_reused_when_provided(self):
        """Test request ID is reused when provided by client."""
        provided_id = str(uuid.uuid4())
        request = MagicMock()
        request.META = {"HTTP_X_REQUEST_ID": provided_id}
        request.id = None

        self.middleware.process_request(request)

        self.assertEqual(request.id, provided_id)

    def test_request_id_invalid_uuid_rejected(self):
        """Test invalid request ID is rejected and new one generated."""
        request = MagicMock()
        request.META = {"HTTP_X_REQUEST_ID": "invalid-uuid"}
        request.id = None

        self.middleware.process_request(request)

        self.assertIsNotNone(request.id)
        self.assertNotEqual(request.id, "invalid-uuid")
        uuid.UUID(request.id)  # Should not raise

    def test_request_id_added_to_response(self):
        """Test request ID is added to response headers."""
        request = MagicMock()
        request.id = "test-request-id"
        response = MagicMock()

        self.middleware.process_response(request, response)

        response.__setitem__.assert_called_once_with("X-Request-ID", "test-request-id")

    def test_request_id_header_in_api_response(self):
        """Test X-Request-ID header is present in API responses."""
        response = self.client.get("/health/")
        self.assertIn("X-Request-ID", response)

    def test_request_id_filter_injects_request_id(self):
        """Test RequestIDFilter injects request_id into log records."""
        log_filter = RequestIDFilter()
        log_filter.request_id = "test-request-id"

        record = MagicMock()
        log_filter.filter(record)

        self.assertEqual(record.request_id, "test-request-id")

    def test_request_id_filter_handles_none(self):
        """Test RequestIDFilter handles None request_id."""
        log_filter = RequestIDFilter()
        log_filter.request_id = None

        record = MagicMock()
        log_filter.filter(record)

        self.assertIsNone(record.request_id)


class StartupValidationTests(TestCase):
    """Test startup configuration validation."""

    @override_settings(DEBUG=True)
    @patch("matchhire_backend.core.startup_checks.get_env")
    def test_startup_validation_passes_with_valid_config(self, mock_get_env):
        """Test startup validation passes with valid configuration."""
        mock_get_env.side_effect = lambda key, default=None, cast=None: {
            "SECRET_KEY": "valid-secret-key",
            "DEBUG": True,
            "DJANGO_SETTINGS_MODULE": "matchhire_backend.settings.dev",
            "DB_NAME": "testdb",
            "DB_USER": "testuser",
            "DB_PASSWORD": "testpass",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "JWT_ACCESS_COOKIE_NAME": "access_token",
            "JWT_REFRESH_COOKIE_NAME": "refresh_token",
            "ALLOWED_HOSTS": "localhost,127.0.0.1",
        }.get(key, default)

        # Should not raise
        validate_startup_configuration()

    @patch("matchhire_backend.core.startup_checks.get_env")
    def test_startup_validation_fails_with_missing_secret_key(self, mock_get_env):
        """Test startup validation fails when SECRET_KEY is missing."""
        mock_get_env.side_effect = lambda key, default=None, cast=None: {
            "SECRET_KEY": "",
            "DEBUG": False,
            "DJANGO_SETTINGS_MODULE": "matchhire_backend.settings.prod",
            "DB_NAME": "testdb",
            "DB_USER": "testuser",
            "DB_PASSWORD": "testpass",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "JWT_ACCESS_COOKIE_NAME": "access_token",
            "JWT_REFRESH_COOKIE_NAME": "refresh_token",
            "ALLOWED_HOSTS": "example.com",
        }.get(key, default)

        with self.assertRaises(ImproperlyConfigured) as context:
            validate_startup_configuration()

        self.assertIn("SECRET_KEY", str(context.exception))

    @patch("matchhire_backend.core.startup_checks.get_env")
    def test_startup_validation_fails_with_default_secret_key(self, mock_get_env):
        """Test startup validation fails when SECRET_KEY is default value."""
        mock_get_env.side_effect = lambda key, default=None, cast=None: {
            "SECRET_KEY": "change-me",
            "DEBUG": False,
            "DJANGO_SETTINGS_MODULE": "matchhire_backend.settings.prod",
            "DB_NAME": "testdb",
            "DB_USER": "testuser",
            "DB_PASSWORD": "testpass",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "JWT_ACCESS_COOKIE_NAME": "access_token",
            "JWT_REFRESH_COOKIE_NAME": "refresh_token",
            "ALLOWED_HOSTS": "example.com",
        }.get(key, default)

        with self.assertRaises(ImproperlyConfigured) as context:
            validate_startup_configuration()

        self.assertIn("SECRET_KEY", str(context.exception))

    @patch("matchhire_backend.core.startup_checks.get_env")
    def test_startup_validation_fails_with_debug_in_production(self, mock_get_env):
        """Test startup validation fails when DEBUG=True in production."""
        mock_get_env.side_effect = lambda key, default=None, cast=None: {
            "SECRET_KEY": "valid-secret-key",
            "DEBUG": True,
            "DJANGO_SETTINGS_MODULE": "matchhire_backend.settings.prod",
            "DB_NAME": "testdb",
            "DB_USER": "testuser",
            "DB_PASSWORD": "testpass",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "JWT_ACCESS_COOKIE_NAME": "access_token",
            "JWT_REFRESH_COOKIE_NAME": "refresh_token",
            "ALLOWED_HOSTS": "example.com",
        }.get(key, default)

        with self.assertRaises(ImproperlyConfigured) as context:
            validate_startup_configuration()

        self.assertIn("DEBUG", str(context.exception))

    @patch("matchhire_backend.core.startup_checks.get_env")
    def test_startup_validation_fails_with_missing_database_config(self, mock_get_env):
        """Test startup validation fails when database config is missing."""
        mock_get_env.side_effect = lambda key, default=None, cast=None: {
            "SECRET_KEY": "valid-secret-key",
            "DEBUG": False,
            "DJANGO_SETTINGS_MODULE": "matchhire_backend.settings.prod",
            "DB_NAME": "",
            "DB_USER": "testuser",
            "DB_PASSWORD": "testpass",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "JWT_ACCESS_COOKIE_NAME": "access_token",
            "JWT_REFRESH_COOKIE_NAME": "refresh_token",
            "ALLOWED_HOSTS": "example.com",
        }.get(key, default)

        with self.assertRaises(ImproperlyConfigured) as context:
            validate_startup_configuration()

        self.assertIn("DB_NAME", str(context.exception))

    @patch("matchhire_backend.core.startup_checks.get_env")
    def test_startup_validation_fails_with_invalid_allowed_hosts(self, mock_get_env):
        """Test startup validation fails when ALLOWED_HOSTS is not configured for production."""
        mock_get_env.side_effect = lambda key, default=None, cast=None: {
            "SECRET_KEY": "valid-secret-key",
            "DEBUG": False,
            "DJANGO_SETTINGS_MODULE": "matchhire_backend.settings.prod",
            "DB_NAME": "testdb",
            "DB_USER": "testuser",
            "DB_PASSWORD": "testpass",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "JWT_ACCESS_COOKIE_NAME": "access_token",
            "JWT_REFRESH_COOKIE_NAME": "refresh_token",
            "ALLOWED_HOSTS": "localhost,127.0.0.1",
        }.get(key, default)

        with self.assertRaises(ImproperlyConfigured) as context:
            validate_startup_configuration()

        self.assertIn("ALLOWED_HOSTS", str(context.exception))


class DatabaseConnectionTests(TestCase):
    """Test database connection checks."""

    def test_database_connection_check_succeeds(self):
        """Test database connection check succeeds when database is available."""
        result = check_database_connection()
        self.assertTrue(result)

    def test_database_connection_check_fails_on_error(self):
        """Test database connection check fails on database error."""
        with patch(
            "matchhire_backend.core.startup_checks.connections"
        ) as mock_connections:
            mock_connections.__getitem__.return_value.cursor.side_effect = Exception(
                "DB error"
            )
            result = check_database_connection()
            self.assertFalse(result)


class RedisConnectionTests(TestCase):
    """Test Redis connection checks."""

    @patch("matchhire_backend.core.startup_checks.redis")
    @patch("matchhire_backend.core.startup_checks.get_env")
    def test_redis_connection_check_succeeds(self, mock_get_env, mock_redis):
        """Test Redis connection check succeeds when Redis is available."""
        mock_get_env.return_value = "redis://localhost:6379/0"
        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis.Redis.from_url.return_value = mock_redis_client

        result = check_redis_connection()
        self.assertTrue(result)

    @patch("matchhire_backend.core.startup_checks.redis")
    @patch("matchhire_backend.core.startup_checks.get_env")
    def test_redis_connection_check_fails_on_error(self, mock_get_env, mock_redis):
        """Test Redis connection check fails on Redis error."""
        mock_get_env.return_value = "redis://localhost:6379/0"
        mock_redis.Redis.from_url.side_effect = Exception("Redis error")

        result = check_redis_connection()
        self.assertFalse(result)


class LoggingConfigurationTests(TestCase):
    """Test logging configuration."""

    @override_settings(
        LOGGING={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "verbose": {
                    "format": "{levelname} {asctime} {module} {message}",
                    "style": "{",
                },
            },
            "handlers": {
                "console": {
                    "level": "INFO",
                    "class": "logging.StreamHandler",
                    "formatter": "verbose",
                },
            },
            "loggers": {
                "matchhire": {
                    "handlers": ["console"],
                    "level": "INFO",
                },
            },
        }
    )
    def test_logging_configuration_loads(self):
        """Test logging configuration loads without errors."""
        from django.conf import settings

        self.assertIsNotNone(settings.LOGGING)
        self.assertEqual(settings.LOGGING["version"], 1)

    def test_logging_has_required_handlers(self):
        """Test logging has required handlers configured."""
        from django.conf import settings

        self.assertIn("LOGGING", dir(settings))
        if hasattr(settings, "LOGGING"):
            handlers = settings.LOGGING.get("handlers", {})
            # Check for at least console handler
            self.assertIn("console", handlers)
