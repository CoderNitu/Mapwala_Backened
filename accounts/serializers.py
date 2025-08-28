# accounts/serializers.py
from rest_framework import serializers
from .models import User, Role
# accounts/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims (extra info inside JWT itself)
        token['username'] = user.username
        token['role'] = user.role.name if user.role else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add extra info to response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'role': self.user.role.name if self.user.role else None,
        }
        return data


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "key", "name"]


class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    reports_to = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "role", "reports_to"]

    def get_reports_to(self, obj):
        if obj.reports_to:
            return {
                "id": obj.reports_to.id,
                "username": obj.reports_to.username,
                "role": {
                    "id": obj.reports_to.role.id if obj.reports_to.role else None,
                    "key": obj.reports_to.role.key if obj.reports_to.role else None,
                    "name": obj.reports_to.role.name if obj.reports_to.role else None,
                } if obj.reports_to.role else None,
            }
        return None


class UserCreateSerializer(serializers.ModelSerializer):
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        source="role",
        write_only=True
    )

    # 🔹 Instead of forcing PK only, allow username as input
    reports_to_username = serializers.SlugRelatedField(
        slug_field="username",
        queryset=User.objects.all(),
        source="reports_to",
        required=False,
        allow_null=True,
        write_only=True
    )

    class Meta:                                                              
        model = User
        fields = [
            "id", "username","password", "role_id", "reports_to_username"
        ]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user
