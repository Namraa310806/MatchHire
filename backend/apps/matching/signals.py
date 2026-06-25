from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.matching.models import JobMatch


@receiver(post_save, sender=JobMatch)
def enqueue_match_notification(sender, instance: JobMatch, created: bool, **kwargs) -> None:
    if not created:
        return

    def enqueue() -> None:
        from apps.notifications.tasks import notify_match_created

        notify_match_created.delay(str(instance.id))

    transaction.on_commit(enqueue)
