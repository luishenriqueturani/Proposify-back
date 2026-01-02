"""
Serializers para o app services (categorias e serviços).
"""
from rest_framework import serializers
from api.services.models import ServiceCategory, Service


class ServiceCategorySerializer(serializers.ModelSerializer):
    """
    Serializer para categorias de serviço.
    
    Campos somente leitura:
    - id, slug, created_at, updated_at, deleted_at
    - is_subcategory (propriedade calculada)
    - full_path (caminho completo da categoria)
    - children_count (número de subcategorias)
    - services_count (número de serviços)
    
    Campos editáveis:
    - name, description, parent, is_active
    """
    is_subcategory = serializers.ReadOnlyField()
    full_path = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()
    services_count = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()

    class Meta:
        model = ServiceCategory
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'parent_name',
            'is_active', 'is_subcategory', 'full_path', 'children_count',
            'services_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_full_path(self, obj):
        """Retorna o caminho completo da categoria."""
        return obj.get_full_path()

    def get_children_count(self, obj):
        """Retorna o número de subcategorias."""
        return obj.children.filter(deleted_at__isnull=True).count()

    def get_services_count(self, obj):
        """Retorna o número de serviços na categoria."""
        return obj.services.filter(deleted_at__isnull=True).count()

    def get_parent_name(self, obj):
        """Retorna o nome da categoria pai."""
        return obj.parent.name if obj.parent else None

    def validate_name(self, value):
        """Valida que o nome não está vazio e tem tamanho adequado."""
        if not value or not value.strip():
            raise serializers.ValidationError('O nome da categoria é obrigatório.')
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                'O nome da categoria deve ter pelo menos 2 caracteres.'
            )
        return value.strip()

    def validate_parent(self, value):
        """Valida que a categoria pai não cria ciclo."""
        if value:
            # Verifica se está tentando definir a si mesmo como pai
            if self.instance and value.pk == self.instance.pk:
                raise serializers.ValidationError(
                    'Uma categoria não pode ser pai de si mesma.'
                )
            
            # Verifica se o pai não é um descendente (evita ciclos)
            if self.instance:
                current = value
                while current:
                    if current.pk == self.instance.pk:
                        raise serializers.ValidationError(
                            'Não é possível definir um descendente como categoria pai.'
                        )
                    current = current.parent
        return value


class ServiceCategoryListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de categorias.
    Usado em listas e seletores.
    """
    parent_name = serializers.SerializerMethodField()

    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'slug', 'parent', 'parent_name', 'is_active']

    def get_parent_name(self, obj):
        """Retorna o nome da categoria pai."""
        return obj.parent.name if obj.parent else None


class ServiceCategoryTreeSerializer(serializers.ModelSerializer):
    """
    Serializer para árvore de categorias com subcategorias aninhadas.
    """
    children = serializers.SerializerMethodField()
    services_count = serializers.SerializerMethodField()

    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'slug', 'description', 'is_active', 'children', 'services_count']

    def get_children(self, obj):
        """Retorna subcategorias de forma recursiva."""
        children = obj.children.filter(deleted_at__isnull=True, is_active=True)
        return ServiceCategoryTreeSerializer(children, many=True).data

    def get_services_count(self, obj):
        """Retorna o número de serviços na categoria."""
        return obj.services.filter(deleted_at__isnull=True).count()


class ServiceSerializer(serializers.ModelSerializer):
    """
    Serializer para serviços.
    
    Campos somente leitura:
    - id, created_at, updated_at, deleted_at
    - category_name (nome da categoria)
    - category_full_path (caminho completo da categoria)
    
    Campos editáveis:
    - name, description, category, is_active
    """
    category_name = serializers.SerializerMethodField()
    category_full_path = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'category_full_path', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_category_name(self, obj):
        """Retorna o nome da categoria."""
        return obj.category.name

    def get_category_full_path(self, obj):
        """Retorna o caminho completo da categoria."""
        return obj.category.get_full_path()

    def validate_name(self, value):
        """Valida que o nome não está vazio e tem tamanho adequado."""
        if not value or not value.strip():
            raise serializers.ValidationError('O nome do serviço é obrigatório.')
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                'O nome do serviço deve ter pelo menos 3 caracteres.'
            )
        return value.strip()

    def validate_category(self, value):
        """Valida que a categoria está ativa."""
        if value and not value.is_active:
            raise serializers.ValidationError(
                'Não é possível associar um serviço a uma categoria inativa.'
            )
        if value and value.deleted_at:
            raise serializers.ValidationError(
                'Não é possível associar um serviço a uma categoria deletada.'
            )
        return value


class ServiceListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de serviços.
    """
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = ['id', 'name', 'category', 'category_name', 'is_active']

    def get_category_name(self, obj):
        """Retorna o nome da categoria."""
        return obj.category.name


class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação e atualização de serviços.
    """
    class Meta:
        model = Service
        fields = ['name', 'description', 'category', 'is_active']

    def validate_name(self, value):
        """Valida que o nome não está vazio e tem tamanho adequado."""
        if not value or not value.strip():
            raise serializers.ValidationError('O nome do serviço é obrigatório.')
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                'O nome do serviço deve ter pelo menos 3 caracteres.'
            )
        return value.strip()

    def validate_category(self, value):
        """Valida que a categoria está ativa e não deletada."""
        if value and not value.is_active:
            raise serializers.ValidationError(
                'Não é possível associar um serviço a uma categoria inativa.'
            )
        if value and value.deleted_at:
            raise serializers.ValidationError(
                'Não é possível associar um serviço a uma categoria deletada.'
            )
        return value


class ServiceCategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação e atualização de categorias.
    """
    class Meta:
        model = ServiceCategory
        fields = ['name', 'description', 'parent', 'is_active']

    def validate_name(self, value):
        """Valida que o nome não está vazio e tem tamanho adequado."""
        if not value or not value.strip():
            raise serializers.ValidationError('O nome da categoria é obrigatório.')
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                'O nome da categoria deve ter pelo menos 2 caracteres.'
            )
        return value.strip()

    def validate_parent(self, value):
        """Valida que a categoria pai não cria ciclo."""
        if value:
            # Verifica se está tentando definir a si mesmo como pai
            if self.instance and value.pk == self.instance.pk:
                raise serializers.ValidationError(
                    'Uma categoria não pode ser pai de si mesma.'
                )
            
            # Verifica se o pai não é um descendente (evita ciclos)
            if self.instance:
                current = value
                while current:
                    if current.pk == self.instance.pk:
                        raise serializers.ValidationError(
                            'Não é possível definir um descendente como categoria pai.'
                        )
                    current = current.parent
            
            # Verifica se a categoria pai está ativa
            if not value.is_active:
                raise serializers.ValidationError(
                    'Não é possível definir uma categoria inativa como pai.'
                )
        return value
