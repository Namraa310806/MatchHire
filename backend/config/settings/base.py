"""
Base Django settings for MatchHire.
"""

from datetime import timedelta
from os import environ
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = environ.get(
    "SECRET_KEY", "django-insecure-development-key-change-in-production"
)  # noqa: S105

DEBUG = False

ALLOWED_HOSTS = environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "celery",
    "django_celery_beat",
    "api",
]

# Celery Beat scheduler (use database scheduler for dynamic scheduling)
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": environ.get("DB_NAME", "matchhire"),
        "USER": environ.get("DB_USER", "matchhire"),
        "PASSWORD": environ.get("DB_PASSWORD", "matchhire"),
        "HOST": environ.get("DB_HOST", "localhost"),
        "PORT": environ.get("DB_PORT", "5432"),
    }
}

AUTH_USER_MODEL = "api.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

# File storage: local filesystem by default; S3/R2-compatible when
# AWS_STORAGE_BUCKET_NAME is configured (see docs/RESUME_PROCESSING.md).
MEDIA_ROOT = environ.get("MEDIA_ROOT", str(BASE_DIR / "media"))

STORAGES: dict[str, Any] = {}
if environ.get("AWS_STORAGE_BUCKET_NAME"):
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    AWS_STORAGE_BUCKET_NAME = environ["AWS_STORAGE_BUCKET_NAME"]
    AWS_S3_REGION_NAME = environ.get("AWS_S3_REGION_NAME", "")
    AWS_S3_ENDPOINT_URL = environ.get("AWS_S3_ENDPOINT_URL") or None
    AWS_ACCESS_KEY_ID = environ.get("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = environ.get("AWS_SECRET_ACCESS_KEY", "")
    AWS_QUERYSTRING_AUTH = True
    AWS_S3_FILE_OVERWRITE = False
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {"location": MEDIA_ROOT},
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Redis-backed cache (also used by DRF throttling)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": environ.get("REDIS_CACHE_URL", "redis://localhost:6379/1"),
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "api.authentication.CookieOrBearerJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "resume_upload": environ.get("RESUME_UPLOAD_THROTTLE_RATE", "10/hour"),
        "auth_token": environ.get("AUTH_THROTTLE_RATE", "20/minute"),
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# JWT configuration (Decision 8: 15-minute access, 7-day refresh with rotation)
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# JWT cookie transport for browser clients (Decision 8)
JWT_AUTH_COOKIE = "mh_access"
JWT_REFRESH_COOKIE = "mh_refresh"
JWT_COOKIE_SECURE = environ.get("JWT_COOKIE_SECURE", "false").lower() == "true"
JWT_COOKIE_SAMESITE = environ.get("JWT_COOKIE_SAMESITE", "Lax")
JWT_COOKIE_DOMAIN = environ.get("JWT_COOKIE_DOMAIN") or None
JWT_COOKIE_PATH = "/"

# Resume processing settings.
# NOTE: size limit, status TTL, and throttle rate are PROPOSED values pending
# stakeholder approval (see docs/DECISIONS.md, Phase 3B).
RESUME_MAX_UPLOAD_BYTES = int(environ.get("RESUME_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
RESUME_TASK_STATUS_TTL_SECONDS = int(
    environ.get("RESUME_TASK_STATUS_TTL_SECONDS", str(24 * 60 * 60))
)
RESUME_MIN_TEXT_LENGTH = int(environ.get("RESUME_MIN_TEXT_LENGTH", "20"))

# Celery Configuration
CELERY_BROKER_URL = environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# Redis client configuration for distributed locking
REDIS_LOCK_URL = environ.get("REDIS_LOCK_URL", CELERY_BROKER_URL)

# Named queues
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_QUEUES = {
    "fetch_queue": {
        "exchange": "fetch_queue",
        "routing_key": "fetch_queue",
    },
    "parse_queue": {
        "exchange": "parse_queue",
        "routing_key": "parse_queue",
    },
    "match_queue": {
        "exchange": "match_queue",
        "routing_key": "match_queue",
    },
}
