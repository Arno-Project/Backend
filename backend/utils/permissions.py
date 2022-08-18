from rest_framework import permissions

from accounts.models import User


class BasicUserPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return False


class PermissionFactory():
    def __init__(self, user_type: User.UserRole):
        self.user_type: User.UserRole = user_type

    def get_permission_class(self):
        user_type = self.user_type

        class Permission(BasicUserPermission):
            def has_object_permission(self, request, view, obj):
                permitted = super().has_object_permission(request, view, obj)
                if permitted:
                    return True
                if hasattr(request.user, 'get_role') and request.user.get_role() == user_type:
                    return True
                return False

            def has_permission(self, request, view):
                return self.has_object_permission(request, view, None) and super().has_permission(request, view)

        return Permission
