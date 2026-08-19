from django.contrib import admin

from .models import Badge, Streak


@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    list_display = ["user", "current_streak", "longest_streak", "last_logged_date"]
    search_fields = ["user__email"]


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ["user", "slug", "created_at"]
    list_filter = ["slug"]
    search_fields = ["user__email"]
