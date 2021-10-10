from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'username', 'first_name', 'last_name', 'email', 'date_joined',
        'get_favorited', 'get_subscribed', 'get_subscribers')
    list_display_links = ('pk', 'username',)
    search_fields = ('email', 'username')
    filter_horizontal = ('groups', 'user_permissions', 'subscribed',
                         'favorited', 'in_shopping_cart')
    list_per_page = 20

    def get_favorited(self, obj):
        return obj.favorited.count()
    get_favorited.short_description = 'любимых рецептов'

    def get_subscribed(self, obj):
        return obj.subscribed.count()
    get_subscribed.short_description = 'подписан'

    def get_subscribers(self, obj):
        return obj.subscribers.count()
    get_subscribers.short_description = 'подписчиков'
