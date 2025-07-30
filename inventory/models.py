from django.db import models
from django.conf import settings
from django.db.models import Sum


class ItemCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, null=True, blank=True)
    description = models.TextField(blank=True,null=True)

    def __str__(self):
        return self.name
    
class ItemBatch(models.Model):
    batch_number = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.batch_number
    
class ItemLot(models.Model):
    lot_number = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.lot_number
    
class QualityStatus(models.Model):
    code = models.CharField(max_length=20, unique=True)  # e.g., good, damaged, expired
    name = models.CharField(max_length=50)               # e.g., Good, Damaged, Expired
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
    


class Item(models.Model):
    name = models.CharField(max_length=100, unique=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
    unit = models.CharField(max_length=20, null=True, blank=True)  # e.g., pcs, kg, box
    sku = models.CharField(max_length=100, unique=True, null=True, blank=True)  # Stock Keeping Unit
    
    category = models.ForeignKey(ItemCategory, on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.CharField(max_length=100, null=True, blank=True)
    model = models.CharField(max_length=100, null=True, blank=True)
    supplier = models.CharField(max_length=200, null=True, blank=True)
    
    minimum_stock_level = models.PositiveIntegerField(default=0, null=True, blank=True)
    reorder_point = models.PositiveIntegerField(default=0, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name or ''



class Inventory(models.Model):
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING, null=True, blank=True)
    location = models.ForeignKey('warehouse.Location', on_delete=models.DO_NOTHING, null=True, blank=True)

    quantity = models.FloatField(null=True, blank=True)
    reserved_quantity = models.FloatField(null=True, blank=True)

    batch = models.ForeignKey('ItemBatch', on_delete=models.SET_NULL, null=True, blank=True)
    lot = models.ForeignKey('ItemLot', on_delete=models.SET_NULL, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    quality_status = models.ForeignKey('QualityStatus', on_delete=models.SET_NULL, null=True, blank=True)

    remarks = models.TextField(null=True, blank=True)
    deleted = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        related_name='inventory_created_by',
        null=True, blank=True
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        related_name='inventory_updated_by',
        null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = ('item', 'location', 'batch', 'lot')

    def __str__(self):
        return f"{self.item.name} at {self.location.code} - {self.quantity}" if self.item and self.location else "Inventory Entry"



class Inward(models.Model):
    item = models.ForeignKey('Item', on_delete=models.DO_NOTHING, null=True, blank=True)
    location = models.ForeignKey('warehouse.Location', on_delete=models.DO_NOTHING, null=True, blank=True)
    quantity = models.FloatField(null=True, blank=True)

    purchase_order = models.ForeignKey('PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True)
    purchase_order_item = models.ForeignKey('PurchaseOrderItem', on_delete=models.SET_NULL, null=True, blank=True)

    supplier = models.ForeignKey('Supplier', on_delete=models.DO_NOTHING, null=True, blank=True)
    delivery_note = models.CharField(max_length=100, null=True, blank=True)
    invoice_number = models.CharField(max_length=100, null=True, blank=True)
    payment_terms = models.CharField(max_length=100, null=True, blank=True)
    supplier_rating = models.FloatField(null=True, blank=True)
    reference_number = models.CharField(max_length=100, null=True, blank=True)

    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    date = models.DateField(auto_now_add=True, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Inward #{self.id} - {self.item.name if self.item else 'Unknown Item'} at {self.location.code if self.location else 'Unknown Location'}"

class InwardItem(models.Model):
    inward = models.ForeignKey(Inward, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.FloatField(null=True, blank=True)
    rate = models.FloatField(null=True, blank=True)
    quality_status = models.ForeignKey(QualityStatus, on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(blank=True)

    purchase_order = models.ForeignKey('PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True)
    purchase_order_item = models.ForeignKey('PurchaseOrderItem', on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)



class Outward(models.Model):
    item = models.ForeignKey('Item', on_delete=models.DO_NOTHING, null=True, blank=True)
    location = models.ForeignKey('warehouse.Location', on_delete=models.DO_NOTHING, null=True, blank=True)
    quantity = models.FloatField(null=True, blank=True)
    dispatched_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, blank=True)
    date = models.DateField(auto_now_add=True, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='outward_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='outward_updated')
    deleted = models.BooleanField(default=False)
    is_dispatched = models.BooleanField(default=False)
    dispatched_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Outward #{self.id} - {self.item.name if self.item else 'Unknown Item'} from {self.location.code if self.location else 'Unknown Location'}"

class InventoryTransfer(models.Model):
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING, null=True, blank=True)
    from_location = models.ForeignKey('warehouse.Location', on_delete=models.DO_NOTHING, related_name='transfer_from', null=True, blank=True)
    to_location = models.ForeignKey('warehouse.Location', on_delete=models.DO_NOTHING, related_name='transfer_to', null=True, blank=True)

    quantity = models.FloatField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    transfer_date = models.DateField(auto_now_add=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='transfer_created_by', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.name} transfer from {self.from_location.code} to {self.to_location.code}"


class InventoryAdjustment(models.Model):
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING, null=True, blank=True)
    location = models.ForeignKey('warehouse.Location', on_delete=models.DO_NOTHING, null=True, blank=True)

    quantity_before = models.FloatField(null=True, blank=True)
    quantity_after = models.FloatField(null=True, blank=True)
    reason = models.TextField(null=True, blank=True)
    adjustment_date = models.DateField(auto_now_add=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='adjustment_created_by', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Adjustment for {self.item.name} at {self.location.code}"


class InventoryReturn(models.Model):
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING, null=True, blank=True)
    location = models.ForeignKey('warehouse.Location', on_delete=models.DO_NOTHING, null=True, blank=True)

    quantity = models.FloatField(null=True, blank=True)
    reason = models.TextField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    is_defective = models.BooleanField(default=False)
    return_date = models.DateField(auto_now_add=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='return_created_by', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Return of {self.item.name} from {self.location.code}"

#inventory reconciliation / physical counting
class CycleCount(models.Model):
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING, null=True, blank=True)
    location = models.ForeignKey('warehouse.Location', on_delete=models.DO_NOTHING, null=True, blank=True)

    system_quantity = models.FloatField(null=True, blank=True)
    counted_quantity = models.FloatField(null=True, blank=True)
    discrepancy = models.FloatField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    count_date = models.DateField(auto_now_add=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name='cycle_count_created_by', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # def save(self, *args, **kwargs):
    #     if self.system_quantity is not None and self.counted_quantity is not None:
    #         self.discrepancy = self.counted_quantity - self.system_quantity
    #     super().save(*args, **kwargs)

    def __str__(self):
        return f"Cycle count for {self.item.name} at {self.location.code}"


class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    payment_terms = models.CharField(max_length=100, null=True, blank=True)  # e.g., Net 30, Advance
    supplier_rating = models.IntegerField(null=True, blank=True)  # 1 to 5 or percentage

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.DO_NOTHING)
    order_date = models.DateField(auto_now_add=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    reference_number = models.CharField(max_length=100, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PO#{self.id} - {self.supplier.name}"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey('PurchaseOrder', on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey('inventory.Item', on_delete=models.DO_NOTHING)
    quantity = models.FloatField(null=True, blank=True)
    rate = models.FloatField(null=True, blank=True)  
    remarks = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.item.name} x {self.quantity} (PO#{self.purchase_order.id})"
    
    @property
    def fulfilled_quantity(self):
        total = InwardItem.objects.filter(purchase_order_item=self).aggregate(
            total_received=Sum('quantity')
        )['total_received'] or 0
        return total

    @property
    def remaining_quantity(self):
        return self.quantity - self.fulfilled_quantity

class InventoryActionType(models.Model):
    code = models.CharField(max_length=50, unique=True)  # e.g., 'inward', 'transfer'
    name = models.CharField(max_length=100)              # e.g., 'Inward Entry', 'Stock Transfer'
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

class InventoryLog(models.Model):
    inventory = models.ForeignKey('Inventory', on_delete=models.CASCADE, null=True, blank=True)
    item = models.ForeignKey('Item', on_delete=models.DO_NOTHING, null=True, blank=True)
    location = models.ForeignKey('warehouse.Location', on_delete=models.DO_NOTHING, null=True, blank=True)

    action_type = models.ForeignKey('InventoryActionType', on_delete=models.SET_NULL, null=True, blank=True)
    reference_id = models.IntegerField(null=True, blank=True)       # ID from related model
    reference_type = models.CharField(max_length=50, null=True, blank=True)

    quantity_before = models.FloatField(null=True, blank=True)
    quantity_changed = models.FloatField(null=True, blank=True)
    quantity_after = models.FloatField(null=True, blank=True)

    remarks = models.TextField(null=True, blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.name} at {self.location.code} - {self.action_type.name if self.action_type else 'Unknown'}"
