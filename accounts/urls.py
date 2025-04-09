# accounts/urls.py
from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    EmailVerificationView,
    ResendVerificationView,
    PasswordResetRequestView,
    PasswordResetConfirmView
)

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('reset-password/', PasswordResetConfirmView.as_view(), name='reset-password'),
]
