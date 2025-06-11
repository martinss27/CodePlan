from django.urls import path
from .views import JiraAuthInit, JiraAuthCallback, JiraUserInfo

urlpatterns = [
    path('oauth/login/', JiraAuthInit.as_view()),
    path('oauth/callback/', JiraAuthCallback.as_view()),
    path('oauth/userinfo/', JiraUserInfo.as_view()),
]