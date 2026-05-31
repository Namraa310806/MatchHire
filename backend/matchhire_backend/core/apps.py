import os

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "matchhire_backend.core"

    def ready(self) -> None:
        if os.environ.get("MATCHHIRE_SKIP_STARTUP_CHECKS") == "1":
            return

        from .startup_checks import run_startup_checks

        run_startup_checks()
