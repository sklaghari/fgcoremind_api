from django.db import models
from accounts.models import User


class Agent(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    instructions = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agents')
    model = models.CharField(max_length=50, null=True, blank=True)
    is_public = models.BooleanField(default=False)  # Flag to mark public agents
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class AgentPermission(models.Model):
    """
    Model to manage access permissions for agents
    """
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='permissions',null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agent_permissions',null=True, blank=True)

    class Meta:
        unique_together = [['agent', 'user']]

    def __str__(self):
        return f"{self.agent.name} - {self.user.email}"