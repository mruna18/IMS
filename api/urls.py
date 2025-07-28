from django.urls import path
from .views import *

urlpatterns = [
    path('create-employee/', CreateEmployeeView.as_view(), name='create-employee'),
    path('roles/', RoleListView.as_view(), name='role-list'),
    path('create-role/', CreateRoleView.as_view(), name='create-role'),
    path('role-base-options/', RoleBaseOptionsView.as_view(), name='role-base-options'),
]
