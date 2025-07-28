from django.urls import path
from .views import *

urlpatterns = [
    path('list-warehouse/', WarehouseListView.as_view(), name='warehouse-list'),
    path('create-warehouse/', WarehouseCreateView.as_view(), name='warehouse-create'),
    path('list-location/<int:warehouse_id>/', LocationListView.as_view(), name='location-list'),
    path('create-location/<int:warehouse_id>/', LocationCreateView.as_view(), name='location-create'),

]
