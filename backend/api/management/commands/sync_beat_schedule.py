"""Django management command to sync IngestionSource to Celery Beat schedule.

Note: django-celery-beat lacks type stubs, so mypy analysis is skipped for this file.
"""

# mypy: ignore-errors
from django.core.management.base import BaseCommand
from django_celery_beat.models import (
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    PeriodicTasks,
)

from api.models import IngestionSource


class Command(BaseCommand):
    """Management command to sync active IngestionSource records to Celery Beat schedule.

    Usage:
        python manage.py sync_beat_schedule [--dry-run]
    """

    help = "Sync active IngestionSource records to Celery Beat PeriodicTask table"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without applying them",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        dry_run = options["dry_run"]

        self.stdout.write("Syncing IngestionSource to Celery Beat schedule...")

        # Get active sources
        active_sources = IngestionSource.objects.filter(is_active=True, scraper_class__isnull=False)

        if not active_sources:
            self.stdout.write(self.style.WARNING("No active sources with scraper_class found"))
            return

        # Ensure PeriodicTasks table exists
        PeriodicTasks.objects.get_or_create(ident="beat_schedule")

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for source in active_sources:
            if not source.fetch_interval_hours or source.fetch_interval_hours < 1:
                self.stdout.write(f"Skipping {source.name}: invalid fetch_interval_hours")
                skipped_count += 1
                continue

            task_name = f"ingest_source_{source.id}_{source.name.replace(' ', '_').lower()}"

            # Determine schedule type and value
            interval_hours = source.fetch_interval_hours
            schedule, created = self._get_or_create_schedule(interval_hours, dry_run)

            if created and not dry_run:
                self.stdout.write(f"Created schedule for {source.name} ({interval_hours}h)")
            elif not dry_run:
                self.stdout.write(f"Using existing schedule for {source.name} ({interval_hours}h)")

            # Create or update PeriodicTask
            task, task_created = PeriodicTask.objects.get_or_create(
                name=task_name,
                defaults={
                    "task": "api.tasks.ingest_source_task",
                    "args": f"[{source.id}]",
                    "schedule": schedule,
                    "enabled": True,
                },
            )

            if task_created:
                created_count += 1
                self.stdout.write(f"  Created PeriodicTask: {task_name}")
            else:
                # Update existing task
                task.schedule = schedule
                task.args = f"[{source.id}]"
                task.enabled = True
                task.save()
                updated_count += 1
                self.stdout.write(f"  Updated PeriodicTask: {task_name}")

        # Disable tasks for inactive sources
        active_task_names = [
            f"ingest_source_{s.id}_{s.name.replace(' ', '_').lower()}"
            for s in active_sources
        ]
        disabled_count = PeriodicTask.objects.filter(
            name__startswith="ingest_source_"
        ).exclude(name__in=active_task_names).update(enabled=False)

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("SYNC SUMMARY")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Active sources processed: {len(active_sources)}")
        self.stdout.write(f"PeriodicTasks created: {created_count}")
        self.stdout.write(f"PeriodicTasks updated: {updated_count}")
        self.stdout.write(f"PeriodicTasks disabled: {disabled_count}")
        self.stdout.write(f"Skipped (invalid interval): {skipped_count}")

        if dry_run:
            self.stdout.write("\nDRY-RUN MODE - No changes applied")

    def _get_or_create_schedule(self, interval_hours: int, dry_run: bool):
        """Get or create a CrontabSchedule or IntervalSchedule based on interval.

        Args:
            interval_hours: The fetch interval in hours
            dry_run: If True, don't create new schedules

        Returns:
            (schedule, created) tuple
        """
        # Standard intervals use crontab
        if interval_hours == 1:
            # Every hour
            schedule, created = CrontabSchedule.objects.get_or_create(
                minute=0,
                hour="*",
                defaults={"crontab": "0 * * * *"},
            )
        elif interval_hours == 6:
            # Every 6 hours
            schedule, created = CrontabSchedule.objects.get_or_create(
                minute=0,
                hour="*/6",
                defaults={"crontab": "0 */6 * * *"},
            )
        elif interval_hours == 12:
            # Every 12 hours
            schedule, created = CrontabSchedule.objects.get_or_create(
                minute=0,
                hour="*/12",
                defaults={"crontab": "0 */12 * * *"},
            )
        elif interval_hours == 24:
            # Daily at midnight
            schedule, created = CrontabSchedule.objects.get_or_create(
                minute=0,
                hour=0,
                defaults={"crontab": "0 0 * * *"},
            )
        else:
            # Custom interval - use IntervalSchedule
            seconds = interval_hours * 3600
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=seconds,
                period=IntervalSchedule.SECONDS,
            )

        return schedule, created
