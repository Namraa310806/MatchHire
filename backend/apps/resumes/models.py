import uuid

from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.users.models import User


def resume_upload_path(instance, filename):
    """Generate upload path for resume files: media/resumes/<user_id>/<unique_filename>"""
    return f"resumes/{instance.user_id}/{instance.stored_filename}"


class Resume(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="resumes",
    )
    original_filename = models.CharField(max_length=255)
    stored_filename = models.CharField(max_length=255, unique=True)
    file = models.FileField(upload_to=resume_upload_path)
    file_size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=False)

    class Meta:
        db_table = "resumes"
        verbose_name = "resume"
        verbose_name_plural = "resumes"
        ordering = ["-uploaded_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_active=True),
                name="unique_active_resume_per_user",
                violation_error_message="A user can only have one active resume at a time.",
            )
        ]

    def __str__(self) -> str:
        return f"Resume<{self.user.email}>"
