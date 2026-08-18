from django.contrib import admin

from .models import Budget


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ["user", "category", "month", "amount_cents", "alerted_80_at", "alerted_100_at"]
    list_filter = ["month"]
    search_fields = ["user__email"]
