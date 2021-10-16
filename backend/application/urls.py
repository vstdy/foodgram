from django.conf import settings
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path(settings.API_BASE_URL, include([
        path('', include('users.urls')),
        path('', include('api.urls'))
    ]))
]
