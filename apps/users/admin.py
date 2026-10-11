from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm

from apps.users.forms import CustomUserChangeForm, CustomUserCreationForm
from apps.users.models import User, OTPAuthentication


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active", "created_at")
    list_filter = ("is_staff", "is_superuser", "is_active", "is_deleted")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "created_at", "modified_at")}),
        ("Status", {"fields": ("is_deleted",)}),
    )

    readonly_fields = ("created_at", "modified_at", "last_login")

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )


@admin.register(OTPAuthentication)
class OTPAuthenticationAdmin(ModelAdmin):
    list_display = ("email", "purpose", "is_used", "expired", "expires_at", "created_at")
    list_filter = ("purpose", "is_used", "created_at")
    search_fields = ("email",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    @admin.display(description="Expired", boolean=True)
    def expired(self, obj):
        return obj.is_expired()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False