from django.db import models

# Create your models here.
from django.conf import settings

class Loading(models.Model):
    outward = models.ForeignKey('inventory.Outward', on_delete=models.DO_NOTHING, related_name='loadings')
    vehicle_number = models.CharField(max_length=50, blank=True, null=True)
    driver_name = models.CharField(max_length=100, blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='created_loadings', null=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='updated_loadings', null=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Loading for Outward #{self.outward.id}"
