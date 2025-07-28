from django.contrib import admin
from .models import Warehouse, Location

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'owner','is_active','created_at', 'updated_at','deleted')
    search_fields = ('name',)
    list_filter = ('is_active',)

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'warehouse', 'is_active', 'created_at', 'updated_at', 'deleted')
    search_fields = ('code', 'warehouse__name')
    list_filter = ('warehouse', 'is_active')
