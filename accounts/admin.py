from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from accounts.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "username", "membership", "role", "is_active", "email_verified_at")
    list_filter = ("membership", "role", "is_active", "is_staff", "mfa_required")
    search_fields = ("email", "username", "full_name")
    readonly_fields = ("date_joined", "last_login", "email_verified_at", "accepted_terms_at")
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Profile", {"fields": ("full_name", "country", "learning_interest")}),
        ("Access", {"fields": ("membership", "role", "is_active", "is_staff", "is_superuser", "mfa_required", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined", "email_verified_at", "accepted_terms_at", "onboarding_completed_at")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "username", "full_name", "password1", "password2")}),
    )
    filter_horizontal = ("groups", "user_permissions")
