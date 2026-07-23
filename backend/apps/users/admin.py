from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .forms import UserChangeForm, UserCreationForm
from .models import CandidateProfile, RecruiterProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    add_form = UserCreationForm
    form = UserChangeForm
    ordering = ("email",)
    list_display = (
        "email",
        "full_name",
        "role",
        "is_staff",
        "is_active",
        "is_verified",
    )
    list_filter = ("role", "is_staff", "is_active", "is_verified", "is_superuser")
    search_fields = ("email", "full_name")
    readonly_fields = ("date_joined", "updated_at", "last_login")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("full_name", "role")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_verified",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "role",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                    "is_verified",
                ),
            },
        ),
    )


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "headline",
        "current_location",
        "years_of_experience",
        "resume_uploaded",
        "created_at",
    )
    list_select_related = ("user",)
    search_fields = (
        "user__email",
        "user__full_name",
        "headline",
        "current_location",
        "skills_text",
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(RecruiterProfile)
class RecruiterProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "company_name",
        "job_title",
        "verified_company",
        "created_at",
    )
    list_select_related = ("user",)
    search_fields = ("user__email", "user__full_name", "company_name", "job_title")
    readonly_fields = ("created_at", "updated_at")
