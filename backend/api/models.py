from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model using email as the primary identifier."""

    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True, db_index=True)
    password = models.CharField(max_length=128)  # Hashed by Django
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_staff = models.BooleanField(default=False)  # Admin access, not for job creation
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        db_table = "auth_user"
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        return self.email  # type: ignore[no-any-return]


class CandidateProfile(models.Model):
    """Extended candidate information beyond Django auth user."""

    REMOTE_CHOICES = [
        ("on-site", "On-site"),
        ("remote", "Remote"),
        ("hybrid", "Hybrid"),
        ("any", "Any"),
    ]

    ROLE_TYPE_CHOICES = [
        ("full-time", "Full-time"),
        ("internship", "Internship"),
        ("contract", "Contract"),
        ("any", "Any"),
    ]

    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_index=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, db_index=True)
    remote_preference = models.CharField(
        max_length=20, choices=REMOTE_CHOICES, blank=True, db_index=True
    )
    salary_min = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    salary_max = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    salary_currency = models.CharField(max_length=3, default="INR")
    role_type_preference = models.CharField(
        max_length=50, choices=ROLE_TYPE_CHOICES, blank=True
    )
    bio = models.TextField(blank=True)
    total_experience_years = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    resume_file = models.FileField(max_length=255, blank=True)
    resume_uploaded_at = models.DateTimeField(null=True, blank=True)
    resume_consent_given = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidate_profile"
        verbose_name = "candidate profile"
        verbose_name_plural = "candidate profiles"

    def __str__(self) -> str:  # type: ignore[no-any-return]
        return f"{self.user.email} - Profile"


class Skill(models.Model):
    """Normalized skill taxonomy for matching (fixed vocabulary)."""

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, db_index=True)
    category = models.CharField(max_length=50, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "skill"
        verbose_name = "skill"
        verbose_name_plural = "skills"

    def __str__(self) -> str:
        return self.name  # type: ignore[no-any-return]


class CandidateSkill(models.Model):
    """Many-to-many relationship between candidates and skills with proficiency."""

    PROFICIENCY_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]

    id = models.BigAutoField(primary_key=True)
    candidate = models.ForeignKey(
        CandidateProfile, on_delete=models.CASCADE, db_index=True
    )
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT, db_index=True)
    proficiency = models.CharField(
        max_length=20, choices=PROFICIENCY_CHOICES, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "candidate_skill"
        unique_together = ("candidate", "skill")
        verbose_name = "candidate skill"
        verbose_name_plural = "candidate skills"

    def __str__(self) -> str:
        return f"{self.candidate.user.email} - {self.skill.name}"  # type: ignore[no-any-return]


class WorkExperience(models.Model):
    """Candidate work history entries."""

    id = models.BigAutoField(primary_key=True)
    candidate = models.ForeignKey(
        CandidateProfile, on_delete=models.CASCADE, db_index=True
    )
    company_name = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "work_experience"
        verbose_name = "work experience"
        verbose_name_plural = "work experiences"
        indexes = [
            models.Index(fields=["start_date", "end_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.candidate.user.email} - {self.role} at {self.company_name}"  # type: ignore[no-any-return]


class Company(models.Model):
    """Companies with approved or candidate job sources."""

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200, unique=True, db_index=True)
    website = models.URLField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "company"
        verbose_name = "company"
        verbose_name_plural = "companies"

    def __str__(self) -> str:
        return self.name  # type: ignore[no-any-return]


class IngestionSource(models.Model):
    """Approved job sources (career pages, ATS) for automated ingestion."""

    SOURCE_TYPE_CHOICES = [
        ("career_page", "Career Page"),
        ("ats", "ATS"),
        ("api", "API"),
        ("other", "Other"),
    ]

    FETCH_STATUS_CHOICES = [
        ("success", "Success"),
        ("failure", "Failure"),
        ("partial", "Partial"),
    ]

    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, db_index=True)
    name = models.CharField(max_length=200)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPE_CHOICES)
    base_url = models.URLField(max_length=500)
    listing_url_pattern = models.CharField(max_length=500, blank=True)
    job_url_pattern = models.CharField(max_length=500, blank=True)
    fetch_interval_hours = models.IntegerField(default=24)
    stale_threshold = models.IntegerField(default=3)
    is_active = models.BooleanField(default=True, db_index=True)
    last_fetched_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_fetch_status = models.CharField(
        max_length=50, choices=FETCH_STATUS_CHOICES, blank=True
    )
    consecutive_failures = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ingestion_source"
        unique_together = ("company", "base_url")
        verbose_name = "ingestion source"
        verbose_name_plural = "ingestion sources"

    def __str__(self) -> str:
        return f"{self.company.name} - {self.name}"  # type: ignore[no-any-return]


class FetchRun(models.Model):
    """Individual fetch attempts from sources."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("success", "Success"),
        ("failure", "Failure"),
        ("partial", "Partial"),
    ]

    id = models.BigAutoField(primary_key=True)
    source = models.ForeignKey(IngestionSource, on_delete=models.CASCADE, db_index=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, db_index=True)
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    jobs_fetched = models.IntegerField(default=0)
    jobs_created = models.IntegerField(default=0)
    jobs_updated = models.IntegerField(default=0)
    jobs_stale = models.IntegerField(default=0)
    jobs_closed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    celery_task_id = models.CharField(max_length=255, blank=True, db_index=True)

    class Meta:
        db_table = "fetch_run"
        verbose_name = "fetch run"
        verbose_name_plural = "fetch runs"

    def __str__(self) -> str:
        return f"{self.source.name} - {self.status} at {self.started_at}"  # type: ignore[no-any-return]


class Job(models.Model):
    """Job listings from approved sources."""

    REMOTE_TYPE_CHOICES = [
        ("on-site", "On-site"),
        ("remote", "Remote"),
        ("hybrid", "Hybrid"),
    ]

    ROLE_TYPE_CHOICES = [
        ("full-time", "Full-time"),
        ("internship", "Internship"),
        ("contract", "Contract"),
    ]

    id = models.BigAutoField(primary_key=True)
    source = models.ForeignKey(IngestionSource, on_delete=models.PROTECT, db_index=True)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, db_index=True)
    external_id = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=300)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    remote_type = models.CharField(
        max_length=50, choices=REMOTE_TYPE_CHOICES, blank=True
    )
    role_type = models.CharField(max_length=50, choices=ROLE_TYPE_CHOICES, blank=True)
    experience_min_years = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    experience_max_years = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    salary_min = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    salary_max = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    salary_currency = models.CharField(max_length=3, blank=True)
    application_url = models.URLField(max_length=1000)
    posted_date = models.DateField(null=True, blank=True, db_index=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    job_hash = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_sponsored = models.BooleanField(default=False, db_index=True)
    sponsored_boost = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True
    )
    consecutive_misses = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "job"
        unique_together = (("source", "external_id"),)
        indexes = [
            models.Index(fields=["application_url"]),
            models.Index(fields=["is_active", "last_seen_at"]),
            models.Index(fields=["last_seen_at"]),
        ]
        verbose_name = "job"
        verbose_name_plural = "jobs"

    def __str__(self) -> str:
        return f"{self.title} at {self.company.name}"  # type: ignore[no-any-return]


class JobSkill(models.Model):
    """Many-to-many relationship between jobs and required skills."""

    id = models.BigAutoField(primary_key=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, db_index=True)
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT, db_index=True)
    is_required = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "job_skill"
        unique_together = ("job", "skill")
        verbose_name = "job skill"
        verbose_name_plural = "job skills"

    def __str__(self) -> str:
        return f"{self.job.title} - {self.skill.name}"  # type: ignore[no-any-return]


class MatchScore(models.Model):
    """Candidate-job match scores with component breakdown."""

    id = models.BigAutoField(primary_key=True)
    candidate = models.ForeignKey(
        CandidateProfile, on_delete=models.CASCADE, db_index=True
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, db_index=True)
    base_score = models.DecimalField(max_digits=5, decimal_places=4)  # 0.0 to 1.0
    final_score = models.DecimalField(
        max_digits=5, decimal_places=4
    )  # 0.0 to 1.0, capped
    skill_similarity = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True
    )  # 0.0 to 1.0, 50% weight
    experience_match = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True
    )  # 0.0 to 1.0, 30% weight
    keyword_overlap = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True
    )  # 0.0 to 1.0, 20% weight
    computed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "match_score"
        unique_together = ("candidate", "job")
        indexes = [
            models.Index(fields=["final_score"]),
            models.Index(fields=["candidate", "final_score"]),
        ]
        verbose_name = "match score"
        verbose_name_plural = "match scores"

    def __str__(self) -> str:
        return f"{self.candidate.user.email} - {self.job.title}: {self.final_score}"  # type: ignore[no-any-return]


class ApplicationClick(models.Model):
    """Record when candidates click to apply for jobs."""

    id = models.BigAutoField(primary_key=True)
    candidate = models.ForeignKey(
        CandidateProfile, on_delete=models.CASCADE, db_index=True
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, db_index=True)
    clicked_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "application_click"
        indexes = [
            models.Index(fields=["candidate", "job", "clicked_at"]),
        ]
        verbose_name = "application click"
        verbose_name_plural = "application clicks"

    def __str__(self) -> str:
        return (
            f"{self.candidate.user.email} clicked {self.job.title} at {self.clicked_at}"
        )  # type: ignore[no-any-return]
