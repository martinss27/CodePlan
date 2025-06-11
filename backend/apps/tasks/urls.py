from django.urls import path
from .views import JiraAuthInit, JiraAuthCallback, JiraUserInfo, JiraProjects, JiraProjectIssues

urlpatterns = [
    path('oauth/login/', JiraAuthInit.as_view()),
    path('oauth/callback/', JiraAuthCallback.as_view()),
    path('oauth/userinfo/', JiraUserInfo.as_view()),
]

urlpatterns += [
    path('oauth/projects/', JiraProjects.as_view()),
    path('oauth/projects/<str:project_key>/issues/', JiraProjectIssues.as_view()),
]