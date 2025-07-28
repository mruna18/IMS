from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import *
from .serializers import *
from tasks.models import *

# ------------------- ITEM ------------------- #
class ItemListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = Item.objects.filter(deleted=False)
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ItemCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['created_by'] = request.user.id
        serializer = ItemSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ------------------- INVENTORY SUMMARY ------------------- #
class InventorySummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        inventory = Inventory.objects.filter(deleted=False)
        serializer = InventorySerializer(inventory, many=True)
        return Response(serializer.data)


# ------------------- INWARD ------------------- #

class InwardListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        inwards = Inward.objects.filter(deleted=False)
        serializer = InwardSerializer(inwards, many=True)
        return Response(serializer.data)


class InwardCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['received_by'] = request.user.id
        serializer = InwardSerializer(data=data)
        if serializer.is_valid():
            inward = serializer.save()

            inventory, created = Inventory.objects.get_or_create(
            item=inward.item,
            location=inward.location,
            defaults={
                'quantity': inward.quantity,
                'remarks': inward.remarks,
                'created_by': request.user,
                'updated_by': request.user
            }
        )
            if not created:
                inventory.quantity += inward.quantity
                inventory.updated_by = request.user
                inventory.save()

            InventoryLog.objects.create(
                item=inward.item,
                location=inward.location,
                quantity=inward.quantity,
                movement_type='IN',
                reference_id=inward.id,
                deleted=False
            )

            putaway_type = TaskType.objects.get(code="PUTAWAY")

            PutAwayTask.objects.create(
                 inward=inward,  
                item=inward.item,
                from_location=inward.location,
                to_location=inward.location, # Assuming putaway to the same location for simplicity
                quantity=inward.quantity,
                assigned_to=request.user,
                task_type=putaway_type,
                created_by=request.user,
                updated_by=request.user
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------- OUTWARD ------------------- #

class OutwardListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        outwards = Outward.objects.filter(deleted=False)
        serializer = OutwardSerializer(outwards, many=True)
        return Response(serializer.data)


class OutwardCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['dispatched_by'] = request.user.id
        serializer = OutwardSerializer(data=data)
        if serializer.is_valid():
            outward = serializer.save()

            try:
                inventory = Inventory.objects.get(item=outward.item, location=outward.location)

                if inventory.quantity < outward.quantity:
                    return Response({"error": "Not enough stock"}, status=status.HTTP_400_BAD_REQUEST)
                
                inventory.quantity -= outward.quantity
                inventory.updated_by = request.user
                inventory.save()

                InventoryLog.objects.create(
                    item=outward.item,
                    location=outward.location,
                    quantity=outward.quantity,
                    movement_type='OUT',
                    reference_id=outward.id,
                    deleted=False
                )

                    
                pickup_type = TaskType.objects.get(code="PICKUP")

                PickUpTask.objects.create(
                    item=outward.item,
                    from_location=outward.location,
                    to_location=outward.location,  # or final delivery location
                    quantity=outward.quantity,
                    assigned_to=request.user,
                    task_type=pickup_type,
                    created_by=request.user,
                    updated_by=request.user
                )

                return Response(serializer.data, status=status.HTTP_201_CREATED)

            except Inventory.DoesNotExist:
                return Response({"error": "Inventory not found"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InventoryLogListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logs = InventoryLog.objects.filter(deleted=False).order_by('-created_at')
        serializer = InventoryLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    