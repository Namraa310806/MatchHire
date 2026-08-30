from django.db import models
from django.core.validators import URLValidator
from django.db.models import Q, F, Case, When, IntegerField
from django.db.models.functions import Coalesce
from typing import Dict, Any


class IngestionRun(models.Model):
    """
    Track a single job ingestion run for a source.
    
    This model provides operational visibility into ingestion execution,
    distinguishing "the scraper ran" from "jobs exist in the database."
    
    Each run represents one logical ingestion attempt for a source.
    Retries may create new runs or update the same run depending on design.
    
    Important architectural invariants:
    - PostgreSQL is the source of truth for run state
    - Redis is only the Celery broker, not run storage
    - Runs are created by controlled backend tasks/commands only
    - No candidate can trigger or modify ingestion runs
    """
    
    class RunStatus(models.TextChoices):
        """Ingestion run status with controlled state transitions."""
        PENDING = 'PENDING', 'Pending'
        RUNNING = 'RUNNING', 'Running'
        RETRYING = 'RETRYING', 'Retrying'
        SUCCEEDED = 'SUCCEEDED', 'Succeeded'
        PARTIAL = 'PARTIAL', 'Partial'
        FAILED = 'FAILED', 'Failed'
    
    # Source identification - use existing Company architecture
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.PROTECT,
        related_name='ingestion_runs',
        verbose_name='Company'
    )
    
    # Source identifier from registry (e.g., 'stripe', 'nexus_technologies')
    source = models.CharField(
        max_length=100,
        help_text='Source identifier from registry'
    )
    
    # Run status
    status = models.CharField(
        max_length=20,
        choices=RunStatus.choices,
        default=RunStatus.PENDING,
        help_text='Ingestion run status'
    )
    
    # Celery task identifier for tracking
    task_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Celery task ID if executed via Celery'
    )
    
    # Timestamps
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the ingestion run started'
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the ingestion run finished'
    )
    
    # Counters for observability
    fetched_count = models.IntegerField(
        default=0,
        help_text='Number of jobs fetched from source'
    )
    normalized_count = models.IntegerField(
        default=0,
        help_text='Number of jobs normalized successfully'
    )
    created_count = models.IntegerField(
        default=0,
        help_text='Number of new jobs created'
    )
    updated_count = models.IntegerField(
        default=0,
        help_text='Number of existing jobs updated'
    )
    skipped_count = models.IntegerField(
        default=0,
        help_text='Number of jobs skipped (validation/integrity errors)'
    )
    failed_count = models.IntegerField(
        default=0,
        help_text='Number of jobs that failed to ingest'
    )
    
    # Error information (bounded, no secrets)
    error_type = models.CharField(
        max_length=100,
        blank=True,
        help_text='Type of error if run failed'
    )
    error_message = models.TextField(
        blank=True,
        help_text='Error message if run failed (bounded size, no secrets)'
    )
    
    # Retry tracking
    retry_count = models.IntegerField(
        default=0,
        help_text='Number of retry attempts for this run'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ingestion_runs'
        verbose_name = 'Ingestion Run'
        verbose_name_plural = 'Ingestion Runs'
        ordering = ['-started_at']
        constraints = [
            # Prevent counters from going negative
            models.CheckConstraint(
                check=models.Q(fetched_count__gte=0),
                name='check_fetched_count_nonnegative'
            ),
            models.CheckConstraint(
                check=models.Q(normalized_count__gte=0),
                name='check_normalized_count_nonnegative'
            ),
            models.CheckConstraint(
                check=models.Q(created_count__gte=0),
                name='check_created_count_nonnegative'
            ),
            models.CheckConstraint(
                check=models.Q(updated_count__gte=0),
                name='check_updated_count_nonnegative'
            ),
            models.CheckConstraint(
                check=models.Q(skipped_count__gte=0),
                name='check_skipped_count_nonnegative'
            ),
            models.CheckConstraint(
                check=models.Q(failed_count__gte=0),
                name='check_failed_count_nonnegative'
            ),
            models.CheckConstraint(
                check=models.Q(retry_count__gte=0),
                name='check_retry_count_nonnegative'
            ),
            # Ensure finished_at is not before started_at
            models.CheckConstraint(
                check=models.Q(finished_at__isnull=True) | 
                       models.Q(started_at__isnull=True) |
                       models.Q(finished_at__gte=models.F('started_at')),
                name='check_finished_after_started'
            ),
            # Prevent overlapping RUNNING runs for the same source
            # This ensures only one active ingestion per source at a time
            models.UniqueConstraint(
                fields=['source'],
                condition=models.Q(status='RUNNING'),
                name='unique_running_per_source',
                violation_error_message='An ingestion run is already in progress for this source'
            ),
        ]
        indexes = [
            models.Index(
                fields=['source', 'status'],
                name='idx_ing_run_src_status'
            ),
            models.Index(
                fields=['started_at'],
                name='idx_ing_run_started'
            ),
            models.Index(
                fields=['source', 'started_at'],
                name='idx_ing_run_src_start'
            ),
            models.Index(
                fields=['task_id'],
                name='idx_ing_run_task_id'
            ),
        ]
    
    def __str__(self):
        return f"{self.source} - {self.status} ({self.started_at})"
    
    def mark_running(self, task_id: str = None):
        """Mark run as RUNNING and set started_at."""
        self.status = self.RunStatus.RUNNING
        self.started_at = models.functions.Now()
        if task_id:
            self.task_id = task_id
        self.save()
    
    def mark_succeeded(self, result: dict):
        """Mark run as SUCCEEDED with result counters."""
        self.status = self.RunStatus.SUCCEEDED
        self.finished_at = models.functions.Now()
        self.fetched_count = result.get('fetched', 0)
        self.normalized_count = result.get('normalized', 0)
        self.created_count = result.get('created', 0)
        self.updated_count = result.get('updated', 0)
        self.skipped_count = result.get('skipped', 0)
        self.failed_count = result.get('failed', 0)
        self.save()
    
    def mark_partial(self, result: dict):
        """Mark run as PARTIAL with result counters."""
        self.status = self.RunStatus.PARTIAL
        self.finished_at = models.functions.Now()
        self.fetched_count = result.get('fetched', 0)
        self.normalized_count = result.get('normalized', 0)
        self.created_count = result.get('created', 0)
        self.updated_count = result.get('updated', 0)
        self.skipped_count = result.get('skipped', 0)
        self.failed_count = result.get('failed', 0)
        self.save()
    
    def mark_failed(self, error_type: str = None, error_message: str = None):
        """Mark run as FAILED with error information."""
        self.status = self.RunStatus.FAILED
        self.finished_at = models.functions.Now()
        if error_type:
            self.error_type = error_type[:100]  # Bound size
        if error_message:
            self.error_message = error_message[:1000]  # Bound size, no secrets
        self.save()
    
    def increment_retry(self):
        """Increment retry count."""
        self.retry_count += 1
        self.save()
    
    def mark_retrying(self):
        """Mark run as RETRYING for transient failures."""
        self.status = self.RunStatus.RETRYING
        self.save()
    
    @classmethod
    def get_source_health(cls, source: str) -> Dict[str, Any]:
        """
        Derive source health from recent IngestionRun records.
        
        This provides operational health information without requiring
        a separate SourceHealth model. Health is computed from run history.
        
        Health states:
        - HEALTHY: Recent successful ingestion
        - DEGRADED: Recent partial result or isolated failures
        - FAILING: Repeated consecutive failures
        - UNKNOWN: Source has never run
        
        Args:
            source: Source identifier (e.g., 'stripe')
        
        Returns:
            Dictionary with health information:
            {
                "health": "HEALTHY" | "DEGRADED" | "FAILING" | "UNKNOWN",
                "last_successful_run": datetime or None,
                "last_attempt": datetime or None,
                "consecutive_failures": int,
                "recent_runs": list of recent run summaries
            }
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Get recent runs (last 10) - convert to list to avoid queryset issues
        recent_runs = list(cls.objects.filter(
            source=source
        ).order_by('-started_at')[:10])
        
        if not recent_runs:
            return {
                "health": "UNKNOWN",
                "last_successful_run": None,
                "last_attempt": None,
                "consecutive_failures": 0,
                "recent_runs": []
            }
        
        # Get last attempt
        last_attempt = recent_runs[0].started_at
        
        # Get last successful run
        last_successful = None
        for run in recent_runs:
            if run.status == cls.RunStatus.SUCCEEDED:
                last_successful = run
                break
        last_successful_run = last_successful.started_at if last_successful else None
        
        # Count consecutive failures (from most recent backwards)
        # RETRYING is not a terminal failure - it's an in-progress state
        consecutive_failures = 0
        for run in recent_runs:
            if run.status == cls.RunStatus.FAILED:
                consecutive_failures += 1
            elif run.status in (cls.RunStatus.RUNNING, cls.RunStatus.RETRYING):
                # In-progress states don't count as failures
                break
            else:
                # SUCCEEDED, PARTIAL, PENDING stop the failure count
                break
        
        # Determine health state
        health = "UNKNOWN"
        
        # Check if most recent run is actively retrying
        if recent_runs and recent_runs[0].status == cls.RunStatus.RETRYING:
            # Actively retrying = DEGRADED (in-progress but not healthy)
            health = "DEGRADED"
        elif consecutive_failures >= 3:
            # 3 or more consecutive failures = FAILING
            health = "FAILING"
        elif last_successful_run:
            # Has succeeded before
            if consecutive_failures > 0:
                # Some recent failures but not consecutive = DEGRADED
                health = "DEGRADED"
            else:
                # Recent success = HEALTHY
                # Check if last successful run was recent (within 24 hours)
                if last_successful_run >= timezone.now() - timedelta(hours=24):
                    health = "HEALTHY"
                else:
                    # Last success was old = DEGRADED
                    health = "DEGRADED"
        else:
            # Never succeeded
            if consecutive_failures > 0:
                health = "FAILING"
            else:
                # Only partial runs or in-progress = DEGRADED
                health = "DEGRADED"
        
        # Build recent run summaries
        recent_runs_summary = [
            {
                "id": run.id,
                "status": run.status,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                "created_count": run.created_count,
                "updated_count": run.updated_count,
                "failed_count": run.failed_count,
                "skipped_count": run.skipped_count
            }
            for run in recent_runs
        ]
        
        return {
            "health": health,
            "last_successful_run": last_successful_run.isoformat() if last_successful_run else None,
            "last_attempt": last_attempt.isoformat() if last_attempt else None,
            "consecutive_failures": consecutive_failures,
            "recent_runs": recent_runs_summary
        }


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
