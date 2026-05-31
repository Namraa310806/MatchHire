from typing import Any

from decouple import config
from django.core.exceptions import ImproperlyConfigured


PRODUCTION_REQUIRED_ENV_VARS = (
    "SECRET_KEY",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "DB_HOST",
    "DB_PORT",
    "REDIS_URL",
    "CELERY_BROKER_URL",
)


def get_env(key: str, default: Any = None, cast: Any = None) -> Any:
    if cast is None:
        return config(key, default=default)
    return config(key, default=default, cast=cast)


def get_required_env(key: str, cast: Any = None) -> Any:
    value = get_env(key, default=None, cast=cast)
    if value in (None, ""):
        raise ImproperlyConfigured(f"Missing required environment variable: {key}")
    return value


def validate_production_env() -> dict[str, Any]:
    missing = [key for key in PRODUCTION_REQUIRED_ENV_VARS if get_env(key, default="") in (None, "")]
    if missing:
        raise ImproperlyConfigured(
            "Missing required production environment variables: " + ", ".join(missing)
        )

    return {key: get_required_env(key) for key in PRODUCTION_REQUIRED_ENV_VARS}
