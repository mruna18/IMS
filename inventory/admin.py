from django.contrib import admin

# Register your models here.

from .models import *
from .serializers import *

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'unit', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('is_active',)

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('id','item', 'location', 'quantity', 'created_at', 'updated_at')
    search_fields = ('item__name', 'location__name')
    list_filter = ('location',)

@admin.register(Inward)
class InwardAdmin(admin.ModelAdmin):
    list_display = ('id','item', 'location', 'quantity', 'received_by', 'date', 'created_at', 'updated_at')
    search_fields = ('item__name', 'location__name', 'received_by__username')
    list_filter = ('location', 'received_by')

@admin.register(Outward)
class OutwardAdmin(admin.ModelAdmin):
    list_display = ('id','item', 'location', 'quantity', 'dispatched_by', 'date', 'created_at', 'updated_at')
    search_fields = ('item__name', 'location__name', 'dispatched_by__username')
    list_filter = ('location', 'dispatched_by')
    
@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('id','item', 'location', 'quantity', 'movement_type', 'reference_id', 'created_at')
    search_fields = ('item__name', 'location__name', 'movement_type')
    list_filter = ('movement_type',)
