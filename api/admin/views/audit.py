"""
ViewSet para visualização de logs de auditoria pelo administrador.
"""
from rest_framework import viewsets
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from api.admin.permissions import IsAdmin
from api.admin.models import AdminAction


@extend_schema_view(
    list=extend_schema(
        tags=['Admin - Auditoria'],
        summary='Listar logs de auditoria',
        description='''
Retorna lista paginada de todas as ações administrativas registradas.

Os logs incluem:
- Tipo de ação (USER_SUSPEND, ORDER_UPDATE, etc.)
- Administrador responsável
- Modelo e ID do objeto afetado
- Data/hora da ação
- Endereço IP
- Metadados adicionais
        ''',
        parameters=[
            OpenApiParameter('action_type', OpenApiTypes.STR, description='Filtrar por tipo de ação (ex: USER_SUSPEND)'),
            OpenApiParameter('admin_user', OpenApiTypes.INT, description='Filtrar por ID do administrador'),
            OpenApiParameter('target_model', OpenApiTypes.STR, description='Filtrar por modelo alvo (ex: User, Order)'),
            OpenApiParameter('target_id', OpenApiTypes.INT, description='Filtrar por ID do objeto alvo'),
            OpenApiParameter('start_date', OpenApiTypes.DATE, description='Data inicial (YYYY-MM-DD)'),
            OpenApiParameter('end_date', OpenApiTypes.DATE, description='Data final (YYYY-MM-DD)'),
        ],
    ),
    retrieve=extend_schema(
        tags=['Admin - Auditoria'],
        summary='Detalhes do log',
        description='Retorna informações detalhadas de um log de auditoria específico.',
    ),
)
class AdminAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualização de logs de auditoria pelo administrador.
    
    Permite listar e visualizar ações administrativas (somente leitura).
    Logs de auditoria não podem ser editados ou deletados por segurança.
    
    **Permissão necessária:** IsAdmin
    
    **Importante:** Logs são gerados automaticamente pelo middleware de auditoria
    para todas as ações POST, PUT, PATCH e DELETE nos endpoints /api/admin/.
    """
    queryset = AdminAction.objects.select_related('admin_user')
    permission_classes = [IsAdmin]
    serializer_class = None

    def get_serializer_class(self):
        """Retorna o serializer apropriado."""
        from rest_framework.serializers import ModelSerializer, SerializerMethodField
        
        class AuditLogSerializer(ModelSerializer):
            admin_email = SerializerMethodField()
            
            class Meta:
                model = AdminAction
                fields = [
                    'id', 'admin_user', 'admin_email', 'action_type',
                    'target_model', 'target_id', 'description', 'metadata',
                    'ip_address', 'created_at'
                ]
                read_only_fields = [
                    'id', 'admin_user', 'action_type', 'target_model',
                    'target_id', 'description', 'metadata', 'ip_address', 'created_at'
                ]
            
            def get_admin_email(self, obj):
                return obj.admin_user.email if obj.admin_user else None
        
        return AuditLogSerializer

    def list(self, request, *args, **kwargs):
        """Lista todos os logs de auditoria."""
        queryset = self.get_queryset()
        
        action_type_filter = request.query_params.get('action_type')
        if action_type_filter:
            queryset = queryset.filter(action_type=action_type_filter)
        
        admin_user_filter = request.query_params.get('admin_user')
        if admin_user_filter:
            queryset = queryset.filter(admin_user_id=admin_user_filter)
        
        target_model_filter = request.query_params.get('target_model')
        if target_model_filter:
            queryset = queryset.filter(target_model=target_model_filter)
        
        target_id_filter = request.query_params.get('target_id')
        if target_id_filter:
            queryset = queryset.filter(target_id=target_id_filter)
        
        start_date_filter = request.query_params.get('start_date')
        if start_date_filter:
            queryset = queryset.filter(created_at__date__gte=start_date_filter)
        
        end_date_filter = request.query_params.get('end_date')
        if end_date_filter:
            queryset = queryset.filter(created_at__date__lte=end_date_filter)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Retorna detalhes de um log de auditoria específico."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
