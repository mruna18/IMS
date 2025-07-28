from django.db import models
from django.conf import settings


class Item(models.Model):
    name = models.CharField(max_length=100, unique=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    unit = models.CharField(max_length=20, null=True, blank=True)  # e.g., pcs, kg, box
    is_active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name or ''


class Inventory(models.Model):
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING, null=True, blank=True)
    location = models.ForeignKey('warehouse.Location', on_delete=models.DO_NOTHING, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='inventory_created_by', null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='inventory_updated_by', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('item', 'location')

    def __str__(self):
        return f"{self.item.name} at {self.location.code} - {self.quantity}" if self.item and self.location else "Inventory Item"


class Inward(models.Model):
    item = models.ForeignKey('Item', on_delete=models.DO_NOTHING, null=True, blank=True)
    location = models.ForeignKey('warehouse.Location', on_delete=models.DO_NOTHING, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, blank=True)
    date = models.DateField(auto_now_add=True, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Inward #{self.id} - {self.item.name if self.item else 'Unknown Item'} at {self.location.code if self.location else 'Unknown Location'}"


class Outward(models.Model):
    item = models.ForeignKey('Item', on_delete=models.DO_NOTHING, null=True, blank=True)
    location = models.ForeignKey('warehouse.Location', on_delete=models.DO_NOTHING, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dispatched_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, blank=True)
    date = models.DateField(auto_now_add=True, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted = models.BooleanField(default=False)
    is_dispatched = models.BooleanField(default=False)
    dispatched_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Outward #{self.id} - {self.item.name if self.item else 'Unknown Item'} from {self.location.code if self.location else 'Unknown Location'}"


class InventoryLog(models.Model):
    item = models.ForeignKey('Item', on_delete=models.DO_NOTHING, null=True, blank=True)
    location = models.ForeignKey('warehouse.Location', on_delete=models.DO_NOTHING, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    movement_type = models.CharField(max_length=10, choices=[('IN', 'Inward'), ('OUT', 'Outward')], null=True, blank=True)
    reference_id = models.IntegerField(null=True, blank=True)  # Link to Inward/Outward ID
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted = models.BooleanField(default=False)

