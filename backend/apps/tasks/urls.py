from django.urls import path
from .views import (
    JiraAuthInit,
    JiraAuthCallback,
    JiraUserInfo,
    JiraProjects,
    JiraProjectIssues,
    IntegrationStatusView,
)

urlpatterns = [
    path('jira/login', JiraAuthInit.as_view(), name='jira_auth_init'), # starts the OAuth flow
    path('jira/callback', JiraAuthCallback.as_view(), name='jira_auth_callback'), # handles the OAuth callback
    path('integration/status', IntegrationStatusView.as_view(), name='integration_status'), # checks if Jira is connected
    path('jira/userinfo', JiraUserInfo.as_view(), name='jira_user_info'), # retrieves user info from Jira
    path('jira/projects', JiraProjects.as_view(), name='jira_projects'), # retrieves all Jira projects for the user
    path('jira/projects/<str:project_key>/issues/', JiraProjectIssues.as_view(), name='jira_project_issues'), # retrieves issues for a specific project with AI summary and ordering
]