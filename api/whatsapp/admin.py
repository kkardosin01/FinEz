from django.contrib import admin

from .models import WhatsappLink, WhatsappMessage


@admin.register(WhatsappLink)
class WhatsappLinkAdmin(admin.ModelAdmin):
    list_display = ["user", "phone_e164", "status", "last_message_at"]
    list_filter = ["status"]
    search_fields = ["user__email", "phone_e164"]


@admin.register(WhatsappMessage)
class WhatsappMessageAdmin(admin.ModelAdmin):
    list_display = ["user", "direction", "body", "created_at"]
    list_filter = ["direction"]
    search_fields = ["user__email", "body"]
