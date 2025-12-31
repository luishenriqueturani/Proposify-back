"""
ViewSet para visualização de pagamentos pelo administrador.
"""
from rest_framework import viewsets
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from api.admin.permissions import IsAdmin
from api.payments.models import Payment


@extend_schema_view(
    list=extend_schema(
        tags=['Admin - Pagamentos'],
        summary='Listar pagamentos',
        description='Retorna lista paginada de todos os pagamentos do sistema.',
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR, description='Filtrar por status (PENDING, PAID, FAILED, REFUNDED)'),
        ],
    ),
    retrieve=extend_schema(
        tags=['Admin - Pagamentos'],
        summary='Detalhes do pagamento',
        description='Retorna informações detalhadas de um pagamento específico.',
    ),
)
class AdminPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualização de pagamentos pelo administrador.
    
    Permite listar e visualizar pagamentos (somente leitura).
    
    **Permissão necessária:** IsAdmin
    """
    queryset = Payment.objects.select_related('order', 'proposal')
    permission_classes = [IsAdmin]
    serializer_class = None

    def get_serializer_class(self):
        """Retorna o serializer apropriado."""
        from rest_framework.serializers import ModelSerializer
        
        class PaymentSerializer(ModelSerializer):
            class Meta:
                model = Payment
                fields = [
                    'id', 'order', 'proposal', 'amount', 'payment_method',
                    'payment_status', 'transaction_id', 'payment_date',
                    'metadata', 'created_at', 'updated_at'
                ]
                read_only_fields = ['id', 'created_at', 'updated_at']
        
        return PaymentSerializer

    def list(self, request, *args, **kwargs):
        """Lista todos os pagamentos."""
        queryset = self.get_queryset()
        
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(payment_status=status_filter)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Retorna detalhes de um pagamento específico."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
