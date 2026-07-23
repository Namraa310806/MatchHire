from matchhire_backend.core.env import get_env, validate_production_env
from matchhire_backend.core.logging_config import configure_logging

from .base import *  # noqa: F401,F403,F405


DEBUG = False
ENVIRONMENT = "production"
_production_env = validate_production_env()

SECRET_KEY = _production_env["SECRET_KEY"]
DATABASES["default"] = {  # noqa: F405
    "ENGINE": "django.db.backends.postgresql",
    "NAME": _production_env["DB_NAME"],
    "USER": _production_env["DB_USER"],
    "PASSWORD": _production_env["DB_PASSWORD"],
    "HOST": _production_env["DB_HOST"],
    "PORT": _production_env["DB_PORT"],
}

REDIS_URL = _production_env["REDIS_URL"]
CELERY_BROKER_URL = _production_env["CELERY_BROKER_URL"]
CELERY_RESULT_BACKEND = get_env("CELERY_RESULT_BACKEND", default=REDIS_URL)

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Connection pooling for database
DATABASES["default"]["CONN_MAX_AGE"] = 600  # noqa: F405
DATABASES["default"]["OPTIONS"] = {  # noqa: F405
    "connect_timeout": 10,
}

# Reconfigure logging for production (JSON format)
configure_logging("production")
