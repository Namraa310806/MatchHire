from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CandidateProfile, RecruiterProfile, User


@receiver(post_save, sender=User)
def create_profile_for_user(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.role == User.Roles.RECRUITER:
        RecruiterProfile.objects.create(user=instance)
    else:
        CandidateProfile.objects.create(user=instance)