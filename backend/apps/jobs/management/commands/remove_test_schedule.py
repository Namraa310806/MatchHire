"""
Management command to remove the temporary test schedule.

Usage:
    python manage.py remove_test_schedule

This removes the test schedule created by test_schedule command.
"""

from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule


class Command(BaseCommand):
    help = 'Remove the temporary test schedule for Celery Beat verification'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Removing Test Schedule ==='))

        task_name = 'test-stripe-ingestion'
        
        try:
            periodic_task = PeriodicTask.objects.get(name=task_name)
            crontab_schedule = periodic_task.crontab
            
            periodic_task.delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted test PeriodicTask: {task_name}'))
            
            # Try to delete the crontab schedule if it's not used by other tasks
            if not PeriodicTask.objects.filter(crontab=crontab_schedule).exists():
                crontab_schedule.delete()
                self.stdout.write(self.style.SUCCESS('Deleted test CrontabSchedule'))
            else:
                self.stdout.write('CrontabSchedule still in use by other tasks, not deleted')
                
            self.stdout.write(self.style.SUCCESS('\nTest schedule removed successfully'))
        except PeriodicTask.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'Test PeriodicTask {task_name} not found'))
