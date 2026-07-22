from datetime import timedelta
from pathlib import Path

from decouple import Csv

from matchhire_backend.core.env import get_env
from matchhire_backend.core.logging_config import configure_logging
from matchhire_backend.core.sentry_config import init_sentry


BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = get_env("SECRET_KEY", default="change-me")
DEBUG = get_env("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = get_env("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# Use SQLite for tests
import sys
TESTING = 'test' in sys.argv

if TESTING:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": get_env("DB_NAME", default="matchhire"),
            "USER": get_env("DB_USER", default="matchhire"),
            "PASSWORD": get_env("DB_PASSWORD", default="matchhire"),
            "HOST": get_env("DB_HOST", default="db"),
            "PORT": get_env("DB_PORT", default="5432"),
        }
    }

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "matchhire_backend.core.apps.CoreConfig",
    "apps.users.apps.UsersConfig",
    "apps.jobs.apps.JobsConfig",
    "apps.matching.apps.MatchingConfig",
    "apps.resumes.apps.ResumesConfig",
    "apps.applications.apps.ApplicationsConfig",
    "apps.interviews.apps.InterviewsConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.analytics.apps.AnalyticsConfig",
    "apps.admin.apps.AdminConfig",
]

AUTH_USER_MODEL = "users.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "matchhire_backend.core.middleware.RequestIDMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "matchhire_backend.core.metrics_middleware.PrometheusMetricsMiddleware",
]

ROOT_URLCONF = "matchhire_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "matchhire_backend.wsgi.application"
ASGI_APPLICATION = "matchhire_backend.asgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.users.authentication.CookieJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": (
        "matchhire_backend.core.throttling.AuthenticatedRateThrottle",
    ) if not TESTING else (),
    "DEFAULT_THROTTLE_RATES": {
        "anonymous": "100/day",
        "authenticated": "1000/day",
        "login": "10/hour",
        "registration": "5/hour",
        "resume_upload": "30/hour",
        "resume_parsing": "30/hour",
        "structured_extraction": "30/hour",
        "job_apply": "100/hour",
        "matching": "100/hour",
        "interview_schedule": "50/hour",
        "notification": "500/hour",
        "admin": "200/hour",
        "analytics": "100/hour",
    },
    "EXCEPTION_HANDLER": "matchhire_backend.core.exceptions.custom_exception_handler",
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1"],
    "VERSION_PARAM": "version",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

JWT_ACCESS_COOKIE_NAME = "access_token"
JWT_REFRESH_COOKIE_NAME = "refresh_token"
JWT_COOKIE_SAMESITE = "Lax"
JWT_COOKIE_SECURE = not DEBUG

CORS_ALLOWED_ORIGINS = get_env(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://localhost:5173",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

REDIS_URL = get_env("REDIS_URL", default="redis://redis:6379/0")
CELERY_BROKER_URL = get_env("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = get_env("CELERY_RESULT_BACKEND", default=REDIS_URL)

# drf-spectacular configuration
SPECTACULAR_SETTINGS = {
    "TITLE": "MatchHire API",
    "DESCRIPTION": "Backend API for MatchHire recruitment platform.",
    "VERSION": "v1",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "COMPONENT_NO_READ_ONLY_REQUIRED": True,
    "ENUM_NAME_OVERRIDES": {
        "JobStatus": "apps.jobs.models.Job.JobStatus",
        "ApplicationStatus": "apps.applications.models.Application.ApplicationStatus",
        "InterviewStatus": "apps.interviews.models.Interview.InterviewStatus",
        "EmploymentType": "apps.jobs.models.Job.EmploymentType",
        "ExperienceLevel": "apps.jobs.models.Job.ExperienceLevel",
        "NotificationType": "apps.notifications.models.Notification.NotificationType",
        "UserRole": "apps.users.models.User.Roles",
    },
    "TAGS": [
        {"name": "Authentication", "description": "User authentication and authorization endpoints"},
        {"name": "Users", "description": "User management endpoints"},
        {"name": "Profiles", "description": "User profile management endpoints"},
        {"name": "Resumes", "description": "Resume upload, parsing, and management endpoints"},
        {"name": "Jobs", "description": "Job posting and management endpoints"},
        {"name": "Applications", "description": "Job application management endpoints"},
        {"name": "Matching", "description": "AI-powered candidate-job matching endpoints"},
        {"name": "Interviews", "description": "Interview scheduling and management endpoints"},
        {"name": "Notifications", "description": "Notification management endpoints"},
        {"name": "Analytics", "description": "Dashboard and analytics endpoints"},
        {"name": "Admin", "description": "Admin moderation and management endpoints"},
    ],
    "SECURITY": [
        {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    ],
}

# Configure logging based on environment
ENVIRONMENT = get_env("ENVIRONMENT", default="development")
configure_logging(ENVIRONMENT)

# Initialize Sentry for error monitoring
init_sentry()

