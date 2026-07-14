"""URLs for chat app."""
from django.urls import path

from .views import ConversationListView, MessageListView

urlpatterns = [
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<int:conv_id>/messages/', MessageListView.as_view(), name='message-list'),
]
