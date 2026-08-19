from django.contrib import admin

from .models import Holding


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ["user", "kind", "symbol", "quantity", "avg_price_cents"]
    list_filter = ["kind"]
    search_fields = ["user__email", "symbol"]
