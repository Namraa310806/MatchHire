import logging

import redis
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
    missing = [key for key in STARTUP_REQUIRED_ENV_VARS if get_env(key, default="") in (None, "")]
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
        client = redis.Redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
        return bool(client.ping())
    except Exception as exc:  # pragma: no cover - startup warning path
        logger.warning("Redis connectivity check failed: %s", exc)
        return False


def get_dependency_status() -> dict[str, str]:
    return {
        "database": "connected" if check_database_connection() else "disconnected",
        "redis": "connected" if check_redis_connection() else "disconnected",
    }


def run_startup_checks() -> None:
    check_required_environment()
    if get_env("DJANGO_SETTINGS_MODULE", default="").endswith(".prod"):
        try:
            validate_production_env()
        except Exception as exc:  # pragma: no cover - startup warning path
            logger.warning("Production environment validation failed: %s", exc)
    check_database_connection()
    check_redis_connection()
