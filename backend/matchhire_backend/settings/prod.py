from django.core.exceptions import ImproperlyConfigured

from decouple import config

from .base import *  # noqa: F401,F403


DEBUG = False

SECRET_KEY = config("SECRET_KEY", default="")
DB_PASSWORD = config("DB_PASSWORD", default="")

if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY must be set for production settings.")

if not DB_PASSWORD:
    raise ImproperlyConfigured("DB_PASSWORD must be set for production settings.")

DATABASES["default"]["PASSWORD"] = DB_PASSWORD
