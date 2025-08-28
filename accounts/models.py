# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


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


class User(AbstractUser):
    role = models.ForeignKey(
        Role, null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
    )
    reports_to = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="team_members"
    )

    def save(self, *args, **kwargs):
        # Auto-assign "Admin" role for superusers if not set
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

    # 🔹 Fix: Add capability check for views/permissions
    def has_capability(self, code: str) -> bool:
        if self.is_superuser:
            return True
        return self.role.has_capability(code) if self.role else False

    # 🔹 Fix: Add manager check for views
    def is_manager_of(self, user) -> bool:
        """Check if this user is an ancestor manager of another user."""
        current = user.reports_to
        while current:
            if current == self:
                return True
            current = current.reports_to
        return False
