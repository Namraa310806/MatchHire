from django.contrib import admin

from .models import Resume, ResumeVersion


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("user__email",)
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(ResumeVersion)
class ResumeVersionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "resume",
        "version_number",
        "is_current",
        "original_filename",
        "file_size",
        "uploaded_at",
    )
    list_filter = ("is_current", "uploaded_at", "mime_type")
    search_fields = ("resume__user__email", "original_filename")
    readonly_fields = ("id", "version_number", "uploaded_at", "created_at")
    ordering = ("-uploaded_at",)
