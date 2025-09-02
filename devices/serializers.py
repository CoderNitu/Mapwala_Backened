# devices/serializers.py
from rest_framework import serializers
from .models import Device, BOMEntry, Enclosure, WireHarness, Battery, SOSButton, Sticker
from accounts.models import User

class ManufacturerSerializer(serializers.ModelSerializer):
    """Serializer for manufacturer dropdown options"""
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name']
        read_only_fields = ['id', 'username', 'display_name']
    
    def get_display_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.username

class BOMEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = BOMEntry
        fields = [
            'id',
            'identification_mark',
            'components_required',
            'designator',
            'ship_qty',
            'fp_cross_checked'
        ]

class EnclosureSerializer(serializers.ModelSerializer):
    make_name = serializers.CharField(source='make.username', read_only=True)

    class Meta:
        model = Enclosure
        exclude = ['device']
    
    def validate_make(self, value):
        if not value.role or value.role.key.lower() != 'manufacturer':
            raise serializers.ValidationError("Selected user is not a manufacturer.")
        return value

class WireHarnessSerializer(serializers.ModelSerializer):
    make_name = serializers.CharField(source='make.username', read_only=True)
    pin_type_display = serializers.CharField(source='get_pin_type_display', read_only=True)

    class Meta:
        model = WireHarness
        exclude = ['device']

    def validate_make(self, value):
        if not value.role or value.role.key.lower() != 'manufacturer':
            raise serializers.ValidationError("Selected user is not a manufacturer.")
        return value

class BatterySerializer(serializers.ModelSerializer):
    make_name = serializers.CharField(source='make.username', read_only=True)

    class Meta:
        model = Battery
        exclude = ['device']
    
    def validate_make(self, value):
        if not value.role or value.role.key.lower() != 'manufacturer':
            raise serializers.ValidationError("Selected user is not a manufacturer.")
        return value

class SOSButtonSerializer(serializers.ModelSerializer):
    make_name = serializers.CharField(source='make.username', read_only=True)
    class Meta:
        model = SOSButton
        exclude = ['device']
        
    def validate_make(self, value):
        if not value.role or value.role.key.lower() != 'manufacturer':
            raise serializers.ValidationError("Selected user is not a manufacturer.")
        return value

class StickerSerializer(serializers.ModelSerializer):
    make_name = serializers.CharField(source='make.username', read_only=True)

    class Meta:
        model = Sticker
        exclude = ['device']
    
    def validate_make(self, value):
        if not value.role or value.role.key.lower() != 'manufacturer':
            raise serializers.ValidationError("Selected user is not a manufacturer.")
        return value

class DeviceSerializer(serializers.ModelSerializer):
    manufacturer_name = serializers.CharField(read_only=True)
    unit_of_measure_display = serializers.CharField(source='get_unit_of_measure_display', read_only=True)
    state_of_supply_display = serializers.CharField(source='get_state_of_supply_display', read_only=True)
    
    bom_entries = BOMEntrySerializer(many=True, read_only=True)
    enclosure = EnclosureSerializer(read_only=True)
    wire_harness = WireHarnessSerializer(read_only=True)
    battery = BatterySerializer(read_only=True)
    sos_button = SOSButtonSerializer(read_only=True)
    sticker = StickerSerializer(read_only=True)

    class Meta:
        model = Device
        fields = [
            'id', 'make_id', 'manufacturer_name', 'model', 'mrp',
            'unit_of_measure', 'unit_of_measure_display', 'version', 'variant',
            'state_of_supply', 'state_of_supply_display', 'quantity', 'created_by',
            'created_at', 'updated_at', 'status',
            'bom_entries', 'enclosure', 'wire_harness', 'battery', 'sos_button', 
            'sticker'
        ]
        read_only_fields = [
            'id', 'created_by', 'created_at', 'updated_at', 'manufacturer_name',
            'unit_of_measure_display', 'state_of_supply_display', 'bom_entries',
            'enclosure', 'wire_harness', 'battery', 'sos_button', 'sticker'
        ]

class DeviceCreateSerializer(serializers.ModelSerializer):
    """Serializer specifically for device creation (Step 1)"""
    class Meta:
        model = Device
        fields = [
            'make_id',
            'model',
            'mrp',
            'unit_of_measure',
            'version',
            'variant',
            'state_of_supply'
        ]
    
    def validate_make_id(self, value):
        if not value.role or value.role.key.lower() != 'manufacturer':
            raise serializers.ValidationError("Selected user is not a manufacturer.")
        return value
    
    def validate_mrp(self, value):
        if value <= 0:
            raise serializers.ValidationError("MRP must be greater than 0.")
        return value

