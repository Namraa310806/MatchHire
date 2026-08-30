"""
Management command to test Celery Beat scheduling with a short interval.

This command creates a temporary test schedule with a 1-minute interval
to verify the Beat -> Redis -> Worker -> IngestionRun flow works.

Usage:
    python manage.py test_schedule

After testing, remove the test schedule:
    python manage.py remove_test_schedule

This is for verification only - do not use in production.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from celery.schedules import crontab
import json


class Command(BaseCommand):
    help = 'Create a temporary test schedule for Celery Beat verification'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Creating Test Schedule ==='))

        # Create a 1-minute crontab schedule for testing
        cron_expr = crontab(minute='*')  # Every minute
        
        minute = str(cron_expr._orig_minute)
        hour = str(cron_expr._orig_hour)
        day_of_week = str(cron_expr._orig_day_of_week)
        day_of_month = str(cron_expr._orig_day_of_month)
        month_of_year = str(cron_expr._orig_month_of_year)

        # Get or create CrontabSchedule
        crontab_schedule, created = CrontabSchedule.objects.get_or_create(
            minute=minute,
            hour=hour,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            month_of_year=month_of_year,
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created test CrontabSchedule: {crontab_schedule}'))
        else:
            self.stdout.write(f'Using existing test CrontabSchedule: {crontab_schedule}')

        # Create test PeriodicTask
        task_name = 'test-stripe-ingestion'
        task_path = 'apps.jobs.tasks.ingest_jobs_task'
        
        periodic_task, created = PeriodicTask.objects.get_or_create(
            name=task_name,
            defaults={
                'task': task_path,
                'crontab': crontab_schedule,
                'args': json.dumps(['stripe']),
                'enabled': True,
                'description': 'TEST: Stripe ingestion every minute (for verification only)'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created test PeriodicTask: {task_name}'))
        else:
            periodic_task.enabled = True
            periodic_task.save()
            self.stdout.write(f'Enabled existing test PeriodicTask: {task_name}')

        self.stdout.write(self.style.SUCCESS('\nTest schedule created successfully'))
        self.stdout.write(self.style.WARNING('To remove the test schedule, run: python manage.py remove_test_schedule'))
        self.stdout.write(self.style.WARNING('Start Celery Beat and worker to verify the flow'))
