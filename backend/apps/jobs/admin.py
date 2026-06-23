from django.contrib import admin

from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ["title", "company_name", "status", "recruiter", "created_at"]
    list_filter = ["status", "employment_type", "experience_level", "is_remote"]
    search_fields = ["title", "company_name", "location"]
    readonly_fields = ["id", "created_at", "updated_at", "closed_at"]
