import uuid

from django.db import models

from apps.users.models import User


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        APPLICATION_SUBMITTED = "application_submitted", "Application Submitted"
        APPLICATION_STATUS_CHANGED = (
            "application_status_changed",
            "Application Status Changed",
        )
        INTERVIEW_SCHEDULED = "interview_scheduled", "Interview Scheduled"
        INTERVIEW_COMPLETED = "interview_completed", "Interview Completed"
        INTERVIEW_CANCELLED = "interview_cancelled", "Interview Cancelled"
        MATCH_CREATED = "match_created", "Match Created"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=32,
        choices=NotificationType.choices,
    )
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient"]),
            models.Index(fields=["is_read"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Notification<{self.title} for {self.recipient.email}>"
