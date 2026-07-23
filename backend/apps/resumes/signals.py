from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.resumes.models import ResumeVersion, StructuredResume


@receiver(post_save, sender=ResumeVersion)
def enqueue_resume_version_refresh(sender, instance: ResumeVersion, **kwargs) -> None:
    if not instance.is_current:
        return

    def enqueue() -> None:
        from apps.matching.tasks import recalculate_candidate_profile

        recalculate_candidate_profile.delay(str(instance.resume.user_id))

    transaction.on_commit(enqueue)


@receiver(post_save, sender=StructuredResume)
def enqueue_structured_resume_refresh(
    sender, instance: StructuredResume, **kwargs
) -> None:
    if not instance.resume_version.is_current:
        return

    def enqueue() -> None:
        from apps.matching.tasks import recalculate_candidate_profile

        recalculate_candidate_profile.delay(str(instance.resume_version.resume.user_id))

    transaction.on_commit(enqueue)
