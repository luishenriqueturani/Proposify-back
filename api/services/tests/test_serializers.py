"""
Testes unitários para os serializers do app services.
"""
from django.test import TestCase

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


class ServiceCategorySerializerTestCase(TestCase):
    """Testes para ServiceCategorySerializer."""

    def setUp(self):
        """Cria dados de teste."""
        self.parent_category = ServiceCategory.objects.create(
            name='Tecnologia',
            description='Serviços de tecnologia'
        )
        self.child_category = ServiceCategory.objects.create(
            name='Desenvolvimento Web',
            description='Desenvolvimento de aplicações web',
            parent=self.parent_category
        )
        # Cria serviços para testar contagem
        Service.objects.create(category=self.child_category, name='Site Institucional')
        Service.objects.create(category=self.child_category, name='E-commerce')

    def test_serializer_fields(self):
        """Testa que todos os campos esperados estão presentes."""
        serializer = ServiceCategorySerializer(self.parent_category)
        data = serializer.data
        
        expected_fields = [
            'id', 'name', 'slug', 'description', 'parent', 'parent_name',
            'is_active', 'is_subcategory', 'full_path', 'children_count',
            'services_count', 'created_at', 'updated_at'
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serialize_category_without_parent(self):
        """Testa serialização de categoria sem parent."""
        serializer = ServiceCategorySerializer(self.parent_category)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Tecnologia')
        self.assertEqual(data['slug'], 'tecnologia')
        self.assertIsNone(data['parent'])
        self.assertIsNone(data['parent_name'])
        self.assertFalse(data['is_subcategory'])
        self.assertEqual(data['full_path'], 'Tecnologia')
        self.assertEqual(data['children_count'], 1)

    def test_serialize_category_with_parent(self):
        """Testa serialização de categoria com parent."""
        serializer = ServiceCategorySerializer(self.child_category)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Desenvolvimento Web')
        self.assertEqual(data['parent'], self.parent_category.pk)
        self.assertEqual(data['parent_name'], 'Tecnologia')
        self.assertTrue(data['is_subcategory'])
        self.assertEqual(data['full_path'], 'Tecnologia > Desenvolvimento Web')
        self.assertEqual(data['services_count'], 2)

    def test_validate_name_empty(self):
        """Testa que nome vazio é rejeitado."""
        serializer = ServiceCategorySerializer(data={'name': '', 'is_active': True})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_validate_name_too_short(self):
        """Testa que nome muito curto é rejeitado."""
        serializer = ServiceCategorySerializer(data={'name': 'A', 'is_active': True})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_validate_name_strips_whitespace(self):
        """Testa que espaços são removidos do nome."""
        serializer = ServiceCategorySerializer(data={'name': '  Categoria Teste  ', 'is_active': True})
        serializer.is_valid()
        
        self.assertEqual(serializer.validated_data['name'], 'Categoria Teste')

    def test_validate_parent_self_reference(self):
        """Testa que categoria não pode ser parent de si mesma."""
        serializer = ServiceCategorySerializer(
            instance=self.parent_category,
            data={'name': 'Tecnologia', 'parent': self.parent_category.pk},
            partial=True
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('parent', serializer.errors)

    def test_validate_parent_descendant(self):
        """Testa que descendente não pode ser parent."""
        serializer = ServiceCategorySerializer(
            instance=self.parent_category,
            data={'name': 'Tecnologia', 'parent': self.child_category.pk},
            partial=True
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('parent', serializer.errors)


class ServiceCategoryListSerializerTestCase(TestCase):
    """Testes para ServiceCategoryListSerializer."""

    def test_serializer_fields(self):
        """Testa que apenas campos essenciais estão presentes."""
        category = ServiceCategory.objects.create(name='Teste')
        serializer = ServiceCategoryListSerializer(category)
        data = serializer.data
        
        self.assertEqual(set(data.keys()), {'id', 'name', 'slug', 'parent', 'parent_name', 'is_active'})


class ServiceCategoryTreeSerializerTestCase(TestCase):
    """Testes para ServiceCategoryTreeSerializer."""

    def test_tree_with_children(self):
        """Testa serialização de árvore com filhos."""
        parent = ServiceCategory.objects.create(name='Tecnologia')
        child1 = ServiceCategory.objects.create(name='Web', parent=parent)
        child2 = ServiceCategory.objects.create(name='Mobile', parent=parent)
        grandchild = ServiceCategory.objects.create(name='React', parent=child1)
        
        serializer = ServiceCategoryTreeSerializer(parent)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Tecnologia')
        self.assertEqual(len(data['children']), 2)
        
        # Verifica neto
        web_child = next(c for c in data['children'] if c['name'] == 'Web')
        self.assertEqual(len(web_child['children']), 1)
        self.assertEqual(web_child['children'][0]['name'], 'React')


class ServiceCategoryCreateUpdateSerializerTestCase(TestCase):
    """Testes para ServiceCategoryCreateUpdateSerializer."""

    def test_create_category(self):
        """Testa criação de categoria via serializer."""
        data = {'name': 'Nova Categoria', 'description': 'Descrição', 'is_active': True}
        serializer = ServiceCategoryCreateUpdateSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        category = serializer.save()
        
        self.assertEqual(category.name, 'Nova Categoria')
        self.assertEqual(category.description, 'Descrição')

    def test_update_category(self):
        """Testa atualização de categoria via serializer."""
        category = ServiceCategory.objects.create(name='Original')
        serializer = ServiceCategoryCreateUpdateSerializer(
            instance=category,
            data={'name': 'Atualizada'},
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        
        self.assertEqual(updated.name, 'Atualizada')

    def test_validate_inactive_parent(self):
        """Testa que parent inativo é rejeitado."""
        parent = ServiceCategory.objects.create(name='Parent', is_active=False)
        serializer = ServiceCategoryCreateUpdateSerializer(
            data={'name': 'Child', 'parent': parent.pk}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('parent', serializer.errors)


class ServiceSerializerTestCase(TestCase):
    """Testes para ServiceSerializer."""

    def setUp(self):
        """Cria dados de teste."""
        self.category = ServiceCategory.objects.create(name='Desenvolvimento Web')
        self.service = Service.objects.create(
            category=self.category,
            name='Criação de Sites',
            description='Desenvolvimento de sites institucionais'
        )

    def test_serializer_fields(self):
        """Testa que todos os campos esperados estão presentes."""
        serializer = ServiceSerializer(self.service)
        data = serializer.data
        
        expected_fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'category_full_path', 'is_active', 'created_at', 'updated_at'
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_serialize_service(self):
        """Testa serialização de serviço."""
        serializer = ServiceSerializer(self.service)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Criação de Sites')
        self.assertEqual(data['category'], self.category.pk)
        self.assertEqual(data['category_name'], 'Desenvolvimento Web')
        self.assertEqual(data['category_full_path'], 'Desenvolvimento Web')
        self.assertTrue(data['is_active'])

    def test_validate_name_empty(self):
        """Testa que nome vazio é rejeitado."""
        serializer = ServiceSerializer(data={
            'name': '',
            'category': self.category.pk
        })
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_validate_name_too_short(self):
        """Testa que nome muito curto é rejeitado."""
        serializer = ServiceSerializer(data={
            'name': 'AB',
            'category': self.category.pk
        })
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_validate_inactive_category(self):
        """Testa que categoria inativa é rejeitada."""
        self.category.is_active = False
        self.category.save()
        
        serializer = ServiceSerializer(data={
            'name': 'Novo Serviço',
            'category': self.category.pk
        })
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('category', serializer.errors)


class ServiceListSerializerTestCase(TestCase):
    """Testes para ServiceListSerializer."""

    def test_serializer_fields(self):
        """Testa que apenas campos essenciais estão presentes."""
        category = ServiceCategory.objects.create(name='Teste')
        service = Service.objects.create(category=category, name='Serviço Teste')
        
        serializer = ServiceListSerializer(service)
        data = serializer.data
        
        self.assertEqual(set(data.keys()), {'id', 'name', 'category', 'category_name', 'is_active'})


class ServiceCreateUpdateSerializerTestCase(TestCase):
    """Testes para ServiceCreateUpdateSerializer."""

    def setUp(self):
        """Cria dados de teste."""
        self.category = ServiceCategory.objects.create(name='Desenvolvimento')

    def test_create_service(self):
        """Testa criação de serviço via serializer."""
        data = {
            'name': 'Novo Serviço',
            'description': 'Descrição do serviço',
            'category': self.category.pk,
            'is_active': True
        }
        serializer = ServiceCreateUpdateSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        service = serializer.save()
        
        self.assertEqual(service.name, 'Novo Serviço')
        self.assertEqual(service.category, self.category)

    def test_update_service(self):
        """Testa atualização de serviço via serializer."""
        service = Service.objects.create(category=self.category, name='Original')
        serializer = ServiceCreateUpdateSerializer(
            instance=service,
            data={'name': 'Atualizado'},
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        
        self.assertEqual(updated.name, 'Atualizado')

    def test_validate_deleted_category(self):
        """Testa que categoria deletada é rejeitada."""
        self.category.delete()  # Soft delete
        
        serializer = ServiceCreateUpdateSerializer(data={
            'name': 'Novo Serviço',
            'category': self.category.pk
        })
        
        # A categoria deletada não deve ser encontrada pelo queryset padrão
        self.assertFalse(serializer.is_valid())
        self.assertIn('category', serializer.errors)
