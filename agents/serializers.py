from rest_framework import serializers
from .models import Agent, AgentPermission
from accounts.models import User
from accounts.serializers import UserSerializer


class AgentSerializer(serializers.ModelSerializer):
    is_public = serializers.BooleanField(default=False)
    owner = UserSerializer()  # Include owner details

    class Meta:
        model = Agent
        fields = ['id', 'name', 'description', 'model', 'is_public', 'created_at', 'updated_at', 'owner']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AgentDetailSerializer(serializers.ModelSerializer):
    is_public = serializers.BooleanField(default=False)

    class Meta:
        model = Agent
        fields = ['id', 'name', 'description', 'instructions', 'model', 'is_public', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AgentPermissionSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True, required=True)
    user = UserSerializer(read_only=True)  # Make it explicitly read_only

    class Meta:
        model = AgentPermission
        fields = ['id', 'agent', 'user', 'email']
        read_only_fields = ['id', 'user']

    def create(self, validated_data):
        email = validated_data.pop('email', None)

        try:
            user = User.objects.get(email=email)
            validated_data['user'] = user
        except User.DoesNotExist:
            raise serializers.ValidationError(f"User with email {email} does not exist")

        return super().create(validated_data)
