from django.urls import path
from .views import RegisterView, LoginView, LogoutView


urlpatterns = [
    path('register', RegisterView.as_view(), name='register'), # endpoint for user registration
    path('login', LoginView.as_view(), name='login'), # endpoint for user login, returns access and refresh tokens in cookies
    path('logout', LogoutView.as_view(), name='logout'), # endpoint for user logout, clears cookies and redirects to login page
]