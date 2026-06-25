from celery import shared_task

from apps.applications.models import Application, ApplicationStatusHistory
from apps.interviews.models import Interview, InterviewStatusHistory
from apps.matching.models import JobMatch
from apps.notifications.services.notification_service import NotificationService


TASK_RETRY_OPTIONS = {
    "autoretry_for": (Exception,),
    "retry_backoff": True,
    "retry_kwargs": {"max_retries": 3},
}


@shared_task(**TASK_RETRY_OPTIONS)
def notify_match_created(job_match_id: str):
    job_match = JobMatch.objects.select_related("candidate", "job").get(id=job_match_id)
    return str(
        NotificationService.notify_match_created(
            candidate=job_match.candidate,
            job_id=str(job_match.job_id),
            match_score=float(job_match.match_score),
            job_match_id=str(job_match.id),
        ).id
    )


@shared_task(**TASK_RETRY_OPTIONS)
def notify_application_submitted(application_id: str):
    application = Application.objects.select_related("job__recruiter", "candidate").get(id=application_id)
    return str(
        NotificationService.notify_application_submitted(
            recruiter=application.job.recruiter,
            application_id=str(application.id),
            job_id=str(application.job_id),
            candidate_id=str(application.candidate_id),
        ).id
    )


@shared_task(**TASK_RETRY_OPTIONS)
def notify_application_status_changed(history_id: str):
    history = ApplicationStatusHistory.objects.select_related("application__candidate").get(id=history_id)
    return str(
        NotificationService.notify_application_status_changed(
            candidate=history.application.candidate,
            application_id=str(history.application_id),
            old_status=history.old_status,
            new_status=history.new_status,
        ).id
    )


@shared_task(**TASK_RETRY_OPTIONS)
def notify_interview_scheduled(interview_id: str):
    interview = Interview.objects.select_related("application__candidate").get(id=interview_id)
    return str(
        NotificationService.notify_interview_scheduled(
            candidate=interview.application.candidate,
            interview_id=str(interview.id),
            application_id=str(interview.application_id),
        ).id
    )


@shared_task(**TASK_RETRY_OPTIONS)
def notify_interview_completed(history_id: str):
    history = InterviewStatusHistory.objects.select_related("interview__application__candidate").get(id=history_id)
    return str(
        NotificationService.notify_interview_completed(
            candidate=history.interview.application.candidate,
            interview_id=str(history.interview_id),
            application_id=str(history.interview.application_id),
        ).id
    )


@shared_task(**TASK_RETRY_OPTIONS)
def notify_interview_cancelled(history_id: str):
    history = InterviewStatusHistory.objects.select_related("interview__application__candidate").get(id=history_id)
    return str(
        NotificationService.notify_interview_cancelled(
            candidate=history.interview.application.candidate,
            interview_id=str(history.interview_id),
            application_id=str(history.interview.application_id),
        ).id
    )
