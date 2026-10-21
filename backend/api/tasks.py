from celery import shared_task


@shared_task(name="ping", queue="fetch_queue")
def ping():
    """Trivial task to verify Celery task execution."""
    return "pong"
