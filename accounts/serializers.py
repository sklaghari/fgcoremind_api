# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
import random


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'usage_limit', 'usage_count']
        read_only_fields = ['usage_count']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']

    def validate(self, data):
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'email': 'An account with this email already exists.'})

        if len(data['password']) < 8:
            raise serializers.ValidationError({'password': 'Password must be at least 8 characters'})

        return data

    def create(self, validated_data):
        username = validated_data['email'].split('@')[0]

        # Generate verification code
        verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            verification_code=verification_code,  # Add verification code during user creation
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['email'].split('@')[0], password=data['password'])

        if not user:
            raise serializers.ValidationError('Invalid email or password')

        if not user.email_verified:
            raise serializers.ValidationError('Email not verified. Please verify your email first.')

        return {'user': user}


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError('User with this email does not exist')

        if user.verification_code != data['code']:
            raise serializers.ValidationError('Invalid verification code')

        return data


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError('User with this email does not exist')

        if user.email_verified:
            raise serializers.ValidationError('Email is already verified')

        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError('User with this email does not exist')

        return data


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField()

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match'})

        return data


class PasswordResetCodeConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reset_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField()

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match'})

        # Validate reset code length
        if len(data['reset_code']) != 6 or not data['reset_code'].isdigit():
            raise serializers.ValidationError({'reset_code': 'Invalid reset code format'})

        return data
