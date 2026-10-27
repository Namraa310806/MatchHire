from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    ApplicationClick,
    CandidateProfile,
    CandidateSkill,
    Company,
    FetchRun,
    IngestionSource,
    Job,
    JobSkill,
    MatchScore,
    Skill,
    User,
    WorkExperience,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""

    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = ("is_staff", "is_active", "date_joined")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    """Admin interface for CandidateProfile model."""

    list_display = (
        "user",
        "location",
        "remote_preference",
        "total_experience_years",
        "created_at",
    )
    list_filter = ("remote_preference", "created_at")
    search_fields = ("user__email", "location")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """Admin interface for Skill model (read-only for canonical vocabulary)."""

    list_display = ("name", "category", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("name", "category")
    readonly_fields = ("name", "category", "created_at")

    def has_add_permission(self, request):
        """Prevent adding skills (canonical vocabulary)."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing skills (canonical vocabulary)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting skills (canonical vocabulary)."""
        return False


@admin.register(CandidateSkill)
class CandidateSkillAdmin(admin.ModelAdmin):
    """Admin interface for CandidateSkill model."""

    list_display = ("candidate", "skill", "proficiency", "created_at")
    list_filter = ("proficiency", "created_at")
    search_fields = ("candidate__user__email", "skill__name")


@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    """Admin interface for WorkExperience model."""

    list_display = ("candidate", "company_name", "role", "start_date", "end_date")
    list_filter = ("start_date", "end_date", "created_at")
    search_fields = ("candidate__user__email", "company_name", "role")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin interface for Company model (read-only to prevent manual creation)."""

    list_display = ("name", "website", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "website")
    readonly_fields = (
        "name",
        "website",
        "description",
        "is_active",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        """Prevent adding companies (must go through source approval)."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing companies (must go through source approval)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting companies (must go through source approval)."""
        return False


@admin.register(IngestionSource)
class IngestionSourceAdmin(admin.ModelAdmin):
    """Admin interface for IngestionSource model (read-only to prevent manual creation)."""

    list_display = (
        "company",
        "name",
        "source_type",
        "is_active",
        "last_fetched_at",
        "last_fetch_status",
    )
    list_filter = ("source_type", "is_active", "last_fetch_status", "created_at")
    search_fields = ("company__name", "name", "base_url")
    readonly_fields = (
        "company",
        "name",
        "source_type",
        "base_url",
        "listing_url_pattern",
        "job_url_pattern",
        "fetch_interval_hours",
        "stale_threshold",
        "is_active",
        "last_fetched_at",
        "last_fetch_status",
        "consecutive_failures",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        """Prevent adding sources (must go through source approval)."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing sources (must go through source approval)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting sources (must go through source approval)."""
        return False


@admin.register(FetchRun)
class FetchRunAdmin(admin.ModelAdmin):
    """Admin interface for FetchRun model (read-only monitoring)."""

    list_display = (
        "source",
        "status",
        "started_at",
        "completed_at",
        "jobs_fetched",
        "jobs_created",
        "jobs_updated",
    )
    list_filter = ("status", "started_at")
    search_fields = ("source__name", "celery_task_id")
    readonly_fields = (
        "source",
        "status",
        "started_at",
        "completed_at",
        "jobs_fetched",
        "jobs_created",
        "jobs_updated",
        "jobs_stale",
        "jobs_closed",
        "error_message",
        "celery_task_id",
    )

    def has_add_permission(self, request):
        """Prevent manual fetch run creation (automated only)."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing fetch runs (automated only)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting fetch runs (audit trail)."""
        return False


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Admin interface for Job model (read-only to prevent manual creation)."""

    list_display = (
        "title",
        "company",
        "source",
        "location",
        "is_active",
        "is_sponsored",
        "posted_date",
        "last_seen_at",
    )
    list_filter = (
        "is_active",
        "is_sponsored",
        "remote_type",
        "role_type",
        "posted_date",
    )
    search_fields = ("title", "company__name", "location", "external_id")
    readonly_fields = (
        "source",
        "company",
        "external_id",
        "title",
        "description",
        "requirements",
        "location",
        "remote_type",
        "role_type",
        "experience_min_years",
        "experience_max_years",
        "salary_min",
        "salary_max",
        "salary_currency",
        "application_url",
        "posted_date",
        "first_seen_at",
        "last_seen_at",
        "job_hash",
        "is_active",
        "is_sponsored",
        "sponsored_boost",
        "consecutive_misses",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        """Prevent adding jobs (ingestion pipeline only)."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing jobs (ingestion pipeline only)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting jobs (ingestion pipeline only)."""
        return False


@admin.register(JobSkill)
class JobSkillAdmin(admin.ModelAdmin):
    """Admin interface for JobSkill model (read-only)."""

    list_display = ("job", "skill", "is_required", "created_at")
    list_filter = ("is_required", "created_at")
    search_fields = ("job__title", "skill__name")
    readonly_fields = ("job", "skill", "is_required", "created_at")

    def has_add_permission(self, request):
        """Prevent manual job-skill assignment (ingestion pipeline only)."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing job-skill assignment (ingestion pipeline only)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting job-skill assignment (ingestion pipeline only)."""
        return False


@admin.register(MatchScore)
class MatchScoreAdmin(admin.ModelAdmin):
    """Admin interface for MatchScore model (read-only monitoring)."""

    list_display = ("candidate", "job", "base_score", "final_score", "computed_at")
    list_filter = ("computed_at", "updated_at")
    search_fields = ("candidate__user__email", "job__title")
    readonly_fields = (
        "candidate",
        "job",
        "base_score",
        "final_score",
        "skill_similarity",
        "experience_match",
        "keyword_overlap",
        "computed_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        """Prevent manual match score creation (automated only)."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing match scores (automated only)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting match scores (automated only)."""
        return False


@admin.register(ApplicationClick)
class ApplicationClickAdmin(admin.ModelAdmin):
    """Admin interface for ApplicationClick model (read-only monitoring)."""

    list_display = ("candidate", "job", "clicked_at", "ip_address")
    list_filter = ("clicked_at",)
    search_fields = ("candidate__user__email", "job__title", "ip_address")
    readonly_fields = ("candidate", "job", "clicked_at", "ip_address", "user_agent")

    def has_add_permission(self, request):
        """Prevent manual application click creation (user action only)."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing application clicks (audit trail)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting application clicks (audit trail)."""
        return False
