from django.contrib.auth import get_user_model
from djoser.conf import settings
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from api.mixins import RelEntryAddRemoveMixin
from api.serializers import UserWithRecipesSerializer

User = get_user_model()


class UserViewSet(DjoserUserViewSet, RelEntryAddRemoveMixin):
    def get_serializer_class(self):
        if self.action in ['subscriptions', 'subscribe']:
            return UserWithRecipesSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in ['subscriptions', 'subscribe']:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        queryset = (
            user.subscribed.prefetch_related('recipes')
            if self.action == 'subscriptions' else super().get_queryset())
        queryset = queryset.only(
            'id', 'email', 'username', 'first_name', 'last_name'
        ).add_is_subscribed_annotation(user.id)

        if (settings.HIDE_USERS and self.action == "list"
                and not user.is_staff):
            queryset = queryset.filter(pk=user.pk)

        return queryset

    def get_instance(self):
        user = self.request.user
        user.is_subscribed = False
        return user

    @action(detail=False, methods=['GET'])
    def subscriptions(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @action(detail=True, methods=['GET', 'DELETE'])
    def subscribe(self, request, *args, **kwargs):
        return self.rel_entry_add_remove(
            request, 'subscribed',
            add_error_msg='Вы уже подписаны на этого пользователя',
            remove_error_msg='Вы не подписаны на этого пользователя')
