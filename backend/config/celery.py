import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("matchhire")

app.config_from_object("django.conf:settings", namespace="CELERY")

# Explicitly discover tasks from api app
app.autodiscover_tasks(["api"])

# Use static schedule by default
# In production, use django-celery-beat's database scheduler for dynamic scheduling
try:
    from config.celery_schedule import STATIC_SCHEDULE

    app.conf.beat_schedule = STATIC_SCHEDULE
except Exception:
    app.conf.beat_schedule = {}


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
