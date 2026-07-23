from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.search"
    verbose_name = "Search"

    def ready(self):
        import apps.search.signals  # noqa: F401

        from apps.search.indexing import register_indexing_signals

        register_indexing_signals()
