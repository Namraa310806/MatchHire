from django.contrib import admin
from .models import Job


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
