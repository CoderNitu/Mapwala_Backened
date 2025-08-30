from django.contrib import admin
from .models import District

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "state", "status", "created_at")
    search_fields = ("name", "code", "state__name")
    list_filter = ("status", "state")

