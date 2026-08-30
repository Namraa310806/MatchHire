"""
Management command to register periodic task schedules in django-celery-beat.

This command creates or updates PeriodicTask records for controlled job ingestion.
It is safe to run multiple times - it will not create duplicate schedules.

Usage:
    python manage.py register_schedule

This ensures the database-backed scheduler has the required schedules configured.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from celery.schedules import crontab
import json


class Command(BaseCommand):
    help = 'Register periodic task schedules in django-celery-beat database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Registering Periodic Task Schedules ==='))

        # Register Stripe ingestion schedule
        self.register_stripe_schedule()

        # Register Spotify ingestion schedule
        self.register_spotify_schedule()

        # Register Linear ingestion schedule
        self.register_linear_schedule()

        self.stdout.write(self.style.SUCCESS('Schedule registration complete'))

    def register_stripe_schedule(self):
        """Register Stripe ingestion schedule."""
        self.stdout.write('\nRegistering Stripe ingestion schedule...')

        # Get configured interval from settings
        stripe_hours = settings.INGESTION_SCHEDULE_STRIPE_HOURS
        self.stdout.write(f'  Interval: every {stripe_hours} hours')

        # Create or get CrontabSchedule
        # crontab(minute=0, hour=f'*/{stripe_hours}') means run at minute 0 of every Nth hour
        cron_expr = crontab(minute=0, hour=f'*/{stripe_hours}')
        
        # Parse the crontab schedule components
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
            self.stdout.write(self.style.SUCCESS(f'  Created CrontabSchedule: {crontab_schedule}'))
        else:
            self.stdout.write(f'  Using existing CrontabSchedule: {crontab_schedule}')

        # Get or create PeriodicTask
        task_name = 'stripe-ingestion'
        task_path = 'apps.jobs.tasks.ingest_jobs_task'
        
        periodic_task, created = PeriodicTask.objects.get_or_create(
            name=task_name,
            defaults={
                'task': task_path,
                'crontab': crontab_schedule,
                'args': json.dumps(['stripe']),
                'enabled': True,
                'description': f'Ingest jobs from Stripe every {stripe_hours} hours'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Created PeriodicTask: {task_name}'))
        else:
            # Update existing task to ensure it matches current configuration
            periodic_task.task = task_path
            periodic_task.crontab = crontab_schedule
            periodic_task.args = json.dumps(['stripe'])
            periodic_task.enabled = True
            periodic_task.description = f'Ingest jobs from Stripe every {stripe_hours} hours'
            periodic_task.save()
            self.stdout.write(f'  Updated existing PeriodicTask: {task_name}')

        self.stdout.write(self.style.SUCCESS(f'  Stripe schedule registered successfully'))

    def register_spotify_schedule(self):
        """Register Spotify ingestion schedule."""
        self.stdout.write('\nRegistering Spotify ingestion schedule...')

        # Get configured interval from settings (default to 4 hours if not set)
        spotify_hours = getattr(settings, 'INGESTION_SCHEDULE_SPOTIFY_HOURS', 4)
        self.stdout.write(f'  Interval: every {spotify_hours} hours')

        # Create or get CrontabSchedule
        cron_expr = crontab(minute=0, hour=f'*/{spotify_hours}')
        
        # Parse the crontab schedule components
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
            self.stdout.write(self.style.SUCCESS(f'  Created CrontabSchedule: {crontab_schedule}'))
        else:
            self.stdout.write(f'  Using existing CrontabSchedule: {crontab_schedule}')

        # Get or create PeriodicTask
        task_name = 'spotify-ingestion'
        task_path = 'apps.jobs.tasks.ingest_jobs_task'
        
        periodic_task, created = PeriodicTask.objects.get_or_create(
            name=task_name,
            defaults={
                'task': task_path,
                'crontab': crontab_schedule,
                'args': json.dumps(['spotify']),
                'enabled': True,
                'description': f'Ingest jobs from Spotify every {spotify_hours} hours'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Created PeriodicTask: {task_name}'))
        else:
            # Update existing task to ensure it matches current configuration
            periodic_task.task = task_path
            periodic_task.crontab = crontab_schedule
            periodic_task.args = json.dumps(['spotify'])
            periodic_task.enabled = True
            periodic_task.description = f'Ingest jobs from Spotify every {spotify_hours} hours'
            periodic_task.save()
            self.stdout.write(f'  Updated existing PeriodicTask: {task_name}')

        self.stdout.write(self.style.SUCCESS(f'  Spotify schedule registered successfully'))

    def register_linear_schedule(self):
        """Register Linear ingestion schedule."""
        self.stdout.write('\nRegistering Linear ingestion schedule...')

        # Get configured interval from settings (default to 4 hours if not set)
        linear_hours = getattr(settings, 'INGESTION_SCHEDULE_LINEAR_HOURS', 4)
        self.stdout.write(f'  Interval: every {linear_hours} hours')

        # Create or get CrontabSchedule
        cron_expr = crontab(minute=0, hour=f'*/{linear_hours}')
        
        # Parse the crontab schedule components
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
            self.stdout.write(self.style.SUCCESS(f'  Created CrontabSchedule: {crontab_schedule}'))
        else:
            self.stdout.write(f'  Using existing CrontabSchedule: {crontab_schedule}')

        # Get or create PeriodicTask
        task_name = 'linear-ingestion'
        task_path = 'apps.jobs.tasks.ingest_jobs_task'
        
        periodic_task, created = PeriodicTask.objects.get_or_create(
            name=task_name,
            defaults={
                'task': task_path,
                'crontab': crontab_schedule,
                'args': json.dumps(['linear']),
                'enabled': True,
                'description': f'Ingest jobs from Linear every {linear_hours} hours'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Created PeriodicTask: {task_name}'))
        else:
            # Update existing task to ensure it matches current configuration
            periodic_task.task = task_path
            periodic_task.crontab = crontab_schedule
            periodic_task.args = json.dumps(['linear'])
            periodic_task.enabled = True
            periodic_task.description = f'Ingest jobs from Linear every {linear_hours} hours'
            periodic_task.save()
            self.stdout.write(f'  Updated existing PeriodicTask: {task_name}')

        self.stdout.write(self.style.SUCCESS(f'  Linear schedule registered successfully'))
