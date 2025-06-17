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
        response = authed.get('https://api.trello.com/1/members/me/boards')
        return Response(response.json())