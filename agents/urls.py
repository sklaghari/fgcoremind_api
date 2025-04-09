# Step 5: Update URLs
# agents/urls.py (updated)
from django.urls import path
from .views import (
    AgentListCreateView,
    AgentDetailView,
    AgentPermissionView,
    AgentPermissionDetailView
)

urlpatterns = [
    path('', AgentListCreateView.as_view(), name='agent-list-create'),
    path('<int:pk>/', AgentDetailView.as_view(), name='agent-detail'),
    path('<int:agent_id>/permissions/', AgentPermissionView.as_view(), name='agent-permissions'),
    path('<int:agent_id>/permissions/<int:permission_id>/',
         AgentPermissionDetailView.as_view(), name='agent-permission-detail'),
]
