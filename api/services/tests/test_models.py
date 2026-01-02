"""
Testes unitários para os modelos do app services.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from django.utils.text import slugify
import time

from api.services.models import ServiceCategory, Service


class ServiceCategoryModelTestCase(TestCase):
    """Testes unitários para o modelo ServiceCategory."""

    def setUp(self):
        """Cria dados de teste."""
        pass

    def test_create_category_with_minimal_fields(self):
        """Testa criação de categoria com campos mínimos."""
        category = ServiceCategory.objects.create(name='Desenvolvimento Web')
        
        self.assertEqual(category.name, 'Desenvolvimento Web')
        self.assertEqual(category.slug, slugify('Desenvolvimento Web'))
        self.assertIsNone(category.description)
        self.assertIsNone(category.parent)
        self.assertTrue(category.is_active)
        self.assertIsNotNone(category.created_at)
        self.assertIsNotNone(category.updated_at)
        self.assertIsNone(category.deleted_at)
        self.assertFalse(category.is_subcategory)

    def test_create_category_with_all_fields(self):
        """Testa criação de categoria com todos os campos."""
        category = ServiceCategory.objects.create(
            name='Design Gráfico',
            slug='design-grafico',
            description='Serviços de design gráfico',
            is_active=True
        )
        
        self.assertEqual(category.name, 'Design Gráfico')
        self.assertEqual(category.slug, 'design-grafico')
        self.assertEqual(category.description, 'Serviços de design gráfico')
        self.assertTrue(category.is_active)

    def test_name_is_unique(self):
        """Testa que name deve ser único."""
        ServiceCategory.objects.create(name='Marketing Digital')
        
        with self.assertRaises(IntegrityError):
            ServiceCategory.objects.create(name='Marketing Digital')

    def test_slug_is_unique(self):
        """Testa que slug deve ser único."""
        ServiceCategory.objects.create(name='Consultoria', slug='consultoria')
        
        with self.assertRaises(IntegrityError):
            ServiceCategory.objects.create(name='Outra Consultoria', slug='consultoria')

    def test_slug_auto_generation(self):
        """Testa que slug é gerado automaticamente se não fornecido."""
        category = ServiceCategory.objects.create(name='Desenvolvimento Mobile')
        expected_slug = slugify('Desenvolvimento Mobile')
        self.assertEqual(category.slug, expected_slug)

    def test_slug_not_overwritten_if_provided(self):
        """Testa que slug não é sobrescrito se já fornecido."""
        category = ServiceCategory.objects.create(
            name='Desenvolvimento Web',
            slug='web-dev'
        )
        self.assertEqual(category.slug, 'web-dev')
        
        # Atualiza o nome mas o slug deve permanecer
        category.name = 'Desenvolvimento Web Avançado'
        category.save()
        self.assertEqual(category.slug, 'web-dev')

    def test_description_is_optional(self):
        """Testa que description é opcional."""
        category1 = ServiceCategory.objects.create(name='Categoria 1')
        self.assertIsNone(category1.description)
        
        category2 = ServiceCategory.objects.create(
            name='Categoria 2',
            description='Descrição da categoria'
        )
        self.assertEqual(category2.description, 'Descrição da categoria')

    def test_parent_is_optional(self):
        """Testa que parent é opcional."""
        category1 = ServiceCategory.objects.create(name='Categoria Principal')
        self.assertIsNone(category1.parent)
        self.assertFalse(category1.is_subcategory)
        
        # Cria subcategoria
        category2 = ServiceCategory.objects.create(
            name='Subcategoria',
            parent=category1
        )
        self.assertEqual(category2.parent, category1)
        self.assertTrue(category2.is_subcategory)

    def test_self_relationship_parent_child(self):
        """Testa relacionamento self (parent-child)."""
        parent = ServiceCategory.objects.create(name='Tecnologia')
        child1 = ServiceCategory.objects.create(name='Desenvolvimento', parent=parent)
        child2 = ServiceCategory.objects.create(name='Infraestrutura', parent=parent)
        
        # Verifica relacionamento direto
        self.assertEqual(child1.parent, parent)
        self.assertEqual(child2.parent, parent)
        
        # Verifica relacionamento reverso
        children = parent.children.all()
        self.assertEqual(children.count(), 2)
        self.assertIn(child1, children)
        self.assertIn(child2, children)

    def test_nested_categories(self):
        """Testa categorias aninhadas (múltiplos níveis)."""
        level1 = ServiceCategory.objects.create(name='Tecnologia')
        level2 = ServiceCategory.objects.create(name='Desenvolvimento', parent=level1)
        level3 = ServiceCategory.objects.create(name='Frontend', parent=level2)
        
        # Verifica hierarquia
        self.assertEqual(level3.parent, level2)
        self.assertEqual(level2.parent, level1)
        self.assertIsNone(level1.parent)
        
        # Verifica propriedades
        self.assertFalse(level1.is_subcategory)
        self.assertTrue(level2.is_subcategory)
        self.assertTrue(level3.is_subcategory)

    def test_is_active_default(self):
        """Testa que is_active padrão é True."""
        category = ServiceCategory.objects.create(name='Categoria Teste')
        self.assertTrue(category.is_active)
        
        category.is_active = False
        category.save()
        self.assertFalse(category.is_active)

    def test_str_representation_without_parent(self):
        """Testa representação string sem parent."""
        category = ServiceCategory.objects.create(name='Marketing')
        self.assertEqual(str(category), 'Marketing')

    def test_str_representation_with_parent(self):
        """Testa representação string com parent."""
        parent = ServiceCategory.objects.create(name='Tecnologia')
        child = ServiceCategory.objects.create(name='Desenvolvimento', parent=parent)
        self.assertEqual(str(child), 'Tecnologia > Desenvolvimento')

    def test_get_full_path_single_level(self):
        """Testa get_full_path para categoria sem parent."""
        category = ServiceCategory.objects.create(name='Marketing')
        self.assertEqual(category.get_full_path(), 'Marketing')

    def test_get_full_path_two_levels(self):
        """Testa get_full_path para dois níveis."""
        parent = ServiceCategory.objects.create(name='Tecnologia')
        child = ServiceCategory.objects.create(name='Desenvolvimento', parent=parent)
        self.assertEqual(child.get_full_path(), 'Tecnologia > Desenvolvimento')

    def test_get_full_path_three_levels(self):
        """Testa get_full_path para três níveis."""
        level1 = ServiceCategory.objects.create(name='Tecnologia')
        level2 = ServiceCategory.objects.create(name='Desenvolvimento', parent=level1)
        level3 = ServiceCategory.objects.create(name='Frontend', parent=level2)
        self.assertEqual(level3.get_full_path(), 'Tecnologia > Desenvolvimento > Frontend')

    def test_is_subcategory_property(self):
        """Testa a propriedade is_subcategory."""
        parent = ServiceCategory.objects.create(name='Tecnologia')
        child = ServiceCategory.objects.create(name='Desenvolvimento', parent=parent)
        
        self.assertFalse(parent.is_subcategory)
        self.assertTrue(child.is_subcategory)
        
        # Remove parent
        child.parent = None
        child.save()
        self.assertFalse(child.is_subcategory)

    def test_created_at_auto_now_add(self):
        """Testa que created_at é preenchido automaticamente."""
        before = timezone.now()
        category = ServiceCategory.objects.create(name='Categoria Teste')
        after = timezone.now()
        
        self.assertIsNotNone(category.created_at)
        self.assertGreaterEqual(category.created_at, before)
        self.assertLessEqual(category.created_at, after)

    def test_updated_at_auto_now(self):
        """Testa que updated_at é atualizado automaticamente."""
        category = ServiceCategory.objects.create(name='Categoria Teste')
        original_updated_at = category.updated_at
        
        # Aguarda um pouco para garantir diferença de tempo
        time.sleep(0.01)
        
        category.name = 'Categoria Atualizada'
        category.save()
        
        self.assertGreater(category.updated_at, original_updated_at)

    def test_soft_delete_functionality(self):
        """Testa funcionalidade de soft delete."""
        category = ServiceCategory.objects.create(name='Categoria Teste')
        category_id = category.id
        
        # Categoria está ativa
        self.assertIsNone(category.deleted_at)
        self.assertTrue(category.is_alive)
        self.assertFalse(category.is_deleted)
        self.assertEqual(ServiceCategory.objects.count(), 1)
        
        # Deleta (soft delete)
        category.delete()
        category.refresh_from_db()
        
        # Categoria está deletada
        self.assertIsNotNone(category.deleted_at)
        self.assertFalse(category.is_alive)
        self.assertTrue(category.is_deleted)
        self.assertEqual(ServiceCategory.objects.count(), 0)
        self.assertEqual(ServiceCategory.all_objects.count(), 1)
        self.assertEqual(ServiceCategory.deleted_objects.count(), 1)
        
        # Restaura
        category.restore()
        category.refresh_from_db()
        
        # Categoria está ativa novamente
        self.assertIsNone(category.deleted_at)
        self.assertTrue(category.is_alive)
        self.assertFalse(category.is_deleted)
        self.assertEqual(ServiceCategory.objects.count(), 1)

    def test_soft_delete_cascade_to_children(self):
        """Testa que soft delete não deleta automaticamente os filhos."""
        parent = ServiceCategory.objects.create(name='Tecnologia')
        child = ServiceCategory.objects.create(name='Desenvolvimento', parent=parent)
        
        # Deleta o parent
        parent.delete()
        child.refresh_from_db()
        
        # O child ainda existe, mas o parent está deletado
        self.assertIsNotNone(parent.deleted_at)
        # Nota: Com soft delete, o relacionamento ainda existe no banco
        # mas o parent está marcado como deletado
        self.assertIsNotNone(child.parent)

    def test_ordering_by_name(self):
        """Testa que ordenação padrão é por name."""
        category_c = ServiceCategory.objects.create(name='Categoria C')
        category_a = ServiceCategory.objects.create(name='Categoria A')
        category_b = ServiceCategory.objects.create(name='Categoria B')
        
        categories = list(ServiceCategory.objects.all())
        
        # Deve estar ordenado por name
        self.assertEqual(categories[0], category_a)
        self.assertEqual(categories[1], category_b)
        self.assertEqual(categories[2], category_c)

    def test_indexes_exist(self):
        """Testa que os índices foram criados corretamente."""
        category = ServiceCategory.objects.create(name='Categoria Teste')
        
        # Testa queries que usam os índices (verifica que não há erros)
        ServiceCategory.objects.filter(slug=category.slug).first()
        ServiceCategory.objects.filter(parent=category).first()
        ServiceCategory.objects.filter(is_active=True).first()
        ServiceCategory.objects.filter(deleted_at__isnull=True).first()
        
        # Verifica que os índices estão definidos no Meta
        index_names = [idx.name for idx in ServiceCategory._meta.indexes]
        self.assertIn('category_slug_idx', index_names)
        self.assertIn('category_parent_idx', index_names)
        self.assertIn('category_is_active_idx', index_names)
        self.assertIn('category_deleted_at_idx', index_names)

    def test_cascade_delete_when_parent_hard_deleted(self):
        """Testa que filhos são deletados quando parent é hard deleted."""
        parent = ServiceCategory.objects.create(name='Tecnologia')
        child = ServiceCategory.objects.create(name='Desenvolvimento', parent=parent)
        child_id = child.id
        
        # Hard delete do parent
        parent.hard_delete()
        
        # O child também deve ser deletado (CASCADE)
        self.assertFalse(ServiceCategory.all_objects.filter(id=child_id).exists())

    def test_name_max_length(self):
        """Testa que name tem limite de 100 caracteres."""
        # Nome válido
        category = ServiceCategory.objects.create(name='A' * 100)
        self.assertEqual(len(category.name), 100)
        
        # Nome muito longo (mais de 100 caracteres)
        long_name = 'A' * 101
        category.name = long_name
        with self.assertRaises((ValidationError, ValueError)):
            category.full_clean()

    def test_slug_max_length(self):
        """Testa que slug tem limite de 100 caracteres."""
        # Slug válido
        category = ServiceCategory.objects.create(name='Test Category')
        # O slug gerado deve ter no máximo 100 caracteres
        self.assertLessEqual(len(category.slug), 100)


class ServiceModelTestCase(TestCase):
    """Testes unitários para o modelo Service."""

    def setUp(self):
        """Cria dados de teste."""
        self.category = ServiceCategory.objects.create(name='Desenvolvimento Web')

    def test_create_service_with_minimal_fields(self):
        """Testa criação de serviço com campos mínimos."""
        service = Service.objects.create(
            category=self.category,
            name='Desenvolvimento de Site'
        )
        
        self.assertEqual(service.category, self.category)
        self.assertEqual(service.name, 'Desenvolvimento de Site')
        self.assertIsNone(service.description)
        self.assertTrue(service.is_active)
        self.assertIsNotNone(service.created_at)
        self.assertIsNotNone(service.updated_at)
        self.assertIsNone(service.deleted_at)

    def test_create_service_with_all_fields(self):
        """Testa criação de serviço com todos os campos."""
        service = Service.objects.create(
            category=self.category,
            name='Desenvolvimento de E-commerce',
            description='Desenvolvimento completo de loja virtual',
            is_active=True
        )
        
        self.assertEqual(service.category, self.category)
        self.assertEqual(service.name, 'Desenvolvimento de E-commerce')
        self.assertEqual(service.description, 'Desenvolvimento completo de loja virtual')
        self.assertTrue(service.is_active)

    def test_category_foreign_key_relationship(self):
        """Testa relacionamento ForeignKey com ServiceCategory."""
        service1 = Service.objects.create(
            category=self.category,
            name='Serviço 1'
        )
        service2 = Service.objects.create(
            category=self.category,
            name='Serviço 2'
        )
        
        # Verifica relacionamento direto
        self.assertEqual(service1.category, self.category)
        self.assertEqual(service2.category, self.category)
        
        # Verifica relacionamento reverso
        services = self.category.services.all()
        self.assertEqual(services.count(), 2)
        self.assertIn(service1, services)
        self.assertIn(service2, services)

    def test_category_is_required(self):
        """Testa que category é obrigatório."""
        with self.assertRaises((IntegrityError, ValueError)):
            Service.objects.create(name='Serviço sem categoria')

    def test_name_is_required(self):
        """Testa que name é obrigatório."""
        # Tenta criar serviço sem name (deve falhar na validação)
        service = Service(category=self.category)
        with self.assertRaises(ValidationError):
            service.full_clean()
        
        # Com name, deve funcionar
        service.name = 'Serviço Teste'
        service.full_clean()  # Não deve levantar exceção

    def test_description_is_optional(self):
        """Testa que description é opcional."""
        service1 = Service.objects.create(
            category=self.category,
            name='Serviço 1'
        )
        self.assertIsNone(service1.description)
        
        service2 = Service.objects.create(
            category=self.category,
            name='Serviço 2',
            description='Descrição do serviço'
        )
        self.assertEqual(service2.description, 'Descrição do serviço')

    def test_is_active_default(self):
        """Testa que is_active padrão é True."""
        service = Service.objects.create(
            category=self.category,
            name='Serviço Teste'
        )
        self.assertTrue(service.is_active)
        
        service.is_active = False
        service.save()
        self.assertFalse(service.is_active)

    def test_name_max_length(self):
        """Testa que name tem limite de 200 caracteres."""
        # Nome válido
        service = Service.objects.create(
            category=self.category,
            name='A' * 200
        )
        self.assertEqual(len(service.name), 200)
        
        # Nome muito longo (mais de 200 caracteres)
        long_name = 'A' * 201
        service.name = long_name
        with self.assertRaises((ValidationError, ValueError)):
            service.full_clean()

    def test_str_representation(self):
        """Testa a representação string do modelo."""
        service = Service.objects.create(
            category=self.category,
            name='Desenvolvimento de App'
        )
        expected = f"Desenvolvimento de App ({self.category.name})"
        self.assertEqual(str(service), expected)

    def test_created_at_auto_now_add(self):
        """Testa que created_at é preenchido automaticamente."""
        before = timezone.now()
        service = Service.objects.create(
            category=self.category,
            name='Serviço Teste'
        )
        after = timezone.now()
        
        self.assertIsNotNone(service.created_at)
        self.assertGreaterEqual(service.created_at, before)
        self.assertLessEqual(service.created_at, after)

    def test_updated_at_auto_now(self):
        """Testa que updated_at é atualizado automaticamente."""
        service = Service.objects.create(
            category=self.category,
            name='Serviço Teste'
        )
        original_updated_at = service.updated_at
        
        # Aguarda um pouco para garantir diferença de tempo
        time.sleep(0.01)
        
        service.name = 'Serviço Atualizado'
        service.save()
        
        self.assertGreater(service.updated_at, original_updated_at)

    def test_soft_delete_functionality(self):
        """Testa funcionalidade de soft delete."""
        service = Service.objects.create(
            category=self.category,
            name='Serviço Teste'
        )
        service_id = service.id
        
        # Serviço está ativo
        self.assertIsNone(service.deleted_at)
        self.assertTrue(service.is_alive)
        self.assertFalse(service.is_deleted)
        self.assertEqual(Service.objects.count(), 1)
        
        # Deleta (soft delete)
        service.delete()
        service.refresh_from_db()
        
        # Serviço está deletado
        self.assertIsNotNone(service.deleted_at)
        self.assertFalse(service.is_alive)
        self.assertTrue(service.is_deleted)
        self.assertEqual(Service.objects.count(), 0)
        self.assertEqual(Service.all_objects.count(), 1)
        self.assertEqual(Service.deleted_objects.count(), 1)
        
        # Restaura
        service.restore()
        service.refresh_from_db()
        
        # Serviço está ativo novamente
        self.assertIsNone(service.deleted_at)
        self.assertTrue(service.is_alive)
        self.assertFalse(service.is_deleted)
        self.assertEqual(Service.objects.count(), 1)

    def test_ordering_by_category_and_name(self):
        """Testa que ordenação padrão é por category e name."""
        category_a = ServiceCategory.objects.create(name='Categoria A')
        category_b = ServiceCategory.objects.create(name='Categoria B')
        
        # Cria serviços em ordem diferente
        service_b2 = Service.objects.create(category=category_b, name='Serviço B2')
        service_a1 = Service.objects.create(category=category_a, name='Serviço A1')
        service_b1 = Service.objects.create(category=category_b, name='Serviço B1')
        service_a2 = Service.objects.create(category=category_a, name='Serviço A2')
        
        services = list(Service.objects.all())
        
        # Deve estar ordenado por category primeiro, depois por name
        self.assertEqual(services[0], service_a1)
        self.assertEqual(services[1], service_a2)
        self.assertEqual(services[2], service_b1)
        self.assertEqual(services[3], service_b2)

    def test_indexes_exist(self):
        """Testa que os índices foram criados corretamente."""
        service = Service.objects.create(
            category=self.category,
            name='Serviço Teste'
        )
        
        # Testa queries que usam os índices
        Service.objects.filter(category=self.category).first()
        Service.objects.filter(is_active=True).first()
        Service.objects.filter(deleted_at__isnull=True).first()
        
        # Verifica que os índices estão definidos no Meta
        index_names = [idx.name for idx in Service._meta.indexes]
        self.assertIn('service_category_idx', index_names)
        self.assertIn('service_is_active_idx', index_names)
        self.assertIn('service_deleted_at_idx', index_names)

    def test_cascade_delete_when_category_hard_deleted(self):
        """Testa que serviços são deletados quando categoria é hard deleted."""
        service = Service.objects.create(
            category=self.category,
            name='Serviço Teste'
        )
        service_id = service.id
        
        # Hard delete da categoria
        self.category.hard_delete()
        
        # O serviço também deve ser deletado (CASCADE)
        self.assertFalse(Service.all_objects.filter(id=service_id).exists())

    def test_multiple_services_per_category(self):
        """Testa que uma categoria pode ter múltiplos serviços."""
        service1 = Service.objects.create(category=self.category, name='Serviço 1')
        service2 = Service.objects.create(category=self.category, name='Serviço 2')
        service3 = Service.objects.create(category=self.category, name='Serviço 3')
        
        self.assertEqual(self.category.services.count(), 3)

    def test_services_with_different_categories(self):
        """Testa que serviços podem pertencer a categorias diferentes."""
        category1 = ServiceCategory.objects.create(name='Categoria 1')
        category2 = ServiceCategory.objects.create(name='Categoria 2')
        
        service1 = Service.objects.create(category=category1, name='Serviço 1')
        service2 = Service.objects.create(category=category2, name='Serviço 2')
        
        self.assertEqual(service1.category, category1)
        self.assertEqual(service2.category, category2)
        self.assertNotEqual(service1.category, service2.category)

    def test_filter_services_by_category(self):
        """Testa filtro de serviços por categoria."""
        category1 = ServiceCategory.objects.create(name='Categoria 1')
        category2 = ServiceCategory.objects.create(name='Categoria 2')
        
        service1 = Service.objects.create(category=category1, name='Serviço 1')
        service2 = Service.objects.create(category=category1, name='Serviço 2')
        service3 = Service.objects.create(category=category2, name='Serviço 3')
        
        services_cat1 = Service.objects.filter(category=category1)
        self.assertEqual(services_cat1.count(), 2)
        self.assertIn(service1, services_cat1)
        self.assertIn(service2, services_cat1)
        self.assertNotIn(service3, services_cat1)

    def test_filter_services_by_is_active(self):
        """Testa filtro de serviços por is_active."""
        service_active = Service.objects.create(
            category=self.category,
            name='Serviço Ativo',
            is_active=True
        )
        service_inactive = Service.objects.create(
            category=self.category,
            name='Serviço Inativo',
            is_active=False
        )
        
        active_services = Service.objects.filter(is_active=True)
        self.assertIn(service_active, active_services)
        self.assertNotIn(service_inactive, active_services)
