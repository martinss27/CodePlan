import os
from dotenv import load_dotenv
load_dotenv()
import requests
import re
import json

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

        # new: Get the order_by parameter from the request
        order_by = request.GET.get("order_by", "").strip().lower()
        order_options = {
            "dificuldade": "dificuldade",
            "prazo": "prazo",
            "prioridade": "prioridade",
            "impacto": "impacto no projeto",
            "dependencias": "dependências"
        }
        order_label = order_options.get(order_by)

        def extract_description(desc):
                if isinstance(desc, dict) and "content" in desc:
                    #extract text from Jira structured description
                    try:
                        return " ".join(
                            t["text"]
                            for p in desc["content"]
                            for t in p.get("content", [])
                            if t.get("type") == "text"
                        )
                    except Exception:
                        return str(desc)
                return desc if desc else ""
        
        # Filter to get only essential fields
        filtered_issues = [
            {
                "id": issue["id"],
                "key": issue["key"],
                "summary": issue["fields"].get("summary"),
                "description": extract_description(issue["fields"].get("description")),
                "status": issue["fields"].get("status", {}).get("name"),
                "assignee": (
                    issue["fields"].get("assignee", {}).get("displayName")
                    if issue["fields"].get("assignee") else None
                ),
                #"created": issue["fields"].get("created"),
                #"updated": issue["fields"].get("updated"),
                "issuetype": issue["fields"].get("issuetype", {}).get("name"),
                "priority": issue["fields"].get("priority", {}).get("name"),
            }
            for issue in data.get("issues", [])
        ]
#       return Response(filtered_issues)
    
        
        # Create the prompt for the AI
        # new dynamic prompt based on the order_by parameter

        if order_label:
            prompt = (
        f"Você é uma SCRUM MASTER sênior, especialista em priorização de tarefas de desenvolvimento ágil.\n"
        f"Analise as tasks abaixo e ORDENE pelo critério: '{order_label}'.\n"
        f"Monte uma mensagem prévia e refinada para orientar o usuário sobre o que ele precisa saber para tomar decisões estratégicas no JIRA. Siga este formato:\n"
        f"1. Um RESUMO EXECUTIVO sobre a lógica de ordenação e o objetivo estratégico.\n"
        f"2. Blocos destacados:\n"
        f"   -  POR QUE ESSA ORDEM? (explique o racional, cite exemplos práticos)\n"
        f"   -  IMPACTO PRÁTICO (o que muda para o negócio e para o usuário, de uma perspectiva de o quanto esse impacto sera efetivo e forte)\n"
        f"   -  RECOMENDAÇÕES ESTRATÉGICAS (com exemplos de aplicação, e explicação breve do motivo dessas recomendações)\n"
        f"   -  RISCOS DE NÃO SEGUIR ESSA ORDEM\n"
        f"   -  CHECKLIST DE PRÓXIMOS PASSOS\n"
        f"Use linguagem clara, objetiva, tom de liderança ágil, destacar em bullet points.\n"

        #each task prompt:
        f"Para cada task, inclua:\n"
        f"- Descrição (resuma para os 50 primeiros caracteres da descrição original e adicione '...' ao final, mesmo que a descrição seja menor)\n"
        f"- Dicas de bibliotecas úteis (se for backend, sugira para Python, JavaScript e Java; se for frontend, sugira para JavaScript, React e Vue)\n"
        f"- Fatores de risco(traga 2 possiveis fatores de risco que podem acontecer)\n"
        f"- Estratégia recomendada(seja mais profundo aqui, pode dizer de uma forma mais lógica, como a estratégia deve ser aplicada, para que seja algo funcional independentemente da task ou independentemente da linguagem)\n"
        f"- Estimativa de tempo\n"
        f"Responda com um JSON: {{ 'mensagem': <mensagem_geral>, 'tasks': [ ...tasks_ordenadas... ] }}\n\n"
        f"Tasks:\n"
            )
        else:
            prompt = (
        "Você é uma SCRUM MASTER sênior, especialista em priorização de tarefas de desenvolvimento ágil.\n"
        "Analise as tasks abaixo e ORDENE conforme sua experiência, considerando o que for mais estratégico para o time.\n"
        "Monte uma mensagem prévia e refinada para orientar o usuário sobre o que ele precisa saber para tomar decisões estratégicas no JIRA. Siga este formato:\n"
        "1. Um RESUMO EXECUTIVO sobre a lógica de ordenação e o objetivo estratégico.\n"
        "2. Blocos destacados:\n"
        "   -  POR QUE ESSA ORDEM? (explique o racional, cite exemplos práticos)\n"
        "   -  IMPACTO PRÁTICO (o que muda para o negócio e para o usuário, de uma perspectiva de o quanto esse impacto sera efetivo e forte)\n"
        "   -  RECOMENDAÇÕES ESTRATÉGICAS (com exemplos de aplicação, e explicação breve do motivo dessas recomendações)\n"
        "   -  RISCOS DE NÃO SEGUIR ESSA ORDEM\n"
        "   -  CHECKLIST DE PRÓXIMOS PASSOS\n"
        "Use linguagem clara, objetiva, tom de liderança ágil, destacar em bullet points.\n"
        
        # each task prompt:
        "Para cada task, inclua:\n"
        "- Descrição (resuma para os 50 primeiros caracteres da descrição original e adicione '...' ao final, mesmo que a descrição seja menor)\n"
        "- Dicas de bibliotecas úteis (se for backend, sugira para Python, JavaScript e Java; se for frontend, sugira para JavaScript, React e Vue)\n"
        "- Fatores de risco(traga 2 possiveis fatores de risco que podem acontecer)\n"
        "- Estratégia recomendada(seja mais profundo aqui, pode dizer de uma forma mais lógica, como a estratégia deve ser aplicada, para que seja algo funcional independentemente da task ou independentemente da linguagem)\n"
        "- Estimativa de tempo\n"
        "Responda com um JSON: { 'mensagem': <mensagem_geral>, 'tasks': [ ...tasks_ordenadas... ] }\n\n"
        "Tasks:\n"
            )


        # Add each issue to the prompt
        for issue in filtered_issues:
            prompt += (
                f"- ID: {issue['id']}\n"
                f"- Título: {issue['summary']}\n"
                f"Descrição: {extract_description(issue['description'])}\n"
                f"Status: {issue['status']}\n"
                f"Tipo: {issue['issuetype']}\n"
                f"Prioridade: {issue['priority']}\n"
                f"Responsável: {issue['assignee']}\n\n"
            )

        # call the Deepseek API 

        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost:8000",
            "X-title": "Jira DeepSeek Integration",
            }
        payload = {
            "model": "deepseek/deepseek-chat:free",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        ia_response = None
        try:
            ia_resp = requests.post(api_url, headers=headers, json=payload, timeout=30)
            if ia_resp.ok:
                ia_json = ia_resp.json()
                ia_response = ia_json["choices"][0]["message"]["content"]

                # remove markdown code blocks, if they exist
                if ia_response:
                    ia_response = re.sub(r"^```json\s*|\s*```$", "", ia_response.strip(), flags=re.MULTILINE)
                    
                    # try to convert as a python object
                    try:
                        ia_response = json.loads(ia_response)
                    except Exception:
                        pass
            else:
                ia_response = f"Error: {ia_resp.status_code} - {ia_resp.text}"
        except Exception as e:
            ia_response = f"error calling IA: {str(e)}"


        # Return the filtered issues and the AI summary
        if isinstance(ia_response, list) and len(ia_response) == len(filtered_issues):
            enriched_ia_summary = []
            for issue, ai_item in zip(filtered_issues, ia_response):
                enriched_ia_summary.append({
                    "id": issue['id'],
                    "summary": issue['summary'],
                    **ai_item
                })
        else:
            enriched_ia_summary = ia_response # fallback to the raw IA response if it doesn't match the expected format

        # new: filter the issues based on the order_by parameter
        if isinstance(ia_response, dict) and "tasks" in ia_response and "mensagem" in ia_response:
            enriched_ia_summary = ia_response["tasks"]
            mensagem_ordenacao = ia_response["mensagem"]
        elif isinstance(ia_response, list) and len(ia_response) == len(filtered_issues):
            enriched_ia_summary = ia_response
            mensagem_ordenacao = None
        else:
            enriched_ia_summary = ia_response
            mensagem_ordenacao = None

        return Response({
            "issues": filtered_issues,
            "ai_summary": enriched_ia_summary,
            "mensagem_ordenacao": mensagem_ordenacao
        })