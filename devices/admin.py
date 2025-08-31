# devices/admin.py
from django.contrib import admin
from .models import Device

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'model', 
        'manufacturer_name', 
        'mrp', 
        'unit_of_measure', 
        'state_of_supply', 
        'created_by', 
        'created_at', 
        'status'
    ]
    list_filter = [
        'unit_of_measure', 
        'state_of_supply', 
        'status', 
        'created_at'
    ]
    search_fields = [
        'model', 
        'make_id__username',
        'make_id__first_name', 
        'make_id__last_name',
        'variant',
        'version'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Device Information', {
            'fields': (
                'make_id', 
                'model', 
                'mrp', 
                'unit_of_measure', 
                'version', 
                'variant', 
                'state_of_supply'
            )
        }),
        ('Metadata', {
            'fields': (
                'created_by', 
                'status', 
                'created_at', 
                'updated_at'
            )
        }),
    )
    
    def manufacturer_name(self, obj):
        return obj.manufacturer_name
    manufacturer_name.short_description = 'Manufacturer'