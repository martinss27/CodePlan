from django.urls import path
from .views import TrelloCallbackView, trello_login, TrelloAllBoardsView, TrelloBoardDetailsView, TrelloBoardAIAssistantView

urlpatterns = [
    path('login/', trello_login, name='trello_login'),
    path('callback/', TrelloCallbackView.as_view(), name='trello_callback'),
    path('board/', TrelloAllBoardsView.as_view(), name='trello_all_boards'),
    path('board/<str:board_id>/details', TrelloBoardDetailsView.as_view(), name='trello_board_details'),
    path('board/<str:board_id>/ai', TrelloBoardAIAssistantView.as_view(), name='trello_board_ai_response'),
]