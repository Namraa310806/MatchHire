from .base import *

DEBUG = True

INSTALLED_APPS += ["django_extensions"]

DATABASES["default"]["NAME"] = environ.get("DB_NAME", "matchhire_dev")
