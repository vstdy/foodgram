from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS


class UserPermissions(permissions.IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if view.action in ['set_password', 'set_username', 'destroy'] or (
                view.action == "me" and view.request and
                view.request.method == "DELETE"
        ):
            return user.is_admin or obj.pk == user.pk
        return True

    def has_permission(self, request, view):
        if view.action in [
            'subscriptions', 'subscribe', 'token_destroy'
        ]:
            return bool(request.user and request.user.is_authenticated)
        if view.action == 'create':
            return True
        return super().has_permission(request, view)


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.method in SAFE_METHODS or
                    request.user and request.user.is_authenticated and
                    request.user.is_admin)
