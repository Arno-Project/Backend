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
                if request.user.role == user_type[0]:
                    return True
                return False

        return Permission

