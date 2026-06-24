from django.contrib import admin

from .models import Interview, InterviewStatusHistory


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ["id", "application", "scheduled_at", "interview_type", "status"]
    list_filter = ["status", "interview_type", "scheduled_at"]
    search_fields = ["id", "application__candidate__email"]


@admin.register(InterviewStatusHistory)
class InterviewStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ["id", "interview", "old_status", "new_status", "changed_at"]
    list_filter = ["new_status", "changed_at"]
