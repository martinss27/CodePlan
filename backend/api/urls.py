
from django.contrib import admin
from django.urls import path, include
# API URL patterns for the application

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('apps.users.urls')),
]
