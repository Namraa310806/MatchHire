from django.contrib import admin
from .models import ApplyClick


@admin.register(ApplyClick)
class ApplyClickAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'clicked_at')
    list_filter = ('clicked_at',)
    search_fields = ('user__email', 'job__title')
    readonly_fields = ('clicked_at',)
