import os
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
        authed = OAuth1Session(
            API_KEY,
            client_secret=API_SECRET,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )
        
        boards_response = authed.get('https://api.trello.com/1/members/me/boards')
        boards = boards_response.json()
        result = []
        for board in boards:
            board_id = board.get('id')
            board_name = board.get('name')
            board_url = board.get('url')
            # boards lists
            lists_response = authed.get(f'https://api.trello.com/1/boards/{board_id}/lists')
            lists = lists_response.json()
            list_id_to_name = {lst['id']: lst['name'] for lst in lists}
            # cards
            cards_response = authed.get(f'https://api.trello.com/1/boards/{board_id}/cards')
            cards = cards_response.json()
            cards_info = [
                {
                    "id": card.get("id"),
                    "name": card.get("name"),
                    "url": card.get("url"),
                    "desc": card.get("desc"),
                    "board_name": board_name,
                    "list_id": card.get("idList"),
                    "list_name": list_id_to_name.get(card.get("idList"))
                }
                for card in cards
            ]
            result.append({
                "id": board_id,
                "name": board_name,
                "url": board_url,
                "cards": cards_info
            })
        return Response(result)