from django.db import models

class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Location(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="locations")
    code = models.CharField(max_length=50)  # e.g., "A1-R2"
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} ({self.warehouse.name})"
    class Meta:
        unique_together = ('warehouse', 'code')     

        # Ensures that each location code is unique within a warehouse
        # This prevents duplicate location codes within the same warehouse.
        