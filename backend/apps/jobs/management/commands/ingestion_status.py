"""
Management command to inspect ingestion run status and source health.

Usage:
    python manage.py ingestion_status
    python manage.py ingestion_status --source stripe
    python manage.py ingestion_status --source stripe --health

This command provides operational visibility into ingestion runs
and source health without requiring a full monitoring dashboard.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.jobs.models import IngestionRun
from apps.jobs.scrapers.registry import get_supported_sources


class Command(BaseCommand):
    help = 'Inspect ingestion run status and source health'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            help='Source identifier to filter (e.g., stripe, nexus_technologies)'
        )
        parser.add_argument(
            '--health',
            action='store_true',
            help='Show source health information'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Number of recent runs to show (default: 10)'
        )

    def handle(self, *args, **options):
        source = options.get('source')
        show_health = options.get('health', False)
        limit = options.get('limit', 10)

        # Validate source if provided
        if source:
            supported_sources = get_supported_sources()
            if source not in supported_sources:
                raise CommandError(
                    f"Unknown source: {source}. "
                    f"Available sources: {', '.join(supported_sources)}"
                )

        # Show source health if requested
        if show_health:
            self.show_source_health(source)
            self.stdout.write('')

        # Show recent runs
        self.show_recent_runs(source, limit)

    def show_source_health(self, source=None):
        """Show source health information."""
        self.stdout.write(self.style.SUCCESS('=== Source Health ==='))

        if source:
            # Show health for specific source
            health_info = IngestionRun.get_source_health(source)
            self.display_health(source, health_info)
        else:
            # Show health for all supported sources
            supported_sources = get_supported_sources()
            for src in supported_sources:
                health_info = IngestionRun.get_source_health(src)
                self.display_health(src, health_info)

    def display_health(self, source, health_info):
        """Display health information for a single source."""
        health = health_info['health']
        last_successful = health_info['last_successful_run']
        last_attempt = health_info['last_attempt']
        consecutive_failures = health_info['consecutive_failures']

        # Color-code health status
        if health == 'HEALTHY':
            health_display = self.style.SUCCESS(health)
        elif health == 'DEGRADED':
            health_display = self.style.WARNING(health)
        elif health == 'FAILING':
            health_display = self.style.ERROR(health)
        else:  # UNKNOWN
            health_display = self.style.NOTICE(health)

        self.stdout.write(f"\nSource: {source}")
        self.stdout.write(f"Health: {health_display}")
        self.stdout.write(f"Last successful run: {last_successful or 'Never'}")
        self.stdout.write(f"Last attempt: {last_attempt or 'Never'}")
        self.stdout.write(f"Consecutive failures: {consecutive_failures}")

    def show_recent_runs(self, source=None, limit=10):
        """Show recent ingestion runs."""
        self.stdout.write(self.style.SUCCESS('=== Recent Ingestion Runs ==='))

        # Query runs
        queryset = IngestionRun.objects.all()
        if source:
            queryset = queryset.filter(source=source)

        queryset = queryset.order_by('-started_at')[:limit]

        if not queryset.exists():
            self.stdout.write(self.style.WARNING('No ingestion runs found'))
            return

        # Display runs
        for run in queryset:
            # Color-code status
            if run.status == IngestionRun.RunStatus.SUCCEEDED:
                status_display = self.style.SUCCESS(run.status)
            elif run.status == IngestionRun.RunStatus.PARTIAL:
                status_display = self.style.WARNING(run.status)
            elif run.status == IngestionRun.RunStatus.RETRYING:
                status_display = self.style.WARNING(run.status)
            elif run.status == IngestionRun.RunStatus.FAILED:
                status_display = self.style.ERROR(run.status)
            elif run.status == IngestionRun.RunStatus.RUNNING:
                status_display = self.style.NOTICE(run.status)
            else:  # PENDING
                status_display = self.style.NOTICE(run.status)

            self.stdout.write(f"\nRun ID: {run.id}")
            self.stdout.write(f"Source: {run.source}")
            self.stdout.write(f"Status: {status_display}")
            self.stdout.write(f"Started: {run.started_at or 'N/A'}")
            self.stdout.write(f"Finished: {run.finished_at or 'N/A'}")
            self.stdout.write(f"Task ID: {run.task_id or 'N/A'}")
            self.stdout.write(f"Fetched: {run.fetched_count}")
            self.stdout.write(f"Normalized: {run.normalized_count}")
            self.stdout.write(f"Created: {run.created_count}")
            self.stdout.write(f"Updated: {run.updated_count}")
            self.stdout.write(f"Skipped: {run.skipped_count}")
            self.stdout.write(f"Failed: {run.failed_count}")
            self.stdout.write(f"Retry count: {run.retry_count}")

            if run.error_type:
                self.stdout.write(self.style.ERROR(f"Error type: {run.error_type}"))
            if run.error_message:
                self.stdout.write(self.style.ERROR(f"Error: {run.error_message[:200]}"))
