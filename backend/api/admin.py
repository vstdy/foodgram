from django.contrib import admin

from .models import Recipe, Tag, Ingredient, Composition


class CompositionInlineAdmin(admin.TabularInline):
    model = Composition


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'author', 'name', 'image', 'text',
                    'get_ingredients', 'get_tags', 'get_fans', 'cooking_time')
    list_display_links = ('pk', 'name',)
    search_fields = ('author__username', 'name', 'tags__name')
    list_filter = ('tags',)
    fields = ('author', 'name', 'image', 'text', 'tags', 'cooking_time')
    filter_horizontal = ('ingredients', 'tags')
    inlines = (CompositionInlineAdmin,)
    list_per_page = 20

    def get_ingredients(self, obj):
        return ',\n'.join(obj.ingredients.values_list('name', flat=True))
    get_ingredients.short_description = 'ингредиенты'

    def get_tags(self, obj):
        return ',\n'.join(obj.tags.values_list('name', flat=True))
    get_tags.short_description = 'тэги'

    def get_fans(self, obj):
        return obj.fans.count()
    get_fans.short_description = 'фанаты'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'slug', 'color')
    list_display_links = ('pk', 'name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    list_display_links = ('pk', 'name',)
    search_fields = ('name',)
    list_per_page = 20
