from django.db import models
from django.conf import settings
# from django.contrib.auth.models import User
from inventory.models import *


class Loading(models.Model):
    outward = models.ForeignKey('inventory.Outward', on_delete=models.DO_NOTHING, related_name='loadings')
    vehicle_number = models.CharField(max_length=50, blank=True, null=True)
    driver_name = models.CharField(max_length=100, blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    loaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    loaded_at = models.DateTimeField(null=True, blank=True)
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING,null=True, blank=True)  
    quantity = models.FloatField(null=True, blank=True)  

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='created_loadings', null=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='updated_loadings', null=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Loading for Outward #{self.outward.id}"
