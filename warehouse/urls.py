
from django.urls import path
from .views import WarehouseListCreateView, LocationListCreateView

urlpatterns = [
    path('', WarehouseListCreateView.as_view(), name='warehouse-list-create'),
    path('<int:warehouse_id>/locations/', LocationListCreateView.as_view(), name='location-list-create'),
]

