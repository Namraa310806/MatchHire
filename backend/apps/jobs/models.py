import uuid

from django.db import models
from django.utils import timezone

from apps.users.models import User


class Job(models.Model):
    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full Time"
        PART_TIME = "part_time", "Part Time"
        CONTRACT = "contract", "Contract"
        INTERNSHIP = "internship", "Internship"

    class ExperienceLevel(models.TextChoices):
        ENTRY = "entry", "Entry Level"
        JUNIOR = "junior", "Junior"
        MID = "mid", "Mid Level"
        SENIOR = "senior", "Senior"
        LEAD = "lead", "Lead"

    class JobStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        CLOSED = "closed", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recruiter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="jobs",
        limit_choices_to={"role": User.Roles.RECRUITER},
    )
    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    employment_type = models.CharField(
        max_length=32,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )
    experience_level = models.CharField(
        max_length=32,
        choices=ExperienceLevel.choices,
        default=ExperienceLevel.MID,
    )
    description = models.TextField()
    requirements = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    salary_min = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    salary_max = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    currency = models.CharField(max_length=3, default="USD")
    is_remote = models.BooleanField(default=False)
    status = models.CharField(
        max_length=32,
        choices=JobStatus.choices,
        default=JobStatus.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "jobs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["recruiter"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} at {self.company_name}"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.salary_min and self.salary_max and self.salary_min > self.salary_max:
            raise ValidationError(
                {"salary_min": "salary_min must be less than or equal to salary_max"}
            )
