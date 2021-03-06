from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Exists, OuterRef


class RecipeQuerySet(models.QuerySet):
    def add_user_annotations(self, user_id):
        favorites_model = self.model.fans.through
        buyers_model = self.model.buyers.through
        return self.annotate(
            is_favorited=Exists(
                favorites_model.objects.filter(
                    user_id=user_id, recipe_id=OuterRef('id')
                )
            ),
            is_in_shopping_cart=Exists(
                buyers_model.objects.filter(
                    user_id=user_id, recipe_id=OuterRef('id')
                )
            )
        )


class Recipe(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.CASCADE,
                               related_name='recipes',
                               verbose_name='Автор')
    name = models.CharField('Имя', max_length=200, unique=True)
    image = models.ImageField('Изображение', max_length=200, upload_to='api/',
                              blank=True, null=True)
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField('Ingredient', through='Composition',
                                         related_name='recipes',
                                         verbose_name='Ингредиенты')
    tags = models.ManyToManyField('Tag', verbose_name='Теги')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления', validators=[MinValueValidator(1)])
    pub_date = models.DateTimeField(
        'Опубликовано', auto_now_add=True, db_index=True)

    objects = RecipeQuerySet.as_manager()

    class Meta:
        verbose_name_plural = 'Рецепты'
        verbose_name = 'Рецепт'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name[:15]


class Tag(models.Model):
    name = models.CharField('Имя', max_length=200, unique=True)
    slug = models.SlugField('Слаг', max_length=200, unique=True)
    color = models.CharField('Цветовой HEX-код', max_length=7,
                             null=True, unique=True)

    class Meta:
        verbose_name_plural = 'Теги'
        verbose_name = 'Тег'
        ordering = ['id']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Имя', max_length=200, unique=True)
    measurement_unit = models.CharField('Единица измерения', max_length=200)

    class Meta:
        verbose_name_plural = 'Ингредиенты'
        verbose_name = 'Ингредиент'
        ordering = ['id']

    def __str__(self):
        return self.name


class Composition(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='composition',
                               verbose_name='Рецепт')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   related_name='in_composition',
                                   verbose_name='Ингредиент')
    amount = models.PositiveSmallIntegerField(
        'Количество', validators=[MinValueValidator(1)])

    class Meta:
        verbose_name_plural = 'Состав рецепта'
        verbose_name = 'Ингредиент'
        ordering = ['id']
        unique_together = ('recipe', 'ingredient')
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='recipe_ingredient_constraint')
        ]

    def __str__(self):
        return f'{self.recipe} - {self.ingredient}'
