import uuid

from django.db import models

from apps.users.models import User


class ModerationLog(models.Model):
    class ResourceType(models.TextChoices):
        USER = "USER", "User"
        JOB = "JOB", "Job"
        RESUME = "RESUME", "Resume"
        APPLICATION = "APPLICATION", "Application"

    class ActionType(models.TextChoices):
        UPDATE = "UPDATE", "Update"
        DISABLE = "DISABLE", "Disable"
        ENABLE = "ENABLE", "Enable"
        STATUS_CHANGE = "STATUS_CHANGE", "Status Change"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admin_moderation_logs",
        limit_choices_to={"role": User.Roles.ADMIN},
    )
    action = models.CharField(
        max_length=32,
        choices=ActionType.choices,
    )
    resource_type = models.CharField(
        max_length=32,
        choices=ResourceType.choices,
    )
    resource_id = models.UUIDField()
    reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "admin_moderation_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["admin"]),
            models.Index(fields=["resource_type"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["resource_type", "resource_id"]),
        ]

    def __str__(self) -> str:
        return f"ModerationLog<{self.admin.email if self.admin else 'System'} - {self.action} {self.resource_type}>"
