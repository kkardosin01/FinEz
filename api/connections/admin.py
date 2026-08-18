from django.contrib import admin

from .models import Connection


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ["institution_name", "user", "status", "last_synced_at", "created_at"]
    list_filter = ["status", "provider"]
    search_fields = ["institution_name", "user__email"]
    readonly_fields = ["access_token_encrypted"]
