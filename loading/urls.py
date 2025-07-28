from django.urls import path
from .views import LoadingStartView, LoadingCompleteView, LoadingListView

urlpatterns = [
    path('post-start/', LoadingStartView.as_view(), name='loading-start'),
    path('post-complete/<int:pk>/', LoadingCompleteView.as_view(), name='loading-complete'),
    path('get-loading/', LoadingListView.as_view(), name='loading-list'),
]
