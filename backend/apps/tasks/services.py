import requests
import os
import re
import json
from .models import JiraToken

def get_cloud_id(access_token): #Function to get the cloud_id (will be reused throughout the code)
    url = "https://api.atlassian.com/oauth/token/accessible-resources"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    resources = resp.json()
    return resources[0]["id"] if resources else None

def get_user_jira_projects(user):
    try:
        jira_token = JiraToken.objects.get(user=user)
    except JiraToken.DoesNotExist:
        return None, "Token not found"
    cloud_id = get_cloud_id(jira_token.access_token)
    if not cloud_id:
        return None, "Cloud ID not found"
    url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project/search"
    headers = {"Authorization": f"Bearer {jira_token.access_token}"}
    resp = requests.get(url, headers=headers)
    data = resp.json()
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
    return filtered_projects, None

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

def get_jira_token_and_cloud_id(user):

    try:
        jira_token = JiraToken.objects.get(user=user)
    except JiraToken.DoesNotExist:
        return None, None, "Token not found"
    cloud_id = get_cloud_id(jira_token.access_token)
    if not cloud_id:
        return None, None, "Cloud ID not found"
    return jira_token, cloud_id, None

def get_project_issues(jira_token, cloud_id, project_key):
    url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/search?jql=project={project_key}"
    headers = {"Authorization": f"Bearer {jira_token.access_token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    return data.get("issues", [])

def filter_issues(issues): #filter and format just the necessary fields
         return [
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
            "issuetype": issue["fields"].get("issuetype", {}).get("name"),
            "priority": issue["fields"].get("priority", {}).get("name"),
        }
        for issue in issues
    ]

def build_ai_prompt(filtered_issues, order_label):
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
    return prompt

def call_ai(prompt):
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
    try:
        ia_resp = requests.post(api_url, headers=headers, json=payload, timeout=30)
        if ia_resp.ok:
            ia_json = ia_resp.json()
            ia_response = ia_json["choices"][0]["message"]["content"]
            if ia_response:
                ia_response = re.sub(r"^```json\s*|\s*```$", "", ia_response.strip(), flags=re.MULTILINE)
                try:
                    ia_response = json.loads(ia_response)
                except Exception:
                    pass
            return ia_response
        else:
            return f"Error: {ia_resp.status_code} - {ia_resp.text}"
    except Exception as e:
        return f"error calling IA: {str(e)}"