from django.contrib import admin
from .models import MatchScore


@admin.register(MatchScore)
class MatchScoreAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'job', 'final_score', 'version', 'updated_at')
    list_filter = ('version', 'updated_at')
    search_fields = ('user_profile__user__email', 'job__title')
    readonly_fields = ('created_at', 'updated_at')
