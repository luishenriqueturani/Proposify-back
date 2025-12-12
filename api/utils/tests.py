"""
Testes para Soft Delete functionality.
"""
from django.test import TransactionTestCase
from django.utils import timezone
from django.db import models, connection
from .models import SoftDeleteModel, SoftDeleteMixin


# Modelo de teste usando SoftDeleteModel
class TestModel(SoftDeleteModel):
    """Modelo de teste para Soft Delete."""
    name = models.CharField(max_length=100)  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)  # type: ignore

    class Meta:
        app_label = 'utils'
        db_table = 'utils_testmodel'


# Modelo de teste usando SoftDeleteMixin
class TestMixinModel(SoftDeleteMixin, models.Model):
    """Modelo de teste usando SoftDeleteMixin."""
    name = models.CharField(max_length=100)  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)  # type: ignore

    class Meta:
        app_label = 'utils'
        db_table = 'utils_testmixinmodel'


class SoftDeleteModelTestCase(TransactionTestCase):
    """Testes para SoftDeleteModel."""

    def setUp(self):
        """Cria dados de teste."""
        # Cria as tabelas manualmente para os testes
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(TestModel)
        
        self.obj1 = TestModel.objects.create(name='Objeto 1')
        self.obj2 = TestModel.objects.create(name='Objeto 2')
        self.obj3 = TestModel.objects.create(name='Objeto 3')
    
    def tearDown(self):
        """Remove as tabelas após os testes."""
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(TestModel)

    def test_objects_excludes_deleted(self):
        """Testa se objects exclui registros deletados."""
        # Todos os objetos devem estar visíveis
        self.assertEqual(TestModel.objects.count(), 3)
        
        # Deleta um objeto
        self.obj1.delete()
        
        # Agora deve ter apenas 2 objetos visíveis
        self.assertEqual(TestModel.objects.count(), 2)
        self.assertNotIn(self.obj1, TestModel.objects.all())
        self.assertIn(self.obj2, TestModel.objects.all())
        self.assertIn(self.obj3, TestModel.objects.all())

    def test_all_objects_includes_deleted(self):
        """Testa se all_objects inclui registros deletados."""
        # Deleta um objeto
        self.obj1.delete()
        
        # all_objects deve incluir todos
        self.assertEqual(TestModel.all_objects.count(), 3)
        self.assertIn(self.obj1, TestModel.all_objects.all())

    def test_deleted_objects_only_deleted(self):
        """Testa se deleted_objects retorna apenas deletados."""
        # Nenhum deletado ainda
        self.assertEqual(TestModel.deleted_objects.count(), 0)
        
        # Deleta dois objetos
        self.obj1.delete()
        self.obj2.delete()
        
        # deleted_objects deve retornar apenas os deletados
        self.assertEqual(TestModel.deleted_objects.count(), 2)
        self.assertIn(self.obj1, TestModel.deleted_objects.all())
        self.assertIn(self.obj2, TestModel.deleted_objects.all())
        self.assertNotIn(self.obj3, TestModel.deleted_objects.all())

    def test_delete_sets_deleted_at(self):
        """Testa se delete() define deleted_at."""
        self.assertIsNone(self.obj1.deleted_at)
        
        self.obj1.delete()
        
        self.assertIsNotNone(self.obj1.deleted_at)
        self.assertIsInstance(self.obj1.deleted_at, timezone.datetime)  # type: ignore

    def test_hard_delete_removes_from_db(self):
        """Testa se hard_delete() remove do banco."""
        obj_id = self.obj1.id
        
        self.obj1.hard_delete()
        
        # Não deve existir mais no banco
        self.assertFalse(TestModel.all_objects.filter(id=obj_id).exists())

    def test_restore_clears_deleted_at(self):
        """Testa se restore() limpa deleted_at."""
        # Deleta o objeto
        self.obj1.delete()
        self.assertIsNotNone(self.obj1.deleted_at)
        
        # Restaura
        result = self.obj1.restore()
        
        self.assertTrue(result)
        self.assertIsNone(self.obj1.deleted_at)
        # Deve estar visível novamente
        self.assertIn(self.obj1, TestModel.objects.all())

    def test_restore_already_alive_returns_false(self):
        """Testa se restore() em objeto não deletado retorna False."""
        result = self.obj1.restore()
        self.assertFalse(result)

    def test_is_deleted_property(self):
        """Testa a propriedade is_deleted."""
        self.assertFalse(self.obj1.is_deleted)
        
        self.obj1.delete()
        
        self.assertTrue(self.obj1.is_deleted)

    def test_is_alive_property(self):
        """Testa a propriedade is_alive."""
        self.assertTrue(self.obj1.is_alive)
        
        self.obj1.delete()
        
        self.assertFalse(self.obj1.is_alive)

    def test_queryset_delete(self):
        """Testa delete() em queryset."""
        # Deleta múltiplos objetos
        TestModel.objects.filter(name__in=['Objeto 1', 'Objeto 2']).delete()
        
        # Apenas um deve estar visível
        self.assertEqual(TestModel.objects.count(), 1)
        self.assertEqual(TestModel.deleted_objects.count(), 2)

    def test_queryset_restore(self):
        """Testa restore() em queryset."""
        # Deleta dois objetos
        self.obj1.delete()
        self.obj2.delete()
        
        # Restaura todos os deletados
        TestModel.deleted_objects.all().restore()  # type: ignore
        
        # Todos devem estar visíveis novamente
        self.assertEqual(TestModel.objects.count(), 3)

    def test_queryset_hard_delete(self):
        """Testa hard_delete() em queryset."""
        # Deleta um objeto
        self.obj1.delete()
        obj_id = self.obj1.id
        
        # Hard delete em queryset
        TestModel.deleted_objects.all().hard_delete()  # type: ignore
        
        # Não deve existir mais
        self.assertFalse(TestModel.all_objects.filter(id=obj_id).exists())

    def test_queryset_alive(self):
        """Testa método alive() do queryset."""
        self.obj1.delete()
        
        # alive() deve retornar apenas não deletados
        alive = TestModel.all_objects.all().alive()  # type: ignore
        self.assertEqual(alive.count(), 2)
        self.assertNotIn(self.obj1, alive)

    def test_queryset_dead(self):
        """Testa método dead() do queryset."""
        self.obj1.delete()
        
        # dead() deve retornar apenas deletados
        dead = TestModel.all_objects.all().dead()  # type: ignore
        self.assertEqual(dead.count(), 1)
        self.assertIn(self.obj1, dead)


class SoftDeleteMixinTestCase(TransactionTestCase):
    """Testes para SoftDeleteMixin."""

    def setUp(self):
        """Cria dados de teste."""
        # Cria as tabelas manualmente para os testes
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(TestMixinModel)
        
        self.obj1 = TestMixinModel.objects.create(name='Objeto 1')
    
    def tearDown(self):
        """Remove as tabelas após os testes."""
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(TestMixinModel)

    def test_mixin_works_same_as_model(self):
        """Testa se o mixin funciona igual ao modelo."""
        self.assertIsNone(self.obj1.deleted_at)
        
        self.obj1.delete()
        
        self.assertIsNotNone(self.obj1.deleted_at)
        self.assertEqual(TestMixinModel.objects.count(), 0)
        self.assertEqual(TestMixinModel.deleted_objects.count(), 1)
