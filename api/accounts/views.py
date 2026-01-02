"""
Views para o app accounts (autenticação e usuários).
"""
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from api.accounts.models import User, ProviderProfile, ClientProfile
from api.accounts.permissions import IsAdmin, IsOwnerOrAdmin
from api.accounts.serializers import (
    UserRegisterSerializer,
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserUpdateSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ProviderProfileSerializer,
    ProviderProfileUpdateSerializer,
    ClientProfileSerializer,
    ClientProfileUpdateSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
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


# =============================================================================
# ViewSets de Usuário e Perfis
# =============================================================================


@extend_schema(tags=['Usuários'])
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de usuários.
    
    Endpoints:
    - GET /users/ - Lista usuários (admin only)
    - POST /users/ - Cria usuário (admin only)
    - GET /users/{id}/ - Detalhes do usuário
    - PATCH /users/{id}/ - Atualiza usuário
    - DELETE /users/{id}/ - Deleta usuário (soft delete)
    - GET /users/{id}/profile/ - Retorna perfil completo
    
    Permissões:
    - Listagem: apenas admin
    - Detalhes/Atualização/Deleção: dono ou admin
    """
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'profile':
            return UserProfileSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['list', 'create']:
            # Apenas admin pode listar todos ou criar usuários
            return [IsAuthenticated(), IsAdmin()]
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'profile']:
            # Dono ou admin pode ver/editar/deletar
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filtra queryset baseado no usuário."""
        user = self.request.user
        if user.is_admin_user:
            return User.objects.all()
        # Usuário comum só vê a si mesmo
        return User.objects.filter(pk=user.pk)

    @extend_schema(
        summary='Lista usuários',
        description='Retorna lista de usuários. Apenas administradores têm acesso.',
        responses={
            200: OpenApiResponse(
                response=UserSerializer(many=True),
                description='Lista de usuários',
                examples=[
                    OpenApiExample(
                        'Sucesso',
                        value=[
                            {
                                'id': 1,
                                'email': 'user@example.com',
                                'first_name': 'João',
                                'last_name': 'Silva',
                                'user_type': 'CLIENT',
                                'is_active': True
                            }
                        ]
                    )
                ]
            ),
            403: OpenApiResponse(description='Acesso negado - apenas administradores'),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Detalhes do usuário',
        description='Retorna detalhes de um usuário específico.',
        responses={
            200: UserSerializer,
            404: OpenApiResponse(description='Usuário não encontrado'),
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Atualiza usuário',
        description='Atualiza dados de um usuário. Campos permitidos: first_name, last_name, phone.',
        request=UserUpdateSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description='Dados inválidos'),
            403: OpenApiResponse(description='Acesso negado'),
        },
        examples=[
            OpenApiExample(
                'Exemplo de requisição',
                value={
                    'first_name': 'João',
                    'last_name': 'Silva',
                    'phone': '11999998888'
                },
                request_only=True
            )
        ]
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary='Deleta usuário',
        description='Deleta um usuário (soft delete). O usuário é marcado como deletado mas não é removido do banco.',
        responses={
            204: OpenApiResponse(description='Usuário deletado com sucesso'),
            403: OpenApiResponse(description='Acesso negado'),
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        summary='Perfil completo do usuário',
        description='Retorna dados do usuário com perfis aninhados (cliente e/ou prestador).',
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description='Perfil completo',
                examples=[
                    OpenApiExample(
                        'Cliente',
                        value={
                            'id': 1,
                            'email': 'cliente@example.com',
                            'first_name': 'João',
                            'last_name': 'Silva',
                            'full_name': 'João Silva',
                            'phone': '11999998888',
                            'user_type': 'CLIENT',
                            'is_active': True,
                            'client_profile': {
                                'id': 1,
                                'address': 'Rua das Flores, 123',
                                'city': 'São Paulo',
                                'state': 'SP',
                                'zip_code': '01234-567'
                            },
                            'provider_profile': None
                        }
                    )
                ]
            ),
        }
    )
    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """Retorna o perfil completo do usuário."""
        user = self.get_object()
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)


@extend_schema(tags=['Perfis - Prestador'])
class ProviderProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de perfis de prestadores.
    
    Endpoints:
    - GET /profiles/providers/ - Lista prestadores
    - GET /profiles/providers/{id}/ - Detalhes do prestador
    - PATCH /profiles/providers/{id}/ - Atualiza perfil (dono ou admin)
    
    Listagem disponível para usuários autenticados (para busca de prestadores).
    """
    queryset = ProviderProfile.objects.select_related('user').all()
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return ProviderProfileUpdateSerializer
        return ProviderProfileSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            # Listagem e detalhes são públicos (para busca de prestadores)
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Apenas dono ou admin pode editar
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return [IsAuthenticated()]

    @extend_schema(
        summary='Lista prestadores',
        description='Retorna lista de prestadores de serviços. Disponível para todos os usuários autenticados.',
        responses={
            200: OpenApiResponse(
                response=ProviderProfileSerializer(many=True),
                description='Lista de prestadores',
                examples=[
                    OpenApiExample(
                        'Sucesso',
                        value=[
                            {
                                'id': 1,
                                'user': 2,
                                'user_name': 'Maria Silva',
                                'user_email': 'maria@example.com',
                                'bio': 'Desenvolvedora Full Stack',
                                'rating_avg': '4.50',
                                'total_reviews': 15,
                                'total_orders_completed': 20,
                                'is_verified': True
                            }
                        ]
                    )
                ]
            ),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Detalhes do prestador',
        description='Retorna detalhes de um prestador específico, incluindo avaliação e número de serviços.',
        responses={
            200: ProviderProfileSerializer,
            404: OpenApiResponse(description='Prestador não encontrado'),
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Atualiza perfil do prestador',
        description='Atualiza dados do perfil de prestador. Apenas o próprio prestador ou admin pode atualizar.',
        request=ProviderProfileUpdateSerializer,
        responses={
            200: ProviderProfileSerializer,
            400: OpenApiResponse(description='Dados inválidos'),
            403: OpenApiResponse(description='Acesso negado'),
        },
        examples=[
            OpenApiExample(
                'Atualizar bio',
                value={'bio': 'Nova descrição do meu perfil profissional'},
                request_only=True
            )
        ]
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


@extend_schema(tags=['Perfis - Cliente'])
class ClientProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de perfis de clientes.
    
    Endpoints:
    - GET /profiles/clients/ - Lista clientes (admin only)
    - GET /profiles/clients/{id}/ - Detalhes do cliente
    - PATCH /profiles/clients/{id}/ - Atualiza perfil (dono ou admin)
    
    Listagem restrita a admin (dados sensíveis de clientes).
    """
    queryset = ClientProfile.objects.select_related('user').all()
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return ClientProfileUpdateSerializer
        return ClientProfileSerializer

    def get_permissions(self):
        if self.action == 'list':
            # Apenas admin pode listar todos os clientes
            return [IsAuthenticated(), IsAdmin()]
        elif self.action == 'retrieve':
            # Dono ou admin pode ver detalhes
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Apenas dono ou admin pode editar
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filtra queryset baseado no usuário."""
        user = self.request.user
        if user.is_admin_user:
            return ClientProfile.objects.select_related('user').all()
        # Usuário comum só vê seu próprio perfil
        return ClientProfile.objects.select_related('user').filter(user=user)

    @extend_schema(
        summary='Lista clientes',
        description='Retorna lista de clientes. Apenas administradores têm acesso.',
        responses={
            200: OpenApiResponse(
                response=ClientProfileSerializer(many=True),
                description='Lista de clientes',
                examples=[
                    OpenApiExample(
                        'Sucesso',
                        value=[
                            {
                                'id': 1,
                                'user': 3,
                                'user_name': 'João Silva',
                                'user_email': 'joao@example.com',
                                'address': 'Rua das Flores, 123',
                                'city': 'São Paulo',
                                'state': 'SP',
                                'zip_code': '01234-567'
                            }
                        ]
                    )
                ]
            ),
            403: OpenApiResponse(description='Acesso negado - apenas administradores'),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Detalhes do cliente',
        description='Retorna detalhes de um cliente específico. Apenas o próprio cliente ou admin.',
        responses={
            200: ClientProfileSerializer,
            404: OpenApiResponse(description='Cliente não encontrado'),
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Atualiza perfil do cliente',
        description='Atualiza dados do perfil de cliente. Apenas o próprio cliente ou admin pode atualizar.',
        request=ClientProfileUpdateSerializer,
        responses={
            200: ClientProfileSerializer,
            400: OpenApiResponse(description='Dados inválidos'),
            403: OpenApiResponse(description='Acesso negado'),
        },
        examples=[
            OpenApiExample(
                'Atualizar endereço',
                value={
                    'address': 'Av. Paulista, 1000',
                    'city': 'São Paulo',
                    'state': 'SP',
                    'zip_code': '01310100'
                },
                request_only=True
            )
        ]
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
