from os import environ

ENV = environ.get("DJANGO_SETTINGS_MODULE", "config.settings.development")

if ENV == "config.settings.production":
    from .production import *
elif ENV == "config.settings.test":
    from .test import *
else:
    from .development import *
