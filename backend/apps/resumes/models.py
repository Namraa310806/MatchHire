import uuid

from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.users.models import User


def resume_version_upload_path(instance, filename):
    """Generate upload path for resume version files: media/resumes/<user_id>/<version_id>/<unique_filename>"""
    return f"resumes/{instance.resume.user_id}/{instance.id}/{instance.stored_filename}"


class Resume(models.Model):
    """
    Resume container - represents a user's resume history.
    Does NOT store file data. File data lives in ResumeVersion.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="resume",
    )
    created_at = models.DateTimeField(default=timezone.now, auto_now_add=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resumes"
        verbose_name = "resume"
        verbose_name_plural = "resumes"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                name="unique_resume_per_user",
                violation_error_message="A user can only have one resume container.",
            )
        ]

    def __str__(self) -> str:
        return f"Resume<{self.user.email}>"


class ParsedResume(models.Model):
    """Model to store parsed resume text and metadata for a specific version."""
    
    class ParseStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume_version = models.OneToOneField(
        'ResumeVersion',
        on_delete=models.CASCADE,
        related_name="parsed_resume",
    )
    raw_text = models.TextField(blank=True)
    parsed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ParseStatus.choices,
        default=ParseStatus.PENDING,
    )
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "parsed_resumes"
        verbose_name = "parsed resume"
        verbose_name_plural = "parsed resumes"
        ordering = ["-parsed_at"]

    def __str__(self) -> str:
        return f"ParsedResume<{self.resume_version.resume.user.email} - v{self.resume_version.version_number} - {self.status}>"


class ResumeVersion(models.Model):
    """
    Immutable document snapshot - stores actual file data.
    Each version is a complete, independent copy of the resume at a point in time.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    
    # File data (moved from Resume)
    original_filename = models.CharField(max_length=255)
    stored_filename = models.CharField(max_length=255, unique=True)
    file = models.FileField(upload_to=resume_version_upload_path)
    file_size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    # Version metadata
    version_number = models.PositiveIntegerField()
    is_current = models.BooleanField(default=False)
    change_reason = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "resume_versions"
        verbose_name = "resume version"
        verbose_name_plural = "resume versions"
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["resume"],
                condition=Q(is_current=True),
                name="unique_current_version_per_resume",
                violation_error_message="A resume can only have one current version at a time.",
            ),
            models.UniqueConstraint(
                fields=["resume", "version_number"],
                name="unique_version_number_per_resume",
                violation_error_message="A resume cannot have duplicate version numbers.",
            ),
        ]

    def __str__(self) -> str:
        return f"ResumeVersion<{self.resume.user.email} - v{self.version_number}>"


class StructuredResume(models.Model):
    """
    Structured resume data extracted from parsed resume text.
    Contains contact information, summary, and links.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume_version = models.OneToOneField(
        ResumeVersion,
        on_delete=models.CASCADE,
        related_name="structured_resume",
    )
    full_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, auto_now_add=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "structured_resumes"
        verbose_name = "structured resume"
        verbose_name_plural = "structured resumes"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"StructuredResume<{self.resume_version.resume.user.email} - v{self.resume_version.version_number}>"


class ResumeSkill(models.Model):
    """
    Individual skill extracted from a structured resume.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    structured_resume = models.ForeignKey(
        StructuredResume,
        on_delete=models.CASCADE,
        related_name="skills",
    )
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "resume_skills"
        verbose_name = "resume skill"
        verbose_name_plural = "resume skills"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"ResumeSkill<{self.name}>"


class ResumeEducation(models.Model):
    """
    Education entry extracted from a structured resume.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    structured_resume = models.ForeignKey(
        StructuredResume,
        on_delete=models.CASCADE,
        related_name="education",
    )
    institution = models.CharField(max_length=255, blank=True)
    degree = models.CharField(max_length=255, blank=True)
    field_of_study = models.CharField(max_length=255, blank=True)
    start_year = models.PositiveIntegerField(null=True, blank=True)
    end_year = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "resume_education"
        verbose_name = "resume education"
        verbose_name_plural = "resume education"
        ordering = ["-end_year"]

    def __str__(self) -> str:
        return f"ResumeEducation<{self.institution} - {self.degree}>"


class ResumeExperience(models.Model):
    """
    Work experience entry extracted from a structured resume.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    structured_resume = models.ForeignKey(
        StructuredResume,
        on_delete=models.CASCADE,
        related_name="experience",
    )
    company = models.CharField(max_length=255, blank=True)
    job_title = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "resume_experience"
        verbose_name = "resume experience"
        verbose_name_plural = "resume experience"
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return f"ResumeExperience<{self.company} - {self.job_title}>"


class ResumeProject(models.Model):
    """
    Project entry extracted from a structured resume.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    structured_resume = models.ForeignKey(
        StructuredResume,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    github_url = models.URLField(blank=True)
    project_url = models.URLField(blank=True)

    class Meta:
        db_table = "resume_projects"
        verbose_name = "resume project"
        verbose_name_plural = "resume projects"
        ordering = ["title"]

    def __str__(self) -> str:
        return f"ResumeProject<{self.title}>"


class ResumeCertification(models.Model):
    """
    Certification entry extracted from a structured resume.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    structured_resume = models.ForeignKey(
        StructuredResume,
        on_delete=models.CASCADE,
        related_name="certifications",
    )
    name = models.CharField(max_length=255, blank=True)
    issuer = models.CharField(max_length=255, blank=True)
    issue_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "resume_certifications"
        verbose_name = "resume certification"
        verbose_name_plural = "resume certifications"
        ordering = ["-issue_date"]

    def __str__(self) -> str:
        return f"ResumeCertification<{self.name} - {self.issuer}>"
