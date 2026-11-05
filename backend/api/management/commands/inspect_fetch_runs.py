"""Django management command to inspect FetchRun records."""

from django.core.management.base import BaseCommand

from api.models import FetchRun


class Command(BaseCommand):
    """Management command to inspect recent FetchRun records.

    Usage:
        python manage.py inspect_fetch_runs [--source <source-id>] [--status <status>] [--limit <n>]
    """

    help = "Inspect recent FetchRun records for monitoring and debugging"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--source",
            type=int,
            help="Filter by IngestionSource ID",
        )
        parser.add_argument(
            "--status",
            type=str,
            choices=["pending", "running", "succeeded", "partially_succeeded", "failed"],
            help="Filter by status",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Maximum number of records to show (default: 20)",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        source_id = options["source"]
        status = options["status"]
        limit = options["limit"]

        # Build queryset
        queryset = FetchRun.objects.select_related("source").order_by("-started_at")

        if source_id:
            queryset = queryset.filter(source_id=source_id)

        if status:
            queryset = queryset.filter(status=status)

        queryset = queryset[:limit]

        # Display results
        if not queryset:
            self.stdout.write(self.style.WARNING("No FetchRun records found"))
            return

        self.stdout.write("\n" + "=" * 100)
        self.stdout.write("FETCH RUN INSPECTION")
        self.stdout.write("=" * 100)

        for run in queryset:
            self.stdout.write(f"\nID: {run.id}")
            self.stdout.write(f"Source: {run.source.company.name} - {run.source.name}")
            self.stdout.write(f"Status: {run.status}")
            self.stdout.write(f"Started: {run.started_at}")
            if run.completed_at:
                duration = run.completed_at - run.started_at
                self.stdout.write(f"Completed: {run.completed_at} (duration: {duration})")
            else:
                self.stdout.write("Completed: (not completed)")
            self.stdout.write(f"Jobs Fetched: {run.jobs_fetched}")
            self.stdout.write(f"Jobs Parsed: {run.jobs_parsed}")
            self.stdout.write(f"Jobs Created: {run.jobs_created}")
            self.stdout.write(f"Jobs Updated: {run.jobs_updated}")
            self.stdout.write(f"Jobs Skipped: {run.jobs_skipped}")
            self.stdout.write(f"Jobs Invalid: {run.jobs_invalid}")
            if run.celery_task_id:
                self.stdout.write(f"Celery Task ID: {run.celery_task_id}")
            if run.retry_count > 0:
                self.stdout.write(f"Retry Count: {run.retry_count}")
                if run.last_retry_at:
                    self.stdout.write(f"Last Retry: {run.last_retry_at}")
            if run.error_message:
                self.stdout.write(f"Error: {run.error_message[:200]}{'...' if len(run.error_message) > 200 else ''}")
            self.stdout.write("-" * 100)

        self.stdout.write(f"\nTotal records shown: {len(queryset)}")
