from django.db.models import Count, Q

from apps.applications.models import Application
from apps.interviews.models import Interview
from apps.jobs.models import Job


class AnalyticsRefreshService:
    """Service layer for analytics refresh orchestration.

    Analytics are computed from source tables at read time. These refresh
    methods intentionally do not persist rows; they exercise the same aggregate
    queries used by dashboard views so async workflows can warm database/cache
    paths later without changing the data model.
    """

    @classmethod
    def refresh_recruiter_dashboard(cls, recruiter_id: str) -> dict:
        job_metrics = Job.objects.filter(recruiter_id=recruiter_id).aggregate(
            total_jobs=Count("id"),
            active_jobs=Count("id", filter=Q(status=Job.JobStatus.ACTIVE)),
            closed_jobs=Count("id", filter=Q(status=Job.JobStatus.CLOSED)),
        )
        application_metrics = Application.objects.filter(job__recruiter_id=recruiter_id).aggregate(
            total_applications=Count("id"),
            hired_applications=Count("id", filter=Q(status=Application.ApplicationStatus.HIRED)),
        )
        interview_metrics = Interview.objects.filter(application__job__recruiter_id=recruiter_id).aggregate(
            completed_interviews=Count("id", filter=Q(status=Interview.InterviewStatus.COMPLETED)),
            cancelled_interviews=Count("id", filter=Q(status=Interview.InterviewStatus.CANCELLED)),
        )
        return {**job_metrics, **application_metrics, **interview_metrics}

    @classmethod
    def refresh_job_analytics(cls, job_id: str) -> dict:
        application_metrics = Application.objects.filter(job_id=job_id).aggregate(
            total_applications=Count("id"),
            submitted=Count("id", filter=Q(status=Application.ApplicationStatus.SUBMITTED)),
            under_review=Count("id", filter=Q(status=Application.ApplicationStatus.UNDER_REVIEW)),
            shortlisted=Count("id", filter=Q(status=Application.ApplicationStatus.SHORTLISTED)),
            rejected=Count("id", filter=Q(status=Application.ApplicationStatus.REJECTED)),
            hired=Count("id", filter=Q(status=Application.ApplicationStatus.HIRED)),
        )
        total = application_metrics["total_applications"]
        hired = application_metrics["hired"]
        return {**application_metrics, "conversion_rate": (hired / total * 100) if total else 0.0}
