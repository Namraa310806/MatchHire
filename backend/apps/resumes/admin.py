from django.contrib import admin

from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "original_filename", "file_size", "is_active", "uploaded_at")
    list_filter = ("is_active", "uploaded_at")
    search_fields = ("user__email", "original_filename")
    readonly_fields = ("id", "uploaded_at")
    ordering = ("-uploaded_at",)
