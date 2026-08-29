from django.contrib import admin
from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'start_time', 'expiration_time')
    list_filter = ('plan', 'status')
    search_fields = ('user__email', 'provider_subscription_id')
    readonly_fields = ('created_at', 'updated_at')
