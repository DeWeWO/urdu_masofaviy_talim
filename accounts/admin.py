from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("id", "username", "telegram_id", "is_superadmin", "is_staff", "is_active", "date_joined")
    list_filter = ("is_superadmin", "is_staff", "is_active")
    search_fields = ("username", "telegram_id")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Telegram", {"fields": ("telegram_id",)}),
        ("Permissions", {"fields": ("is_superadmin", "is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "telegram_id", "password1", "password2", "is_staff", "is_superadmin", "is_active"),
        }),
    )

    ordering = ("-date_joined",)
