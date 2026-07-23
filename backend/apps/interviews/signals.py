from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.interviews.models import Interview, InterviewStatusHistory


@receiver(post_save, sender=Interview)
def enqueue_interview_scheduled(
    sender, instance: Interview, created: bool, **kwargs
) -> None:
    if not created or instance.status != Interview.InterviewStatus.SCHEDULED:
        return

    def enqueue() -> None:
        from apps.notifications.tasks import notify_interview_scheduled

        notify_interview_scheduled.delay(str(instance.id))

    transaction.on_commit(enqueue)


@receiver(post_save, sender=InterviewStatusHistory)
def enqueue_interview_status_changed(
    sender, instance: InterviewStatusHistory, created: bool, **kwargs
) -> None:
    if not created:
        return

    def enqueue() -> None:
        from apps.analytics.tasks import refresh_recruiter_analytics
        from apps.notifications.tasks import (
            notify_interview_completed,
            notify_interview_cancelled,
        )

        if instance.new_status == Interview.InterviewStatus.COMPLETED:
            notify_interview_completed.delay(str(instance.id))
        elif instance.new_status == Interview.InterviewStatus.CANCELLED:
            notify_interview_cancelled.delay(str(instance.id))
        refresh_recruiter_analytics.delay(
            str(instance.interview.application.job.recruiter_id)
        )

    transaction.on_commit(enqueue)
