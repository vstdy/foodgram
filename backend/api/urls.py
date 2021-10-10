from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('tags', views.TagViewSet)
router.register('recipes', views.RecipeViewSet)
router.register('ingredients', views.IngredientViewSet)

urlpatterns = router.urls
