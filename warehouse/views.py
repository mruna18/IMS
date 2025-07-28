
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Warehouse, Location
from .serializers import WarehouseSerializer, LocationSerializer

class WarehouseListCreateView(APIView):
    def get(self, request):
        warehouses = Warehouse.objects.filter(is_active=True)
        serializer = WarehouseSerializer(warehouses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = WarehouseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LocationListCreateView(APIView):
    def get(self, request, warehouse_id):
        locations = Location.objects.filter(warehouse_id=warehouse_id, is_active=True)
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data)

    def post(self, request, warehouse_id):
        data = request.data.copy()
        data['warehouse'] = warehouse_id
        serializer = LocationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

