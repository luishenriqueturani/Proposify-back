"""
Permissões customizadas para verificação de tipo de usuário.

Este módulo centraliza as permissões baseadas em UserType para reutilização
em toda a aplicação.
"""
from rest_framework import permissions
from api.accounts.enums import UserType


class IsClient(permissions.BasePermission):
    """
    Permissão que verifica se o usuário é um cliente.
    
    Apenas usuários autenticados com user_type='CLIENT' podem acessar.
    """
    message = 'Apenas clientes podem acessar este recurso.'

    def has_permission(self, request, view):
        """
        Verifica se o usuário tem permissão de cliente.
        
        Args:
            request: Objeto de requisição
            view: View que está sendo acessada
            
        Returns:
            bool: True se o usuário é cliente, False caso contrário
        """
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.user_type == UserType.CLIENT.value  # type: ignore


class IsProvider(permissions.BasePermission):
    """
    Permissão que verifica se o usuário é um prestador de serviços.
    
    Apenas usuários autenticados com user_type='PROVIDER' podem acessar.
    """
    message = 'Apenas prestadores podem acessar este recurso.'

    def has_permission(self, request, view):
        """
        Verifica se o usuário tem permissão de prestador.
        
        Args:
            request: Objeto de requisição
            view: View que está sendo acessada
            
        Returns:
            bool: True se o usuário é prestador, False caso contrário
        """
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.user_type == UserType.PROVIDER.value  # type: ignore


class IsAdmin(permissions.BasePermission):
    """
    Permissão que verifica se o usuário é um administrador.
    
    Apenas usuários com user_type='ADMIN', is_staff=True ou is_superuser=True
    podem acessar.
    """
    message = 'Apenas administradores podem acessar este recurso.'

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

        # Verifica se é admin pelo tipo de usuário ou pelo flag is_staff/is_superuser
        return (
            request.user.user_type == UserType.ADMIN.value or  # type: ignore
            request.user.is_staff or  # type: ignore
            request.user.is_superuser  # type: ignore
        )


class IsClientOrProvider(permissions.BasePermission):
    """
    Permissão que verifica se o usuário é cliente OU prestador.
    
    Útil para endpoints que ambos os tipos podem acessar, mas não admins.
    """
    message = 'Apenas clientes ou prestadores podem acessar este recurso.'

    def has_permission(self, request, view):
        """
        Verifica se o usuário é cliente ou prestador.
        
        Args:
            request: Objeto de requisição
            view: View que está sendo acessada
            
        Returns:
            bool: True se o usuário é cliente ou prestador, False caso contrário
        """
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.user_type in [  # type: ignore
            UserType.CLIENT.value,
            UserType.PROVIDER.value,
        ]


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão que verifica se o usuário é o dono do objeto ou um admin.
    
    Funciona com:
    - Objetos User (verifica se obj == request.user)
    - Objetos com campo 'user' (ex: Profile)
    - Objetos com campo 'client' ou 'provider'
    - Objetos com método 'get_owner()'
    """
    message = 'Você não tem permissão para acessar este recurso.'

    def has_object_permission(self, request, view, obj):
        """
        Verifica se o usuário é o dono do objeto ou um administrador.
        
        Args:
            request: Objeto de requisição
            view: View que está sendo acessada
            obj: Objeto sendo acessado
            
        Returns:
            bool: True se o usuário é o dono ou admin, False caso contrário
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Verifica se é admin
        if (request.user.user_type == UserType.ADMIN.value or  # type: ignore
                request.user.is_staff or request.user.is_superuser):  # type: ignore
            return True

        # Se o objeto é o próprio usuário (para UserViewSet)
        if obj == request.user:
            return True

        # Verifica se é o dono via campo 'user'
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'get_owner'):
            return obj.get_owner() == request.user
        elif hasattr(obj, 'client'):
            return obj.client == request.user
        elif hasattr(obj, 'provider'):
            return obj.provider == request.user

        return False
