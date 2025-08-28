from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, Capability, State  # 🔹 Added State


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("phone_number", "role", "reports_to", "state", "is_staff")  # 🔹 Added state
    list_filter = ("is_staff", "is_superuser", "is_active", "role", "state")    # 🔹 Added state
    search_fields = ("phone_number", "username", "state__name")                  # 🔹 Can search by state
    ordering = ("phone_number",)

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Role & Manager", {"fields": ("role", "reports_to", "state")}),          # 🔹 Added state
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "key", "name")
    search_fields = ("key", "name")


@admin.register(Capability)
class CapabilityAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "description")
    search_fields = ("code", "description")


# 🔹 Register State
@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
