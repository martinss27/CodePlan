from django.urls import path
from .views import TrelloCallbackView, trello_login, TrelloAllBoardsView, TrelloBoardDetailsView

urlpatterns = [
    path('login/', trello_login, name='trello_login'),
    path('callback/', TrelloCallbackView.as_view(), name='trello_callback'),
    path('allboards/', TrelloAllBoardsView.as_view(), name='trello_all_boards'),
    path('board/<str:board_id>/details/', TrelloBoardDetailsView.as_view(), name='trello_board_details'),
]