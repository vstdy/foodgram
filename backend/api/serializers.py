from django.db import transaction
from rest_framework import serializers

from application.utils import ImageField
from users.serializers import UserSerializer
from .models import Tag, Ingredient, Recipe, Composition


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
    ingredients = IngredientInRecipeSerializer(many=True)
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

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

        if ingredients is not None:
            objs = [Composition(recipe=recipe,
                                ingredient_id=ingredient.get('id'),
                                amount=ingredient.get('amount'))
                    for ingredient in ingredients]
            Composition.objects.bulk_create(objs)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        author = self.context.get('request').user
        validated_data['author'] = author
        recipe = super().update(instance, validated_data)

        if ingredients is not None:
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
