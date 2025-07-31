from rest_framework import serializers
from .models import *


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'

class ItemCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCategory
        fields = '__all__'
class ItemBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemBatch
        fields = '__all__'


class ItemLotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemLot
        fields = '__all__'


class QualityStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityStatus
        fields = '__all__'

class InventorySerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    location_code = serializers.CharField(source='location.code', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    lot_number = serializers.CharField(source='lot.lot_number', read_only=True)
    quality_status_name = serializers.CharField(source='quality_status.name', read_only=True)

    class Meta:
        model = Inventory
        fields = '__all__'
        # fields = [
        #     'id', 'item', 'item_name',
        #     'location', 'location_code',
        #     'quantity', 'remarks',
        #     'created_by', 'created_by_name',
        #     'updated_by', 'updated_by_name',
        #     'created_at', 'updated_at', 'deleted'
        # ]


# class InwardItemSerializer(serializers.ModelSerializer):
#     item_name = serializers.CharField(source='item.name', read_only=True)
#     quality_status_display = serializers.CharField(source='quality_status.name', read_only=True)

#     class Meta:
#         model = InwardItem
#         fields = [
#             'id', 'inward', 'item', 'item_name',
#             'quantity', 'rate', 'quality_status', 'quality_status_display', 'remarks',
#             'purchase_order', 'purchase_order_item'
#         ]
#     def __str__(self):
#         return f"{self.item.name} - {self.inward.reference_number}"

# class InwardSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Inward
#         fields = [
#             'id', 'supplier', 'location', 'reference_number',
#             'received_by', 'received_at', 'remarks'
#         ]
#         read_only_fields = ['id', 'created_at', 'received_by']
#     def __str__(self):
#         return self.name


# class OutwardSerializer(serializers.ModelSerializer):
#     item_name = serializers.CharField(source='item.name', read_only=True)
#     location_code = serializers.CharField(source='location.code', read_only=True)
#     dispatched_by_name = serializers.CharField(source='dispatched_by.username', read_only=True)

#     class Meta:
#         model = Outward
#         fields = [
#             'id', 'item', 'location', 'quantity', 'dispatched_by',
#             'date', 'remarks', 'created_at', 'updated_at', 'deleted',
#             'item_name', 'location_code', 'dispatched_by_name'
#         ]


# class InventoryLogSerializer(serializers.ModelSerializer):
#     item_name = serializers.CharField(source='item.name', read_only=True)
#     location_code = serializers.CharField(source='location.code', read_only=True)

#     class Meta:
#         model = InventoryLog
#         fields = [
#             'id', 'item', 'location', 'quantity', 'movement_type',
#             'reference_id', 'created_at', 'updated_at',
#             'item_name', 'location_code'
#             ]

# class InventoryTransferSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = InventoryTransfer
#         fields = '__all__'

# class InventoryAdjustmentSerializer(serializers.ModelSerializer):
#     adjustment_quantity = serializers.FloatField(write_only=True)

#     class Meta:
#         model = InventoryAdjustment
#         fields = ['item', 'location', 'reason', 'adjustment_quantity']

# class InventoryReturnSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = InventoryReturn
#         fields = '__all__'

# class CycleCountSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CycleCount
#         fields = '__all__'

#!-----------------------------------------------------------------
class InventoryTransactionSerializer(serializers.ModelSerializer):
    process_type_display = serializers.CharField(source='process_type.name', read_only=True)

    class Meta:
        model = InventoryTransaction
        fields = '__all__'  # Include all fields for internal use
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        process_type = data.get('process_type')
        code = process_type.code if process_type else None

        if not code:
            raise serializers.ValidationError("process_type is required.")

        # Dynamic validations based on process_type
        if code == 'INWARD':
            if not data.get('location') or not data.get('supplier'):
                raise serializers.ValidationError("Inward requires location and supplier.")
        elif code == 'OUTWARD':
            if not data.get('location'):
                raise serializers.ValidationError("Outward requires location.")
        elif code == 'TRANSFER':
            if not data.get('from_location') or not data.get('to_location'):
                raise serializers.ValidationError("Transfer requires from_location and to_location.")
        elif code == 'RETURN':
            if not data.get('reason'):
                raise serializers.ValidationError("Return requires a reason.")
        elif code == 'ADJUSTMENT':
            if not data.get('reason'):
                raise serializers.ValidationError("Adjustment requires a reason.")

        return data

#!-----------------------------------------------------------------
class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'




class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = ['id', 'item', 'item_name', 'quantity', 'rate', 'remarks']



class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    items = PurchaseOrderItemSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'supplier', 'supplier_name',
            'order_date', 'expected_delivery_date',
            'reference_number', 'remarks',
            'created_by', 'created_at',
            'items'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')
        created_by = request.user if request else None

        po = PurchaseOrder.objects.create(**validated_data, created_by=created_by)

        for item_data in items_data:
            PurchaseOrderItem.objects.create(purchase_order=po, **item_data)

        return po

class InventorySummarySerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)

    class Meta:
        model = Inventory
        fields = ['id', 'item', 'item_name', 'location', 'location_name', 'quantity']


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class SalesOrderItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)

    class Meta:
        model = SalesOrderItem
        fields = ['id', 'item', 'item_name', 'quantity', 'rate', 'remarks']

class SalesOrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    items = SalesOrderItemSerializer(many=True)

    class Meta:
        model = SalesOrder
        fields = [
            'id', 'customer', 'customer_name', 'order_date', 'reference_number',
            'remarks', 'created_by', 'created_at', 'updated_at', 'is_fulfilled', 'items'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')
        created_by = request.user if request else None

        sales_order = SalesOrder.objects.create(created_by=created_by, **validated_data)

        for item_data in items_data:
            SalesOrderItem.objects.create(sales_order=sales_order, **item_data)

        return sales_order

#! invoice
class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    outward_id = serializers.IntegerField(source="outward.id", read_only=True)
    sales_order_id = serializers.IntegerField(source="sales_order.id", required=False, allow_null=True)

    class Meta:
        model = Invoice
        fields = [
            "id", "customer", "customer_name", "outward", "outward_id", "sales_order", "sales_order_id",
            "invoice_date", "total_amount", "payment_status", "remarks", "created_at"
        ]

