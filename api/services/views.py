"""
ViewSets para o app services (categorias e serviços).
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter

from api.accounts.permissions import IsAdmin
from api.services.models import ServiceCategory, Service
from api.services.serializers import (
    ServiceCategorySerializer,
    ServiceCategoryListSerializer,
    ServiceCategoryTreeSerializer,
    ServiceCategoryCreateUpdateSerializer,
    ServiceSerializer,
    ServiceListSerializer,
    ServiceCreateUpdateSerializer,
)


@extend_schema(tags=['Serviços - Categorias'])
class ServiceCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de categorias de serviço.
    
    Endpoints:
    - GET /categories/ - Lista categorias (autenticado)
    - POST /categories/ - Cria categoria (admin only)
    - GET /categories/{id}/ - Detalhes da categoria (autenticado)
    - PATCH /categories/{id}/ - Atualiza categoria (admin only)
    - DELETE /categories/{id}/ - Deleta categoria (admin only, soft delete)
    - GET /categories/tree/ - Retorna árvore de categorias (autenticado)
    - GET /categories/root/ - Retorna apenas categorias raiz (autenticado)
    
    Filtros disponíveis:
    - is_active: filtra por status ativo/inativo
    - parent: filtra por categoria pai
    - search: busca por nome ou descrição
    """
    queryset = ServiceCategory.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'parent']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return ServiceCategoryListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ServiceCategoryCreateUpdateSerializer
        elif self.action == 'tree':
            return ServiceCategoryTreeSerializer
        return ServiceCategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'tree', 'root', 'services']:
            # Leitura disponível para usuários autenticados
            return [IsAuthenticated()]
        # Criação, atualização e deleção apenas para admin
        return [IsAuthenticated(), IsAdmin()]

    @extend_schema(
        summary='Lista categorias',
        description='Retorna lista de categorias de serviço. Suporta filtros e busca.',
        parameters=[
            OpenApiParameter(name='is_active', description='Filtrar por status ativo', type=bool),
            OpenApiParameter(name='parent', description='Filtrar por categoria pai (ID)', type=int),
            OpenApiParameter(name='search', description='Buscar por nome ou descrição', type=str),
        ],
        responses={
            200: OpenApiResponse(
                response=ServiceCategoryListSerializer(many=True),
                description='Lista de categorias',
                examples=[
                    OpenApiExample(
                        'Sucesso',
                        value=[
                            {'id': 1, 'name': 'Tecnologia', 'slug': 'tecnologia', 'parent': None, 'parent_name': None, 'is_active': True},
                            {'id': 2, 'name': 'Desenvolvimento Web', 'slug': 'desenvolvimento-web', 'parent': 1, 'parent_name': 'Tecnologia', 'is_active': True},
                        ]
                    )
                ]
            ),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Cria categoria',
        description='Cria uma nova categoria de serviço. Apenas administradores.',
        request=ServiceCategoryCreateUpdateSerializer,
        responses={
            201: ServiceCategorySerializer,
            400: OpenApiResponse(description='Dados inválidos'),
            403: OpenApiResponse(description='Acesso negado - apenas administradores'),
        },
        examples=[
            OpenApiExample(
                'Criar categoria raiz',
                value={'name': 'Tecnologia', 'description': 'Serviços de tecnologia', 'is_active': True},
                request_only=True
            ),
            OpenApiExample(
                'Criar subcategoria',
                value={'name': 'Desenvolvimento Web', 'description': 'Criação de sites', 'parent': 1, 'is_active': True},
                request_only=True
            ),
        ]
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        # Retorna com serializer completo
        return Response(
            ServiceCategorySerializer(category).data,
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        summary='Detalhes da categoria',
        description='Retorna detalhes completos de uma categoria específica, incluindo contagem de filhos e serviços.',
        responses={
            200: OpenApiResponse(
                response=ServiceCategorySerializer,
                examples=[
                    OpenApiExample(
                        'Categoria com subcategorias',
                        value={
                            'id': 1,
                            'name': 'Tecnologia',
                            'slug': 'tecnologia',
                            'description': 'Serviços de tecnologia da informação',
                            'parent': None,
                            'parent_name': None,
                            'is_active': True,
                            'is_subcategory': False,
                            'full_path': 'Tecnologia',
                            'children_count': 3,
                            'services_count': 5,
                            'created_at': '2024-01-01T10:00:00Z',
                            'updated_at': '2024-01-15T14:30:00Z'
                        }
                    )
                ]
            ),
            404: OpenApiResponse(description='Categoria não encontrada'),
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Atualiza categoria',
        description='Atualiza dados de uma categoria. Apenas administradores.',
        request=ServiceCategoryCreateUpdateSerializer,
        responses={
            200: ServiceCategorySerializer,
            400: OpenApiResponse(description='Dados inválidos'),
            403: OpenApiResponse(description='Acesso negado'),
        }
    )
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        return Response(ServiceCategorySerializer(category).data)

    @extend_schema(
        summary='Deleta categoria',
        description='Deleta uma categoria (soft delete). Apenas administradores.',
        responses={
            204: OpenApiResponse(description='Categoria deletada com sucesso'),
            403: OpenApiResponse(description='Acesso negado'),
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        summary='Árvore de categorias',
        description='Retorna categorias em formato de árvore hierárquica.',
        responses={
            200: OpenApiResponse(
                response=ServiceCategoryTreeSerializer(many=True),
                description='Árvore de categorias',
                examples=[
                    OpenApiExample(
                        'Sucesso',
                        value=[
                            {
                                'id': 1, 'name': 'Tecnologia', 'slug': 'tecnologia',
                                'is_active': True, 'services_count': 0,
                                'children': [
                                    {'id': 2, 'name': 'Web', 'slug': 'web', 'is_active': True, 'services_count': 3, 'children': []}
                                ]
                            }
                        ]
                    )
                ]
            ),
        }
    )
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Retorna categorias em formato de árvore."""
        # Busca apenas categorias raiz (sem parent) e ativas
        root_categories = ServiceCategory.objects.filter(
            parent__isnull=True,
            is_active=True
        )
        serializer = ServiceCategoryTreeSerializer(root_categories, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary='Categorias raiz',
        description='Retorna apenas categorias sem parent (categorias principais).',
        responses={200: ServiceCategoryListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def root(self, request):
        """Retorna apenas categorias raiz."""
        root_categories = ServiceCategory.objects.filter(parent__isnull=True)
        serializer = ServiceCategoryListSerializer(root_categories, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary='Serviços da categoria',
        description='Retorna todos os serviços ativos pertencentes a uma categoria específica.',
        responses={
            200: OpenApiResponse(
                response=ServiceListSerializer(many=True),
                description='Lista de serviços da categoria',
                examples=[
                    OpenApiExample(
                        'Serviços da categoria Web',
                        value=[
                            {'id': 1, 'name': 'Desenvolvimento de Sites', 'category': 2, 'category_name': 'Web', 'is_active': True},
                            {'id': 2, 'name': 'Criação de E-commerce', 'category': 2, 'category_name': 'Web', 'is_active': True},
                            {'id': 3, 'name': 'Landing Pages', 'category': 2, 'category_name': 'Web', 'is_active': True},
                        ]
                    ),
                    OpenApiExample(
                        'Categoria sem serviços',
                        value=[]
                    )
                ]
            ),
            404: OpenApiResponse(description='Categoria não encontrada'),
        }
    )
    @action(detail=True, methods=['get'])
    def services(self, request, pk=None):
        """Retorna serviços de uma categoria específica."""
        category = self.get_object()
        services = Service.objects.filter(category=category, is_active=True)
        serializer = ServiceListSerializer(services, many=True)
        return Response(serializer.data)


@extend_schema(tags=['Serviços'])
class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de serviços.
    
    Endpoints:
    - GET /services/ - Lista serviços (autenticado)
    - POST /services/ - Cria serviço (admin only)
    - GET /services/{id}/ - Detalhes do serviço (autenticado)
    - PATCH /services/{id}/ - Atualiza serviço (admin only)
    - DELETE /services/{id}/ - Deleta serviço (admin only, soft delete)
    
    Filtros disponíveis:
    - category: filtra por categoria (ID)
    - is_active: filtra por status ativo/inativo
    - search: busca por nome ou descrição
    """
    queryset = Service.objects.select_related('category').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'category__name', 'created_at']
    ordering = ['category__name', 'name']

    def get_serializer_class(self):
        if self.action == 'list':
            return ServiceListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ServiceCreateUpdateSerializer
        return ServiceSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            # Leitura disponível para usuários autenticados
            return [IsAuthenticated()]
        # Criação, atualização e deleção apenas para admin
        return [IsAuthenticated(), IsAdmin()]

    @extend_schema(
        summary='Lista serviços',
        description='Retorna lista de serviços. Suporta filtros por categoria e busca.',
        parameters=[
            OpenApiParameter(name='category', description='Filtrar por categoria (ID)', type=int),
            OpenApiParameter(name='is_active', description='Filtrar por status ativo', type=bool),
            OpenApiParameter(name='search', description='Buscar por nome ou descrição', type=str),
        ],
        responses={
            200: OpenApiResponse(
                response=ServiceListSerializer(many=True),
                description='Lista de serviços',
                examples=[
                    OpenApiExample(
                        'Sucesso',
                        value=[
                            {'id': 1, 'name': 'Desenvolvimento de Sites', 'category': 2, 'category_name': 'Web', 'is_active': True},
                            {'id': 2, 'name': 'Criação de E-commerce', 'category': 2, 'category_name': 'Web', 'is_active': True},
                        ]
                    )
                ]
            ),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary='Cria serviço',
        description='Cria um novo serviço. Apenas administradores.',
        request=ServiceCreateUpdateSerializer,
        responses={
            201: ServiceSerializer,
            400: OpenApiResponse(description='Dados inválidos'),
            403: OpenApiResponse(description='Acesso negado - apenas administradores'),
        },
        examples=[
            OpenApiExample(
                'Exemplo',
                value={'name': 'Desenvolvimento de Sites', 'description': 'Criação de sites institucionais', 'category': 2, 'is_active': True},
                request_only=True
            ),
        ]
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = serializer.save()
        # Retorna com serializer completo
        return Response(
            ServiceSerializer(service).data,
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        summary='Detalhes do serviço',
        description='Retorna detalhes completos de um serviço, incluindo informações da categoria.',
        responses={
            200: OpenApiResponse(
                response=ServiceSerializer,
                examples=[
                    OpenApiExample(
                        'Detalhes do serviço',
                        value={
                            'id': 1,
                            'name': 'Desenvolvimento de Sites',
                            'description': 'Criação de sites institucionais modernos e responsivos',
                            'category': 2,
                            'category_name': 'Web',
                            'category_full_path': 'Tecnologia > Web',
                            'is_active': True,
                            'created_at': '2024-01-05T09:00:00Z',
                            'updated_at': '2024-01-10T11:30:00Z'
                        }
                    )
                ]
            ),
            404: OpenApiResponse(description='Serviço não encontrado'),
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Atualiza serviço',
        description='Atualiza dados de um serviço. Apenas administradores.',
        request=ServiceCreateUpdateSerializer,
        responses={
            200: ServiceSerializer,
            400: OpenApiResponse(description='Dados inválidos'),
            403: OpenApiResponse(description='Acesso negado'),
        }
    )
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        service = serializer.save()
        return Response(ServiceSerializer(service).data)

    @extend_schema(
        summary='Deleta serviço',
        description='Deleta um serviço (soft delete). Apenas administradores.',
        responses={
            204: OpenApiResponse(description='Serviço deletado com sucesso'),
            403: OpenApiResponse(description='Acesso negado'),
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
