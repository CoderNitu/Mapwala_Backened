# devices/serializers.py
from rest_framework import serializers
from .models import Device
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

class DeviceSerializer(serializers.ModelSerializer):
    manufacturer_name = serializers.CharField(read_only=True)

    class Meta:
        model = Device
        fields = '__all__'

    unit_of_measure_display = serializers.CharField(source='get_unit_of_measure_display', read_only=True)
    state_of_supply_display = serializers.CharField(source='get_state_of_supply_display', read_only=True)
    
    class Meta:
        model = Device
        fields = [
            'id',
            'make_id',
            'manufacturer_name',
            'model',
            'mrp',
            'unit_of_measure',
            'unit_of_measure_display',
            'version',
            'variant',
            'state_of_supply',
            'state_of_supply_display',
            'created_by',
            'created_at',
            'updated_at',
            'status'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'manufacturer_name', 'unit_of_measure_display', 'state_of_supply_display']
    
    def validate_make_id(self, value):
        """Validate that the selected manufacturer exists and has manufacturer role"""
        if not value.role or value.role.key.lower() != 'manufacturer':
            raise serializers.ValidationError("Selected user is not a manufacturer.")
        return value
    
    def validate_mrp(self, value):
        """Validate MRP is positive"""
        if value <= 0:
            raise serializers.ValidationError("MRP must be greater than 0.")
        return value

class DeviceCreateSerializer(serializers.ModelSerializer):
    """Serializer specifically for device creation"""
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
        """Validate that the selected manufacturer exists and has manufacturer role"""
        if not value.role or value.role.key.lower() != 'manufacturer':
            raise serializers.ValidationError("Selected user is not a manufacturer.")
        return value
    
    def validate_mrp(self, value):
        """Validate MRP is positive"""
        if value <= 0:
            raise serializers.ValidationError("MRP must be greater than 0.")
        return value
    
    def create(self, validated_data):
        # Set created_by from the request user
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)