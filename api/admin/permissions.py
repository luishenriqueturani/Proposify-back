"""
Permissões customizadas para o app admin.
"""
from rest_framework import permissions
from api.accounts.enums import UserType


class IsAdmin(permissions.BasePermission):
    """
    Permissão que verifica se o usuário é um administrador.
    Apenas usuários com user_type='ADMIN' ou is_staff=True podem acessar.
    """
    def has_permission(self, request, view):
        """
        Verifica se o usuário tem permissão de administrador.
        Args:
            request: Objeto de requisição
            view: View que está sendo acessada
        Returns:
            bool: True se o usuário é admin, False caso contrário
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Verifica se é admin pelo tipo de usuário ou pelo flag is_staff
        return (
            request.user.user_type == UserType.ADMIN.value or  # type: ignore[attr-defined]
            request.user.is_staff or  # type: ignore[attr-defined]
            request.user.is_superuser  # type: ignore[attr-defined]
        )
