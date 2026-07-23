"""
Structured logging configuration for MatchHire backend.

Provides JSON-formatted logging suitable for containerized deployments
with correlation IDs, user context, and structured fields.
"""

import logging
import logging.config
import sys
from datetime import datetime
from typing import Any

from pythonjsonlogger import jsonlogger

from matchhire_backend.core.env import get_env


class JsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter with additional context fields.

    Adds standard fields for observability:
    - timestamp
    - level
    - logger name
    - message
    - request_id (correlation ID)
    - user_id (when available)
    - service
    - environment
    - module
    - pathname
    - lineno
    """

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        log_record["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Add standard fields
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["service"] = "matchhire-backend"
        log_record["environment"] = get_env("ENVIRONMENT", default="development")

        # Add request_id if available (from middleware)
        if hasattr(record, "request_id") and record.request_id:
            log_record["request_id"] = record.request_id

        # Add user_id if available (from middleware or context)
        if hasattr(record, "user_id") and record.user_id:
            log_record["user_id"] = record.user_id

        # Add module/function context
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["process"] = record.process
        log_record["thread"] = record.thread


class ContextFilter(logging.Filter):
    """
    Filter to inject additional context into log records.

    This filter adds user_id and organization_id to log records
    when available from the request context.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        # Try to get user_id from thread-local storage (set by middleware)
        if hasattr(self, "user_id") and self.user_id:
            record.user_id = self.user_id
        if hasattr(self, "organization_id") and self.organization_id:
            record.organization_id = self.organization_id
        return True


def get_logging_config(environment: str = "production") -> dict[str, Any]:
    """
    Get logging configuration based on environment.

    Args:
        environment: Environment name (development, production, test)

    Returns:
        Logging configuration dictionary
    """
    is_production = environment == "production"
    is_development = environment == "development"

    if is_production:
        # Production: JSON logging to stdout
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "matchhire_backend.core.logging_config.JsonFormatter",
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                },
            },
            "filters": {
                "context": {
                    "()": "matchhire_backend.core.logging_config.ContextFilter",
                },
                "request_id": {
                    "()": "matchhire_backend.core.middleware.RequestIDFilter",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": sys.stdout,
                    "filters": ["context", "request_id"],
                },
            },
            "root": {
                "handlers": ["console"],
                "level": "INFO",
            },
            "loggers": {
                "django": {
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": False,
                },
                "django.request": {
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": False,
                },
                "django.db.backends": {
                    "handlers": ["console"],
                    "level": "WARNING",
                    "propagate": False,
                },
                "django.security": {
                    "handlers": ["console"],
                    "level": "WARNING",
                    "propagate": False,
                },
                "matchhire": {
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": False,
                },
                "celery": {
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": False,
                },
                "celery.task": {
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        }
    elif is_development:
        # Development: Human-readable logging with colors
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "verbose": {
                    "format": "{levelname} {asctime} {module} {request_id} {message}",
                    "style": "{",
                },
                "simple": {
                    "format": "{levelname} {message}",
                    "style": "{",
                },
            },
            "filters": {
                "request_id": {
                    "()": "matchhire_backend.core.middleware.RequestIDFilter",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "verbose",
                    "filters": ["request_id"],
                },
            },
            "root": {
                "handlers": ["console"],
                "level": "DEBUG",
            },
            "loggers": {
                "django": {
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": True,
                },
                "django.request": {
                    "handlers": ["console"],
                    "level": "DEBUG",
                    "propagate": False,
                },
                "django.db.backends": {
                    "handlers": ["console"],
                    "level": "DEBUG",
                    "propagate": False,
                },
                "matchhire": {
                    "handlers": ["console"],
                    "level": "DEBUG",
                    "propagate": True,
                },
                "celery": {
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
        }
    else:
        # Test: Minimal logging
        return {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "simple": {
                    "format": "{levelname} {message}",
                    "style": "{",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "simple",
                },
            },
            "root": {
                "handlers": ["console"],
                "level": "WARNING",
            },
        }


def configure_logging(environment: str = "production") -> None:
    """
    Configure logging for the application.

    Args:
        environment: Environment name (development, production, test)
    """
    config = get_logging_config(environment)
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
