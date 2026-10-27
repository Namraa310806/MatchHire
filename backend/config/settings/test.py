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
