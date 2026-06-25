from celery import shared_task

from apps.matching.services.matching import MatchingService


TASK_RETRY_OPTIONS = {
    "autoretry_for": (Exception,),
    "retry_backoff": True,
    "retry_kwargs": {"max_retries": 3},
}


@shared_task(**TASK_RETRY_OPTIONS)
def recalculate_candidate_matches(candidate_id: str) -> int:
    """Recalculate all cached JobMatch rows for one candidate."""
    return MatchingService.recalculate_for_candidate(candidate_id)


@shared_task(**TASK_RETRY_OPTIONS)
def refresh_candidate_recommendations(candidate_id: str) -> int:
    """Refresh candidate recommendation cache backed by JobMatch rows."""
    return MatchingService.refresh_candidate_recommendations(candidate_id)


@shared_task(**TASK_RETRY_OPTIONS)
def recalculate_job_matches(job_id: str) -> int:
    """Recalculate cached JobMatch rows for every candidate for one job."""
    return MatchingService.recalculate_for_job(job_id)


@shared_task(**TASK_RETRY_OPTIONS)
def recalculate_candidate_profile(candidate_id: str) -> dict:
    """Refresh candidate matches and recommendations after resume changes."""
    matches = MatchingService.recalculate_for_candidate(candidate_id)
    recommendations = MatchingService.refresh_candidate_recommendations(candidate_id)
    return {"matches": matches, "recommendations": recommendations}
