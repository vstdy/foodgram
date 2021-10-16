import base64
import re
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from users.serializers import UserSerializer
from .models import Tag, Ingredient, Recipe, Composition

User = get_user_model()


class ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        data = re.search(r'(?<=data:)(.+);base64,(.+)$', data)
        if data is None:
            self.fail('invalid')
        content_type, file = data.groups()
        file_format = content_type.split('/')[1]
        file_name = self.context.get('request').data.get('name')
        full_name = f'{file_name}.{file_format}'
        file = base64.b64decode(file)
        file_size = len(file)
        file = BytesIO(file)
        data = UploadedFile(
            file=file,
            name=full_name,
            content_type=content_type,
            size=file_size,
            charset=None
        )
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', queryset=Ingredient.objects)
    name = serializers.StringRelatedField(source='ingredient.name')
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit')

    class Meta:
        model = Composition
        fields = ['id', 'name', 'measurement_unit', 'amount']


class IngredientCreateInRecipeSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', queryset=Ingredient.objects)
    amount = serializers.IntegerField()

    class Meta:
        model = Composition
        fields = ['id', 'recipe', 'amount']


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

    def get_ingredients(self, obj):
        return IngredientInRecipeSerializer(
            obj.composition.all(), many=True).data

    class Meta:
        model = Recipe
        exclude = ['pub_date']


class RecipeCreateUpdateSerializer(RecipeSerializer):
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects, many=True)
    author = serializers.SerializerMethodField()
    ingredients = IngredientCreateInRecipeSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = ImageField()

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        author = self.context.get('request').user
        validated_data['author'] = author
        recipe = super().create(validated_data)

        objs = [Composition(recipe=recipe,
                            ingredient_id=ingredient['ingredient'].id,
                            amount=ingredient['amount'])
                for ingredient in ingredients]
        Composition.objects.bulk_create(objs)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        author = self.context.get('request').user
        validated_data['author'] = author
        recipe = super().update(instance, validated_data)

        composition = {
            obj.ingredient_id: obj
            for obj in Composition.objects.filter(recipe=recipe)
        }
        objs_update, objs_create = [], []
        for ingredient in ingredients:
            if ingredient['ingredient'].id in composition:
                obj = composition.pop(ingredient['ingredient'].id)
                obj.amount = ingredient['amount']
                objs_update.append(obj)
            else:
                objs_create.append(
                    Composition(recipe=recipe,
                                ingredient_id=ingredient['ingredient'].id,
                                amount=ingredient['amount']))
        Composition.objects.bulk_update(objs_update, ['amount'])
        Composition.objects.bulk_create(objs_create)
        Composition.objects.filter(
            recipe=recipe, ingredient_id__in=composition.keys()).delete()

        return recipe

    def validate(self, attrs):
        if not attrs.get('ingredients'):
            raise serializers.ValidationError({
                'ingredients': 'В рецепте должен быть как минимум 1 ингредиент'
            })
        ingredients = []
        for ingredient in attrs['ingredients']:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError({
                    'amount': 'Убедитесь, что это значение больше либо равно 1.'
                })
            ingredients.append(ingredient['ingredient'])
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты должны быть уникальны'
            })
        if len(attrs['tags']) != len(set(attrs['tags'])):
            raise serializers.ValidationError({
                'tags': 'Тэги должны быть уникальны'
            })
        return super().validate(attrs)

    def get_author(self, obj):
        user = self.context.get('request').user
        obj.author.is_subscribed = obj in user.subscribed.all()
        return UserSerializer(obj.author).data

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return obj in user.favorited.all()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return obj in user.in_shopping_cart.all()

    def to_representation(self, instance):
        self.fields.pop('ingredients')
        self.fields['tags'] = TagSerializer(many=True)
        representation = super().to_representation(instance)
        representation['ingredients'] = IngredientInRecipeSerializer(
            instance.composition, many=True).data
        return representation


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class UserWithRecipesSerializer(DjoserUserSerializer):
    is_subscribed = serializers.BooleanField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = (obj.recipes.all()[:int(recipes_limit)] if recipes_limit
                   else obj.recipes)
        return RecipeMinifiedSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
