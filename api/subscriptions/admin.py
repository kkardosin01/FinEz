from django.contrib import admin

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "name", "amount_cents", "previous_amount_cents", "status", "last_charged_at"]
    list_filter = ["status"]
    search_fields = ["user__email", "name", "merchant_key"]
