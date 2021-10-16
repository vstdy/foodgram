from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS


class RecipePermissions(permissions.IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if view.action in ['update', 'partial_update', 'destroy']:
            return user.is_admin or obj.author_id == user.pk
        return True

    def has_permission(self, request, view):
        if view.action in [
            'shopping_cart', 'favorite', 'download_shopping_cart'
        ]:
            return bool(request.user and request.user.is_authenticated)
        return super().has_permission(request, view)


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.method in SAFE_METHODS or
                    request.user and request.user.is_authenticated and
                    request.user.is_admin)
