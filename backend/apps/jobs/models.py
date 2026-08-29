from django.db import models
from django.core.validators import URLValidator


class Job(models.Model):
    """
    Job model representing a verified job from an official source.
    
    This is one of the most important models in MatchHire. It supports
    the future verified ingestion pipeline:
    
    official source -> fetch -> normalize -> validate -> deduplicate -> Job
    
    Important architectural invariants:
    - Jobs must enter MatchHire only through verified sources
    - External source identifiers are distinct from internal database IDs
    - No public API allows arbitrary users to create jobs
    """
    
    class JobStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
    
    class EmploymentType(models.TextChoices):
        FULL_TIME = 'FULL_TIME', 'Full-time'
        PART_TIME = 'PART_TIME', 'Part-time'
        CONTRACT = 'CONTRACT', 'Contract'
        INTERNSHIP = 'INTERNSHIP', 'Internship'
        REMOTE = 'REMOTE', 'Remote'
    
    # Company relationship - every job must belong to a verified source
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.PROTECT,
        related_name='jobs',
        verbose_name='Company'
    )
    
    # External/source job identifier
    # This is distinct from the internal database primary key
    # The scraper must be able to identify a source job independently
    external_job_id = models.CharField(
        max_length=200,
        help_text='External job identifier from the source system'
    )
    
    # Core job information
    title = models.CharField(
        max_length=300,
        help_text='Job title'
    )
    description = models.TextField(
        help_text='Job description'
    )
    
    # Location information
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text='Job location (city, state/country, or remote)'
    )
    
    # Employment type
    employment_type = models.CharField(
        max_length=50,
        choices=EmploymentType.choices,
        blank=True,
        help_text='Type of employment'
    )
    
    # Experience requirement
    experience_required = models.CharField(
        max_length=200,
        blank=True,
        help_text='Required experience level (e.g., "3-5 years", "Senior")'
    )
    # Structured experience fields for matching
    # These allow numeric experience matching against UserProfile.years_of_experience
    # Populated by the future job ingestion/normalization pipeline
    minimum_experience_years = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text='Minimum years of experience required (numeric)'
    )
    maximum_experience_years = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text='Maximum years of experience required (numeric)'
    )
    
    # Skills and keywords for matching
    # Skills: A list of normalized concrete skills/capabilities/technologies.
    # Examples: ["python", "django", "postgresql", "redis"]
    # Keywords: A list of normalized broader terms extracted from job content
    # useful for keyword/domain overlap.
    # Examples: ["backend", "distributed systems", "scalability", "rest api"]
    # The exact normalization algorithm belongs to future job processing phases.
    skills = models.JSONField(
        default=list,
        blank=True,
        help_text='List of normalized concrete skills/capabilities/technologies'
    )
    keywords = models.JSONField(
        default=list,
        blank=True,
        help_text='List of normalized broader terms for keyword/domain overlap'
    )
    
    # URLs
    # Official application URL where users apply
    application_url = models.URLField(
        max_length=500,
        help_text='Official company application URL for this job'
    )
    # Source URL if distinct from application URL (e.g., job listing page)
    source_url = models.URLField(
        max_length=500,
        blank=True,
        help_text='Source URL where the job was found (if distinct from application URL)'
    )
    
    # Active/inactive state
    # Use soft deactivation instead of deletion to preserve historical data
    status = models.CharField(
        max_length=20,
        choices=JobStatus.choices,
        default=JobStatus.ACTIVE,
        help_text='Job status'
    )
    
    # Timestamps with semantic meaning
    # first_seen_at: when the job was first discovered by the scraper
    # last_fetched_at: when the job was last fetched from the source
    first_seen_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the job was first discovered'
    )
    last_fetched_at = models.DateTimeField(
        auto_now=True,
        help_text='When the job was last fetched from the source'
    )
    
    # Deterministic deduplication identity/hash
    # This ensures the same job from the same source is not duplicated
    deduplication_hash = models.CharField(
        max_length=64,
        unique=True,
        help_text='Deterministic hash for deduplication'
    )
    
    # Future sponsored-job fields placeholder
    is_sponsored = models.BooleanField(
        default=False,
        help_text='Whether this job is sponsored'
    )
    
    # Flexible job metadata for variable extracted data
    job_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional structured metadata from job processing'
    )
    
    class Meta:
        db_table = 'jobs'
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
        ordering = ['-first_seen_at']
        # Ensure uniqueness of external job ID per company
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'external_job_id'],
                name='unique_company_external_job'
            ),
            models.CheckConstraint(
                check=models.Q(
                    minimum_experience_years__isnull=True
                ) | models.Q(
                    maximum_experience_years__isnull=True
                ) | models.Q(
                    minimum_experience_years__lte=models.F('maximum_experience_years')
                ),
                name='valid_experience_range',
                violation_error_message='Minimum experience years must be less than or equal to maximum experience years when both are specified'
            )
        ]
        indexes = [
            models.Index(
                fields=['status', '-last_fetched_at'],
                name='idx_job_status_freshness'
            )
        ]
    
    def __str__(self):
        return f"{self.company.name} - {self.title}"
