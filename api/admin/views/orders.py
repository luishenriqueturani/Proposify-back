"""
ViewSets para visualização de pedidos e propostas pelo administrador.
"""
from rest_framework import viewsets
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from api.admin.permissions import IsAdmin
from api.orders.models import Order, Proposal


@extend_schema_view(
    list=extend_schema(
        tags=['Admin - Pedidos'],
        summary='Listar pedidos',
        description='Retorna lista paginada de todos os pedidos do sistema.',
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR, description='Filtrar por status (PENDING, ACCEPTED, IN_PROGRESS, COMPLETED, CANCELLED)'),
        ],
    ),
    retrieve=extend_schema(
        tags=['Admin - Pedidos'],
        summary='Detalhes do pedido',
        description='Retorna informações detalhadas de um pedido específico.',
    ),
)
class AdminOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualização de pedidos pelo administrador.
    
    Permite listar e visualizar pedidos (somente leitura).
    
    **Permissão necessária:** IsAdmin
    """
    queryset = Order.objects.select_related('client', 'client__user', 'service', 'service__category')
    permission_classes = [IsAdmin]
    serializer_class = None

    def get_serializer_class(self):
        """Retorna o serializer apropriado."""
        from rest_framework.serializers import ModelSerializer
        
        class OrderSerializer(ModelSerializer):
            class Meta:
                model = Order
                fields = [
                    'id', 'client', 'service', 'title', 'description',
                    'budget_min', 'budget_max', 'deadline', 'status',
                    'created_at', 'updated_at'
                ]
                read_only_fields = ['id', 'created_at', 'updated_at']
        
        return OrderSerializer

    def list(self, request, *args, **kwargs):
        """Lista todos os pedidos."""
        queryset = self.get_queryset()
        
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Retorna detalhes de um pedido específico."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        tags=['Admin - Propostas'],
        summary='Listar propostas',
        description='Retorna lista paginada de todas as propostas do sistema.',
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR, description='Filtrar por status (PENDING, ACCEPTED, DECLINED, EXPIRED)'),
        ],
    ),
    retrieve=extend_schema(
        tags=['Admin - Propostas'],
        summary='Detalhes da proposta',
        description='Retorna informações detalhadas de uma proposta específica.',
    ),
)
class AdminProposalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualização de propostas pelo administrador.
    
    Permite listar e visualizar propostas (somente leitura).
    
    **Permissão necessária:** IsAdmin
    """
    queryset = Proposal.objects.select_related('order', 'provider', 'provider__user')
    permission_classes = [IsAdmin]
    serializer_class = None

    def get_serializer_class(self):
        """Retorna o serializer apropriado."""
        from rest_framework.serializers import ModelSerializer
        
        class ProposalSerializer(ModelSerializer):
            class Meta:
                model = Proposal
                fields = [
                    'id', 'order', 'provider', 'message', 'price',
                    'estimated_days', 'status', 'created_at', 'updated_at',
                    'expires_at'
                ]
                read_only_fields = ['id', 'created_at', 'updated_at']
        
        return ProposalSerializer

    def list(self, request, *args, **kwargs):
        """Lista todas as propostas."""
        queryset = self.get_queryset()
        
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Retorna detalhes de uma proposta específica."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
