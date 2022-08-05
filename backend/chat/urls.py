from django.urls import path

from chat.views import ChatsView

urlpatterns = [
    path('all/', ChatsView.as_view(), name='chats'),
    path('all/<int:peer_id>/', ChatsView.as_view(), name='chats'),
]
