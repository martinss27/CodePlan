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
            f"You are a senior SCRUM MASTER, expert in agile task prioritization.\n"
            f"Analyze the tasks below and ORDER them by the criterion: '{order_label}'.\n"
            f"Create a preliminary and refined message to guide the user on what they need to know to make strategic decisions in JIRA. Follow this format:\n"
            f"1. An EXECUTIVE SUMMARY about the ordering logic and the strategic objective.\n"
            f"2. Highlighted blocks:\n"
            f"   - WHY THIS ORDER? (explain the rationale, give practical examples)\n"
            f"   - PRACTICAL IMPACT (what changes for the business and the user, from the perspective of how effective and strong this impact will be)\n"
            f"   - STRATEGIC RECOMMENDATIONS (with application examples and a brief explanation of the reasons for these recommendations)\n"
            f"   - RISKS OF NOT FOLLOWING THIS ORDER\n"
            f"   - NEXT STEPS CHECKLIST\n"
            f"Use clear, objective language, agile leadership tone, highlight in bullet points.\n"

            # each task prompt:
            f"For each task, include:\n"
            f"- Description (summarize to the first 50 characters of the original description and add '...' at the end, even if the description is shorter)\n"
            f"- Useful libraries (if backend, suggest for Python, JavaScript, and Java; if frontend, suggest for JavaScript, React, and Vue)\n"
            f"- Risk factors (bring 2 possible risk factors that may occur)\n"
            f"- Recommended strategy (be more thorough here, you can explain logically how the strategy should be applied, so it is functional regardless of the task or programming language)\n"
            f"- Time estimate\n"
            f"Respond with a JSON: {{ 'mensagem': <mensagem_geral>, 'tasks': [ ...tasks_ordenadas... ] }}\n\n"
            f"Tasks:\n"
    )
    else:
        prompt = (
            "You are a senior SCRUM MASTER, expert in agile task prioritization.\n"
            "Analyze the tasks below and ORDER them according to your experience, considering what is most strategic for the team.\n"
            "Create a preliminary and refined message to guide the user on what they need to know to make strategic decisions in JIRA. Follow this format:\n"
            "1. An EXECUTIVE SUMMARY about the ordering logic and the strategic objective.\n"
            "2. Highlighted blocks:\n"
            "   - WHY THIS ORDER? (explain the rationale, give practical examples)\n"
            "   - PRACTICAL IMPACT (what changes for the business and the user, from the perspective of how effective and strong this impact will be)\n"
            "   - STRATEGIC RECOMMENDATIONS (with application examples and a brief explanation of the reasons for these recommendations)\n"
            "   - RISKS OF NOT FOLLOWING THIS ORDER\n"
            "   - NEXT STEPS CHECKLIST\n"
            "Use clear, objective language, agile leadership tone, highlight in bullet points.\n"

            # each task prompt:
            "For each task, include:\n"
            "- Description (summarize to the first 50 characters of the original description and add '...' at the end, even if the description is shorter)\n"
            "- Useful libraries (if backend, suggest for Python, JavaScript, and Java; if frontend, suggest for JavaScript, React, and Vue)\n"
            "- Risk factors (bring 2 possible risk factors that may occur)\n"
            "- Recommended strategy (be more thorough here, you can explain logically how the strategy should be applied, so it is functional regardless of the task or programming language)\n"
            "- Time estimate\n"
            "Respond with a JSON: { 'mensagem': <mensagem_geral>, 'tasks': [ ...tasks_ordenadas... ] }\n\n"
            "Tasks:\n"
                    )


        # Add each issue to the prompt
    for issue in filtered_issues:
            prompt += (
                f"- ID: {issue['id']}\n"
                f"- Title: {issue['summary']}\n"
                f"Description: {extract_description(issue['description'])}\n"
                f"Status: {issue['status']}\n"
                f"Type: {issue['issuetype']}\n"
                f"Priority: {issue['priority']}\n"
                f"Assignee: {issue['assignee']}\n\n"
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