from django.urls import path
from .views import *

urlpatterns = [
    path('items/', ItemListView.as_view()),
    path('post-item/', ItemCreateView.as_view()),
    path('stock-summary/', InventorySummaryView.as_view()),
    path('list-inward/', InwardListView.as_view()),
    path('create-inward/', InwardCreateView.as_view()),
    path('list-outward/', OutwardListView.as_view()),
    path('create-outward/', OutwardCreateView.as_view()),

    path('logs/', InventoryLogListView.as_view()),

]
