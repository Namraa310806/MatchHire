from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.applications.models import Application, ApplicationStatusHistory


@receiver(post_save, sender=Application)
def enqueue_application_submitted(
    sender, instance: Application, created: bool, **kwargs
) -> None:
    if not created:
        return

    def enqueue() -> None:
        from apps.analytics.tasks import refresh_recruiter_analytics
        from apps.notifications.tasks import notify_application_submitted

        notify_application_submitted.delay(str(instance.id))
        refresh_recruiter_analytics.delay(str(instance.job.recruiter_id))

    transaction.on_commit(enqueue)


@receiver(post_save, sender=ApplicationStatusHistory)
def enqueue_application_status_changed(
    sender, instance: ApplicationStatusHistory, created: bool, **kwargs
) -> None:
    if not created:
        return

    def enqueue() -> None:
        from apps.analytics.tasks import refresh_recruiter_analytics
        from apps.notifications.tasks import notify_application_status_changed

        notify_application_status_changed.delay(str(instance.id))
        refresh_recruiter_analytics.delay(str(instance.application.job.recruiter_id))

    transaction.on_commit(enqueue)
