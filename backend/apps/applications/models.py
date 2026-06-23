import uuid

from django.db import models
from django.utils import timezone

from apps.jobs.models import Job
from apps.resumes.models import ResumeVersion
from apps.users.models import User


class Application(models.Model):
    class ApplicationStatus(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under Review"
        SHORTLISTED = "shortlisted", "Shortlisted"
        REJECTED = "rejected", "Rejected"
        HIRED = "hired", "Hired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    candidate = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="applications",
        limit_choices_to={"role": User.Roles.CANDIDATE},
    )
    resume_version = models.ForeignKey(
        ResumeVersion,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    status = models.CharField(
        max_length=32,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.SUBMITTED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "applications"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["job", "candidate"],
                name="unique_application_per_job_candidate",
                violation_error_message="A candidate may only apply once per job.",
            )
        ]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["job"]),
            models.Index(fields=["candidate"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Application<{self.candidate.email} -> {self.job.title}>"
