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
    permission_classes = [IsAuthenticated]
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
        return redirect("http://127.0.0.1:8000/trello/allboards/")
    
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
        # Monta o prompt para a IA
        prompt = (
            "Você é um assistente sênior de engenharia de software. "
            "Analise as tarefas abaixo, organize-as de forma estratégica e explique sua lógica. "
            "Para cada tarefa, retorne: nome, descrição resumida (20 caracteres + ...), riscos, estratégia recomendada, estimativa de tempo e impacto.\n\n"
            "Formato de resposta: JSON com {'mensagem': <resumo>, 'tasks': [ ... ]}\n\n"
            "Tarefas:\n"
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