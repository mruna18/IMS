from django.contrib import admin

# Register your models here.

from .models import *
from .serializers import *

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'unit', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('is_active',)

# @admin.register(Inward)
# class InwardAdmin(admin.ModelAdmin):
#     list_display = ('id','item', 'location', 'quantity', 'received_by', 'date', 'created_at', 'updated_at')
#     search_fields = ('item__name', 'location__name', 'received_by__username')
#     list_filter = ('location', 'received_by')

@admin.register(Inward)
class InwardAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_items', 'location', 'get_total_quantity', 'received_by', 'received_at', 'created_at', 'updated_at']

    def get_items(self, obj):
        return ", ".join(str(item.item.name) for item in obj.items.all())
    get_items.short_description = 'Items'

    def get_total_quantity(self, obj):
        return sum(item.quantity for item in obj.items.all())
    get_total_quantity.short_description = 'Quantity'

@admin.register(Outward)
class OutwardAdmin(admin.ModelAdmin):
    list_display = ('id','item', 'location', 'quantity', 'dispatched_by', 'date', 'created_at', 'updated_at')
    search_fields = ('item__name', 'location__name', 'dispatched_by__username')
    list_filter = ('location', 'dispatched_by')

@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'item',
        'location',
        'action_type',
        'quantity_before',
        'quantity_changed',
        'quantity_after',
        'reference_type',
        'reference_id',
        'changed_by',
        'timestamp'
    ]
    list_filter = ['action_type', 'item', 'location', 'timestamp']
    search_fields = ['item__name', 'location__code', 'reference_type', 'remarks']


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'location', 'quantity', 'reserved_quantity', 'batch', 'lot', 'quality_status', 'expiry_date')
    list_filter = ('location', 'quality_status', 'deleted')
    search_fields = ('item__name', 'batch__batch_number', 'lot__lot_number')
    autocomplete_fields = ('item', 'location', 'batch', 'lot', 'quality_status', 'created_by', 'updated_by')

@admin.register(ItemBatch)
class ItemBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'batch_number', 'description')
    search_fields = ('batch_number',)

@admin.register(ItemLot)
class ItemLotAdmin(admin.ModelAdmin):
    list_display = ('id', 'lot_number', 'description')
    search_fields = ('lot_number',)

@admin.register(QualityStatus)
class QualityStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name')
    search_fields = ('code', 'name')

@admin.register(InventoryTransfer)
class InventoryTransferAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'from_location', 'to_location', 'quantity', 'transfer_date')
    search_fields = ('item__name', 'from_location__code', 'to_location__code')
    list_filter = ('transfer_date',)

@admin.register(InventoryAdjustment)
class InventoryAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'location', 'quantity_before', 'quantity_after', 'adjustment_date')
    search_fields = ('item__name', 'location__code')
    list_filter = ('adjustment_date',)

@admin.register(InventoryReturn)
class InventoryReturnAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'location', 'quantity', 'reason','remarks','is_defective', 'return_date')
    search_fields = ('item__name', 'location__code')
    list_filter = ('is_defective', 'return_date')

@admin.register(CycleCount)
class CycleCountAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'location', 'system_quantity', 'counted_quantity', 'discrepancy', 'count_date')
    search_fields = ('item__name', 'location__code')
    list_filter = ('count_date',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'contact_person', 'phone', 'email', 'supplier_rating')
    search_fields = ('name', 'contact_person')

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'order_date', 'expected_delivery_date', 'reference_number')
    search_fields = ('supplier__name', 'reference_number')

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'purchase_order', 'item', 'quantity', 'rate']
    search_fields = ['purchase_order__id', 'item__name']

@admin.register(InventoryActionType)
class InventoryActionTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name')
    search_fields = ('code', 'name')

@admin.register(InwardItem)
class InwardItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'item', 'inward', 'quantity', 'rate', 'quality_status']
