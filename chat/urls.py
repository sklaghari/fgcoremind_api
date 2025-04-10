from django.urls import path
from . import views

urlpatterns = [
    # Conversation endpoints
    path('send', views.send_message, name='send_message'),
    path('conversations', views.get_recent_conversations, name='get_recent_conversations'),
    path('new', views.create_new_conversation, name='create_new_conversation'),
    path('conversation/<str:conversation_id>/messages', views.get_conversation_messages, name='get_conversation_messages'),
    path('conversation/<str:conversation_id>/clear', views.clear_conversation_messages, name='clear_conversation_messages'),
]