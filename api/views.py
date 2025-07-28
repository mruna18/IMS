# api/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from api.models import Role, Employee
from warehouse.models import Location
from rest_framework.permissions import IsAuthenticated
from .permission import *

User = get_user_model()

class RoleListView(APIView):
    def get(self, request):
        roles = Role.objects.filter().values('id', 'code', 'name')
        return Response({"roles": list(roles)})
    
#! role
class CreateRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            creator = request.user.employee
        except Employee.DoesNotExist:
            return Response({"error": "Only valid employees can create roles."}, status=403)

        if creator.role.code.lower() not in ["admin", "hr"]:
            return Response({"error": "Not allowed to create roles."}, status=403)

        data = request.data
        code = data.get("code", "").strip().lower()
        name = data.get("name", "").strip()
        based_on = data.get("based_on", "").strip().lower()

        if not code or not name:
            return Response({"error": "Code and name are required."}, status=400)

        if Role.objects.filter(code=code).exists():
            return Response({"error": "Role code already exists."}, status=400)

        # Get permission groups
        group_keys = PERMISSION_GROUPS.get(based_on, [])
        permissions = [perm for key in group_keys for perm in PERMISSIONS.get(key, [])]

        role = Role.objects.create(
            code=code,
            name=name,
            permissions=permissions
        )

        return Response({
            "message": "Role created successfully",
            "role": {
                "id": role.id,
                "code": role.code,
                "name": role.name,
                "permissions": permissions
            }
        }, status=201)
    

class RoleBaseOptionsView(APIView):
    def get(self, request):
        return Response({
            "available_base_roles": list(PERMISSION_GROUPS.keys())
        })


#! Employee
ALLOWED_CREATOR_ROLES = ['admin', 'hr']  # Based on Role.code field

class CreateEmployeeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
      
        try:
            employee = request.user.employee
            if employee.role.code.lower() not in ALLOWED_CREATOR_ROLES:
                return Response({"error": "You are not allowed to create employees."}, status=status.HTTP_403_FORBIDDEN)
        except Employee.DoesNotExist:
            return Response({"error": "Only valid employees can perform this action."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        username = data.get('username')
        password = data.get('password')
        phone_number = data.get('phone_number')
        role_id = data.get('role_id')
        location_id = data.get('location_id')  # optional

        # Basic validations
        if not all([username, password, phone_number, role_id]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        if Employee.objects.filter(phone_number=phone_number).exists():
            return Response({"error": "Phone number already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Create user
        user = User.objects.create_user(username=username, password=password)

        # Fetch role and location
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return Response({"error": "Invalid role_id"}, status=status.HTTP_400_BAD_REQUEST)

        location = None
        if location_id:
            location = Location.objects.filter(id=location_id).first()

        # Create employee
        Employee.objects.create(
            user=user,
            phone_number=phone_number,
            role=role,
            location=location,
            is_active=True
        )

        return Response({"message": "Employee created successfully"}, status=status.HTTP_201_CREATED)
