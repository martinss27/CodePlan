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
            f"You are a highly experienced software engineering advisor with senior Scrum Master knowledge. "
            f"Your goal is to support Scrum Masters and tech leads in making strategic and tactical decisions in JIRA.\n\n"

            f"Analyze the tasks below and ORDER them according to the following criterion: '{order_label}'.\n"
            f"Then, generate a strategic message summarizing the logic behind the ordering. Use the structure below:\n\n"

            f"1. EXECUTIVE SUMMARY (briefly explain the overall logic and strategic goal of the task ordering)\n"
            f"2. WHY THIS ORDER? (justify the prioritization with practical reasoning and examples)\n"
            f"3. PRACTICAL IMPACT (explain the expected impact for the business and user, clearly and realistically)\n"
            f"4. STRATEGIC RECOMMENDATIONS (give practical suggestions with short examples of how they should be applied)\n"
            f"5. RISKS OF NOT FOLLOWING THIS ORDER (technical and business risks)\n"
            f"6. NEXT STEPS CHECKLIST (a bullet list of 3–5 clear, actionable next steps)\n\n"

            f"Use objective language, direct but insightful, avoiding buzzwords. Write in clear bullet points when appropriate.\n\n"

            f"For each task, return the following:\n"
            f"- ID (as given)\n"
            f"- Title (as given)\n"
            f"- Description (summarize only the first 20 characters of the original description and add '...')\n"
            f"- Useful libraries & tools (for backend tasks, suggest Python, JavaScript, and Java tools; for frontend, suggest JavaScript, React, and Vue tools)\n"
            f"- Risk factors (provide two real technical or project risks specific to the task)\n"
            f"- Recommended strategy (respond with a **step-by-step implementation plan**, include best practices, name relevant tools or techniques, and **justify each step**. This is the most important section — be thorough. Think like a senior engineer mentoring someone on how to approach this specific task. Use numbered steps.)\n"
            f"- Time estimate (in hours or days)\n"
            f"- Time saved with AI support (in hours and include estimated percentage. Example: '2 hours (~25%)')\n"
            f"- Potential delay margin (%) (percentage that reflects estimated risk of delay due to unexpected issues or blockers)\n\n"

            f"Return everything in a JSON format:\n"
            f"{{ 'mensagem': <ordering_summary>, 'tasks': [ ...ordered_tasks... ] }}\n\n"

            f"Tasks:\n"
    )
    else:
        prompt = (
            "You are a highly experienced software engineering advisor with senior Scrum Master knowledge. "
            "Your goal is to support Scrum Masters and tech leads in making strategic and tactical decisions in JIRA.\n\n"

            "Analyze the tasks below and ORDER them according to what is most strategic for the team, based on your expertise.\n"
            "Then, generate a strategic message summarizing the logic behind the ordering. Use the structure below:\n\n"

            "1. EXECUTIVE SUMMARY (briefly explain the overall logic and strategic goal of the task ordering)\n"
            "2. WHY THIS ORDER? (justify the prioritization with practical reasoning and examples)\n"
            "3. PRACTICAL IMPACT (explain the expected impact for the business and user, clearly and realistically)\n"
            "4. STRATEGIC RECOMMENDATIONS (give practical suggestions with short examples of how they should be applied)\n"
            "5. RISKS OF NOT FOLLOWING THIS ORDER (technical and business risks)\n"
            "6. NEXT STEPS CHECKLIST (a bullet list of 3–5 clear, actionable next steps)\n\n"

            "Use objective language, direct but insightful, avoiding buzzwords. Write in clear bullet points when appropriate.\n\n"

            "For each task, return the following:\n"
            "- ID (as given)\n"
            "- Title (as given)\n"
            "- Description (summarize only the first 20 characters of the original description and add '...')\n"
            "- Useful libraries & tools (for backend tasks, suggest Python, JavaScript, and Java tools; for frontend, suggest JavaScript, React, and Vue tools)\n"
            "- Risk factors (provide two real technical or project risks specific to the task)\n"
            "- Recommended strategy (respond with a **step-by-step implementation plan**, include best practices, name relevant tools or techniques, and **justify each step**. This is the most important section — be thorough. Think like a senior engineer mentoring someone on how to approach this specific task. Use numbered steps.)\n"
            "- Time estimate (in hours or days)\n"
            "- Time saved with AI support (in hours and include estimated percentage. Example: '2 hours (~25%)')\n"
            "- Potential delay margin (%) (percentage that reflects estimated risk of delay due to unexpected issues or blockers)\n\n"

            "Return everything in a JSON format:\n"
            "{ 'mensagem': <ordering_summary>, 'tasks': [ ...ordered_tasks... ] }\n\n"

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