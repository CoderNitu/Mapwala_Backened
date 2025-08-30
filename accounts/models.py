from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class Capability(models.Model):
    code = models.CharField(max_length=128, unique=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.code


class Role(models.Model):
    key = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    capabilities = models.ManyToManyField(Capability, blank=True, related_name='roles')

    def __str__(self):
        return self.name

    def has_capability(self, code: str) -> bool:
        return self.capabilities.filter(code=code).exists()


# ✅ Custom manager for User
class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("The Phone Number must be set")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone_number, password, **extra_fields)
    


class State(models.Model):
    name = models.CharField(max_length=100, unique=True)
    status = models.BooleanField(default=True)  # active / inactive shown in UI
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name
    



class User(AbstractUser):
    # keep username as a field, but make phone_number the login field
    phone_number = models.CharField(
        max_length=15, unique=True, verbose_name=_("Phone Number")
    )
    role = models.ForeignKey(
        Role, null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
    )
    reports_to = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="team_members"
    )

    # existing fields
    address = models.CharField(max_length=255, blank=True, null=True)
    gst_no = models.CharField(max_length=20, blank=True, null=True, unique=True)
    tan_no = models.CharField(max_length=20, blank=True, null=True, unique=True)
    state = models.ForeignKey(State, null=True, blank=True, on_delete=models.SET_NULL, related_name="users")
    gst_upload = models.FileField(upload_to="uploads/gst/", null=True, blank=True)
    tan_upload = models.FileField(upload_to="uploads/tan/", null=True, blank=True)

    # ---- NEW FIELDS to support Manufacturer/Vendor/Distributor forms ----
    # These are snake_case in DB but serializers expose camelCase names expected by frontend
    account_holder_name = models.CharField(max_length=255, null=True, blank=True)
    account_number = models.CharField(max_length=64, null=True, blank=True)
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    ifsc = models.CharField(max_length=64, null=True, blank=True)
    district = models.CharField(max_length=150, null=True, blank=True)

    district_fk = models.ForeignKey(
        "locations.District",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users"
    )

    pan = models.CharField(max_length=20, null=True, blank=True, unique=True)
    pan_upload = models.FileField(upload_to="uploads/pan/", null=True, blank=True)
    region = models.CharField(max_length=150, null=True, blank=True)
    # link flags
    linked_to_distributor = models.BooleanField(default=False)
    linked_to_manufacturer = models.BooleanField(default=False)
    # NOTE: gst_upload and tan_upload already exist
    manufacturers = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="partners_with",  # manufacturers -> users associated
    )

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    def save(self, *args, **kwargs):
        if self.is_superuser and not self.role:
            try:
                admin_role = Role.objects.get(key__iexact="admin")
                self.role = admin_role
            except Role.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def is_valid_manager(self, manager_user):
        if not self.role or not manager_user or not manager_user.role:
            return False

        role = self.role.key.lower()
        manager_role = manager_user.role.key.lower()

        if role == "admin":
            return False
        elif role == "subadmin":
            return manager_role == "admin"
        elif role in ["gm / manager", "manager"]:
            return manager_role in ["admin", "subadmin"]
        elif role in ["sales executive", "purchase executive", "quality engineer"]:
            return manager_role in ["gm / manager", "manager"]

        return False

    def has_capability(self, code: str) -> bool:
        if self.is_superuser:
            return True
        return self.role.has_capability(code) if self.role else False

    def is_manager_of(self, user) -> bool:
        current = user.reports_to
        while current:
            if current == self:
                return True
            current = current.reports_to
        return False