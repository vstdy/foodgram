import csv

from django.db.models import F, Prefetch, Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .mixins import RelEntryAddRemoveMixin
from users.models import User
from .filters import RecipeFilter, IngredientFilter
from .models import Tag, Recipe, Composition, Ingredient
from .permissions import CurrentUserOrAdmin, IsAdminOrReadOnly
from .serializers import (
    TagSerializer, RecipeSerializer, RecipeCreateUpdateSerializer,
    RecipeMinifiedSerializer, IngredientSerializer)


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None


class RecipeViewSet(ModelViewSet, RelEntryAddRemoveMixin):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        if self.action in ['shopping_cart', 'favorite']:
            return RecipeMinifiedSerializer
        return RecipeSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [CurrentUserOrAdmin()]
        if self.action in ['shopping_cart', 'favorite',
                           'download_shopping_cart']:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        user_queryset = User.objects.only(
            'id', 'email', 'username', 'first_name', 'last_name'
        ).add_is_subscribed_annotation(user.id)

        return super().get_queryset().prefetch_related(Prefetch(
            'author', queryset=user_queryset), 'composition',
            'composition__ingredient', 'tags').add_user_annotations(user.id)

    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="shopping cart.csv"')

        writer = csv.DictWriter(
            response, fieldnames=['name', 'amount', 'unit'])
        writer.writeheader()

        recipes = request.user.in_shopping_cart.values('id')
        ingredients = Composition.objects.filter(
            recipe__in=recipes).values(
            name=F('ingredient__name'),
            unit=F('ingredient__measurement_unit')).annotate(
            amount=Sum('amount'))

        for ingredient in ingredients:
            writer.writerow(ingredient)

        return response

    @action(detail=True, methods=['GET', 'DELETE'])
    def shopping_cart(self, request, *args, **kwargs):
        return self.rel_entry_add_remove(
            request, 'in_shopping_cart',
            add_error_msg='Этот рецепт уже добавлен в корзину',
            remove_error_msg='Этого рецепта нет в корзине')

    @action(detail=True, methods=['GET', 'DELETE'])
    def favorite(self, request, *args, **kwargs):
        return self.rel_entry_add_remove(
            request, 'favorited',
            add_error_msg='Этот рецепт уже добавлен в избранное',
            remove_error_msg='Этого рецепта нет в избранном')


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [IngredientFilter]
    search_fields = ['name']
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None
