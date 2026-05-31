from decouple import config

from .base import *  # noqa: F401,F403


DEBUG = True
ALLOWED_HOSTS = ["*"]
SECRET_KEY = config("SECRET_KEY", default="django-insecure-dev-only")
