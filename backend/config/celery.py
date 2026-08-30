"""
Celery configuration for MatchHire.

This module configures Celery for asynchronous job ingestion tasks.
Celery uses Redis as the message broker.

Architecture:
- Django starts Celery application
- Celery tasks are defined in apps.jobs.tasks
- Redis is used as the broker (already configured in settings)
- PostgreSQL remains the source of truth for job data
- Celery Beat for periodic scheduled ingestion
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('matchhire')

# Load task modules from all registered Django apps.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in installed apps
app.autodiscover_tasks()

# Load periodic tasks from django-celery-beat
app.conf.beat_scheduler = settings.CELERY_BEAT_SCHEDULER


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery connectivity."""
    print(f'Request: {self.request!r}')
