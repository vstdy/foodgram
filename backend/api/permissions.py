from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS


class CurrentUserOrAdmin(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        user = request.user
        return user.is_admin or obj.pk == user.pk


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.method in SAFE_METHODS or
                    request.user and request.user.is_authenticated and
                    request.user.is_admin)
