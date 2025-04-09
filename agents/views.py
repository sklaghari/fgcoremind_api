from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from .models import Agent, AgentPermission
from .serializers import AgentSerializer, AgentDetailSerializer, AgentPermissionSerializer
from accounts.models import User  # Import User model


class AgentListCreateView(APIView):
    """
    API view to retrieve list of agents or create a new agent
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """Get all agents that the user has access to"""
        # Get agents owned by the user
        user_agents = Agent.objects.filter(owner=request.user)

        # Get agents the user has explicit permission for
        permitted_agents = Agent.objects.filter(
            permissions__user=request.user
        )

        # Get public agents
        public_agents = Agent.objects.filter(is_public=True)

        # Combine all agents and remove duplicates
        all_agents = user_agents | permitted_agents | public_agents

        # Remove duplicates
        all_agents = all_agents.distinct().order_by('-created_at')

        serializer = AgentSerializer(all_agents, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """Create a new agent"""
        serializer = AgentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AgentDetailView(APIView):
    """
    API view to retrieve, update or delete an agent instance
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, user):
        """Get agent object if the user has access to it"""
        try:
            agent = Agent.objects.get(pk=pk)

            # Check if the user owns this agent
            if agent.owner == user:
                return agent

            # Check if the user has explicit permission
            if AgentPermission.objects.filter(agent=agent, user=user).exists():
                return agent

            # Check if the agent is marked as public
            if agent.is_public:
                return agent

            # No access
            return None

        except Agent.DoesNotExist:
            return None

    def get(self, request, pk, format=None):
        """Get agent details"""
        agent = self.get_object(pk, request.user)
        if not agent:
            return Response({"detail": "Not found or no permission."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AgentDetailSerializer(agent)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """Update agent details (only owner)"""
        agent = Agent.objects.filter(pk=pk, owner=request.user).first()
        if not agent:
            return Response({"detail": "Not found or not authorized."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AgentDetailSerializer(agent, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk, format=None):
        """Partially update agent details (only owner)"""
        agent = Agent.objects.filter(pk=pk, owner=request.user).first()
        if not agent:
            return Response({"detail": "Not found or not authorized."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AgentDetailSerializer(agent, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """Delete an agent (only owner)"""
        agent = Agent.objects.filter(pk=pk, owner=request.user).first()
        if not agent:
            return Response({"detail": "Not found or not authorized."}, status=status.HTTP_404_NOT_FOUND)

        agent.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AgentPermissionView(APIView):
    """
    API view to manage permissions for an agent
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, agent_id, format=None):
        """Get all permissions for an agent (only owner can see)"""
        try:
            agent = Agent.objects.get(pk=agent_id, owner=request.user)
        except Agent.DoesNotExist:
            return Response({"detail": "Agent not found or you're not the owner."},
                            status=status.HTTP_404_NOT_FOUND)

        permissions = AgentPermission.objects.filter(agent=agent)
        serializer = AgentPermissionSerializer(permissions, many=True)
        return Response(serializer.data)

    def post(self, request, agent_id, format=None):
        print("Request data:", request.data)

        """Add a new permission for an agent (only owner can add)"""
        try:
            agent = Agent.objects.get(pk=agent_id, owner=request.user)
        except Agent.DoesNotExist:
            return Response({"detail": "Agent not found or you're not the owner."},
                            status=status.HTTP_404_NOT_FOUND)

        # Extract the email from the request data
        email = request.data.get('email')
        if not email:
            return Response({"detail": "Email is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Find the user with this email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": f"User with email {email} does not exist"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check if permission already exists
        if AgentPermission.objects.filter(agent=agent, user=user).exists():
            return Response({"detail": "This user already has permission for this agent."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Create the permission
        permission = AgentPermission.objects.create(agent=agent, user=user)
        serializer = AgentPermissionSerializer(permission)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AgentPermissionDetailView(APIView):
    """
    API view to retrieve, update or delete a permission
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, agent_id, permission_id, user):
        try:
            agent = Agent.objects.get(pk=agent_id, owner=user)
            return AgentPermission.objects.get(pk=permission_id, agent=agent)
        except (Agent.DoesNotExist, AgentPermission.DoesNotExist):
            return None

    def delete(self, request, agent_id, permission_id, format=None):
        """Delete a permission (only owner can delete)"""
        permission = self.get_object(agent_id, permission_id, request.user)
        if not permission:
            return Response({"detail": "Permission not found or not authorized."},
                            status=status.HTTP_404_NOT_FOUND)

        permission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
