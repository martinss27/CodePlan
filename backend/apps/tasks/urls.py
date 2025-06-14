from django.urls import path
from .views import (
    JiraAuthInit,
    JiraAuthCallback,
    JiraUserInfo,
    JiraProjects,
    JiraProjectIssues,
)

urlpatterns = [
    path('oauth/login', JiraAuthInit.as_view(), name='jira_auth_init'),
    path('oauth/callback', JiraAuthCallback.as_view(), name='jira_auth_callback'),
    path('oauth/userinfo', JiraUserInfo.as_view(), name='jira_user_info'),
    path('oauth/projects', JiraProjects.as_view(), name='jira_projects'),
    path('oauth/projects/<str:project_key>/issues/', JiraProjectIssues.as_view(), name='jira_project_issues'),
]