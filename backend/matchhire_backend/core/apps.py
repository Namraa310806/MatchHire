import os
import sys

from django.apps import AppConfig
from django.core.checks import register, Error


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "matchhire_backend.core"

    def ready(self) -> None:
        if os.environ.get("MATCHHIRE_SKIP_STARTUP_CHECKS") == "1":
            return

        # Initialize Prometheus metrics
        try:
            from .metrics import init_metrics

            init_metrics()
        except Exception:
            # Don't fail startup if metrics initialization fails
            pass

        from .startup_checks import run_startup_checks

        run_startup_checks()


@register()
def check_production_configuration(app_configs, **kwargs):
    """
    Django system check for production configuration validation.
    Runs during Django's check command and on startup.
    Skips during tests to avoid test environment issues.
    """
    # Skip during tests
    if "test" in sys.argv:
        return []

    from .startup_checks import validate_startup_configuration

    errors = []

    try:
        validate_startup_configuration()
    except Exception as e:
        errors.append(
            Error(
                str(e),
                hint="Ensure all required environment variables are set correctly.",
                id="matchhire.E001",
            )
        )

    return errors
