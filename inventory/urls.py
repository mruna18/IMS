from django.urls import path
from .views import *

urlpatterns = [
    path('items/', ItemListView.as_view()),
    path('post-item/', ItemCreateView.as_view()),

    path('item-categories/', ItemCategoryListView.as_view()),
    path('item-categories/create/', ItemCategoryCreateView.as_view()),

    path('item-batches/', ItemBatchListView.as_view()),
    path('item-batches/create/', ItemBatchCreateView.as_view()),

    path('item-lots/', ItemLotListView.as_view()),
    path('item-lots/create/', ItemLotCreateView.as_view()),

    path('quality-statuses/', QualityStatusListView.as_view()),
    path('quality-statuses/create/', QualityStatusCreateView.as_view()),


    path('stock-summary/', InventorySummaryView.as_view()),
    path('list-inward/', InwardListView.as_view()),
    path('create-inward/', InwardCreateView.as_view()),
    path('list-outward/', OutwardListView.as_view()),
    path('create-outward/', OutwardCreateView.as_view()),

    path('inventory-create/', InventoryCreateView.as_view(), name='inventory-create'),
    path('inventory-update/<int:pk>/', InventoryUpdateView.as_view(), name='inventory-update'),
    path('inventory-delete/<int:pk>/', InventorySoftDeleteView.as_view(), name='inventory-soft-delete'),
    path('inventory-list/', InventoryListView.as_view(), name='inventory-list'),

    path('logs/', InventoryLogListView.as_view()),

    path('inventory-transfer/', InventoryTransferCreateView.as_view(), name='inventory-transfer'),
    path('inventory-adjustment/', InventoryAdjustmentCreateView.as_view(), name='inventory-adjustment'),
    path('inventory-return/', InventoryReturnCreateView.as_view(), name='inventory-return'),
    path('inventory-cycle-count/', CycleCountCreateView.as_view(), name='inventory-cycle-count'),

    path('get-suppliers/', SupplierListView.as_view(), name='supplier-list'),
    path('create-suppliers/', SupplierCreateView.as_view(), name='supplier-create'),

    path('purchase-orders/', PurchaseOrderListView.as_view(), name='purchaseorder-list'),
    path('purchase-orders/create/', PurchaseOrderCreateView.as_view(), name='purchaseorder-create'),
    path('purchase-orders/filter/', FilteredPurchaseOrderListView.as_view(), name='purchaseorder-filter'),

]
