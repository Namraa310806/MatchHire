from django.apps import AppConfig


class ResumesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.resumes"

    def ready(self) -> None:
        from . import signals  # noqa: F401
