from django.contrib import admin
from .models import TaskType, PutAwayTask, PickUpTask

@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'description')
    search_fields = ('code', 'name')


@admin.register(PutAwayTask)
class PutAwayTaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'inward',
        'get_from_location',
        'get_to_location',
        'assigned_to',
        'is_completed',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'inward__id',
        'from_location__code',
        'to_location__code',
        'assigned_to__username',
    )
    list_filter = ('is_completed', 'deleted')

    def get_from_location(self, obj):
        return obj.from_location.code if obj.from_location else None
    get_from_location.short_description = 'From Location'

    def get_to_location(self, obj):
        return obj.to_location.code if obj.to_location else None
    get_to_location.short_description = 'To Location'


@admin.register(PickUpTask)
class PickUpTaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'outward',
        'get_from_location',
        'get_to_location',
        'assigned_to',
        'is_completed',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'outward__id',
        'from_location__code',
        'to_location__code',
        'assigned_to__username',
    )
    list_filter = ('is_completed', 'deleted')

    def get_from_location(self, obj):
        return obj.from_location.code if obj.from_location else None
    get_from_location.short_description = 'From Location'

    def get_to_location(self, obj):
        return obj.to_location.code if obj.to_location else None
    get_to_location.short_description = 'To Location'
