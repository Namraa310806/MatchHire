from .base import *

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "matchhire_fresh_test",
        "USER": environ.get("DB_USER", "matchhire"),
        "PASSWORD": environ.get("DB_PASSWORD", "matchhire"),
        "HOST": environ.get("DB_HOST", "localhost"),
        "PORT": environ.get("DB_PORT", "5432"),
    }
}
