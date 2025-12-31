"""
ViewSet para gerenciamento de usuários pelo administrador.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes

from api.admin.permissions import IsAdmin
from api.accounts.models import User


@extend_schema_view(
    list=extend_schema(
        tags=['Admin - Usuários'],
        summary='Listar usuários',
        description='Retorna lista paginada de todos os usuários do sistema.',
        parameters=[
            OpenApiParameter('user_type', OpenApiTypes.STR, description='Filtrar por tipo (CLIENT, PROVIDER, ADMIN)'),
            OpenApiParameter('is_active', OpenApiTypes.BOOL, description='Filtrar por status ativo'),
        ],
    ),
    retrieve=extend_schema(
        tags=['Admin - Usuários'],
        summary='Detalhes do usuário',
        description='Retorna informações detalhadas de um usuário específico.',
    ),
    update=extend_schema(
        tags=['Admin - Usuários'],
        summary='Atualizar usuário',
        description='Atualiza informações de um usuário.',
    ),
    partial_update=extend_schema(
        tags=['Admin - Usuários'],
        summary='Atualizar usuário (parcial)',
        description='Atualiza parcialmente informações de um usuário.',
    ),
    suspend=extend_schema(
        tags=['Admin - Usuários'],
        summary='Suspender usuário',
        description='Desativa um usuário (is_active=False). O usuário não poderá fazer login.',
        responses={
            200: OpenApiResponse(
                description='Usuário suspenso com sucesso',
                examples=[
                    OpenApiExample(
                        'Sucesso',
                        value={'message': 'Usuário user@email.com foi suspenso com sucesso.', 'user_id': 1, 'is_active': False}
                    ),
                ],
            ),
        },
    ),
    activate=extend_schema(
        tags=['Admin - Usuários'],
        summary='Ativar usuário',
        description='Reativa um usuário suspenso (is_active=True).',
        responses={
            200: OpenApiResponse(
                description='Usuário ativado com sucesso',
                examples=[
                    OpenApiExample(
                        'Sucesso',
                        value={'message': 'Usuário user@email.com foi ativado com sucesso.', 'user_id': 1, 'is_active': True}
                    ),
                ],
            ),
        },
    ),
)
class AdminUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de usuários pelo administrador.
    
    Permite listar, visualizar, atualizar, suspender e ativar usuários.
    
    **Permissão necessária:** IsAdmin
    """
    queryset = User.objects.all()
    permission_classes = [IsAdmin]
    serializer_class = None
    lookup_field = 'pk'

    def get_serializer_class(self):
        """Retorna o serializer apropriado baseado na ação."""
        from rest_framework.serializers import ModelSerializer
        
        class UserSerializer(ModelSerializer):
            class Meta:
                model = User
                fields = [
                    'id', 'email', 'first_name', 'last_name', 'phone',
                    'user_type', 'is_active', 'is_staff', 'is_superuser',
                    'date_joined', 'last_login', 'created_at', 'updated_at'
                ]
                read_only_fields = ['id', 'date_joined', 'last_login', 'created_at', 'updated_at']
        
        return UserSerializer

    def list(self, request, *args, **kwargs):
        """Lista todos os usuários."""
        queryset = self.get_queryset()
        
        user_type = request.query_params.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Retorna detalhes de um usuário específico."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Atualiza um usuário."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='suspend')
    def suspend(self, request, pk=None):
        """Suspende um usuário (desativa)."""
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response({
            'message': f'Usuário {user.email} foi suspenso com sucesso.',
            'user_id': user.id,
            'is_active': user.is_active,
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        """Ativa um usuário."""
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=['is_active'])
        return Response({
            'message': f'Usuário {user.email} foi ativado com sucesso.',
            'user_id': user.id,
            'is_active': user.is_active,
        }, status=status.HTTP_200_OK)
