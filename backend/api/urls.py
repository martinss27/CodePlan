
from django.contrib import admin
from django.urls import path, include
# API URL patterns for the application

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('apps.users.urls')), # -> endpoint for user management, authenticate users to be able to use the app with jira integration
    path('', include('apps.jira.urls')), # -> endpoint for task management, create tasks, assign tasks to users, etc.
]
