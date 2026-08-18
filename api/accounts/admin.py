from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Invite, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["-date_joined"]
    list_display = ["email", "name", "is_staff", "is_active", "date_joined", "deleted_at"]
    search_fields = ["email", "name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Pessoal", {"fields": ("name", "birth_date", "theme")}),
        ("Convite", {"fields": ("invited_by_code",)}),
        (
            "Permissões",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Datas", {"fields": ("last_login", "date_joined", "deleted_at")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "name", "password1", "password2")}),
    )
    readonly_fields = ["date_joined", "deleted_at"]


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ["code", "created_by", "max_uses", "used_count", "expires_at", "created_at"]
    search_fields = ["code"]
