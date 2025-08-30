from rest_framework import serializers
from .models import District
from accounts.models import State
from accounts.serializers import StateSerializer  # reuse existing serializer

class DistrictSerializer(serializers.ModelSerializer):
    state = StateSerializer(read_only=True)
    state_id = serializers.PrimaryKeyRelatedField(
        queryset=State.objects.all(), source="state", write_only=True, required=True
    )

    class Meta:
        model = District
        fields = [
            "id",
            "name",          # District Name (UI)
            "code",          # District Code (UI)
            "state",         # nested state object (read)
            "state_id",      # write-only id -> state (write)
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("created_at", "updated_at")
