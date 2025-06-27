import os

from apps.jira.services import call_ai
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import redirect
from requests_oauthlib import OAuth1Session
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

REQUEST_TOKEN_URL = 'https://trello.com/1/OAuthGetRequestToken'
AUTHORIZE_URL = 'https://trello.com/1/OAuthAuthorizeToken'
ACCESS_TOKEN_URL = 'https://trello.com/1/OAuthGetAccessToken'
CALLBACK_URI = 'http://127.0.0.1:8000/trello/callback'

def trello_login(request):
    oauth = OAuth1Session(
        API_KEY,
        client_secret=API_SECRET,
        callback_uri=CALLBACK_URI,
    )
    fetch_response = oauth.fetch_request_token(REQUEST_TOKEN_URL)
    request.session['resource_owner_key'] = fetch_response.get('oauth_token')
    request.session['resource_owner_secret'] = fetch_response.get('oauth_token_secret')
    authorization_url = oauth.authorization_url(AUTHORIZE_URL)
    return redirect(authorization_url)

class TrelloCallbackView(APIView):
#    permission_classes = [IsAuthenticated]
    def get(self, request):
        oauth_verifier = request.GET.get('oauth_verifier')
        resource_owner_key = request.session.get('resource_owner_key')
        resource_owner_secret = request.session.get('resource_owner_secret')
        if not (resource_owner_key and resource_owner_secret and oauth_verifier):
            return Response({"error": "invalid session or params"}, status=400)
        oauth = OAuth1Session(
            API_KEY,
            client_secret=API_SECRET,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret,
            verifier=oauth_verifier,
        )
        oauth_tokens = oauth.fetch_access_token(ACCESS_TOKEN_URL)
        access_token = oauth_tokens['oauth_token']
        access_token_secret = oauth_tokens['oauth_token_secret']

        request.session['access_token'] = access_token
        request.session['access_token_secret'] = access_token_secret

        request.session.pop('resource_owner_key', None)
        request.session.pop('resource_owner_secret', None)
        return redirect("http://127.0.0.1:8000/trello/board/")
    
class TrelloAllBoardsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        access_token = request.session.get('access_token')
        access_token_secret = request.session.get('access_token_secret')
        if not (access_token and access_token_secret):
            return Response({"error": "tokens not found, try again"}, status=401)
        authed = OAuth1Session(
            API_KEY,
            client_secret=API_SECRET,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )
        boards_response = authed.get('https://api.trello.com/1/members/me/boards')
        boards = boards_response.json()
        result = [
            {
                "id": board.get("id"),
                "name": board.get("name"),
                "url": board.get("url")
            }
            for board in boards
        ]
        return Response(result)
    

class TrelloBoardDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, board_id):
        access_token = request.session.get('access_token')
        access_token_secret = request.session.get('access_token_secret')
        if not (access_token and access_token_secret):
            return Response({"error": "tokens not found, try again"}, status=401)
        authed = OAuth1Session(
            API_KEY,
            client_secret=API_SECRET,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )
        board_response = authed.get(f'https://api.trello.com/1/boards/{board_id}')
        if board_response.status_code != 200:
            return Response({"error": "Failed to fetch board info", "details": board_response.text}, status=board_response.status_code)
        board_data = board_response.json()
        board_name = board_data.get("name", "")
        # Get lists
        lists_response = authed.get(f'https://api.trello.com/1/boards/{board_id}/lists')
        if lists_response.status_code != 200:
            return Response({"error": "Failed to fetch lists", "details": lists_response.text}, status=lists_response.status_code)
        lists = lists_response.json()
        # Get cards
        cards_response = authed.get(f'https://api.trello.com/1/boards/{board_id}/cards')
        if cards_response.status_code != 200:
            return Response({"error": "Failed to fetch cards", "details": cards_response.text}, status=cards_response.status_code)
        cards = cards_response.json()
        # Organize cards by list
        list_id_to_cards = {lst['id']: [] for lst in lists}
        for card in cards:
            list_id = card.get('idList')
            if list_id in list_id_to_cards:
                list_id_to_cards[list_id].append({
                    "name": card.get("name"),
                    "desc": card.get("desc"),
                    "board_name": board_name,
                })
        result = []
        for lst in lists:
            result.append({
                "id": lst.get("id"),
                "name": lst.get("name"),
                "cards": list_id_to_cards[lst['id']]
            })
        return Response(result)
    
class TrelloBoardAIAssistantView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, board_id):
        access_token = request.session.get('access_token')
        access_token_secret = request.session.get('access_token_secret')
        if not (access_token and access_token_secret):
            return Response({"error": "tokens not found"}, status=401)
        authed = OAuth1Session(
            API_KEY,
            client_secret=API_SECRET,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )

        board_response = authed.get(f'https://api.trello.com/1/boards/{board_id}')
        if board_response.status_code != 200:
            return Response({"error": "Failed to fetch board info", "details": board_response.text}, status=board_response.status_code)
        board_data = board_response.json()
        board_name = board_data.get("name", "")
        lists_response = authed.get(f'https://api.trello.com/1/boards/{board_id}/lists')
        if lists_response.status_code != 200:
            return Response({"error": "Failed to fetch lists", "details": lists_response.text}, status=lists_response.status_code)
        lists = lists_response.json()
        cards_response = authed.get(f'https://api.trello.com/1/boards/{board_id}/cards')
        if cards_response.status_code != 200:
            return Response({"error": "Failed to fetch cards", "details": cards_response.text}, status=cards_response.status_code)
        cards = cards_response.json()
        # Organiza cards por lista
        list_id_to_cards = {lst['id']: [] for lst in lists}
        for card in cards:
            list_id = card.get('idList')
            if list_id in list_id_to_cards:
                list_id_to_cards[list_id].append({
                    "name": card.get("name"),
                    "desc": card.get("desc"),
                    "board_name": board_name,
                })
        trello_data = []
        for lst in lists:
            trello_data.append({
                "id": lst.get("id"),
                "name": lst.get("name"),
                "cards": list_id_to_cards[lst['id']]
            })

        def get_order_label(user_input):
            valid_labels = {
                "urgencia": "urgencia da tarefa",
                "impacto": "impacto no negócio",
                "facilidade": "facilidade de implementação",
                "complexidade": "complexidade técnica",
                "dependencias": "dependências técnicas",
            }
            return valid_labels.get(user_input.lower()) if user_input else None
        
        order_by = request.GET.get("order_by", "")
        order_label = get_order_label(order_by)
        
        # Monta o prompt para a 
        if order_label:
            prompt = (
            "Você é um assistente sênior de engenharia de software, com experiência prática em desenvolvimento frontend e backend, "
            "além de domínio das melhores práticas de metodologias ágeis como o Scrum.\n\n"
            f"Reorganize as tarefas abaixo de acordo com o critério: '{order_label}'.\n"
            "Explique a lógica da priorização e siga as instruções abaixo:\n\n"
            "1. Reorganize as tarefas dentro de suas respectivas listas (ex: Backlog, To Do, In Progress), considerando o critério acima e também:\n"
            "- Valor de negócio\n"
            "- Dependências entre tarefas\n"
            "- Princípios do Scrum e melhores práticas ágeis\n\n"
            "2. Sugerir movimentações de tarefas entre listas, quando apropriado, e sempre com uma justificativa clara. "
            "Exemplo: mover do Backlog para To Do se a task já estiver madura e desbloqueada. Não crie novas listas.\n\n"
            "3. Para tarefas técnicas, ofereça dicas práticas e contextuais com base no conteúdo da tarefa:\n"
            "- Bibliotecas ou ferramentas úteis (ex: Django REST, Express, FastAPI, React, Vue, Axios)\n"
            "- Linguagens e frameworks mais adequados (ex: Python, JavaScript, TypeScript, etc.)\n"
            "- Boas práticas e sugestões de implementação rápidas (ex: como estruturar endpoints, validar formulários, usar hooks, aplicar SOLID)\n"
            "- Use o conteúdo da descrição ou o nome da tarefa para inferir a stack envolvida. NÃO limite suas dicas a apenas uma tecnologia (como Django). "
            "Adapte conforme o contexto técnico identificado.\n\n"
            "4. Justifique suas decisões de reorganização com explicações objetivas. Use uma linguagem clara e direta para Product Owners e Scrum Masters, e técnica para desenvolvedores.\n\n"
            "Formato de resposta:\n"
            "{\n"
            "  'mensagem': <resumo geral das decisões e lógica usada>,\n"
            "  'tasks_por_lista': {\n"
            "    'nome_da_lista': [\n"
            "      {\n"
            "        'nome': <título do card>,\n"
            "        'resumo': <resumo curto da descrição>,\n"
            "        'riscos': <possíveis riscos>,\n"
            "        'estrategia': <como lidar com a tarefa>,\n"
            "        'estimativa_horas': <tempo estimado>,\n"
            "        'impacto': <valor estratégico ou técnico da tarefa>,\n"
            "        'dicas_tecnicas': <orientações práticas, se aplicável>\n"
            "      }\n"
            "    ]\n"
            "  }\n"
            "}\n\n"
            "Formate o JSON com indentação e quebras de linha para facilitar a leitura humana.\n"
            "Não escreva nenhuma explicação fora do JSON. A resposta deve ser apenas o JSON formatado e indentado.\n\n"
            "Agora, avalie e reorganize as seguintes tarefas:\n"
            )
        else:
            prompt = (
                "Você é um assistente sênior de engenharia de software, com experiência prática em desenvolvimento frontend e backend, "
                "além de domínio das melhores práticas de metodologias ágeis como o Scrum.\n\n"
                "Reorganize as tarefas abaixo de acordo com o que for mais estratégico para o time, usando sua experiência.\n"
                "Explique a lógica da priorização e siga as instruções abaixo:\n\n"
                "1. Reorganize as tarefas dentro de suas respectivas listas (ex: Backlog, To Do, In Progress), considerando:\n"
                "- Urgência\n"
                "- Valor de negócio\n"
                "- Dependências entre tarefas\n"
                "- Princípios do Scrum e melhores práticas ágeis\n\n"
                "2. Sugerir movimentações de tarefas entre listas, quando apropriado, e sempre com uma justificativa clara. "
                "Exemplo: mover do Backlog para To Do se a task já estiver madura e desbloqueada. Não crie novas listas.\n\n"
                "3. Para tarefas técnicas, ofereça dicas práticas e contextuais com base no conteúdo da tarefa:\n"
                "- Bibliotecas ou ferramentas úteis (ex: Django REST, Express, FastAPI, React, Vue, Axios)\n"
                "- Linguagens e frameworks mais adequados (ex: Python, JavaScript, TypeScript, etc.)\n"
                "- Boas práticas e sugestões de implementação rápidas (ex: como estruturar endpoints, validar formulários, usar hooks, aplicar SOLID)\n"
                "- Use o conteúdo da descrição ou o nome da tarefa para inferir a stack envolvida. NÃO limite suas dicas a apenas uma tecnologia (como Django). "
                "Adapte conforme o contexto técnico identificado.\n\n"
                "4. Justifique suas decisões de reorganização com explicações objetivas. Use uma linguagem clara e direta para Product Owners e Scrum Masters, e técnica para desenvolvedores.\n\n"
                "Formato de resposta:\n"
                "{\n"
                "  'mensagem': <resumo geral das decisões e lógica usada>,\n"
                "  'tasks_por_lista': {\n"
                "    'nome_da_lista': [\n"
                "      {\n"
                "        'nome': <título do card>,\n"
                "        'resumo': <resumo curto da descrição>,\n"
                "        'riscos': <possíveis riscos>,\n"
                "        'estrategia': <como lidar com a tarefa>,\n"
                "        'estimativa_horas': <tempo estimado>,\n"
                "        'impacto': <valor estratégico ou técnico da tarefa>,\n"
                "        'dicas_tecnicas': <orientações práticas, se aplicável>\n"
                "      }\n"
                "    ]\n"
                "  }\n"
                "}\n\n"
                "Formate o JSON com indentação e quebras de linha para facilitar a leitura humana.\n"
                "Não escreva nenhuma explicação fora do JSON. A resposta deve ser apenas o JSON formatado e indentado.\n\n"
                "Agora, avalie e reorganize as seguintes tarefas:\n"
                )


        for lista in trello_data:
            for card in lista.get("cards", []):
                prompt += (
                    f"- Nome: {card['name']}\n"
                    f"Descrição: {card['desc']}\n"
                    f"Lista: {lista['name']}\n"
                    f"Quadro: {card['board_name']}\n\n"
                )
        ia_response = call_ai(prompt)
        return Response({"ia_response":ia_response})