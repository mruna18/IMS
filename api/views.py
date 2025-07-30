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
        print('🔐 Role creation attempt')
        
        # Step 1: Get the role code of the creator
        if hasattr(request.user, 'employee'):
            creator_role_code = request.user.employee.role.code.lower()
        elif request.user.is_superuser:
            creator_role_code = "admin"  # Allow superuser to bootstrap
        else:
            return Response({"error": "Only valid employees can create roles."}, status=403)

        # Step 2: Only admin/hr can proceed
        if creator_role_code not in ["admin", "hr"]:
            return Response({"error": "Not allowed to create roles."}, status=403)

        # Step 3: Validate input
        data = request.data
        code = data.get("code", "").strip().lower()
        name = data.get("name", "").strip()
        based_on = data.get("based_on", "").strip().lower()

        if not code or not name:
            return Response({"error": "Code and name are required."}, status=400)

        if Role.objects.filter(code=code).exists():
            return Response({"error": "Role code already exists."}, status=400)

        # Step 4: Determine permissions based on 'based_on' role
        group_keys = PERMISSION_GROUPS.get(based_on, [])
        permissions = [perm for key in group_keys for perm in PERMISSIONS.get(key, [])]

        # Step 5: Create the role
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
        # print('fjdsjfnjd')
        # print("Request Data:", request.data)
        # Check if the current user is allowed to create employees
        if hasattr(request.user, 'employee'):
            creator_role_code = request.user.employee.role.code.lower()
        elif request.user.is_superuser:
            creator_role_code = "admin"  # Bootstrap fallback
        else:
            return Response({"error": "Only valid employees can perform this action."}, status=status.HTTP_403_FORBIDDEN)

        if creator_role_code not in ALLOWED_CREATOR_ROLES:
            return Response({"error": "You are not allowed to create employees."}, status=status.HTTP_403_FORBIDDEN)

        # Step 2: Parse request data
        data = request.data
        username = data.get('username')
        password = data.get('password')
        user_id = data.get('user_id')  # Optional: for existing user
        phone_number = data.get('phone_number')
        role_id = data.get('role_id')
        location_id = data.get('location_id')  # optional

        # Step 3: Validate required fields
        if not phone_number or not role_id:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        if Employee.objects.filter(phone_number=phone_number).exists():
            return Response({"error": "Phone number already exists"}, status=status.HTTP_400_BAD_REQUEST)

        user = None
        if user_id:
            user = User.objects.filter(id=user_id).first()
            if not user:
                return Response({"error": "Invalid user_id"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Ensure username & password are present
            if not username or not password:
                return Response({"error": "Username and password are required for new user creation"}, status=status.HTTP_400_BAD_REQUEST)

            if User.objects.filter(username=username).exists():
                return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.create_user(username=username, password=password)

        # Step 4: Fetch role and location
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return Response({"error": "Invalid role_id"}, status=status.HTTP_400_BAD_REQUEST)

        location = None
        if location_id:
            location = Location.objects.filter(id=location_id).first()

        # Step 5: Create employee
        Employee.objects.create(
            user=user,
            phone_number=phone_number,
            role=role,
            location=location,
            is_active=True
        )

        return Response({"message": "Employee created successfully"}, status=status.HTTP_201_CREATED)
