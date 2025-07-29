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

class InwardSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    location_code = serializers.CharField(source='location.code', read_only=True)
    received_by_name = serializers.CharField(source='received_by.username', read_only=True)

    purchase_order_number = serializers.CharField(source='purchase_order.order_number', read_only=True)
    purchase_order_item_id = serializers.IntegerField(source='purchase_order_item.id', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = Inward
        fields = [
            'id',
            'item', 'location', 'quantity',
            'purchase_order', 'purchase_order_item', 'supplier',
            'delivery_note', 'invoice_number', 'payment_terms', 'supplier_rating',

            'received_by', 'date', 'remarks',
            'created_at', 'updated_at', 'deleted',

            # Read-only display fields
            'item_name', 'location_code', 'received_by_name',
            'purchase_order_number', 'purchase_order_item_id', 'supplier_name',
        ]


class OutwardSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    location_code = serializers.CharField(source='location.code', read_only=True)
    dispatched_by_name = serializers.CharField(source='dispatched_by.username', read_only=True)

    class Meta:
        model = Outward
        fields = [
            'id', 'item', 'location', 'quantity', 'dispatched_by',
            'date', 'remarks', 'created_at', 'updated_at', 'deleted',
            'item_name', 'location_code', 'dispatched_by_name'
        ]


class InventoryLogSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    location_code = serializers.CharField(source='location.code', read_only=True)

    class Meta:
        model = InventoryLog
        fields = [
            'id', 'item', 'location', 'quantity', 'movement_type',
            'reference_id', 'created_at', 'updated_at',
            'item_name', 'location_code'
            ]

class InventoryTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryTransfer
        fields = '__all__'

class InventoryAdjustmentSerializer(serializers.ModelSerializer):
    adjustment_quantity = serializers.FloatField(write_only=True)

    class Meta:
        model = InventoryAdjustment
        fields = ['item', 'location', 'reason', 'adjustment_quantity']

class InventoryReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryReturn
        fields = '__all__'

class CycleCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CycleCount
        fields = '__all__'

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = '__all__'


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = ['id', 'item', 'item_name', 'quantity', 'unit_price', 'remarks']


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

        for item in items_data:
            PurchaseOrderItem.objects.create(purchase_order=po, **item)

        return po
