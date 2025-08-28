from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, Capability


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "role", "reports_to", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active", "role")
    search_fields = ("username",)
    ordering = ("username",)

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Role & Manager", {"fields": ("role", "reports_to")}),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "key", "name")
    search_fields = ("key", "name")


@admin.register(Capability)
class CapabilityAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "description")
    search_fields = ("code", "description")
