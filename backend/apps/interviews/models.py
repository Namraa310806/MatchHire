import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.applications.models import Application
from apps.users.models import User


class Interview(models.Model):
    class InterviewType(models.TextChoices):
        PHONE = "phone", "Phone"
        VIDEO = "video", "Video"
        ONSITE = "onsite", "On-site"

    class InterviewStatus(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="interviews",
    )
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField()
    interview_type = models.CharField(
        max_length=32,
        choices=InterviewType.choices,
        default=InterviewType.VIDEO,
    )
    meeting_link = models.URLField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=32,
        choices=InterviewStatus.choices,
        default=InterviewStatus.SCHEDULED,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_interviews",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "interviews"
        ordering = ["scheduled_at"]
        indexes = [
            models.Index(fields=["application"]),
            models.Index(fields=["scheduled_at"]),
            models.Index(fields=["status"]),
        ]

    def clean(self):
        """Validate interview-specific rules"""
        # VIDEO interviews require meeting_link
        if self.interview_type == self.InterviewType.VIDEO and not self.meeting_link:
            raise ValidationError(
                {"meeting_link": "meeting_link is required for VIDEO interviews."}
            )

        # ONSITE interviews require location
        if self.interview_type == self.InterviewType.ONSITE and not self.location:
            raise ValidationError(
                {"location": "location is required for ONSITE interviews."}
            )

        # duration_minutes must be positive
        if self.duration_minutes <= 0:
            raise ValidationError(
                {"duration_minutes": "duration_minutes must be greater than 0."}
            )

    def __str__(self) -> str:
        return f"Interview<{self.id} - {self.interview_type} for {self.application}>"


class InterviewStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    old_status = models.CharField(max_length=32, blank=True)
    new_status = models.CharField(max_length=32)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="interview_status_changes",
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "interview_status_history"
        ordering = ["changed_at"]
        indexes = [
            models.Index(fields=["interview"]),
            models.Index(fields=["changed_at"]),
        ]

    def __str__(self) -> str:
        return f"InterviewStatusHistory<{self.interview.id}: {self.old_status} -> {self.new_status}>"
