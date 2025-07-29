# from django.contrib import admin
# from .models import Role, Employee

# @admin.register(Role)
# class RoleAdmin(admin.ModelAdmin):
#     list_display = ('id', 'code', 'name', 'description')

from django.contrib import admin
from .models import Role, Employee
from django.contrib.auth import get_user_model
from api.permission import *

User = get_user_model()


# @admin.register(Role)
# class RoleAdmin(admin.ModelAdmin):
#     list_display = ('id', 'code', 'name', 'permission_count')
#     search_fields = ('code', 'name')
#     readonly_fields = ('permission_preview',)

#     def permission_count(self, obj):
#         return len(obj.permissions or [])
#     permission_count.short_description = 'Permissions'

#     def permission_preview(self, obj):
#         if not obj.permissions:
#             return "-"
#         return ", ".join(obj.permissions)
#     permission_preview.short_description = "Permissions"

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'permission_count')
    search_fields = ('code', 'name')
    readonly_fields = ('permission_preview',)

    def permission_count(self, obj):
        role_code = obj.code.lower()
        groups = PERMISSION_GROUPS.get(role_code, [])
        permissions = set()
        for group in groups:
            permissions.update(PERMISSIONS.get(group, []))
        return len(permissions)

    permission_count.short_description = 'Permissions'

    def permission_preview(self, obj):
        role_code = obj.code.lower()
        groups = PERMISSION_GROUPS.get(role_code, [])
        permissions = set()
        for group in groups:
            permissions.update(PERMISSIONS.get(group, []))
        return ", ".join(sorted(permissions)) if permissions else "-"
        
    permission_preview.short_description = "Effective Permissions"


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_username', 'phone_number', 'role', 'is_active')
    search_fields = ('user__username', 'phone_number', 'role__code')
    list_filter = ('role__code', 'is_active')

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'



# @admin.register(Employee)
# class EmployeeAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'phone_number', 'role', 'location', 'is_active')
#     search_fields = ('user__username', 'phone_number')