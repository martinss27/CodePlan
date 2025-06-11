import os
from dotenv import load_dotenv
load_dotenv()
import requests

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework.response import Response
from .models import JiraToken

JIRA_CLIENT_ID = os.getenv("JIRA_CLIENT_ID")
JIRA_CLIENT_SECRET = os.getenv("JIRA_CLIENT_SECRET")

JIRA_REDIRECT_URI = "http://127.0.0.1:8000/oauth/callback"
JIRA_AUTH_URL = "https://auth.atlassian.com/authorize"
JIRA_TOKEN_URL = "https://auth.atlassian.com/oauth/token"

JIRA_API_URL = "https://api.atlassian.com/me"
JIRA_PROJECTS_API = "https://api.atlassian.com/ex/jira/{cloudid}/rest/api/3/project/search"

JIRA_SCOPES = "read:jira-work read:jira-user read:me"

def get_cloud_id(access_token): #Function to get the cloud_id (will be reused throughout the code)
    url = "https://api.atlassian.com/oauth/token/accessible-resources"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    resources = resp.json()
    return resources[0]["id"] if resources else None


class JiraAuthInit(APIView):
    @method_decorator(login_required)
    def get(self, request):
        url = (
            f"{JIRA_AUTH_URL}?audience=api.atlassian.com"
            f"&client_id={JIRA_CLIENT_ID}"
            f"&scope={JIRA_SCOPES.replace(' ', '%20')}"
            f"&redirect_uri={JIRA_REDIRECT_URI}"
            f"&response_type=code"
            f"&prompt=consent"
        )
        return redirect(url)

class JiraAuthCallback(APIView):
    @method_decorator(login_required)
    def get(self, request):
        print("User authenticated:", request.user.is_authenticated)
        print("User:", request.user)
        print("GET params:", request.GET)
        code = request.GET.get("code")
        if not code:
            return Response({"error": "code not found."}, status=400)
        data = {
            "grant_type": "authorization_code",
            "client_id": JIRA_CLIENT_ID,
            "client_secret": JIRA_CLIENT_SECRET,
            "code": code,
            "redirect_uri": JIRA_REDIRECT_URI,
        }
        resp = requests.post(JIRA_TOKEN_URL, json=data)
        if resp.status_code != 200:
            return Response({"error": "Error obtaining token"}, status=400)
        token_data = resp.json()


        JiraToken.objects.update_or_create(
            user=request.user,
            defaults={
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "expires_in": token_data.get("expires_in", 0),
            }
        )
        return Response({"message": "Token saved successfully!"})

class JiraUserInfo(APIView):
    @method_decorator(login_required)
    def get(self, request):
        print("Entered the JiraUserInfo view")
        print("User authenticated:", request.user.is_authenticated)
        print("User:", request.user)
        try:
            jira_token = JiraToken.objects.get(user=request.user)
        except JiraToken.DoesNotExist:
            print("Token not found for the user")
            return Response({"error": "Token not found"}, status=404)
        headers = {"Authorization": f"Bearer {jira_token.access_token}"}
        resp = requests.get(JIRA_API_URL, headers=headers)
        print("Jira response:", resp.status_code, resp.text)
        return Response(resp.json())
    
class JiraProjects(APIView):
    @method_decorator(login_required)
    def get(self, request):
        try:
            jira_token = JiraToken.objects.get(user=request.user)
        except JiraToken.DoesNotExist:
            return Response({"error": "Token not found"}, status=404)
        cloud_id = get_cloud_id(jira_token.access_token)
        if not cloud_id:
            return Response({"error": "Cloud ID not found"}, status=404)
        url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project/search"
        headers = {"Authorization": f"Bearer {jira_token.access_token}"}
        resp = requests.get(url, headers=headers)
        data = resp.json()
        # Filter to get only essential fields
        filtered_projects = [
            {
                "id": p["id"],
                "key": p["key"],
                "name": p["name"],
                "projectType": p.get("projectTypeKey"),
                "IsPrivate": p.get("isPrivate"),
            }
            for p in data.get("values", [])
        ]
        return Response(filtered_projects)
    
class JiraProjectIssues(APIView):
    @method_decorator(login_required)
    def get(self, request, project_key):
        try:
            jira_token = JiraToken.objects.get(user=request.user)
        except JiraToken.DoesNotExist:
            return Response({"error": "Token not found"}, status=404)
        cloud_id = get_cloud_id(jira_token.access_token)
        if not cloud_id:
            return Response({"error": "Cloud ID not found"}, status=404)
        url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/search?jql=project={project_key}"
        headers = {"Authorization": f"Bearer {jira_token.access_token}"}
        resp = requests.get(url, headers=headers)
        data = resp.json()
        
        # Filter to get only essential fields
        filtered_issues = [
            {
                "id": issue["id"],
                "key": issue["key"],
                "summary": issue["fields"].get("summary"),
                "description": issue["fields"].get("description"),
                "status": issue["fields"].get("status", {}).get("name"),
                "assignee": (
                    issue["fields"].get("assignee", {}).get("displayName")
                    if issue["fields"].get("assignee") else None
                ),
                "created": issue["fields"].get("created"),
                "updated": issue["fields"].get("updated"),
                "issuetype": issue["fields"].get("issuetype", {}).get("name"),
                "priority": issue["fields"].get("priority", {}).get("name"),
            }
            for issue in data.get("issues", [])
        ]
        return Response(filtered_issues)