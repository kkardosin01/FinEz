from django.contrib import admin

from .models import Account, CategorizationRule, Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "slug", "name_pt", "color_light", "color_dark"]


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "type", "connection", "created_at"]
    list_filter = ["type"]
    search_fields = ["name", "user__email"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["description", "user", "amount_cents", "date", "category", "origin", "category_source"]
    list_filter = ["origin", "category_source", "category"]
    search_fields = ["description", "user__email"]
    date_hierarchy = "date"


@admin.register(CategorizationRule)
class CategorizationRuleAdmin(admin.ModelAdmin):
    list_display = ["user", "match_type", "match_value", "category", "hits_count"]
