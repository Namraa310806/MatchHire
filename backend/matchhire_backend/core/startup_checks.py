import logging
import sys

import redis
from decouple import Csv
from django.core.exceptions import ImproperlyConfigured
from django.db import connections

from .env import get_env, validate_production_env


logger = logging.getLogger(__name__)

STARTUP_REQUIRED_ENV_VARS = (
    "SECRET_KEY",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "DB_HOST",
    "DB_PORT",
    "REDIS_URL",
    "CELERY_BROKER_URL",
)


def check_required_environment() -> list[str]:
    missing = [
        key
        for key in STARTUP_REQUIRED_ENV_VARS
        if get_env(key, default="") in (None, "")
    ]
    if missing:
        logger.warning("Missing environment variables: %s", ", ".join(missing))
    return missing


def check_database_connection() -> bool:
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception as exc:  # pragma: no cover - startup warning path
        logger.warning("Database connectivity check failed: %s", exc)
        return False


def check_redis_connection() -> bool:
    redis_url = get_env("REDIS_URL", default="redis://redis:6379/0")
    try:
        client = redis.Redis.from_url(
            redis_url, socket_connect_timeout=2, socket_timeout=2
        )
        return bool(client.ping())
    except Exception as exc:  # pragma: no cover - startup warning path
        logger.warning("Redis connectivity check failed: %s", exc)
        return False


def get_dependency_status() -> dict[str, str]:
    return {
        "database": "connected" if check_database_connection() else "disconnected",
        "redis": "connected" if check_redis_connection() else "disconnected",
    }


def is_running_management_command() -> bool:
    """Check if currently running a Django management command."""
    return len(sys.argv) > 1 and "manage.py" in sys.argv[0]


def validate_startup_configuration() -> None:
    """
    Validate critical configuration on startup.

    Raises ImproperlyConfigured if critical configuration is missing.
    This should be called in Django's __init__.py or settings module.
    """
    errors = []

    # Check SECRET_KEY
    secret_key = get_env("SECRET_KEY", default="")
    if not secret_key or secret_key == "change-me":
        errors.append("SECRET_KEY is not set or is using default value")

    # Check DEBUG configuration
    debug = get_env("DEBUG", default=False, cast=bool)
    settings_module = get_env("DJANGO_SETTINGS_MODULE", default="")
    if settings_module.endswith(".prod") and debug:
        errors.append("DEBUG=True is not allowed in production")

    # Check ALLOWED_HOSTS in production
    if settings_module.endswith(".prod"):
        allowed_hosts = get_env("ALLOWED_HOSTS", default="", cast=Csv())
        if not allowed_hosts or allowed_hosts == ["localhost", "127.0.0.1"]:
            errors.append("ALLOWED_HOSTS is not properly configured for production")

    # Check database configuration
    required_db_vars = ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"]
    for var in required_db_vars:
        if not get_env(var, default=""):
            errors.append(f"{var} is not set")

    if errors:
        raise ImproperlyConfigured(
            "Startup configuration validation failed:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )


def run_startup_checks() -> None:
    # Skip connectivity checks during management commands
    if is_running_management_command():
        logger.info("Skipping connectivity checks during management command execution")
        check_required_environment()
        return

    check_required_environment()
    if get_env("DJANGO_SETTINGS_MODULE", default="").endswith(".prod"):
        try:
            validate_production_env()
        except Exception as exc:  # pragma: no cover - startup warning path
            logger.warning("Production environment validation failed: %s", exc)
    check_database_connection()
    check_redis_connection()
