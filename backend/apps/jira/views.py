import os

import requests
import re
import json
from dotenv import load_dotenv

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import JiraToken
from .services import *

load_dotenv()

JIRA_CLIENT_ID = os.getenv("JIRA_CLIENT_ID")
JIRA_CLIENT_SECRET = os.getenv("JIRA_CLIENT_SECRET")

JIRA_REDIRECT_URI = "http://127.0.0.1:8000/jira/callback"
JIRA_AUTH_URL = "https://auth.atlassian.com/authorize"
JIRA_TOKEN_URL = "https://auth.atlassian.com/oauth/token"

JIRA_API_URL = "https://api.atlassian.com/me"
JIRA_PROJECTS_API = "https://api.atlassian.com/ex/jira/{cloudid}/rest/api/3/project/search"

JIRA_SCOPES = "read:jira-work read:jira-user read:me"

class JiraAuthInit(APIView):
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
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
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
        return redirect("http://127.0.0.1:8000/jira/projects")

class JiraUserInfo(APIView):
    @method_decorator(login_required)
    def get(self, request):
        try:
            jira_token = JiraToken.objects.get(user=request.user)
        except JiraToken.DoesNotExist:
            return Response({"error": "Token not found"}, status=404)
        headers = {"Authorization": f"Bearer {jira_token.access_token}"}
        resp = requests.get(JIRA_API_URL, headers=headers)
        return Response(resp.json())
    
class IntegrationStatusView(APIView): #     GET /integrations/status
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            JiraToken.objects.get(user=request.user)
            jira_connected = True
        except JiraToken.DoesNotExist:
            jira_connected = False
        return Response({
            "jira_connected": jira_connected,
        })
    
class JiraProjects(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        projects, error = get_user_jira_projects(request.user)
        if error:
            return Response({"error": error}, status=404)
        for project in projects:
            project_key = project.get("key")
            if project_key:
                project["issues_url"] = f"/jira/projects/{project_key}/issues/"
        return Response(projects)

    
class JiraProjectIssues(APIView):
    @method_decorator(login_required)
    def get(self, request, project_key):
        jira_token, cloud_id, error = self._get_token_and_cloud_id(request.user)
        if error:
            return Response({"error": error}, status=404)

        filtered_issues = self._get_filtered_issues(jira_token, cloud_id, project_key)
        order_label = self._get_order_label(request)
        prompt = build_ai_prompt(filtered_issues, order_label)
        ia_response = call_ai(prompt)

        enriched_ia_summary, ordering_summary = self._process_ai_response(ia_response, filtered_issues)

        return Response({
            "issues": filtered_issues,
            "ai_summary": enriched_ia_summary,
            "ordering_summary": ordering_summary
        })

    def _get_token_and_cloud_id(self, user):
        return get_jira_token_and_cloud_id(user)

    def _get_filtered_issues(self, jira_token, cloud_id, project_key):
        issues = get_project_issues(jira_token, cloud_id, project_key)
        return filter_issues(issues)

    def _get_order_label(self, request):
        order_by = request.GET.get("order_by", "").strip().lower()
        order_options = {
            "dificuldade": "dificuldade",
            "prazo": "prazo",
            "prioridade": "prioridade",
            "impacto": "impacto no projeto",
            "dependencias": "dependências"
        }
        return order_options.get(order_by)

    def _process_ai_response(self, ia_response, filtered_issues):
        if isinstance(ia_response, list) and len(ia_response) == len(filtered_issues):
            enriched_ia_summary = []
            for issue, ai_item in zip(filtered_issues, ia_response):
                enriched_ia_summary.append({
                    "id": issue['id'],
                    "summary": issue['summary'],
                    **ai_item
                })
        else:
            enriched_ia_summary = ia_response

        if isinstance(ia_response, dict) and "tasks" in ia_response and "mensagem" in ia_response:
            enriched_ia_summary = ia_response["tasks"]
            ordering_summary = ia_response["mensagem"]
        elif isinstance(ia_response, list) and len(ia_response) == len(filtered_issues):
            ordering_summary = None
        else:
            ordering_summary = None

        return enriched_ia_summary, ordering_summary