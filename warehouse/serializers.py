from rest_framework import serializers
from .models import Warehouse, Location

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'
        read_only_fields = ['warehouse'] 


class WarehouseSerializer(serializers.ModelSerializer):
    locations = LocationSerializer(many=True, read_only=True)

    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'address', 'is_active', 'locations', 'owner', 'created_at', 'updated_at', 'deleted']
        read_only_fields = ['owner'] # Owner is set automatically in the view

