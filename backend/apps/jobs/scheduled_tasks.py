"""
Scheduled ingestion tasks for Celery Beat.

This module is retained for reference but schedules are now registered
via django-celery-beat's database-backed scheduler.

Use the management command to register schedules:
    python manage.py register_schedule

Architecture:
- Celery Beat triggers scheduled tasks from database
- Tasks call the existing ingest_jobs_task
- Overlap prevention is handled by database constraints
- PostgreSQL remains the source of truth

Security:
- Only sources in SOURCE_REGISTRY can be scheduled
- No arbitrary user input is accepted
- Schedules are registered via controlled management command
"""
