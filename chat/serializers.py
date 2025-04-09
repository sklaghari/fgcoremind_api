from rest_framework import serializers
from .models import Conversation, Message,MessageFeedback


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'created_at']
        read_only_fields = ['created_at']


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    agent_name = serializers.CharField(source='agent.name', read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'agent', 'agent_name', 'created_at', 'updated_at', 'messages']
        read_only_fields = ['user', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class MessageInputSerializer(serializers.Serializer):
    content = serializers.CharField(required=True)


class MessageFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageFeedback
        fields = ['id', 'feedback_type', 'comment', 'created_at']
        read_only_fields = ['created_at']