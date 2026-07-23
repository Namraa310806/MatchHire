from django.apps import AppConfig


class ApplicationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.applications"

    def ready(self) -> None:
        from . import signals  # noqa: F401
