from django.urls import path
from .views import *

urlpatterns = [
    path('task-types/', TaskTypeListView.as_view(), name='task-type-list'),
    path('get-putaway-tasks/', PutAwayTaskListView.as_view(), name='putaway-task-list'),
    path('post-putaway-tasks/complete/<int:pk>/', PutAwayTaskCompleteView.as_view(), name='putaway-task-complete'),
    path('get-pickup-tasks/', PickUpTaskListView.as_view(), name='pickup-task-list'),
    path('post-pickup-tasks/complete/<int:pk>/', PickUpTaskCompleteView.as_view(), name='pickup-task-complete'),
    path('user-task-dashboard/', UserTaskDashboardView.as_view(), name='user-task-dashboard')
]
