from django.urls import path
from .views import TrelloCallbackView, trello_login

urlpatterns = [
    path('login/', trello_login, name='trello_login'),
    path('callback/', TrelloCallbackView.as_view(), name='trello_callback'),
]