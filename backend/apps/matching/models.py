import uuid

from django.db import models

from apps.jobs.models import Job
from apps.users.models import User


class JobMatch(models.Model):
    """
    Stores match scores between a candidate and a job.
    Calculated deterministically based on skills, experience, and education.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="job_matches",
        limit_choices_to={"role": User.Roles.CANDIDATE},
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="job_matches",
    )
    match_score = models.DecimalField(max_digits=5, decimal_places=2)
    skills_score = models.DecimalField(max_digits=5, decimal_places=2)
    experience_score = models.DecimalField(max_digits=5, decimal_places=2)
    education_score = models.DecimalField(max_digits=5, decimal_places=2)
    matched_skills_count = models.PositiveIntegerField(default=0)
    total_required_skills = models.PositiveIntegerField(default=0)
    explanation = models.JSONField(default=dict)
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "job_matches"
        ordering = ["-match_score"]
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "job"],
                name="unique_candidate_job_match",
                violation_error_message="A candidate can only have one match record per job.",
            )
        ]
        indexes = [
            models.Index(fields=["candidate"]),
            models.Index(fields=["job"]),
            models.Index(fields=["match_score"]),
        ]

    def __str__(self) -> str:
        return (
            f"JobMatch<{self.candidate.email} -> {self.job.title}: {self.match_score}%>"
        )


class JobSkill(models.Model):
    """Discrete skill requirement attached to a job."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="required_skills",
    )
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "job_skills"
        verbose_name = "job skill"
        verbose_name_plural = "job skills"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["job", "name"],
                name="unique_job_skill_name",
                violation_error_message="A job cannot list the same required skill twice.",
            )
        ]
        indexes = [
            models.Index(fields=["job"]),
        ]

    def __str__(self) -> str:
        return f"JobSkill<{self.name}>"
