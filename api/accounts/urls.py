"""
URL configuration para o app accounts (autenticação).
"""
from django.urls import path
from api.accounts.views import (
    RegisterView,
    LoginView,
    RefreshView,
    LogoutView,
    MeView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

urlpatterns = [
    # Registro e Login
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    
    # Usuário logado
    path('me/', MeView.as_view(), name='auth-me'),
    
    # Reset de senha
    path('password/reset/', PasswordResetRequestView.as_view(), name='auth-password-reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='auth-password-reset-confirm'),
]
