# accounts/serializers.py
from rest_framework import serializers
from .models import User, Role, State
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate

# -------------------- Custom JWT --------------------
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "phone_number"

    def validate(self, attrs):
        phone_number = attrs.get("phone_number")
        password = attrs.get("password")
        user = authenticate(phone_number=phone_number, password=password)
        if not user:
            raise serializers.ValidationError("Invalid phone number or password.")

        data = super().validate(attrs)

        # Include full user info in login response
        data['user'] = {
            'id': user.id,
            'phone_number': user.phone_number,
            'username': user.username,
            'role': user.role.name if user.role else None,
        }
        if user.role and user.role.key.lower() != "admin":
            data['user']['reports_to'] = user.reports_to.phone_number if user.reports_to else None
        return data

# -------------------- Role Serializer --------------------
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "key", "name"]

# -------------------- State Serializer --------------------
class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ["id", "name"]

# -------------------- User Serializer (for GET/list) --------------------
class UserSerializer(serializers.ModelSerializer):
    role_id = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), source="role")
    username = serializers.CharField(required=False, allow_blank=True)
    reports_to = serializers.SerializerMethodField()
    state = StateSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "phone_number", "username", "role_id", "reports_to",
            "address", "gst_no", "tan_no", "state",
            "gst_upload", "tan_upload"
        ]

    def get_reports_to(self, obj):
        if obj.reports_to:
            return {
                "id": obj.reports_to.id,
                "phone_number": obj.reports_to.phone_number
            }
        return None

# -------------------- User Create Serializer (for POST) --------------------
class UserCreateSerializer(serializers.ModelSerializer):
    role_id = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), source="role", write_only=True)
    reports_to = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    username = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    gst_no = serializers.CharField(required=False, allow_blank=True)
    tan_no = serializers.CharField(required=False, allow_blank=True)
    state_id = serializers.PrimaryKeyRelatedField(queryset=State.objects.all(), source="state", required=False, allow_null=True, write_only=True)
    gst_upload = serializers.FileField(required=False, allow_null=True)
    tan_upload = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            "id", "phone_number", "username", "password", "role_id", "reports_to",
            "address", "gst_no", "tan_no", "state_id", "gst_upload", "tan_upload"
        ]
        extra_kwargs = {"password": {"write_only": True}}

    # Allow reports_to by ID or phone_number
    def validate_reports_to(self, value):
        if not value:
            return None
        if value.isdigit():
            try:
                return User.objects.get(id=int(value))
            except User.DoesNotExist:
                raise serializers.ValidationError("No user found with this ID.")
        else:
            try:
                return User.objects.get(phone_number=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("No user found with this phone_number.")

    def create(self, validated_data):
        reports_to = validated_data.pop("reports_to", None)
        if reports_to:
            validated_data["reports_to"] = reports_to

        password = validated_data.pop("password", None)
        username = validated_data.pop("username", None)
        role = validated_data.get("role")

        user = User(**validated_data)

        # 🔹 Set username for all users, not only admin
        if username:
            user.username = username
        elif not username and role and role.key.lower() == "admin":
            user.username = "admin"

        if password:
            user.set_password(password)

        user.save()
        return user
