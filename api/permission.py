from functools import wraps
from rest_framework.response import Response


# 1. Flat permissions grouped by category
PERMISSIONS = {
    "all": [
        "create_employee", "assign_roles",

        "create_inward", "edit_inward", "view_inward",
        "create_outward", "edit_outward", "view_outward",

        "complete_putaway", "complete_pickup",
        "start_loading", "complete_loading", "view_loading",
        "view_inventory_summary"
    ],
    "employee_mgmt": ["create_employee", "assign_roles"],
    "inward_ops": ["create_inward", "edit_inward", "view_inward"],
    "outward_ops": ["create_outward", "edit_outward", "view_outward"],
    "inventory_view": ["view_inventory_summary"],
    "task_ops": ["complete_putaway", "complete_pickup"],
    "loading_ops": ["start_loading", "complete_loading", "view_loading"],
    "read_only": ["view_inward", "view_outward", "view_inventory_summary"]
}

# 2. Map role codes to permission categories
PERMISSION_GROUPS = {
    "admin": ["all"],
    "hr": ["employee_mgmt", "inward_ops", "inventory_view"],
    "manager": ["inventory_view", "loading_ops"],
    "operator": ["read_only"],
    "dispatcher": ["outward_ops", "loading_ops"]
}

# 3. Who can assign which role
ROLE_ASSIGN_RULES = {
    "admin": ["admin", "hr", "manager", "operator", "dispatcher"],
    "hr": ["manager", "operator"]
}

# 4. Helpers
def has_permission(employee, permission_code):
    return permission_code in (employee.role.permissions or [])

def can_assign_role(creator_employee, target_role_code):
    allowed = ROLE_ASSIGN_RULES.get(creator_employee.role.code.lower(), [])
    return target_role_code.lower() in allowed


def check_employee_permission(permission_code):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            try:
                employee = request.user.employee
            except Exception:
                return Response({"error": "Invalid employee."}, status=403)

            if permission_code not in (employee.role.permissions or []):
                return Response({"error": "Permission denied."}, status=403)

            return view_func(self, request, *args, **kwargs)
        return _wrapped_view
    return decorator