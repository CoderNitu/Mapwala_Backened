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

    address = models.CharField(max_length=255, blank=True, null=True)
    gst_no = models.CharField(max_length=20, blank=True, null=True, unique=True)
    tan_no = models.CharField(max_length=20, blank=True, null=True, unique=True)
    state = models.ForeignKey(State, null=True, blank=True, on_delete=models.SET_NULL, related_name="users")
    gst_upload = models.FileField(upload_to="uploads/gst/", null=True, blank=True)
    tan_upload = models.FileField(upload_to="uploads/tan/", null=True, blank=True)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["username"]  # keep username but not required for login

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
