# accounts/views.py
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
import random

from .models import User
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    EmailVerificationSerializer,
    ResendVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetCodeConfirmSerializer
)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Explicitly generate verification code if not already set
            if not user.verification_code:
                verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                user.verification_code = verification_code
                user.save()

            # Send verification email
            self.send_verification_email(user)

            return Response({
                'message': 'Registration successful. Please check your email for verification code.'
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def send_verification_email(self, user):
        subject = 'Verify your CoreMind account'
        message = f'Your verification code is: {user.verification_code}'
        email_from = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]

        try:
            send_mail(subject, message, email_from, recipient_list)
        except Exception as e:
            print(f"Email sending failed: {str(e)}")

class EmailVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            user.email_verified = True
            user.verification_code = None
            user.save()

            return Response({
                'message': 'Email verified successfully. You can now log in.'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)

            # Generate new verification code
            new_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            user.verification_code = new_code
            user.save()

            # Send verification email
            subject = 'Verify your CoreMind account'
            message = f'Your new verification code is: {new_code}'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [user.email]
            send_mail(subject, message, email_from, recipient_list)

            return Response({
                'message': 'New verification code sent to your email.'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)

            return Response({
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)

            # Generate 6-digit reset code
            reset_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

            # Store reset code with the user
            user.password_reset_code = reset_code
            user.save()

            # Send reset code via email
            subject = 'CoreMind Password Reset Code'
            message = f'Your password reset code is: {reset_code}'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [user.email]
            send_mail(subject, message, email_from, recipient_list)

            return Response({
                'message': 'Password reset code sent to your email.',
                'email': email  # Send email back to use in next screen
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetCodeConfirmSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            reset_code = serializer.validated_data['reset_code']
            new_password = serializer.validated_data['new_password']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)

            # Check if reset code matches
            if user.password_reset_code != reset_code:
                return Response({'error': 'Invalid reset code'}, status=status.HTTP_400_BAD_REQUEST)

            # Reset password and clear reset code
            user.set_password(new_password)
            user.password_reset_code = None
            user.save()

            return Response({
                'message': 'Password reset successful. You can now log in with your new password.'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
