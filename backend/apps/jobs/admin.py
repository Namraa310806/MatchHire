from django.contrib import admin
from .models import Job, IngestionRun


@admin.register(IngestionRun)
class IngestionRunAdmin(admin.ModelAdmin):
    """
    IngestionRun admin interface for operational inspection.
    
    IMPORTANT: Ingestion runs are created by controlled backend tasks/commands only.
    Do not manually create or modify runs through this interface, as it undermines
    the operational integrity of the ingestion system.
    """
    list_display = (
        'source',
        'status',
        'started_at',
        'finished_at',
        'created_count',
        'updated_count',
        'failed_count',
        'retry_count'
    )
    list_filter = ('status', 'source', 'retry_count')
    search_fields = ('source', 'task_id')
    readonly_fields = (
        'company',
        'source',
        'task_id',
        'started_at',
        'finished_at',
        'created_at',
        'updated_at',
        'fetched_count',
        'normalized_count',
        'created_count',
        'updated_count',
        'skipped_count',
        'failed_count',
        'error_type',
        'error_message',
        'retry_count'
    )
    
    def has_add_permission(self, request):
        """Disable manual run creation to preserve operational integrity."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable manual run modification to preserve operational integrity."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable manual run deletion to preserve operational history."""
        return False


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """
    Job admin interface for inspection and debugging only.
    
    IMPORTANT: Jobs must enter MatchHire only through the verified
    source ingestion pipeline. Do not use this admin interface to
    manually create or publish jobs, as it undermines the architectural
    guarantee of source-only job ingestion.
    """
    list_display = ('title', 'company', 'status', 'first_seen_at', 'last_fetched_at')
    list_filter = ('status', 'employment_type', 'company', 'is_sponsored')
    search_fields = ('title', 'external_job_id', 'company__name')
    readonly_fields = ('first_seen_at', 'last_fetched_at', 'deduplication_hash')
    
    def has_add_permission(self, request):
        """
        Disable manual job creation through admin to preserve
        source-only ingestion architectural invariant.
        """
        return False
