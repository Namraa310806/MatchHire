from .base import *

DEBUG = False

# Use SQLite for faster test execution (Phase 0 decision)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Celery test mode - use eager mode for synchronous task execution in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Use local-memory cache in tests so Redis is not required
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Disable rate limiting in tests (throttle state would leak across tests)
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "resume_upload": "10000/hour",
    "auth_token": "10000/minute",
    "github_sync": "10000/hour",
}

# Silence logging during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["null"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
