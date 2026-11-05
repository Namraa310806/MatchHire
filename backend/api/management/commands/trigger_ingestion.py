"""Django management command to trigger ingestion for a source."""

from django.core.management.base import BaseCommand

from api.models import IngestionSource


class Command(BaseCommand):
    """Management command to trigger ingestion for a source via Celery.

    Usage:
        python manage.py trigger_ingestion --source <source-id>
    """

    help = "Trigger ingestion for a source via Celery task"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--source",
            type=int,
            required=True,
            help="IngestionSource ID to trigger ingestion for",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        source_id = options["source"]

        try:
            source = IngestionSource.objects.get(id=source_id)
        except IngestionSource.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Source {source_id} does not exist"))
            return

        self.stdout.write(f"Triggering ingestion for: {source.company.name} - {source.name}")

        if not source.is_active:
            self.stderr.write(self.style.WARNING(f"Source {source_id} is inactive"))
            return

        if not source.scraper_class:
            self.stderr.write(self.style.ERROR(f"Source {source_id} has no scraper_class"))
            return

        # Import task here to avoid circular dependency
        from api.tasks import ingest_source_task

        # Trigger task asynchronously
        result = ingest_source_task.delay(source_id)

        self.stdout.write("Task triggered successfully")
        self.stdout.write(f"Celery Task ID: {result.id}")
        self.stdout.write("Use 'inspect_fetch_runs' to monitor progress")
