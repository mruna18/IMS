from django.db import models
from django.conf import settings
from django.utils import timezone


class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    is_active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='warehouses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Location(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.DO_NOTHING, related_name="locations")
    code = models.CharField(max_length=50)  # e.g., "A1-R2"
    description = models.TextField(blank=True)

    # Address info
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, default="India")  # optional

    is_active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('warehouse', 'code')

    def __str__(self):
        return f"{self.code} ({self.warehouse.name})"
