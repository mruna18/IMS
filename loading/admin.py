from django.contrib import admin

# Register your models here.
from .models import *

@admin.register(Loading)
class LoadingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'outward',
        'vehicle_number',
        'driver_name',
        'is_completed',
        'started_at',
        'completed_at',
        'remarks',
        'created_by',
        'updated_by',
    )
    search_fields = ('outward__id', 'vehicle_number', 'driver_name')
    list_filter = ('is_completed', 'deleted')
   