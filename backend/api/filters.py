from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter

from .models import Recipe, Tag


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter()
    is_in_shopping_cart = filters.BooleanFilter()
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug', to_field_name='slug', queryset=Tag.objects)

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author', 'tags']


class IngredientFilter(SearchFilter):
    search_param = 'name'
