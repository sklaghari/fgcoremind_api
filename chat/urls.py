from django.urls import path
from . import views

urlpatterns = [
    # Conversation-specific endpoints
    path('conversation/<str:conversation_id>/messages', views.get_conversation_messages,
         name='get_conversation_messages'),
    path('conversation/<str:conversation_id>/messages', views.clear_conversation_messages,
         name='clear_conversation_messages'),

    # Agent-specific endpoints
    path('<str:agent_id>/send', views.send_message, name='send_message'),
    path('<str:agent_id>/history', views.get_chat_history, name='get_chat_history'),  # Legacy endpoint
    path('<str:agent_id>/conversations', views.get_recent_conversations, name='get_recent_conversations'),
    path('<str:agent_id>/new', views.create_new_conversation, name='create_new_conversation'),
]