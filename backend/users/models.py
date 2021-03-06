from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models import Exists, OuterRef


class UserQuerySet(models.QuerySet):
    def add_is_subscribed_annotation(self, user_id):
        favorites_model = self.model.subscribed.through
        return self.annotate(
            is_subscribed=Exists(
                favorites_model.objects.filter(
                    from_user_id=user_id, to_user_id=OuterRef('id')
                )
            )
        )


class CustomUserManager(UserManager.from_queryset(UserQuerySet)):
    pass


class User(AbstractUser):
    USER = 'user'
    ADMIN = 'admin'

    ROLES = (
        (USER, 'user'),
        (ADMIN, 'admin')
    )

    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    email = models.EmailField('Электронная почта')
    role = models.CharField('Роль', max_length=5, choices=ROLES, default=USER)
    subscribed = models.ManyToManyField(
        'User', related_name='subscribers', symmetrical=False,
        verbose_name='Подписан')
    favorited = models.ManyToManyField(
        'api.Recipe', related_name='fans',
        verbose_name='Избранные рецепты')
    in_shopping_cart = models.ManyToManyField(
        'api.Recipe', related_name='buyers', verbose_name='В корзине')

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['id']

    @property
    def is_admin(self):
        return self.is_staff or self.role == User.ADMIN
