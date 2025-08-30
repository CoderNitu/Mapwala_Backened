from django.db import models
from django.conf import settings

# Reuse State from accounts app
from accounts.models import State


class District(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="districts")
    status = models.BooleanField(default=True)  # active/inactive
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["state__name", "name"]
        unique_together = ("state", "code")  # optional: ensure unique code per state

    def __str__(self):
        return f"{self.name} ({self.code})"

