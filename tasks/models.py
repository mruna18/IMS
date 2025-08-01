from django.db import models
from django.conf import settings
from inventory.models import *
from warehouse.models import *


class TaskType(models.Model):
    code = models.CharField(max_length=50, unique=True, null=True, blank=True)  # e.g., PUTAWAY, PICKUP
    name = models.CharField(max_length=100, null=True, blank=True)  # e.g., Put Away Task, Pick Up Task
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True) 

    def __str__(self):
        return self.name or "Unnamed TaskType"
    
#!-------------------------------------------------------------------------------------------------
class InventoryTask(models.Model):
    task_type = models.ForeignKey(TaskType, on_delete=models.DO_NOTHING, null=True, blank=True)

    transaction = models.ForeignKey('inventory.InventoryTransaction', on_delete=models.DO_NOTHING, null=True, blank=True)
    item = models.ForeignKey('inventory.Item', on_delete=models.DO_NOTHING, null=True, blank=True)

    from_location = models.ForeignKey('warehouse.Location', on_delete=models.DO_NOTHING, related_name='task_from', null=True, blank=True)
    to_location = models.ForeignKey('warehouse.Location', on_delete=models.DO_NOTHING, related_name='task_to', null=True, blank=True)
    quantity = models.FloatField(null=True, blank=True)

    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='tasks_created', null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='tasks_updated', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.task_type.name} Task #{self.id} - Item: {self.item.name if self.item else 'Unknown'}"


#!-------------------------------------------------------------------------------------------------


# class PutAwayTask(models.Model):
#     inward = models.ForeignKey(Inward, on_delete=models.DO_NOTHING, related_name='putaway_tasks', null=True, blank=True)
#     item = models.ForeignKey('inventory.Item', on_delete=models.DO_NOTHING, null=True, blank=True)
#     from_location = models.ForeignKey(Location, on_delete=models.DO_NOTHING, related_name='putaway_from', null=True, blank=True)
#     to_location = models.ForeignKey(Location, on_delete=models.DO_NOTHING, related_name='putaway_to', null=True, blank=True)
#     quantity = models.FloatField(null=True, blank=True)
#     task_type = models.ForeignKey(TaskType, on_delete=models.DO_NOTHING, null=True, blank=True)
#     assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, blank=True)
#     is_completed = models.BooleanField(default=False)
#     completed_at = models.DateTimeField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     deleted = models.BooleanField(default=False)
#     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='created_putaway_tasks', null=True, blank=True)
#     updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='updated_putaway_tasks', null=True, blank=True)

#     def __str__(self):
#         return f"PutAway Task #{self.id} for Inward #{self.inward.id}" if self.inward else f"PutAway Task #{self.id}"


# class PickUpTask(models.Model):
#     outward = models.ForeignKey(Outward, on_delete=models.DO_NOTHING, related_name='pickup_tasks', null=True, blank=True)
#     item = models.ForeignKey('inventory.Item', on_delete=models.DO_NOTHING, null=True, blank=True)
#     from_location = models.ForeignKey(Location, on_delete=models.DO_NOTHING, related_name='pickup_from', null=True, blank=True)
#     to_location = models.ForeignKey(Location, on_delete=models.DO_NOTHING, related_name='pickup_to', null=True, blank=True)
#     quantity = models.FloatField(null=True, blank=True)
#     task_type = models.ForeignKey(TaskType, on_delete=models.DO_NOTHING, null=True, blank=True)
#     assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, blank=True)
#     is_completed = models.BooleanField(default=False)
#     completed_at = models.DateTimeField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     deleted = models.BooleanField(default=False)
#     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='created_pickup_tasks', null=True, blank=True)
#     updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='updated_pickup_tasks', null=True, blank=True)

#     def __str__(self):
#         return f"PickUp Task #{self.id} for Outward #{self.outward.id}" if self.outward else f"PickUp Task #{self.id}"

class UserTaskStatus(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, blank=True)
    task = models.ForeignKey('InventoryTask', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, default='Pending', null=True, blank=True)  # e.g. Pending, Started, Completed
    remarks = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.task.task_type.name} Task #{self.task.id} - {self.status}" if self.user and self.task else "UserTaskStatus"
