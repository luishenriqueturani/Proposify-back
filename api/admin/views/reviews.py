"""
ViewSet para gerenciamento de avaliações pelo administrador.
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from api.admin.permissions import IsAdmin
from api.reviews.models import Review


@extend_schema_view(
    list=extend_schema(
        tags=['Admin - Avaliações'],
        summary='Listar avaliações',
        description='Retorna lista paginada de todas as avaliações do sistema.',
        parameters=[
            OpenApiParameter('rating', OpenApiTypes.INT, description='Filtrar por nota (1-5)'),
            OpenApiParameter('reviewer', OpenApiTypes.INT, description='Filtrar por ID do avaliador'),
            OpenApiParameter('reviewed_user', OpenApiTypes.INT, description='Filtrar por ID do usuário avaliado'),
            OpenApiParameter('order', OpenApiTypes.INT, description='Filtrar por ID do pedido'),
        ],
    ),
    retrieve=extend_schema(
        tags=['Admin - Avaliações'],
        summary='Detalhes da avaliação',
        description='Retorna informações detalhadas de uma avaliação específica.',
    ),
    update=extend_schema(
        tags=['Admin - Avaliações'],
        summary='Moderar avaliação',
        description='Permite que administradores editem o conteúdo de uma avaliação (moderação).',
    ),
    partial_update=extend_schema(
        tags=['Admin - Avaliações'],
        summary='Moderar avaliação (parcial)',
        description='Permite edição parcial para moderação de conteúdo.',
    ),
    destroy=extend_schema(
        tags=['Admin - Avaliações'],
        summary='Remover avaliação',
        description='Remove uma avaliação do sistema (soft delete). Usada para moderação de conteúdo impróprio.',
        responses={
            200: OpenApiResponse(description='Avaliação removida com sucesso'),
        },
    ),
)
class AdminReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de avaliações pelo administrador.
    
    Permite listar, visualizar, atualizar e remover avaliações para moderação.
    
    **Permissão necessária:** IsAdmin
    """
    queryset = Review.objects.select_related('order', 'reviewer', 'reviewed_user')
    permission_classes = [IsAdmin]
    serializer_class = None

    def get_serializer_class(self):
        """Retorna o serializer apropriado."""
        from rest_framework.serializers import ModelSerializer, SerializerMethodField
        
        class ReviewSerializer(ModelSerializer):
            reviewer_email = SerializerMethodField()
            reviewed_user_email = SerializerMethodField()
            order_title = SerializerMethodField()
            
            class Meta:
                model = Review
                fields = [
                    'id', 'order', 'order_title', 'reviewer', 'reviewer_email',
                    'reviewed_user', 'reviewed_user_email', 'rating', 'comment',
                    'created_at', 'updated_at'
                ]
                read_only_fields = [
                    'id', 'reviewer_email', 'reviewed_user_email', 'order_title',
                    'created_at', 'updated_at'
                ]
            
            def get_reviewer_email(self, obj):
                return obj.reviewer.email if obj.reviewer else None
            
            def get_reviewed_user_email(self, obj):
                return obj.reviewed_user.email if obj.reviewed_user else None
            
            def get_order_title(self, obj):
                return obj.order.title if obj.order else None
        
        return ReviewSerializer

    def list(self, request, *args, **kwargs):
        """Lista todas as avaliações."""
        queryset = self.get_queryset()
        
        rating_filter = request.query_params.get('rating')
        if rating_filter:
            queryset = queryset.filter(rating=rating_filter)
        
        reviewer_filter = request.query_params.get('reviewer')
        if reviewer_filter:
            queryset = queryset.filter(reviewer_id=reviewer_filter)
        
        reviewed_user_filter = request.query_params.get('reviewed_user')
        if reviewed_user_filter:
            queryset = queryset.filter(reviewed_user_id=reviewed_user_filter)
        
        order_filter = request.query_params.get('order')
        if order_filter:
            queryset = queryset.filter(order_id=order_filter)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Retorna detalhes de uma avaliação específica."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Atualiza uma avaliação (moderação)."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        instance.rating = serializer.validated_data.get('rating', instance.rating)
        instance.comment = serializer.validated_data.get('comment', instance.comment)
        instance.save(update_fields=['rating', 'comment', 'updated_at'])
        
        return Response(self.get_serializer(instance).data)

    def destroy(self, request, *args, **kwargs):
        """Remove uma avaliação (soft delete para moderação)."""
        instance = self.get_object()
        review_id = instance.id
        instance.delete()  # SoftDelete
        
        return Response({
            'message': f'Avaliação #{review_id} foi removida com sucesso.',
            'review_id': review_id,
        }, status=status.HTTP_200_OK)
