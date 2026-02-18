from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTPCode


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Fields to display in list view
    list_display = ("phone", "full_name", "city", "is_active", "is_staff", "date_joined")
    list_filter = ("is_active", "is_staff", "preferred_otp_channel", "city")
    search_fields = ("phone", "full_name", "city")
    ordering = ("-date_joined",)

    # Fields shown when editing a user
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Personal Info", {"fields": ("full_name", "city", "address", "preferred_otp_channel")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Timestamps", {"fields": ("date_joined", "updated_at"), "classes": ("collapse",)}),
    )
    readonly_fields = ("date_joined", "updated_at")

    # Fields shown when creating a new user
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "full_name", "password1", "password2"),
            },
        ),
    )


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ("phone", "code", "purpose", "channel", "is_used", "created_at", "expires_at")
    list_filter = ("purpose", "channel", "is_used")
    search_fields = ("phone",)
    readonly_fields = ("code", "created_at", "expires_at")
    ordering = ("-created_at",)
