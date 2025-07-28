from rest_framework import serializers
from .models import *


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'


class InventorySerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    location_code = serializers.CharField(source='location.code', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = Inventory
        fields = [
            'id', 'item', 'item_name',
            'location', 'location_code',
            'quantity', 'remarks',
            'created_by', 'created_by_name',
            'updated_by', 'updated_by_name',
            'created_at', 'updated_at', 'deleted'
        ]

class InwardSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    location_code = serializers.CharField(source='location.code', read_only=True)
    received_by_name = serializers.CharField(source='received_by.username', read_only=True)

    class Meta:
        model = Inward
        fields =[ 'id', 'item', 'location', 'quantity', 'received_by',
                  'date', 'remarks', 'created_at', 'updated_at', 'deleted', 
                  'item_name', 'location_code', 'received_by_name']


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
