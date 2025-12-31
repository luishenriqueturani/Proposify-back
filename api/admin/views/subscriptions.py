"""
ViewSet para gerenciamento de assinaturas pelo administrador.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from api.admin.permissions import IsAdmin
from api.subscriptions.models import UserSubscription
from api.subscriptions.enums import SubscriptionStatus


@extend_schema_view(
    list=extend_schema(
        tags=['Admin - Assinaturas'],
        summary='Listar assinaturas',
        description='Retorna lista paginada de todas as assinaturas do sistema.',
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR, description='Filtrar por status (ACTIVE, CANCELLED, EXPIRED, SUSPENDED)'),
            OpenApiParameter('plan', OpenApiTypes.INT, description='Filtrar por ID do plano'),
            OpenApiParameter('user', OpenApiTypes.INT, description='Filtrar por ID do usuário'),
        ],
    ),
    retrieve=extend_schema(
        tags=['Admin - Assinaturas'],
        summary='Detalhes da assinatura',
        description='Retorna informações detalhadas de uma assinatura específica.',
    ),
    cancel=extend_schema(
        tags=['Admin - Assinaturas'],
        summary='Cancelar assinatura',
        description='Cancela uma assinatura ativa. A assinatura permanece válida até o fim do período.',
        responses={
            200: OpenApiResponse(description='Assinatura cancelada com sucesso'),
            400: OpenApiResponse(description='Assinatura já está cancelada'),
        },
    ),
    reactivate=extend_schema(
        tags=['Admin - Assinaturas'],
        summary='Reativar assinatura',
        description='Reativa uma assinatura cancelada ou suspensa.',
        responses={
            200: OpenApiResponse(description='Assinatura reativada com sucesso'),
            400: OpenApiResponse(description='Assinatura já está ativa'),
        },
    ),
    suspend=extend_schema(
        tags=['Admin - Assinaturas'],
        summary='Suspender assinatura',
        description='Suspende temporariamente uma assinatura ativa.',
        responses={
            200: OpenApiResponse(description='Assinatura suspensa com sucesso'),
            400: OpenApiResponse(description='Assinatura já está suspensa ou não está ativa'),
        },
    ),
)
class AdminSubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de assinaturas pelo administrador.
    
    Permite listar, visualizar, atualizar e gerenciar assinaturas de usuários.
    Inclui ações para cancelar e reativar assinaturas.
    
    **Permissão necessária:** IsAdmin
    """
    queryset = UserSubscription.objects.select_related('user', 'plan')
    permission_classes = [IsAdmin]
    serializer_class = None

    def get_serializer_class(self):
        """Retorna o serializer apropriado."""
        from rest_framework.serializers import ModelSerializer, SerializerMethodField
        
        class SubscriptionSerializer(ModelSerializer):
            user_email = SerializerMethodField()
            plan_name = SerializerMethodField()
            
            class Meta:
                model = UserSubscription
                fields = [
                    'id', 'user', 'user_email', 'plan', 'plan_name', 'status',
                    'start_date', 'end_date', 'auto_renew', 'cancelled_at',
                    'is_active', 'is_expired', 'created_at', 'updated_at'
                ]
                read_only_fields = [
                    'id', 'user_email', 'plan_name', 'is_active', 'is_expired',
                    'created_at', 'updated_at'
                ]
            
            def get_user_email(self, obj):
                return obj.user.email if obj.user else None
            
            def get_plan_name(self, obj):
                return obj.plan.name if obj.plan else None
        
        return SubscriptionSerializer

    def list(self, request, *args, **kwargs):
        """Lista todas as assinaturas."""
        queryset = self.get_queryset()
        
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        plan_filter = request.query_params.get('plan')
        if plan_filter:
            queryset = queryset.filter(plan_id=plan_filter)
        
        user_filter = request.query_params.get('user')
        if user_filter:
            queryset = queryset.filter(user_id=user_filter)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Retorna detalhes de uma assinatura específica."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """Cancela uma assinatura."""
        subscription = self.get_object()
        
        if subscription.status == SubscriptionStatus.CANCELLED.value:
            return Response({
                'error': 'Esta assinatura já está cancelada.',
                'subscription_id': subscription.id,
                'status': subscription.status,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        subscription.cancel()
        
        return Response({
            'message': f'Assinatura #{subscription.id} foi cancelada com sucesso.',
            'subscription_id': subscription.id,
            'status': subscription.status,
            'cancelled_at': subscription.cancelled_at,
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='reactivate')
    def reactivate(self, request, pk=None):
        """Reativa uma assinatura cancelada ou suspensa."""
        subscription = self.get_object()
        
        if subscription.status == SubscriptionStatus.ACTIVE.value:
            return Response({
                'error': 'Esta assinatura já está ativa.',
                'subscription_id': subscription.id,
                'status': subscription.status,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        subscription.status = SubscriptionStatus.ACTIVE.value
        subscription.cancelled_at = None
        subscription.save(update_fields=['status', 'cancelled_at'])
        
        return Response({
            'message': f'Assinatura #{subscription.id} foi reativada com sucesso.',
            'subscription_id': subscription.id,
            'status': subscription.status,
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='suspend')
    def suspend(self, request, pk=None):
        """Suspende uma assinatura ativa."""
        subscription = self.get_object()
        
        if subscription.status == SubscriptionStatus.SUSPENDED.value:
            return Response({
                'error': 'Esta assinatura já está suspensa.',
                'subscription_id': subscription.id,
                'status': subscription.status,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if subscription.status != SubscriptionStatus.ACTIVE.value:
            return Response({
                'error': 'Apenas assinaturas ativas podem ser suspensas.',
                'subscription_id': subscription.id,
                'status': subscription.status,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        subscription.status = SubscriptionStatus.SUSPENDED.value
        subscription.save(update_fields=['status'])
        
        return Response({
            'message': f'Assinatura #{subscription.id} foi suspensa com sucesso.',
            'subscription_id': subscription.id,
            'status': subscription.status,
        }, status=status.HTTP_200_OK)
