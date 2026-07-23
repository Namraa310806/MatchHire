from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.jobs.models import Job


@receiver(post_save, sender=Job)
def enqueue_job_refresh(sender, instance: Job, created: bool, **kwargs) -> None:
    should_recalculate = (
        instance.status == Job.JobStatus.ACTIVE
        if created
        else instance.async_matching_fields_changed()
    )
    should_refresh_analytics = instance.status == Job.JobStatus.CLOSED and (
        created or instance._async_original_values.get("status") != Job.JobStatus.CLOSED
    )

    if not should_recalculate and not should_refresh_analytics:
        instance.reset_async_original_values()
        return

    def enqueue() -> None:
        from apps.analytics.tasks import refresh_recruiter_analytics
        from apps.matching.tasks import recalculate_job_matches

        if should_recalculate:
            recalculate_job_matches.delay(str(instance.id))
        if should_refresh_analytics:
            refresh_recruiter_analytics.delay(str(instance.recruiter_id))

    transaction.on_commit(enqueue)
    instance.reset_async_original_values()
