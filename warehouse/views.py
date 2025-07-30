from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *
from django.shortcuts import get_object_or_404
from api.permission import *
from inventory.serializers import *


class WarehouseListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        warehouses = Warehouse.objects.filter(is_active=True, owner=request.user)
        serializer = WarehouseSerializer(warehouses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WarehouseCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WarehouseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LocationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, warehouse_id):
        locations = Location.objects.filter(warehouse_id=warehouse_id, is_active=True)
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LocationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, warehouse_id):
        serializer = LocationSerializer(data=request.data)
        if serializer.is_valid():
            # serializer.save(warehouse_id=warehouse_id)
            warehouse = get_object_or_404(Warehouse, id=warehouse_id)
            serializer.save(warehouse=warehouse) 
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class WarehouseStorageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        location_id = request.query_params.get("location")

        if location_id:
            inventory = Inventory.objects.filter(location_id=location_id, deleted=False)
        else:
            inventory = Inventory.objects.filter(deleted=False)

        serializer = InventorySummarySerializer(inventory, many=True)
        return Response(serializer.data)


class WarehouseStorageGroupedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        inventory_qs = Inventory.objects.filter(deleted=False).select_related('item', 'location')

        warehouse_map = {}
        for inv in inventory_qs:
            loc_id = inv.location.id
            loc_name = inv.location.code
            warehouse_name = inv.location.warehouse.name


            if loc_id not in warehouse_map:
                warehouse_map[loc_id] = {
                    "location_id": loc_id,
                    "location_name": loc_name,
                    "warehouse_name": warehouse_name,
                    "items": []
                }

            warehouse_map[loc_id]["items"].append({
                "item_id": inv.item.id,
                "item_name": inv.item.name,
                "quantity": inv.quantity
            })

        return Response(list(warehouse_map.values()))
