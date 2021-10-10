from django.contrib.auth import get_user_model
from rest_framework import serializers

from djoser.serializers import (
    UserSerializer as DjoserUserSerializer,
    UserCreateSerializer as DjoserUserCreateSerializer)

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.BooleanField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed')


class UserCreateSerializer(DjoserUserCreateSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'password')


class UserWithRecipesSerializer(DjoserUserSerializer):
    is_subscribed = serializers.BooleanField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        from api.serializers import RecipeMinifiedSerializer

        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = (obj.recipes.all()[:int(recipes_limit)] if recipes_limit
                   else obj.recipes)
        return RecipeMinifiedSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
