from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from api.permission import *
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Sum
from django.core.cache import cache

from .models import *
from .serializers import *
from .services import InventoryTransactionService, InventoryValidationService, TransactionResult
from tasks.models import *

# ------------------- ITEM ------------------- #
class ItemListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request):
        items = Item.objects.filter(deleted=False)
        
        # Apply pagination
        paginator = self.pagination_class()
        paginated_items = paginator.paginate_queryset(items, request)
        
        serializer = ItemSerializer(paginated_items, many=True)
        return paginator.get_paginated_response(serializer.data)


class ItemCreateView(APIView):
    permission_classes = [IsAuthenticated]

    # @check_employee_permission("create_item")
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
            return Response({"data": serializer.data, "message": "Quality status created"}, status=201)
        return Response(serializer.errors, status=400)


class QualityStatusListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        quality_statuses = QualityStatus.objects.all()
        serializer = QualityStatusSerializer(quality_statuses, many=True)
        return Response(serializer.data)

# ------------------- INVENTORY SUMMARY ------------------- #
class InventorySummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Use caching for inventory summary
        cache_key = "inventory_summary"
        summary_data = cache.get(cache_key)
        
        if not summary_data:
            inventory_summary = Inventory.objects.filter(deleted=False).select_related(
                'item', 'location'
            ).values('item__name', 'location__code').annotate(
                total_quantity=Sum('quantity')
            )
            
            summary_data = list(inventory_summary)
            cache.set(cache_key, summary_data, 300)  # Cache for 5 minutes
        
        return Response({
            "summary": summary_data,
            "total_items": len(summary_data)
        })

# ------------------- INVENTORY ------------------- #
class InventoryListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request):
        inventory_list = Inventory.objects.filter(deleted=False).select_related(
            'item', 'location', 'batch', 'lot', 'quality_status'
        )
        
        # Apply pagination
        paginator = self.pagination_class()
        paginated_inventory = paginator.paginate_queryset(inventory_list, request)
        
        serializer = InventorySerializer(paginated_inventory, many=True)
        return paginator.get_paginated_response(serializer.data)


class InventoryCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['created_by'] = request.user.id
        serializer = InventorySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InventoryUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            inventory = Inventory.objects.get(id=pk, deleted=False)
        except Inventory.DoesNotExist:
            return Response({"error": "Inventory not found"}, status=status.HTTP_404_NOT_FOUND)
        
        data = request.data.copy()
        data['updated_by'] = request.user.id
        
        serializer = InventorySerializer(inventory, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InventorySoftDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            inventory = Inventory.objects.get(id=pk, deleted=False)
        except Inventory.DoesNotExist:
            return Response({"error": "Inventory not found"}, status=status.HTTP_404_NOT_FOUND)
        
        inventory.deleted = True
        inventory.updated_by = request.user
        inventory.save()
        
        return Response({"message": "Inventory deleted successfully"}, status=status.HTTP_200_OK)

# ------------------- CENTRALIZED INVENTORY TRANSACTION ------------------- #
class InventoryTransactionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data.copy()

            # Resolve process_type from ID in request
            process_type = data.get("process_type_obj")
            if not process_type:
                return ResultObject(
                    success=False,
                    message="Invalid process type",
                    errors=["Missing or invalid process_type_obj"]
                )

            try:
                process_type = InventoryProcessType.objects.get(id=process_type_id)
            except (InventoryProcessType.DoesNotExist, ValueError, TypeError):
                return Response({
                    "success": False,
                    "message": f"Invalid process type: {process_type_id}",
                    "errors": [f"Invalid process type ID: {process_type_id}"]
                }, status=status.HTTP_400_BAD_REQUEST)

            # Inject resolved process_type object into data
            data["process_type_obj"] = process_type

            # Call the service
            service = InventoryTransactionService(request.user)
            result = service.create_transaction(data)

            if result.success:
                return Response({
                    "success": True,
                    "message": result.message,
                    "transaction_id": result.transaction_id,
                    "process_type": result.process_type,
                    "inventory_updated": result.inventory_updated,
                    "tasks_created": result.tasks_created,
                    "quantity_before": result.quantity_before,
                    "quantity_after": result.quantity_after,
                    "quantity_changed": result.quantity_changed,
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "success": False,
                    "message": result.message,
                    "errors": result.errors,
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Internal server error",
                "errors": [str(e)]
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InventoryTransactionDetailView(APIView):
    """Get detailed information about a specific transaction"""
    permission_classes = [IsAuthenticated]

    def get(self, request, transaction_id):
        try:
            transaction = InventoryTransaction.objects.select_related(
                'process_type', 'item', 'location', 'from_location', 'to_location',
                'supplier', 'purchase_order', 'created_by'
            ).get(id=transaction_id, deleted=False)
            
            serializer = InventoryTransactionSerializer(transaction)
            return Response(serializer.data)
            
        except InventoryTransaction.DoesNotExist:
            return Response({
                "success": False,
                "message": "Transaction not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Error retrieving transaction",
                "errors": [str(e)]
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------- LEGACY VIEWS (DEPRECATED - Use InventoryTransactionCreateView instead) ------------------- #
# These views are kept for backward compatibility but should be phased out

class InwardListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request):
        inward_transactions = InventoryTransaction.objects.filter(
            process_type__code='INWARD',
            deleted=False
        ).select_related('item', 'location', 'supplier').order_by('-created_at')
        
        paginator = self.pagination_class()
        paginated_transactions = paginator.paginate_queryset(inward_transactions, request)
        
        serializer = InventoryTransactionSerializer(paginated_transactions, many=True)
        return paginator.get_paginated_response(serializer.data)


class OutwardListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request):
        outward_transactions = InventoryTransaction.objects.filter(
            process_type__code='OUTWARD',
            deleted=False
        ).select_related('item', 'location').order_by('-created_at')
        
        paginator = self.pagination_class()
        paginated_transactions = paginator.paginate_queryset(outward_transactions, request)
        
        serializer = InventoryTransactionSerializer(paginated_transactions, many=True)
        return paginator.get_paginated_response(serializer.data)


# ------------------- SUPPLIER ------------------- #
class SupplierListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request):
        suppliers = Supplier.objects.all()
        
        paginator = self.pagination_class()
        paginated_suppliers = paginator.paginate_queryset(suppliers, request)
        
        serializer = SupplierSerializer(paginated_suppliers, many=True)
        return paginator.get_paginated_response(serializer.data)


class SupplierCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SupplierSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data, "message": "Supplier created"}, status=201)
        return Response(serializer.errors, status=400)

# ------------------- PURCHASE ORDER ------------------- #
class PurchaseOrderListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request):
        purchase_orders = PurchaseOrder.objects.all().select_related('supplier', 'created_by')
        
        paginator = self.pagination_class()
        paginated_orders = paginator.paginate_queryset(purchase_orders, request)
        
        serializer = PurchaseOrderSerializer(paginated_orders, many=True)
        return paginator.get_paginated_response(serializer.data)


class PurchaseOrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['created_by'] = request.user.id
        serializer = PurchaseOrderSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data, "message": "Purchase order created"}, status=201)
        return Response(serializer.errors, status=400)


class PurchaseOrdersBySupplierView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, supplier_id):
        purchase_orders = PurchaseOrder.objects.filter(
            supplier_id=supplier_id
        ).select_related('supplier', 'created_by')
        
        serializer = PurchaseOrderSerializer(purchase_orders, many=True)
        return Response(serializer.data)


class FilteredPurchaseOrderListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request):
        queryset = PurchaseOrder.objects.all().select_related('supplier', 'created_by')
        
        # Apply filters
        supplier_id = request.query_params.get('supplier')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)
        
        date_from = request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(order_date__gte=date_from)
        
        date_to = request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(order_date__lte=date_to)
        
        # Apply pagination
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        serializer = PurchaseOrderSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)

# ------------------- BARCODE SEARCH ------------------- #
class BarcodeSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        barcode = request.query_params.get('barcode')
        if not barcode:
            return Response({"error": "Barcode parameter is required"}, status=400)
        
        try:
            # Search by barcode
            item = Item.objects.get(barcode=barcode, deleted=False, is_active=True)
            
            # Get inventory for this item
            inventory = Inventory.objects.filter(
                item=item,
                deleted=False
            ).select_related('location', 'batch', 'lot', 'quality_status')
            
            item_serializer = ItemSerializer(item)
            inventory_serializer = InventorySerializer(inventory, many=True)
            
            return Response({
                "item": item_serializer.data,
                "inventory": inventory_serializer.data,
                "total_quantity": sum(inv.quantity or 0 for inv in inventory)
            })
            
        except Item.DoesNotExist:
            return Response({"error": "Item not found"}, status=404)

# ------------------- CUSTOMER ------------------- #
class CustomerListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get(self, request):
        customers = Customer.objects.filter(deleted=False)
        
        paginator = self.pagination_class()
        paginated_customers = paginator.paginate_queryset(customers, request)
        
        serializer = CustomerSerializer(paginated_customers, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data, "message": "Customer created"}, status=201)
        return Response(serializer.errors, status=400)


class CustomerCreateView(APIView):
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data, "message": "Customer created"}, status=201)
        return Response(serializer.errors, status=400)

# ------------------- SALES ORDER ------------------- #
class SalesOrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['created_by'] = request.user.id
        serializer = SalesOrderSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data, "message": "Sales order created"}, status=201)
        return Response(serializer.errors, status=400)

# ------------------- INVOICE ------------------- #
class InvoiceCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['created_by'] = request.user.id
        serializer = InvoiceSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data, "message": "Invoice created"}, status=201)
        return Response(serializer.errors, status=400)
