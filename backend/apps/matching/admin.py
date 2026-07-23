from django.contrib import admin

from .models import JobMatch, JobSkill


@admin.register(JobSkill)
class JobSkillAdmin(admin.ModelAdmin):
	list_display = ("job", "name")
	search_fields = ("name", "job__title", "job__company_name")
	list_select_related = ("job",)


@admin.register(JobMatch)
class JobMatchAdmin(admin.ModelAdmin):
	list_display = ("candidate", "job", "match_score", "calculated_at")
	search_fields = ("candidate__email", "job__title", "job__company_name")
	list_select_related = ("candidate", "job")
