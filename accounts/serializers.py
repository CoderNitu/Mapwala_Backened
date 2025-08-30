# accounts/serializers.py
from rest_framework import serializers
from .models import User, Role, State
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _


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
        data["user"] = {
            "id": user.id,
            "phone_number": user.phone_number,
            "username": user.username,
            "role": user.role.name if user.role else None,
        }
        if user.role and user.role.key.lower() != "admin":
            data["user"]["reports_to"] = user.reports_to.phone_number if user.reports_to else None
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
        fields = ["id", "name", "status", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


# -------------------- Admin User Serializer (Clean response for admins) --------------------
class AdminUserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "phone_number", "username", "role"]


# -------------------- User Serializer (for GET/list/detail) --------------------
class UserSerializer(serializers.ModelSerializer):
    # Frontend expects 'name' but we store 'username'
    name = serializers.CharField(source="username", required=False, allow_blank=True)

    role = RoleSerializer(read_only=True)

    reports_to = serializers.SerializerMethodField()

    # state nested read
    state = StateSerializer(read_only=True)

    # district: nested object if FK present, else fallback to legacy string
    district = serializers.SerializerMethodField()

    # New frontend mappings
    accountHolderName = serializers.CharField(source="account_holder_name", required=False, allow_blank=True)
    accountNumber = serializers.CharField(source="account_number", required=False, allow_blank=True)
    bankName = serializers.CharField(source="bank_name", required=False, allow_blank=True)
    ifsc = serializers.CharField(required=False, allow_blank=True)
    pan = serializers.CharField(required=False, allow_blank=True)
    panUpload = serializers.FileField(source="pan_upload", required=False, allow_null=True)
    gstUpload = serializers.FileField(source="gst_upload", required=False, allow_null=True)
    tanUpload = serializers.FileField(source="tan_upload", required=False, allow_null=True)
    region = serializers.CharField(required=False, allow_blank=True)
    linkedToDistributor = serializers.BooleanField(source="linked_to_distributor", required=False)
    linkedToManufacturer = serializers.BooleanField(source="linked_to_manufacturer", required=False)

    # Read-only manufacturers list
    manufacturers = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "phone_number",
            "role",
            "reports_to",
            "address",
            "gst_no",
            "gstUpload",
            "tan_no",
            "tanUpload",
            "accountHolderName",
            "accountNumber",
            "bankName",
            "ifsc",
            "district",
            "pan",
            "panUpload",
            "region",
            "linkedToDistributor",
            "linkedToManufacturer",
            "state",
            "manufacturers",
        ]

    def get_reports_to(self, obj):
        if obj.reports_to:
            return {"id": obj.reports_to.id, "phone_number": obj.reports_to.phone_number}
        return None

    def get_district(self, obj):
        # Prefer FK (district_fk) if available
        try:
            district_fk = getattr(obj, "district_fk", None)
            if district_fk:
                return {"id": district_fk.id, "name": district_fk.name}
        except Exception:
            # defensive: if locations not available, fall back to string
            pass

        # fallback to legacy string field
        if getattr(obj, "district", None):
            return obj.district
        return None

    def get_manufacturers(self, obj):
        try:
            qs = obj.manufacturers.all()
        except Exception:
            return []
        return [{"id": m.id, "name": m.username, "phone_number": m.phone_number} for m in qs]

    def to_representation(self, instance):
        """
        If the user being serialized is an admin (role.key == 'admin'),
        return the compact admin representation.
        Otherwise return the full representation but remove nulls.
        """
        if instance.role and getattr(instance.role, "key", "").lower() == "admin":
            return AdminUserSerializer(instance, context=self.context).data

        rep = super().to_representation(instance)
        return {k: v for k, v in rep.items() if v is not None}


# -------------------- User Create / Update Serializer (for POST/PUT) --------------------
class UserCreateSerializer(serializers.ModelSerializer):
    # Accept 'name' from frontend to map to username
    name = serializers.CharField(source="username", required=False, allow_blank=True)

    # role write: will provide a Role instance in validated_data under 'role'
    role_id = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), source="role", write_only=True)

    # reports_to: accepts either id or phone_number
    reports_to = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)

    # state write
    state_id = serializers.PrimaryKeyRelatedField(queryset=State.objects.all(), source="state", required=False, allow_null=True, write_only=True)

    # district: write-only -- accept id or name; we'll resolve to district_fk
    district = serializers.CharField(required=False, allow_blank=True, write_only=True)

    # front-end mapped fields (write)
    accountHolderName = serializers.CharField(source="account_holder_name", required=False, allow_blank=True)
    accountNumber = serializers.CharField(source="account_number", required=False, allow_blank=True)
    bankName = serializers.CharField(source="bank_name", required=False, allow_blank=True)
    ifsc = serializers.CharField(required=False, allow_blank=True)
    pan = serializers.CharField(required=False, allow_blank=True)
    panUpload = serializers.FileField(source="pan_upload", required=False, allow_null=True)
    gstUpload = serializers.FileField(source="gst_upload", required=False, allow_null=True)
    tanUpload = serializers.FileField(source="tan_upload", required=False, allow_null=True)
    region = serializers.CharField(required=False, allow_blank=True)
    linkedToDistributor = serializers.BooleanField(source="linked_to_distributor", required=False)
    linkedToManufacturer = serializers.BooleanField(source="linked_to_manufacturer", required=False)

    # manufacturer relation for distributor/dealer
    manufacturer_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), write_only=True, required=False, allow_empty=True)

    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "phone_number",
            "password",
            "role_id",
            "reports_to",
            "address",
            "gst_no",
            "gstUpload",
            "tan_no",
            "tanUpload",
            "accountHolderName",
            "accountNumber",
            "bankName",
            "ifsc",
            "district",
            "pan",
            "panUpload",
            "region",
            "linkedToDistributor",
            "linkedToManufacturer",
            "state_id",
            "manufacturer_ids",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    # ---- field-level validation for reports_to (return User instance or None) ----
    def validate_reports_to(self, value):
        if value in (None, "", "null"):
            return None
        s = str(value).strip()
        if s.isdigit():
            try:
                return User.objects.get(id=int(s))
            except User.DoesNotExist:
                raise serializers.ValidationError("No user found with this ID.")
        else:
            try:
                return User.objects.get(phone_number=s)
            except User.DoesNotExist:
                raise serializers.ValidationError("No user found with this phone_number.")

    # ---- helper: resolve district to District instance ----
    def _resolve_district_value(self, district_value):
        if district_value in (None, "", "null"):
            return None
        s = str(district_value).strip()
        try:
            from locations.models import District
        except Exception:
            raise serializers.ValidationError({"district": _("District model not available.")})

        if s.isdigit():
            try:
                return District.objects.get(pk=int(s))
            except District.DoesNotExist:
                raise serializers.ValidationError({"district": _("No district found with this id.")})
        try:
            return District.objects.get(name__iexact=s)
        except District.DoesNotExist:
            raise serializers.ValidationError({"district": _("No district found with this name.")})

    def validate(self, attrs):
        """
        - Enforce linked flags rules per role
        - Validate manufacturer_ids (ensure they correspond to users with role 'manufacturer') for distributor/dealer
        Returns attrs with optional '_validated_manufacturers' list for use in create/update.
        """
        role = attrs.get("role")  # Role instance (because role_id source="role")
        manu_ids = attrs.get("manufacturer_ids", None)

        # linked flags rules
        if role:
            key = getattr(role, "key", "").lower()
            if key in ["manufacturer", "vendor", "buyer"]:
                attrs["linked_to_distributor"] = False
                attrs["linked_to_manufacturer"] = False
            elif key == "distributor":
                # distributors may have manufacturer links; linked_to_distributor forced False
                attrs["linked_to_distributor"] = False
            elif key == "dealer":
                # dealer may have both flags; allow as provided
                pass

            # manufacturer relationship requirement for distributor/dealer
            if key in ["distributor", "dealer"]:
                # if manu_ids is not provided or empty -> treat as error (business rule)
                if not manu_ids:
                    raise serializers.ValidationError({"manufacturer_ids": _("Distributor/Dealer must be linked to manufacturer(s).")})
                # validate manufacturer ids
                valid_manufacturers = []
                for mid in manu_ids:
                    try:
                        u = User.objects.get(pk=int(mid))
                    except (User.DoesNotExist, ValueError):
                        raise serializers.ValidationError({"manufacturer_ids": _(f"Manufacturer id {mid} not found.")})
                    if not (u.role and getattr(u.role, "key", "").lower() == "manufacturer"):
                        raise serializers.ValidationError({"manufacturer_ids": _(f"User id {mid} is not a manufacturer.")})
                    valid_manufacturers.append(u)
                attrs["_validated_manufacturers"] = valid_manufacturers
            else:
                # not distributor/dealer -> ignore manufacturer_ids if provided
                attrs["_validated_manufacturers"] = []
        else:
            # no role provided -> don't validate manufacturer links; set empty list
            attrs["_validated_manufacturers"] = []

        return attrs

    def create(self, validated_data):
        # Extract helper keys so they are not passed to model constructor
        validated_manufacturers = validated_data.pop("_validated_manufacturers", None)
        # Remove manufacturer_ids (write-only helper) to avoid unexpected kwarg on User()
        validated_data.pop("manufacturer_ids", None)

        # resolve district (write-only field)
        district_value = validated_data.pop("district", None)
        if district_value:
            district_obj = self._resolve_district_value(district_value)
            # set FK and legacy string
            validated_data["district_fk"] = district_obj
            validated_data["district"] = district_obj.name if district_obj else validated_data.get("district", None)

        # password handling
        password = validated_data.pop("password", None)
        # name was mapped to username in serializer source (stored under 'username' key)
        username = validated_data.get("username", None)

        user = User(**validated_data)
        if username:
            user.username = username

        if password:
            user.set_password(password)

        user.save()

        # set M2M manufacturers if any
        if validated_manufacturers is not None:
            user.manufacturers.set(validated_manufacturers)

        return user

    def update(self, instance, validated_data):
        # Extract helper keys so they are not passed to model constructor
        validated_manufacturers = validated_data.pop("_validated_manufacturers", None)
        # Remove manufacturer_ids helper if present
        validated_data.pop("manufacturer_ids", None)

        # handle reports_to (field-level validator already converted to User instance)
        reports_to = validated_data.pop("reports_to", None)
        if reports_to is not None:
            instance.reports_to = reports_to

        # district handling (write-only)
        if "district" in self.initial_data:
            district_value = self.initial_data.get("district")
            if district_value in (None, "", "null"):
                instance.district_fk = None
                instance.district = None
            else:
                district_obj = self._resolve_district_value(district_value)
                instance.district_fk = district_obj
                instance.district = district_obj.name if district_obj else instance.district

        # password handling
        password = validated_data.pop("password", None)
        username = validated_data.pop("username", None)

        # update remaining fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if username is not None:
            instance.username = username

        if password:
            instance.set_password(password)

        instance.save()

        # update M2M manufacturers if present
        if validated_manufacturers is not None:
            instance.manufacturers.set(validated_manufacturers)

        return instance
