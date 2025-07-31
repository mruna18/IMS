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
        process_type = InventoryProcessType.objects.get(code="INWARD")
        inwards = InventoryTransaction.objects.filter(process_type=process_type, deleted=False)
        serializer = InventoryTransactionSerializer(inwards, many=True)
        return Response(serializer.data)


class InwardCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['created_by'] = request.user.id
        to_location_id = data.pop("to_location", None)

        try:
            process_type = InventoryProcessType.objects.get(code="INWARD")
        except InventoryProcessType.DoesNotExist:
            return Response({"error": "INWARD process type not configured."}, status=500)

        # Required fields
        data['process_type'] = process_type.id
        serializer = InventoryTransactionSerializer(data=data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        inward = serializer.save()

        # --- Inventory Update (Handled by signals ideally) ---

        inventory, _ = Inventory.objects.get_or_create(
            item=inward.item,
            location=inward.location,
            defaults={
                'quantity': 0,
                'remarks': inward.remarks,
                'created_by': request.user,
                'updated_by': request.user
            }
        )

        quantity_before = inventory.quantity
        inventory.quantity += inward.quantity
        inventory.updated_by = request.user
        inventory.save()
        quantity_after = inventory.quantity

        # # --- Inventory Log ---
        # try:
        #     action_type = InventoryActionType.objects.get(code='IN')
        # except InventoryActionType.DoesNotExist:
        #     return Response({"error": "Action type 'IN' not configured."}, status=500)

        # InventoryLog.objects.create(
        #     inventory=inventory,
        #     item=inward.item,
        #     location=inward.location,
        #     action_type=action_type,
        #     quantity_before=quantity_before,
        #     quantity_changed=inward.quantity,
        #     quantity_after=quantity_after,
        #     reference_id=inward.id,
        #     reference_type='InventoryTransaction',
        #     changed_by=request.user,
        #     remarks=inward.remarks
        # )

        # --- Create PutAway Task ---
        try:
            putaway_type = TaskType.objects.get(code="PUTAWAY")
        except TaskType.DoesNotExist:
            return Response({"error": "PutAway task type not configured."}, status=500)

        to_location = Location.objects.filter(id=to_location_id).first() or inward.location

        InventoryTask.objects.create(
            transaction=inward,
            item=inward.item,
            from_location=inward.location,
            to_location=to_location,
            quantity=inward.quantity,
            assigned_to=request.user,
            task_type=putaway_type,
            created_by=request.user,
            updated_by=request.user
        )

        return Response({
            "message": "Inward transaction recorded.",
            "inward_id": inward.id
        }, status=201)


# ------------------- OUTWARD ------------------- #

class OutwardListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        process_type = InventoryProcessType.objects.get(code="OUTWARD")
        outwards = InventoryTransaction.objects.filter(process_type=process_type, deleted=False)
        serializer = InventoryTransactionSerializer(outwards, many=True)
        return Response(serializer.data)


class OutwardCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['created_by'] = request.user.id

        to_location_id = data.get("to_location")
        to_location = None

        if to_location_id:
            to_location = Location.objects.filter(id=to_location_id).first()
            if not to_location:
                return Response({"error": "Invalid to_location ID."}, status=400)

        #  Add process_type before serializer
        try:
            process_type = InventoryProcessType.objects.get(code="OUTWARD")
        except InventoryProcessType.DoesNotExist:
            return Response({"error": "OUTWARD process type not configured."}, status=500)

        data["process_type"] = process_type.id  # <-- Critical fix

        # Validate input
        serializer = InventoryTransactionSerializer(data=data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=400)

        validated_data = serializer.validated_data
        item = validated_data['item']
        location = validated_data['location']
        total_quantity = validated_data['quantity']

        # Fetch inventory in FIFO order
        inventory_qs = Inventory.objects.filter(
            item=item,
            location=location,
            deleted=False
        ).order_by('expiry_date', 'id')

        total_available = sum([inv.quantity or 0 for inv in inventory_qs])
        if total_available < total_quantity:
            return Response({
                "error": "Outward quantity exceeds total available stock.",
                "available_quantity": total_available
            }, status=400)

        remaining_qty = total_quantity
        outward_ids = []

        for inv in inventory_qs:
            if remaining_qty <= 0:
                break

            deduct_qty = min(remaining_qty, inv.quantity)
            inv.quantity -= deduct_qty
            inv.updated_by = request.user
            inv.save()

            # Create a separate outward transaction for each deduction
            outward = InventoryTransaction.objects.create(
                item=item,
                location=location,
                quantity=deduct_qty,
                process_type=process_type,
                created_by=request.user,
                updated_by=request.user,
                remarks=validated_data.get("remarks", "")
            )
            outward_ids.append(outward.id)
            remaining_qty -= deduct_qty

            # Create pickup task for each
            try:
                pickup_type = TaskType.objects.get(code="PICKUP")
            except TaskType.DoesNotExist:
                return Response({"error": "PICKUP task type not configured."}, status=500)

            InventoryTask.objects.create(
                transaction=outward,
                item=item,
                from_location=location,
                to_location=to_location or location,
                quantity=deduct_qty,
                assigned_to=request.user,
                task_type=pickup_type,
                created_by=request.user,
                updated_by=request.user
            )

        return Response({
            "message": "Outward transactions created via FIFO.",
            "outward_ids": outward_ids
        }, status=201)



class InventoryTransactionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['created_by'] = request.user.id

        serializer = InventoryTransactionSerializer(data=data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=400)

        transaction = serializer.save()

        # Process logic based on type
        process_type = transaction.process_type.code

        if process_type == 'OUTWARD':
            # Handle stock deduction, pickup task creation etc.
            pass
        elif process_type == 'INWARD':
            # Handle stock addition, putaway task etc.
            pass
        elif process_type == 'TRANSFER':
            # Handle movement from from_location to to_location
            pass
        elif process_type == 'ADJUSTMENT':
            # Update inventory with adjusted quantity
            pass
        elif process_type == 'RETURN':
            # Handle return inventory logic
            pass

        return Response({
            "message": f"{process_type} transaction created successfully.",
            "transaction_id": transaction.id
        }, status=201)


# class InventoryLogListView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         logs = InventoryLog.objects.filter(deleted=False).order_by('-created_at')
#         serializer = InventoryLogSerializer(logs, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)
    
    
# # ------------------- Inventrory transfer ------------------- #
class InventoryTransferCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['created_by'] = request.user.id

        serializer = InventoryTransactionSerializer(data=data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors, "status": "400"}, status=status.HTTP_400_BAD_REQUEST)

        # Add process type for transfer
        try:
            transfer_type = InventoryProcessType.objects.get(code='TRANSFER')
        except InventoryProcessType.DoesNotExist:
            return Response({"error": "Process type 'TRANSFER' not configured."}, status=500)

        serializer.save(process_type=transfer_type, created_by=request.user)

        return Response({
            "data": serializer.data,
            "message": "Transfer transaction recorded. Inventory will be updated via signal.",
            "status": "201"
        }, status=status.HTTP_201_CREATED)


# ------------------- Inventory adjustment ------------------- #
class InventoryAdjustmentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['created_by'] = request.user.id

        try:
            process_type = InventoryProcessType.objects.get(code="ADJUSTMENT")
        except InventoryProcessType.DoesNotExist:
            return Response({"error": "Process type 'ADJUSTMENT' not configured."}, status=500)

        data['process_type'] = process_type.id
        serializer = InventoryTransactionSerializer(data=data)

        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=400)

        validated_data = serializer.validated_data
        item = validated_data['item']
        location = validated_data['location']
        adjustment_qty = validated_data['quantity']  # +ve or -ve adjustment
        remarks = validated_data.get('remarks', '')

        try:
            inventory = Inventory.objects.get(item=item, location=location, deleted=False)
        except Inventory.DoesNotExist:
            return Response({"message": "Inventory not found for this item at the specified location."}, status=400)

        quantity_before = inventory.quantity or 0
        quantity_after = quantity_before + adjustment_qty

        # Update inventory
        inventory.quantity = quantity_after
        inventory.updated_by = request.user
        inventory.save()

        # Save as centralized InventoryTransaction
        adjustment = serializer.save()

        # Log the inventory change
        # try:
        #     action_type = InventoryActionType.objects.get(code="ADJ")
        # except InventoryActionType.DoesNotExist:
        #     return Response({"error": "Action type 'ADJ' not configured."}, status=500)

        # InventoryLog.objects.create(
        #     inventory=inventory,
        #     item=item,
        #     location=location,
        #     action_type=action_type,
        #     quantity_before=quantity_before,
        #     quantity_changed=adjustment_qty,
        #     quantity_after=quantity_after,
        #     reference_id=adjustment.id,
        #     reference_type='InventoryTransaction',
        #     changed_by=request.user,
        #     remarks=remarks
        # )

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
        data = request.data.copy()
        data['created_by'] = request.user.id

        try:
            process_type = InventoryProcessType.objects.get(code="RETURN")
        except InventoryProcessType.DoesNotExist:
            return Response({"error": "Process type 'RETURN' not configured."}, status=500)

        data['process_type'] = process_type.id
        is_defective = data.get('is_defective', False)
        serializer = InventoryTransactionSerializer(data=data)

        if not serializer.is_valid():
            return Response({
                "errors": serializer.errors,
                "status": "400"
            }, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        item = validated_data['item']
        location = validated_data['location']
        return_qty = validated_data['quantity']
        remarks = validated_data.get('remarks', '')

        try:
            inventory = Inventory.objects.get(item=item, location=location, deleted=False)
        except Inventory.DoesNotExist:
            return Response({
                "error": "Inventory not found for given item and location.",
                "status": "404"
            }, status=status.HTTP_404_NOT_FOUND)

        quantity_before = inventory.quantity or 0

        # Only update stock if not defective
        if not is_defective:
            inventory.quantity += return_qty
            inventory.updated_by = request.user
            inventory.save()

        quantity_after = inventory.quantity if not is_defective else quantity_before

        # Save centralized transaction
        return_transaction = serializer.save()

        # Inventory Log
        # try:
        #     action_type = InventoryActionType.objects.get(code='RET')
        # except InventoryActionType.DoesNotExist:
        #     return Response({"error": "Action type 'RET' not configured."}, status=500)

        # InventoryLog.objects.create(
        #     inventory=inventory,
        #     item=item,
        #     location=location,
        #     action_type=action_type,
        #     quantity_before=quantity_before,
        #     quantity_changed=(return_qty if not is_defective else 0),
        #     quantity_after=quantity_after,
        #     reference_id=return_transaction.id,
        #     reference_type='InventoryTransaction',
        #     changed_by=request.user,
        #     remarks=remarks or "Defective item - stock not added" if is_defective else remarks
        # )

        return Response({
            "data": InventoryTransactionSerializer(return_transaction).data,
            "message": "Return recorded successfully. Inventory " +
                       ("updated." if not is_defective else "not updated due to defect."),
            "status": "201"
        })




# ------------------- Cycle count ------------------- #
# class CycleCountCreateView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = CycleCountSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response({"errors": serializer.errors, "status": "400"}, status=status.HTTP_400_BAD_REQUEST)

#         item = serializer.validated_data['item']
#         location = serializer.validated_data['location']
#         counted_quantity = serializer.validated_data['counted_quantity']

#         # Get current inventory
#         try:
#             inventory = Inventory.objects.get(item=item, location=location, deleted=False)
#         except Inventory.DoesNotExist:
#             return Response({
#                 "error": "Inventory not found for given item and location.",
#                 "status": "404"
#             }, status=status.HTTP_404_NOT_FOUND)

#         quantity_before = inventory.quantity or 0
#         inventory.quantity = counted_quantity
#         inventory.updated_by = request.user
#         inventory.save()
#         quantity_after = inventory.quantity

#         # Save Cycle Count record
#         cycle_obj = serializer.save(created_by=request.user)
#         cycle_obj.system_quantity = quantity_before
#         cycle_obj.discrepancy = counted_quantity - quantity_before
#         cycle_obj.save()

#         # Inventory Log
#         try:
#             action_type = InventoryActionType.objects.get(code='CC')
#         except InventoryActionType.DoesNotExist:
#             return Response({"error": "Action type 'CYCLE' not configured."}, status=500)

#         InventoryLog.objects.create(
#             inventory=inventory,
#             item=item,
#             location=location,
#             action_type=action_type,
#             quantity_before=quantity_before,
#             quantity_changed=counted_quantity - quantity_before,
#             quantity_after=quantity_after,
#             reference_id=cycle_obj.id,
#             reference_type='CycleCount',
#             changed_by=request.user,
#             remarks=serializer.validated_data.get('remarks', '')
#         )

#         return Response({
#             "data": CycleCountSerializer(cycle_obj).data,
#             "message": "Cycle count submitted and inventory log updated.",
#             "status": "201"
#         })

    
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
    

# Add this new dashboard view at the end of the file
# class InventoryDashboardView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request):
#         from django.db.models import Sum, Count, Avg
#         from django.utils import timezone
#         from datetime import timedelta
        
#         # Date ranges
#         today = timezone.now().date()
#         last_30_days = today - timedelta(days=30)
#         last_7_days = today - timedelta(days=7)
        
#         # Key metrics
#         total_items = Item.objects.filter(deleted=False).count()
#         total_inventory_value = Inventory.objects.filter(deleted=False).aggregate(
#             total=Sum('quantity')
#         )['total'] or 0
        
#         # Recent activities
#         recent_inwards = Inward.objects.filter(
#             created_at__date__gte=last_7_days
#         ).count()
        
#         recent_outwards = Outward.objects.filter(
#             created_at__date__gte=last_7_days
#         ).count()
        
#         # Low stock items
#         low_stock_items = Inventory.objects.filter(
#             deleted=False,
#             quantity__lte=models.F('item__minimum_stock_level')
#         ).count()
        
#         # Pending tasks
#         pending_putaway_tasks = PutAwayTask.objects.filter(
#             is_completed=False,
#             deleted=False
#         ).count()
        
#         pending_pickup_tasks = PickUpTask.objects.filter(
#             is_completed=False,
#             deleted=False
#         ).count()
        
#         # Supplier performance
#         supplier_performance = Supplier.objects.annotate(
#             avg_rating=Avg('supplier_rating')
#         ).values('name', 'avg_rating')[:5]
        
#         # Top items by quantity
#         top_items = Inventory.objects.filter(
#             deleted=False
#         ).select_related('item').order_by('-quantity')[:10]
        
#         dashboard_data = {
#             'summary': {
#                 'total_items': total_items,
#                 'total_inventory_value': total_inventory_value,
#                 'recent_inwards': recent_inwards,
#                 'recent_outwards': recent_outwards,
#                 'low_stock_items': low_stock_items,
#                 'pending_putaway_tasks': pending_putaway_tasks,
#                 'pending_pickup_tasks': pending_pickup_tasks,
#             },
#             'supplier_performance': list(supplier_performance),
#             'top_items': [
#                 {
#                     'item_name': inv.item.name,
#                     'quantity': inv.quantity,
#                     'location': inv.location.code
#                 } for inv in top_items
#             ]
#         }
        
#         return Response(dashboard_data, status=status.HTTP_200_OK)
    
# Add these notification views at the end of the file
# class NotificationListView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request):
#         notifications = Notification.objects.filter(
#             user=request.user
#         ).order_by('-created_at')[:50]
        
#         serializer = NotificationSerializer(notifications, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

# class NotificationMarkReadView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request, notification_id):
#         try:
#             notification = Notification.objects.get(
#                 id=notification_id,
#                 user=request.user
#             )
#             notification.is_read = True
#             notification.save()
#             return Response({"message": "Notification marked as read"}, status=status.HTTP_200_OK)
#         except Notification.DoesNotExist:
#             return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)

# class NotificationMarkAllReadView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request):
#         Notification.objects.filter(
#             user=request.user,
#             is_read=False
#         ).update(is_read=True)
#         return Response({"message": "All notifications marked as read"}, status=status.HTTP_200_OK)
    
# Add this barcode search view
class BarcodeSearchView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        barcode = request.GET.get('barcode')
        if not barcode:
            return Response({"error": "Barcode parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            item = Item.objects.get(barcode=barcode, deleted=False)
            inventory_items = Inventory.objects.filter(
                item=item,
                deleted=False
            ).select_related('location', 'quality_status')
            
            item_data = {
                'id': item.id,
                'name': item.name,
                'sku': item.sku,
                'barcode': item.barcode,
                'unit': item.unit,
                'category': item.category.name if item.category else None,
                'brand': item.brand,
                'model': item.model,
                'minimum_stock_level': item.minimum_stock_level,
                'reorder_point': item.reorder_point,
                'inventory_locations': [
                    {
                        'location_code': inv.location.code,
                        'location_name': inv.location.description,
                        'quantity': inv.quantity,
                        'quality_status': inv.quality_status.name if inv.quality_status else None,
                        'expiry_date': inv.expiry_date,
                    } for inv in inventory_items
                ]
            }
            
            return Response(item_data, status=status.HTTP_200_OK)
            
        except Item.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
    
    
# customer
class CustomerListCreateView(APIView):
    def get(self, request):
        customers = Customer.objects.filter(deleted=False)
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
class CustomerCreateView(APIView):
    permission_classes = [IsAuthenticated] 
    
    def post(self, request):
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            customer = serializer.save()
            return Response({
                "message": "Customer created successfully",
                "data": CustomerSerializer(customer).data
            }, status=status.HTTP_201_CREATED)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

#! SO

class SalesOrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_data = request.data.copy()
        items_data = order_data.pop("items", [])

        if not items_data:
            return Response({"error": "At least one item is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the sales order
        order = SalesOrder.objects.create(
            customer_id=order_data.get("customer"),
            reference_number=order_data.get("reference_number"),
            remarks=order_data.get("remarks"),
            created_by=request.user,
            updated_by=request.user
        )

        errors = []

        for item_data in items_data:
            item = item_data.get("item")
            location = item_data.get("location")
            quantity = item_data.get("quantity")

            try:
                inventory = Inventory.objects.get(item_id=item, location_id=location, deleted=False)
                available = (inventory.quantity or 0) - (inventory.reserved_quantity or 0)
                if available < quantity:
                    errors.append({
                        "item": item,
                        "location": location,
                        "message": f"Insufficient available stock. Only {available} available."
                    })
                    continue

                # Reserve stock
                inventory.reserved_quantity = (inventory.reserved_quantity or 0) + quantity
                inventory.save()

                SalesOrderItem.objects.create(
                    order=order,
                    item_id=item,
                    location_id=location,
                    quantity=quantity
                )

            except Inventory.DoesNotExist:
                errors.append({
                    "item": item,
                    "location": location,
                    "message": "Inventory record not found"
                })

        if errors:
            return Response({
                "message": "Order created with some issues",
                "order_id": order.id,
                "errors": errors
            }, status=status.HTTP_207_MULTI_STATUS)

        return Response({
            "message": "Sales order created successfully",
            "order_id": order.id
        }, status=status.HTTP_201_CREATED)
    

#! invoice


        
class InvoiceCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        outward_id = data.get("outward")
        sales_order_id = data.get("sales_order")  # Optional
        customer_id = data.get("customer")

        # Validate outward transaction
        try:
            outward = InventoryTransaction.objects.get(id=outward_id, process_type__code="OUTWARD")
        except InventoryTransaction.DoesNotExist:
            return Response({"error": "Invalid or missing outward transaction."}, status=400)

        # Validate customer
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return Response({"error": "Invalid customer ID."}, status=400)

        # Optional: Validate sales order
        sales_order = None
        if sales_order_id:
            try:
                sales_order = SalesOrder.objects.get(id=sales_order_id)
            except SalesOrder.DoesNotExist:
                return Response({"error": "Invalid sales order ID."}, status=400)

        # Calculate total
        total_amount = outward.quantity * (outward.rate or 0)

        invoice = Invoice.objects.create(
            customer=customer,
            outward=outward,
            sales_order=sales_order,
            total_amount=total_amount,
            remarks=data.get("remarks", ""),
            created_by=request.user
        )

        serializer = InvoiceSerializer(invoice)
        return Response({"message": "Invoice created successfully", "data": serializer.data}, status=201)