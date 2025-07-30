from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from api.permission import *
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Sum

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

    @check_employee_permission("create_item")
    def post(self, request):
        data = request.data.copy()
        data['created_by'] = request.user.id
        serializer = ItemSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# ------------------- ITEM CATEGORY ------------------- #
class ItemCategoryCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ItemCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data, "message": "Category created"}, status=201)
        return Response({"errors": serializer.errors}, status=400)


class ItemCategoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = ItemCategory.objects.all()
        serializer = ItemCategorySerializer(categories, many=True)
        return Response(serializer.data)
    
# ------------------- ITEM BATCH ------------------- #
class ItemBatchCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ItemBatchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data, "message": "Batch created"}, status=201)
        return Response(serializer.errors, status=400)


class ItemBatchListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        batches = ItemBatch.objects.all()
        serializer = ItemBatchSerializer(batches, many=True)
        return Response(serializer.data)

# ------------------- ITEM LOT ------------------- #
class ItemLotCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ItemLotSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data, "message": "Lot created"}, status=201)
        return Response(serializer.errors, status=400)


class ItemLotListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        lots = ItemLot.objects.all()
        serializer = ItemLotSerializer(lots, many=True)
        return Response(serializer.data)

#``
class QualityStatusCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = QualityStatusSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data, "message": "Status created"}, status=201)
        return Response(serializer.errors, status=400)


class QualityStatusListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        statuses = QualityStatus.objects.all()
        serializer = QualityStatusSerializer(statuses, many=True)
        return Response(serializer.data)

# ------------------- INVENTORY SUMMARY ------------------- #
class InventorySummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        inventory_qs = Inventory.objects.filter(deleted=False)
        data = []

        for inv in inventory_qs:
            item = inv.item
            location = inv.location
            current_stock = inv.quantity or 0

            # Default values if item is null
            minimum_stock_level = item.minimum_stock_level if item else 0
            reorder_point = item.reorder_point if item else 0

            # Determine stock status
            if current_stock < minimum_stock_level:
                stock_status = "Critical - Below Minimum"
            elif current_stock <= reorder_point:
                stock_status = "Reorder Needed"
            else:
                stock_status = "Sufficient"

            data.append({
                "item_id": item.id if item else None,
                "item_name": item.name if item else None,
                "sku": item.sku if item else None,

                "location_id": location.id if location else None,
                "location_code": location.code if location else None,

                "stock": float(current_stock),
                "minimum_stock_level": minimum_stock_level,
                "reorder_point": reorder_point,
                "stock_status": stock_status,
            })

        return Response({"data": data, "status": "200"})
    
# ------------------- INVENTORY ------------------- #
class InventoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        inventories = Inventory.objects.filter(deleted=False)
        serializer = InventorySerializer(inventories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class InventoryCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InventorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response({"data": serializer.data, "status": "201", "message": "Inventory created successfully"})
        return Response({"errors": serializer.errors, "status": "400"})
    
class InventoryUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            inventory = Inventory.objects.get(pk=pk)
        except Inventory.DoesNotExist:
            return Response({"status": "404", "message": "Inventory record not found"}, status=status.HTTP_404_NOT_FOUND)

        # Soft-delete logic
        if request.data.get('deleted') is True:
            inventory.deleted = True
            inventory.updated_by = request.user
            inventory.save()
            return Response({
                "status": "200",
                "message": "Inventory marked as deleted successfully"
            })

        # Normal update
        serializer = InventorySerializer(inventory, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(updated_by=request.user)
            return Response({"data": serializer.data, "status": "200", "message": "Inventory updated successfully"})
        return Response({"errors": serializer.errors, "status": "400"}, status=status.HTTP_400_BAD_REQUEST)

class InventorySoftDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            inventory = Inventory.objects.get(pk=pk, deleted=False)
        except Inventory.DoesNotExist:
            return Response({"status": "404", "message": "Inventory not found"}, status=status.HTTP_404_NOT_FOUND)

        inventory.deleted = True
        inventory.updated_by = request.user
        inventory.save()

        return Response({"status": "200", "message": "Inventory soft-deleted successfully"})


# ------------------- INWARD ------------------- #

class InwardListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        inwards = Inward.objects.filter(deleted=False)
        serializer = InwardSerializer(inwards, many=True)
        return Response(serializer.data)


class InwardCreateView(APIView):
    permission_classes = [IsAuthenticated]

    # @check_employee_permission("create_inward")
    def post(self, request):
        data = request.data.copy()
        data['received_by'] = request.user.id
        to_location_id = data.pop('to_location', None)

        items_data = data.pop("items", [])
        if not items_data:
            return Response({"error": "At least one item is required."}, status=400)

        inward_serializer = InwardSerializer(data=data)
        if not inward_serializer.is_valid():
            return Response(inward_serializer.errors, status=400)

        inward = inward_serializer.save()

        for item_data in items_data:
            item_data['inward'] = inward.id  # attach inward FK

            # ------------------------------
            # 💡 PO/POI validation
            poi_id = item_data.get("purchase_order_item")
            po_id = item_data.get("purchase_order")

            if poi_id:
                try:
                    poi = PurchaseOrderItem.objects.get(id=poi_id)
                except PurchaseOrderItem.DoesNotExist:
                    return Response({"error": f"PurchaseOrderItem {poi_id} not found."}, status=400)

                # Validate item match
                if poi.item.id != item_data.get("item"):
                    return Response({"error": f"Item does not match PO Item {poi_id}."}, status=400)

                # Validate PO match if given
                if po_id and poi.purchase_order.id != po_id:
                    return Response({"error": f"PO Item does not belong to PO {po_id}."}, status=400)

                # Validate over-fulfillment
                total_received = InwardItem.objects.filter(purchase_order_item=poi).aggregate(
                    total=Sum('quantity'))['total'] or 0
                remaining_qty = poi.quantity - total_received

                if item_data["quantity"] > remaining_qty:
                    return Response({
                        "error": f"Received quantity exceeds remaining for PO Item {poi_id}. Remaining: {remaining_qty}"
                    }, status=400)

            # ------------------------------

            item_serializer = InwardItemSerializer(data=item_data)
            if not item_serializer.is_valid():
                return Response(item_serializer.errors, status=400)

            item_obj = item_serializer.save()

            # Inventory update
            inventory, created = Inventory.objects.get_or_create(
                item=item_obj.item,
                location=inward.location,
                defaults={
                    'quantity': item_obj.quantity,
                    'remarks': inward.remarks,
                    'created_by': request.user,
                    'updated_by': request.user
                }
            )

            if not created:
                quantity_before = inventory.quantity
                inventory.quantity += item_obj.quantity
                inventory.updated_by = request.user
                inventory.save()
                quantity_after = inventory.quantity
            else:
                quantity_before = 0
                quantity_after = item_obj.quantity

            try:
                action_type = InventoryActionType.objects.get(code='IN')
            except InventoryActionType.DoesNotExist:
                return Response({"error": "Action type 'IN' not configured."}, status=500)

            InventoryLog.objects.create(
                inventory=inventory,
                item=item_obj.item,
                location=inward.location,
                action_type=action_type,
                quantity_before=quantity_before,
                quantity_changed=item_obj.quantity,
                quantity_after=quantity_after,
                reference_id=inward.id,
                reference_type='Inward',
                changed_by=request.user,
                remarks=inward.remarks
            )

            try:
                putaway_type = TaskType.objects.get(code="PUTAWAY")
            except TaskType.DoesNotExist:
                return Response({"error": "PutAway task type not configured."}, status=500)

            to_location = Location.objects.filter(id=to_location_id).first() or inward.location

            PutAwayTask.objects.create(
                inward=inward,
                item=item_obj.item,
                from_location=inward.location,
                to_location=to_location,
                quantity=item_obj.quantity,
                assigned_to=request.user,
                task_type=putaway_type,
                created_by=request.user,
                updated_by=request.user
            )

        return Response({"message": "Inward created successfully", "inward_id": inward.id}, status=201)

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
        data["dispatched_by"] = request.user.id
        serializer = OutwardSerializer(data=data)

        if not serializer.is_valid():
            return Response({"errors": serializer.errors, "status": "400"}, status=status.HTTP_400_BAD_REQUEST)

        item = serializer.validated_data['item']
        location = serializer.validated_data['location']
        issue_qty = serializer.validated_data['quantity']

        # --- Handle optional to_location ---
        to_location = None
        to_location_id = data.get("to_location")
        if to_location_id:
            try:
                to_location = Location.objects.get(id=to_location_id)
            except Location.DoesNotExist:
                return Response({
                    "error": "Invalid to_location ID.",
                    "status": "400"
                }, status=status.HTTP_400_BAD_REQUEST)

        # --- Check stock availability ---
        try:
            inventory = Inventory.objects.get(item=item, location=location, deleted=False)
        except Inventory.DoesNotExist:
            return Response({
                "error": "Inventory not found for given item and location.",
                "status": "404"
            }, status=status.HTTP_404_NOT_FOUND)

        if inventory.quantity is None or inventory.quantity < issue_qty:
            return Response({
                "error": "Outward quantity exceeds available stock.",
                "available_quantity": inventory.quantity,
                "status": "400"
            }, status=status.HTTP_400_BAD_REQUEST)


        # --- Deduct stock ---
        quantity_before = inventory.quantity
        inventory.quantity -= issue_qty
        quantity_after = inventory.quantity
        inventory.updated_by = request.user
        inventory.save()


        # --- Save outward entry ---
        outward = serializer.save(created_by=request.user)

        # --- Log inventory movement ---

        try:
            action_type = InventoryActionType.objects.get(code='OUT')
        except InventoryActionType.DoesNotExist:
            return Response({"error": "Action type 'IN' not configured."}, status=500)


        InventoryLog.objects.create(
                inventory=inventory,
                item=outward.item,
                location=outward.location,
                action_type=action_type,
                quantity_before=quantity_before,
                quantity_changed=outward.quantity,
                quantity_after=quantity_after,
                reference_id=outward.id,
                reference_type='Outward',
                changed_by=request.user,
                remarks=outward.remarks
            )

        # --- Try to complete an existing PickUpTask ---
        pickup_task = PickUpTask.objects.filter(
            item=item,
            from_location=location,
            quantity=issue_qty,
            is_completed=False,
            deleted=False
        ).first()

        if pickup_task:
            pickup_task.is_completed = True
            pickup_task.completed_at = timezone.now()
            pickup_task.updated_by = request.user
            pickup_task.to_location = to_location or pickup_task.to_location
            pickup_task.save()
        else:
            # --- Create new PickUpTask if not found ---
            try:
                pickup_type = TaskType.objects.get(code="PICKUP")
            except TaskType.DoesNotExist:
                return Response({"error": "PickUp task type not configured."}, status=500)

            PickUpTask.objects.create(
                outward=outward,
                item=item,
                from_location=location,
                to_location=to_location or location,
                quantity=issue_qty,
                assigned_to=request.user,
                task_type=pickup_type,
                created_by=request.user,
                updated_by=request.user
            )

        return Response({
            "data": serializer.data,
            "message": "Outward transaction recorded. Pickup task updated or created.",
            "status": "201"
        })



class InventoryLogListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logs = InventoryLog.objects.filter(deleted=False).order_by('-created_at')
        serializer = InventoryLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
# ------------------- Inventrory transfer ------------------- #
class InventoryTransferCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InventoryTransferSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors, "status": "400"}, status=status.HTTP_400_BAD_REQUEST)

        item = serializer.validated_data.get('item')
        from_location = serializer.validated_data.get('from_location')
        quantity = serializer.validated_data.get('quantity') or 0

        # Validate stock at from_location
        try:
            source_inventory = Inventory.objects.get(item=item, location=from_location, deleted=False)
            if source_inventory.quantity is None or source_inventory.quantity < quantity:
                return Response({
                    "status": "400",
                    "message": f"Insufficient stock at source location. Only {source_inventory.quantity or 0} available."
                }, status=status.HTTP_400_BAD_REQUEST)
        except Inventory.DoesNotExist:
            return Response({
                "status": "400",
                "message": "No inventory found at source location for this item."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Passed validation → save the transfer
        serializer.save(created_by=request.user)
        return Response({
            "data": serializer.data,
            "message": "Transfer recorded successfully",
            "status": "201"
        }, status=status.HTTP_201_CREATED)


# ------------------- Inventory adjustment ------------------- #
class InventoryAdjustmentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InventoryAdjustmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors, "status": "400"}, status=status.HTTP_400_BAD_REQUEST)

        item = serializer.validated_data['item']
        location = serializer.validated_data['location']
        adjustment_qty = serializer.validated_data['adjustment_quantity']
        reason = serializer.validated_data.get('reason', '')

        try:
            inventory = Inventory.objects.get(item=item, location=location, deleted=False)
        except Inventory.DoesNotExist:
            return Response({"message": "No inventory found at source location for this item.", "status": "400"}, status=400)

        quantity_before = inventory.quantity or 0
        quantity_after = quantity_before + adjustment_qty

        # Update inventory
        inventory.quantity = quantity_after
        inventory.updated_by = request.user
        inventory.save()

        # Save adjustment record
        adjustment = InventoryAdjustment.objects.create(
            item=item,
            location=location,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reason=reason,
            created_by=request.user
        )

        # Inventory log entry
        try:
            action_type = InventoryActionType.objects.get(code='ADJ')
        except InventoryActionType.DoesNotExist:
            return Response({"error": "Action type 'ADJUST' not configured."}, status=500)

        InventoryLog.objects.create(
            inventory=inventory,
            item=item,
            location=location,
            action_type=action_type,
            quantity_before=quantity_before,
            quantity_changed=adjustment_qty,
            quantity_after=quantity_after,
            reference_id=adjustment.id,
            reference_type='InventoryAdjustment',
            changed_by=request.user,
            remarks=reason
        )

        return Response({
            "message": "Inventory adjusted successfully.",
            "adjustment_id": adjustment.id,
            "quantity_before": quantity_before,
            "quantity_after": quantity_after
        }, status=201)



# ------------------- Inventory return ------------------- #
class InventoryReturnCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InventoryReturnSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "errors": serializer.errors,
                "status": "400"
            }, status=status.HTTP_400_BAD_REQUEST)

        item = serializer.validated_data['item']
        location = serializer.validated_data['location']
        return_qty = serializer.validated_data['quantity']
        is_defective = serializer.validated_data.get('is_defective', False)

        try:
            inventory = Inventory.objects.get(item=item, location=location, deleted=False)
        except Inventory.DoesNotExist:
            return Response({
                "error": "Inventory not found for given item and location.",
                "status": "404"
            }, status=status.HTTP_404_NOT_FOUND)

        quantity_before = inventory.quantity or 0

        # Only update inventory if not defective
        if not is_defective:
            inventory.quantity += return_qty
            inventory.updated_by = request.user
            inventory.save()

        quantity_after = inventory.quantity  # This will remain same if defective

        # Save return record
        return_obj = serializer.save(created_by=request.user)

        # Inventory Log
        try:
            action_type = InventoryActionType.objects.get(code='RET')
        except InventoryActionType.DoesNotExist:
            return Response({"error": "Action type 'RET' not configured."}, status=500)

        InventoryLog.objects.create(
            inventory=inventory,
            item=item,
            location=location,
            action_type=action_type,
            quantity_before=quantity_before,
            quantity_changed=(return_qty if not is_defective else 0),
            quantity_after=(quantity_after if not is_defective else quantity_before),
            reference_id=return_obj.id,
            reference_type='InventoryReturn',
            changed_by=request.user,
            remarks=return_obj.remarks or "Defective item - stock not added" if is_defective else return_obj.remarks
        )

        return Response({
            "data": serializer.data,
            "message": "Return recorded successfully. Inventory "
                       + ("updated." if not is_defective else "not updated due to defect."),
            "status": "201"
        })




# ------------------- Cycle count ------------------- #
class CycleCountCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CycleCountSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors, "status": "400"}, status=status.HTTP_400_BAD_REQUEST)

        item = serializer.validated_data['item']
        location = serializer.validated_data['location']
        counted_quantity = serializer.validated_data['counted_quantity']

        # Get current inventory
        try:
            inventory = Inventory.objects.get(item=item, location=location, deleted=False)
        except Inventory.DoesNotExist:
            return Response({
                "error": "Inventory not found for given item and location.",
                "status": "404"
            }, status=status.HTTP_404_NOT_FOUND)

        quantity_before = inventory.quantity or 0
        inventory.quantity = counted_quantity
        inventory.updated_by = request.user
        inventory.save()
        quantity_after = inventory.quantity

        # Save Cycle Count record
        cycle_obj = serializer.save(created_by=request.user)
        cycle_obj.system_quantity = quantity_before
        cycle_obj.discrepancy = counted_quantity - quantity_before
        cycle_obj.save()

        # Inventory Log
        try:
            action_type = InventoryActionType.objects.get(code='CC')
        except InventoryActionType.DoesNotExist:
            return Response({"error": "Action type 'CYCLE' not configured."}, status=500)

        InventoryLog.objects.create(
            inventory=inventory,
            item=item,
            location=location,
            action_type=action_type,
            quantity_before=quantity_before,
            quantity_changed=counted_quantity - quantity_before,
            quantity_after=quantity_after,
            reference_id=cycle_obj.id,
            reference_type='CycleCount',
            changed_by=request.user,
            remarks=serializer.validated_data.get('remarks', '')
        )

        return Response({
            "data": CycleCountSerializer(cycle_obj).data,
            "message": "Cycle count submitted and inventory log updated.",
            "status": "201"
        })

    
# ------------------- supplier ------------------- #
# List all suppliers
class SupplierListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        suppliers = Supplier.objects.all()
        serializer = SupplierSerializer(suppliers, many=True)
        return Response({"data": serializer.data, "status": "200"})


# Create a new supplier
class SupplierCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SupplierSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data, "message": "Supplier created", "status": "201"})
        return Response({"errors": serializer.errors, "status": "400"}, status=status.HTTP_400_BAD_REQUEST)

#-- ------------------- Purchase Order ------------------- ## List all purchase orders
class PurchaseOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = PurchaseOrder.objects.all().order_by('-id')
        serializer = PurchaseOrderSerializer(orders, many=True)
        return Response({"data": serializer.data, "status": "200"})


# Create a new purchase order
class PurchaseOrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    # @check_employee_permission("create_purchase_order")
    def post(self, request):
        serializer = PurchaseOrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            po = serializer.save() 
            return Response({"data": serializer.data, "message": "PO created"}, status=201)
        return Response({"errors": serializer.errors}, status=400)

# Get purchase orders by supplier
class PurchaseOrdersBySupplierView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, supplier_id):
        try:
            supplier = Supplier.objects.get(id=supplier_id)
        except Supplier.DoesNotExist:
            return Response({"error": "Supplier not found", "status": "404"}, status=status.HTTP_404_NOT_FOUND)

        purchase_orders = PurchaseOrder.objects.filter(supplier=supplier).order_by('-id')
        serializer = PurchaseOrderSerializer(purchase_orders, many=True)
        return Response({"data": serializer.data, "status": "200"})

class FilteredPurchaseOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        supplier_id = request.query_params.get('supplier_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        queryset = PurchaseOrder.objects.all().order_by('-order_date')

        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)

        if start_date:
            start_date = parse_date(start_date)
            if start_date:
                queryset = queryset.filter(order_date__gte=start_date)

        if end_date:
            end_date = parse_date(end_date)
            if end_date:
                queryset = queryset.filter(order_date__lte=end_date)

        serializer = PurchaseOrderSerializer(queryset, many=True)
        return Response({"data": serializer.data, "status": "200"})
    
