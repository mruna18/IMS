from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Warehouse, Location
from .serializers import WarehouseSerializer, LocationSerializer


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
            serializer.save(warehouse_id=warehouse_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
