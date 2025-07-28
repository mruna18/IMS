from rest_framework import serializers
from .models import Warehouse, Location

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'code', 'description', 'is_active']


class WarehouseSerializer(serializers.ModelSerializer):
    locations = LocationSerializer(many=True, read_only=True)

    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'address', 'is_active', 'locations']

