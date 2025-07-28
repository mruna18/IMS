from django.db import models
from django.conf import settings
from warehouse.models import Location  # optional

class Role(models.Model):
    code = models.CharField(max_length=50, unique=True)  # e.g., 'admin', 'operator'
    name = models.CharField(max_length=100)              # e.g., 'Warehouse Admin'
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Employee(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, unique=True)
    role = models.ForeignKey(Role, on_delete=models.DO_NOTHING)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role.name})"