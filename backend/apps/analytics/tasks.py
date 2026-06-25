from celery import shared_task

from apps.analytics.services import AnalyticsRefreshService


TASK_RETRY_OPTIONS = {
    "autoretry_for": (Exception,),
    "retry_backoff": True,
    "retry_kwargs": {"max_retries": 3},
}


@shared_task(**TASK_RETRY_OPTIONS)
def refresh_recruiter_analytics(recruiter_id: str) -> dict:
    """Refresh recruiter dashboard aggregates from source tables."""
    return AnalyticsRefreshService.refresh_recruiter_dashboard(recruiter_id)


@shared_task(**TASK_RETRY_OPTIONS)
def refresh_job_analytics(job_id: str) -> dict:
    """Refresh job-level aggregate calculations from source tables."""
    return AnalyticsRefreshService.refresh_job_analytics(job_id)
