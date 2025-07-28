from django.contrib import admin
from .models import TaskType, PutAwayTask, PickUpTask

@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'description')
    search_fields = ('code', 'name')


@admin.register(PutAwayTask)
class PutAwayTaskAdmin(admin.ModelAdmin):
    list_display = ('inward', 'get_destination_location', 'assigned_to', 'is_completed', 'created_at', 'updated_at')
    search_fields = ('inward__id', 'inward__location__code', 'assigned_to__username')
    list_filter = ('is_completed', 'deleted')

    def get_destination_location(self, obj):
        return obj.inward.location.code if obj.inward and obj.inward.location else None
    get_destination_location.short_description = 'Destination Location'


@admin.register(PickUpTask)
class PickUpTaskAdmin(admin.ModelAdmin):
    list_display = ('outward', 'get_source_location', 'assigned_to', 'is_completed', 'created_at', 'updated_at')
    search_fields = ('outward__id', 'outward__location__code', 'assigned_to__username')
    list_filter = ('is_completed', 'deleted')

    def get_source_location(self, obj):
        return obj.outward.location.code if obj.outward and obj.outward.location else None
    get_source_location.short_description = 'Source Location'
