"""
Views para o app accounts (autenticação e usuários).
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from api.accounts.serializers import (
    UserRegisterSerializer,
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserUpdateSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)


@extend_schema(
    tags=['Autenticação'],
    summary='Registrar novo usuário',
    description='''
Cria um novo usuário na plataforma.

**Tipos de usuário disponíveis:**
- `CLIENT` - Cliente (padrão)
- `PROVIDER` - Prestador de serviços

O perfil correspondente (ClientProfile ou ProviderProfile) é criado automaticamente.
    ''',
    responses={
        201: OpenApiResponse(
            description='Usuário criado com sucesso',
            examples=[
                OpenApiExample(
                    'Sucesso',
                    value={
                        'message': 'Usuário criado com sucesso.',
                        'user': {
                            'id': 1,
                            'email': 'user@example.com',
                            'first_name': 'João',
                            'last_name': 'Silva',
                            'user_type': 'CLIENT'
                        }
                    }
                ),
            ],
        ),
        400: OpenApiResponse(description='Dados inválidos'),
    },
)
class RegisterView(CreateAPIView):
    """
    View para registro de novos usuários.
    
    POST /auth/register/
    """
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'message': 'Usuário criado com sucesso.',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type,
            }
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Autenticação'],
    summary='Login',
    description='''
Autentica o usuário e retorna os tokens JWT.

**Tokens retornados:**
- `access` - Token de acesso (válido por 15 minutos)
- `refresh` - Token de refresh (válido por 7 dias)

Use o token de acesso no header `Authorization: Bearer <access_token>`.
    ''',
    responses={
        200: OpenApiResponse(
            description='Login bem-sucedido',
            examples=[
                OpenApiExample(
                    'Sucesso',
                    value={
                        'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'user': {
                            'id': 1,
                            'email': 'user@example.com',
                            'first_name': 'João',
                            'last_name': 'Silva',
                            'user_type': 'CLIENT',
                            'is_active': True
                        }
                    }
                ),
            ],
        ),
        401: OpenApiResponse(description='Credenciais inválidas'),
    },
)
class LoginView(TokenObtainPairView):
    """
    View para login de usuários.
    
    POST /auth/login/
    """
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    tags=['Autenticação'],
    summary='Renovar token',
    description='''
Renova o token de acesso usando o token de refresh.

O token de refresh antigo é invalidado e um novo é retornado (rotação de tokens).
    ''',
    responses={
        200: OpenApiResponse(description='Token renovado com sucesso'),
        401: OpenApiResponse(description='Token de refresh inválido ou expirado'),
    },
)
class RefreshView(TokenRefreshView):
    """
    View para renovar token de acesso.
    
    POST /auth/refresh/
    """
    pass


@extend_schema(
    tags=['Autenticação'],
    summary='Logout',
    description='''
Invalida o token de refresh, efetivamente fazendo logout do usuário.

O token de refresh é adicionado à blacklist e não pode mais ser usado.
    ''',
    responses={
        200: OpenApiResponse(
            description='Logout bem-sucedido',
            examples=[
                OpenApiExample(
                    'Sucesso',
                    value={'message': 'Logout realizado com sucesso.'}
                ),
            ],
        ),
        400: OpenApiResponse(description='Token de refresh não fornecido'),
    },
)
class LogoutView(APIView):
    """
    View para logout de usuários.
    
    POST /auth/logout/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({
                    'error': 'Token de refresh não fornecido.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'message': 'Logout realizado com sucesso.'
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                'error': 'Token inválido ou já invalidado.'
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Autenticação'],
    summary='Dados do usuário logado',
    description='Retorna os dados do usuário autenticado.',
    responses={
        200: UserSerializer,
        401: OpenApiResponse(description='Não autenticado'),
    },
)
class MeView(RetrieveUpdateAPIView):
    """
    View para obter e atualizar dados do usuário logado.
    
    GET /auth/me/ - Retorna dados do usuário
    PATCH /auth/me/ - Atualiza dados do usuário
    """
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PATCH', 'PUT']:
            return UserUpdateSerializer
        return UserSerializer

    @extend_schema(
        tags=['Autenticação'],
        summary='Atualizar dados do usuário',
        description='Atualiza os dados do usuário autenticado.',
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description='Dados inválidos'),
            401: OpenApiResponse(description='Não autenticado'),
        },
    )
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = UserUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Retorna os dados completos do usuário
        return Response(UserSerializer(instance).data)


@extend_schema(
    tags=['Autenticação'],
    summary='Solicitar reset de senha',
    description='''
Solicita o reset de senha para o email informado.

Se o email existir no sistema, um email com instruções será enviado.
Por segurança, sempre retorna sucesso mesmo se o email não existir.
    ''',
    responses={
        200: OpenApiResponse(
            description='Solicitação processada',
            examples=[
                OpenApiExample(
                    'Sucesso',
                    value={'message': 'Se o email existir, você receberá instruções para reset de senha.'}
                ),
            ],
        ),
    },
)
class PasswordResetRequestView(APIView):
    """
    View para solicitar reset de senha.
    
    POST /auth/password/reset/
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.get_user()
        if user:
            uid, token = serializer.generate_reset_token(user)
            # TODO: Enviar email com link de reset
            # Por enquanto, apenas loga o token (para desenvolvimento)
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Password reset token for {user.email}: uid={uid}, token={token}")
        
        # Sempre retorna sucesso por segurança
        return Response({
            'message': 'Se o email existir, você receberá instruções para reset de senha.'
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Autenticação'],
    summary='Confirmar reset de senha',
    description='''
Confirma o reset de senha usando o UID e token recebidos por email.

Após a confirmação, a nova senha é aplicada e o usuário pode fazer login.
    ''',
    responses={
        200: OpenApiResponse(
            description='Senha alterada com sucesso',
            examples=[
                OpenApiExample(
                    'Sucesso',
                    value={'message': 'Senha alterada com sucesso.'}
                ),
            ],
        ),
        400: OpenApiResponse(description='Token inválido ou expirado'),
    },
)
class PasswordResetConfirmView(APIView):
    """
    View para confirmar reset de senha.
    
    POST /auth/password/reset/confirm/
    """
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Senha alterada com sucesso.'
        }, status=status.HTTP_200_OK)
