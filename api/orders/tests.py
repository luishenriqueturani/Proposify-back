"""
Testes unitários para o app orders.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import time
from datetime import timedelta
from api.orders.models import Order, Proposal
from api.orders.enums import OrderStatus, ProposalStatus
from api.accounts.models import User, ClientProfile, ProviderProfile
from api.accounts.enums import UserType
from api.services.models import ServiceCategory, Service


class OrderModelTestCase(TestCase):
    """Testes unitários para o modelo Order."""

    def setUp(self):
        """Cria dados de teste."""
        # Cria usuário cliente
        self.client_user = User.objects.create_user(  # type: ignore[call-arg]
            email='client@example.com',
            first_name='Client',
            last_name='User',
            password='testpass123',
            user_type=UserType.CLIENT.value
        )
        self.client_profile = ClientProfile.objects.create(user=self.client_user)
        
        # Cria categoria e serviço
        self.category = ServiceCategory.objects.create(name='Desenvolvimento Web')
        self.service = Service.objects.create(
            category=self.category,
            name='Desenvolvimento de Site'
        )
        
        # Data futura para deadline
        self.future_deadline = timezone.now() + timedelta(days=30)

    def test_create_order_with_all_fields(self):
        """Testa criação de pedido com todos os campos."""
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Desenvolvimento de E-commerce',
            description='Preciso de um e-commerce completo',
            budget_min=Decimal('5000.00'),
            budget_max=Decimal('10000.00'),
            deadline=self.future_deadline,
            status=OrderStatus.PENDING.value
        )
        
        self.assertEqual(order.client, self.client_profile)
        self.assertEqual(order.service, self.service)
        self.assertEqual(order.title, 'Desenvolvimento de E-commerce')
        self.assertEqual(order.description, 'Preciso de um e-commerce completo')
        self.assertEqual(order.budget_min, Decimal('5000.00'))
        self.assertEqual(order.budget_max, Decimal('10000.00'))
        self.assertEqual(order.deadline, self.future_deadline)
        self.assertEqual(order.status, OrderStatus.PENDING.value)
        self.assertIsNotNone(order.created_at)
        self.assertIsNotNone(order.updated_at)
        self.assertIsNone(order.deleted_at)

    def test_order_status_default_is_pending(self):
        """Testa que status padrão é PENDING."""
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição do pedido',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline
        )
        self.assertEqual(order.status, OrderStatus.PENDING.value)
        self.assertTrue(order.is_pending)

    def test_order_status_choices(self):
        """Testa que status aceita apenas valores válidos."""
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline
        )
        
        # Testa todos os status válidos
        order.status = OrderStatus.PENDING.value
        order.save()
        self.assertEqual(order.status, OrderStatus.PENDING.value)
        self.assertTrue(order.is_pending)
        
        order.status = OrderStatus.ACCEPTED.value
        order.save()
        self.assertEqual(order.status, OrderStatus.ACCEPTED.value)
        self.assertTrue(order.is_accepted)
        
        order.status = OrderStatus.IN_PROGRESS.value
        order.save()
        self.assertEqual(order.status, OrderStatus.IN_PROGRESS.value)
        
        order.status = OrderStatus.COMPLETED.value
        order.save()
        self.assertEqual(order.status, OrderStatus.COMPLETED.value)
        self.assertTrue(order.is_completed)
        
        order.status = OrderStatus.CANCELLED.value
        order.save()
        self.assertEqual(order.status, OrderStatus.CANCELLED.value)
        self.assertTrue(order.is_cancelled)

    def test_is_pending_property(self):
        """Testa a propriedade is_pending."""
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline,
            status=OrderStatus.PENDING.value
        )
        self.assertTrue(order.is_pending)
        
        order.status = OrderStatus.ACCEPTED.value
        order.save()
        self.assertFalse(order.is_pending)

    def test_is_accepted_property(self):
        """Testa a propriedade is_accepted."""
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline,
            status=OrderStatus.ACCEPTED.value
        )
        self.assertTrue(order.is_accepted)
        
        order.status = OrderStatus.PENDING.value
        order.save()
        self.assertFalse(order.is_accepted)

    def test_is_completed_property(self):
        """Testa a propriedade is_completed."""
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline,
            status=OrderStatus.COMPLETED.value
        )
        self.assertTrue(order.is_completed)
        
        order.status = OrderStatus.PENDING.value
        order.save()
        self.assertFalse(order.is_completed)

    def test_is_cancelled_property(self):
        """Testa a propriedade is_cancelled."""
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline,
            status=OrderStatus.CANCELLED.value
        )
        self.assertTrue(order.is_cancelled)
        
        order.status = OrderStatus.PENDING.value
        order.save()
        self.assertFalse(order.is_cancelled)

    def test_can_be_cancelled_method(self):
        """Testa o método can_be_cancelled."""
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline
        )
        
        # PENDING pode ser cancelado
        order.status = OrderStatus.PENDING.value
        order.save()
        self.assertTrue(order.can_be_cancelled())
        
        # ACCEPTED pode ser cancelado
        order.status = OrderStatus.ACCEPTED.value
        order.save()
        self.assertTrue(order.can_be_cancelled())
        
        # IN_PROGRESS não pode ser cancelado
        order.status = OrderStatus.IN_PROGRESS.value
        order.save()
        self.assertFalse(order.can_be_cancelled())
        
        # COMPLETED não pode ser cancelado
        order.status = OrderStatus.COMPLETED.value
        order.save()
        self.assertFalse(order.can_be_cancelled())
        
        # CANCELLED não pode ser cancelado (já está cancelado)
        order.status = OrderStatus.CANCELLED.value
        order.save()
        self.assertFalse(order.can_be_cancelled())

    def test_client_foreign_key_relationship(self):
        """Testa relacionamento ForeignKey com ClientProfile."""
        order1 = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido 1',
            description='Descrição 1',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline
        )
        order2 = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido 2',
            description='Descrição 2',
            budget_min=Decimal('2000.00'),
            budget_max=Decimal('3000.00'),
            deadline=self.future_deadline
        )
        
        # Verifica relacionamento direto
        self.assertEqual(order1.client, self.client_profile)
        self.assertEqual(order2.client, self.client_profile)
        
        # Verifica relacionamento reverso
        orders = self.client_profile.orders.all()
        self.assertEqual(orders.count(), 2)
        self.assertIn(order1, orders)
        self.assertIn(order2, orders)

    def test_service_foreign_key_relationship(self):
        """Testa relacionamento ForeignKey com Service."""
        order1 = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido 1',
            description='Descrição 1',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline
        )
        order2 = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido 2',
            description='Descrição 2',
            budget_min=Decimal('2000.00'),
            budget_max=Decimal('3000.00'),
            deadline=self.future_deadline
        )
        
        # Verifica relacionamento direto
        self.assertEqual(order1.service, self.service)
        self.assertEqual(order2.service, self.service)
        
        # Verifica relacionamento reverso
        orders = self.service.orders.all()
        self.assertEqual(orders.count(), 2)
        self.assertIn(order1, orders)
        self.assertIn(order2, orders)

    def test_budget_min_less_than_or_equal_budget_max(self):
        """Testa que budget_min deve ser menor ou igual a budget_max."""
        # Caso válido: budget_min < budget_max
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline
        )
        self.assertLessEqual(order.budget_min, order.budget_max)
        
        # Caso válido: budget_min == budget_max
        order.budget_min = Decimal('1500.00')
        order.budget_max = Decimal('1500.00')
        order.save()
        self.assertEqual(order.budget_min, order.budget_max)

    def test_title_max_length(self):
        """Testa que title tem limite de 200 caracteres."""
        # Título válido
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='A' * 200,
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline
        )
        self.assertEqual(len(order.title), 200)
        
        # Título muito longo (mais de 200 caracteres)
        long_title = 'A' * 201
        order.title = long_title
        with self.assertRaises((ValidationError, ValueError)):
            order.full_clean()

    def test_description_is_required(self):
        """Testa que description é obrigatório."""
        order = Order(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline
        )
        with self.assertRaises(ValidationError):
            order.full_clean()
        
        # Com description, deve funcionar
        order.description = 'Descrição do pedido'
        order.full_clean()  # Não deve levantar exceção

    def test_str_representation(self):
        """Testa a representação string do modelo."""
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline,
            status=OrderStatus.PENDING.value
        )
        expected = f"Pedido #{order.id}: Pedido Teste ({OrderStatus.PENDING.label})"
        self.assertEqual(str(order), expected)

    def test_created_at_auto_now_add(self):
        """Testa que created_at é preenchido automaticamente."""
        before = timezone.now()
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline
        )
        after = timezone.now()
        
        self.assertIsNotNone(order.created_at)
        self.assertGreaterEqual(order.created_at, before)
        self.assertLessEqual(order.created_at, after)

    def test_updated_at_auto_now(self):
        """Testa que updated_at é atualizado automaticamente."""
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline
        )
        original_updated_at = order.updated_at
        
        # Aguarda um pouco para garantir diferença de tempo
        time.sleep(0.01)
        
        order.title = 'Pedido Atualizado'
        order.save()
        
        self.assertGreater(order.updated_at, original_updated_at)

    def test_soft_delete_functionality(self):
        """Testa funcionalidade de soft delete."""
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline
        )

        # Pedido está ativo
        self.assertIsNone(order.deleted_at)
        self.assertTrue(order.is_alive)
        self.assertFalse(order.is_deleted)
        self.assertEqual(Order.objects.count(), 1)
        
        # Deleta (soft delete)
        order.delete()
        order.refresh_from_db()
        
        # Pedido está deletado
        self.assertIsNotNone(order.deleted_at)
        self.assertFalse(order.is_alive)
        self.assertTrue(order.is_deleted)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Order.all_objects.count(), 1)
        self.assertEqual(Order.deleted_objects.count(), 1)
        
        # Restaura
        order.restore()
        order.refresh_from_db()
        
        # Pedido está ativo novamente
        self.assertIsNone(order.deleted_at)
        self.assertTrue(order.is_alive)
        self.assertFalse(order.is_deleted)
        self.assertEqual(Order.objects.count(), 1)

    def test_ordering_by_created_at_desc(self):
        """Testa que ordenação padrão é por created_at descendente."""
        order1 = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido 1',
            description='Descrição 1',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline
        )
        
        time.sleep(0.01)
        
        order2 = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido 2',
            description='Descrição 2',
            budget_min=Decimal('2000.00'),
            budget_max=Decimal('3000.00'),
            deadline=self.future_deadline
        )
        
        orders = list(Order.objects.all())
        
        # order2 é mais recente, deve aparecer primeiro
        self.assertEqual(orders[0], order2)
        self.assertEqual(orders[1], order1)

    def test_indexes_exist(self):
        """Testa que os índices foram criados corretamente."""
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline
        )
        
        # Testa queries que usam os índices (verifica que não há erros)
        Order.objects.filter(client=self.client_profile).first()
        Order.objects.filter(service=self.service).first()
        Order.objects.filter(status=OrderStatus.PENDING.value).first()
        Order.objects.filter(deadline__gte=timezone.now()).first()
        Order.objects.filter(deleted_at__isnull=True).first()
        
        # Verifica que os índices estão definidos no Meta
        index_names = [idx.name for idx in Order._meta.indexes]
        self.assertIn('order_client_idx', index_names)
        self.assertIn('order_service_idx', index_names)
        self.assertIn('order_status_idx', index_names)
        self.assertIn('order_deadline_idx', index_names)
        self.assertIn('order_deleted_at_idx', index_names)

    def test_cascade_delete_when_client_hard_deleted(self):
        """Testa que pedidos são deletados quando cliente é hard deleted."""
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline
        )
        order_id = order.id
        
        # Hard delete do cliente
        self.client_profile.hard_delete()
        
        # O pedido também deve ser deletado (CASCADE)
        self.assertFalse(Order.all_objects.filter(id=order_id).exists())

    def test_cascade_delete_when_service_hard_deleted(self):
        """Testa que pedidos são deletados quando serviço é hard deleted."""
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline
        )
        order_id = order.id
        
        # Hard delete do serviço
        self.service.hard_delete()
        
        # O pedido também deve ser deletado (CASCADE)
        self.assertFalse(Order.all_objects.filter(id=order_id).exists())

    def test_budget_decimal_precision(self):
        """Testa precisão decimal dos campos budget."""
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1234.56'),
            budget_max=Decimal('5678.90'),
            deadline=self.future_deadline
        )
        
        # Verifica que os valores decimais são preservados
        self.assertEqual(order.budget_min, Decimal('1234.56'))
        self.assertEqual(order.budget_max, Decimal('5678.90'))

    def test_deadline_is_required(self):
        """Testa que deadline é obrigatório."""
        order = Order(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00')
        )
        with self.assertRaises(ValidationError):
            order.full_clean()
        
        # Com deadline, deve funcionar
        order.deadline = self.future_deadline
        order.full_clean()  # Não deve levantar exceção


class ProposalModelTestCase(TestCase):
    """Testes unitários para o modelo Proposal."""

    def setUp(self):
        """Cria dados de teste."""
        # Cria usuário cliente
        self.client_user = User.objects.create_user(  # type: ignore[call-arg]
            email='client@example.com',
            first_name='Client',
            last_name='User',
            password='testpass123',
            user_type=UserType.CLIENT.value
        )
        self.client_profile = ClientProfile.objects.create(user=self.client_user)

        # Cria usuário prestador
        self.provider_user = User.objects.create_user(  # type: ignore[call-arg]
            email='provider@example.com',
            first_name='Provider',
            last_name='User',
            password='testpass123',
            user_type=UserType.PROVIDER.value
        )
        self.provider_profile = ProviderProfile.objects.create(user=self.provider_user)

        # Cria categoria e serviço
        self.category = ServiceCategory.objects.create(name='Desenvolvimento Web')
        self.service = Service.objects.create(
            category=self.category,
            name='Desenvolvimento de Site'
        )

        # Cria pedido
        self.future_deadline = timezone.now() + timedelta(days=30)
        self.order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Desenvolvimento de E-commerce',
            description='Preciso de um e-commerce completo',
            budget_min=Decimal('5000.00'),
            budget_max=Decimal('10000.00'),
            deadline=self.future_deadline
        )

        # Data futura para expires_at
        self.future_expires_at = timezone.now() + timedelta(days=7)

    def test_create_proposal_with_all_fields(self):
        """Testa criação de proposta com todos os campos."""
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Posso fazer este projeto em 30 dias',
            price=Decimal('7500.00'),
            estimated_days=30,
            status=ProposalStatus.PENDING.value,
            expires_at=self.future_expires_at
        )

        self.assertEqual(proposal.order, self.order)
        self.assertEqual(proposal.provider, self.provider_profile)
        self.assertEqual(proposal.message, 'Posso fazer este projeto em 30 dias')
        self.assertEqual(proposal.price, Decimal('7500.00'))
        self.assertEqual(proposal.estimated_days, 30)
        self.assertEqual(proposal.status, ProposalStatus.PENDING.value)
        self.assertEqual(proposal.expires_at, self.future_expires_at)
        self.assertIsNotNone(proposal.created_at)
        self.assertIsNotNone(proposal.updated_at)
        self.assertIsNone(proposal.deleted_at)

    def test_proposal_status_default_is_pending(self):
        """Testa que status padrão é PENDING."""
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem da proposta',
            price=Decimal('5000.00'),
            estimated_days=20
        )
        self.assertEqual(proposal.status, ProposalStatus.PENDING.value)
        self.assertTrue(proposal.is_pending)

    def test_proposal_status_choices(self):
        """Testa que status aceita apenas valores válidos."""
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('5000.00'),
            estimated_days=20
        )

        # Testa todos os status válidos
        proposal.status = ProposalStatus.PENDING.value
        proposal.save()
        self.assertEqual(proposal.status, ProposalStatus.PENDING.value)
        self.assertTrue(proposal.is_pending)

        proposal.status = ProposalStatus.ACCEPTED.value
        proposal.save()
        self.assertEqual(proposal.status, ProposalStatus.ACCEPTED.value)
        self.assertTrue(proposal.is_accepted)

        proposal.status = ProposalStatus.DECLINED.value
        proposal.save()
        self.assertEqual(proposal.status, ProposalStatus.DECLINED.value)

        proposal.status = ProposalStatus.EXPIRED.value
        proposal.save()
        self.assertEqual(proposal.status, ProposalStatus.EXPIRED.value)

    def test_is_pending_property(self):
        """Testa a propriedade is_pending."""
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('5000.00'),
            estimated_days=20,
            status=ProposalStatus.PENDING.value
        )
        self.assertTrue(proposal.is_pending)

        proposal.status = ProposalStatus.ACCEPTED.value
        proposal.save()
        self.assertFalse(proposal.is_pending)

    def test_is_accepted_property(self):
        """Testa a propriedade is_accepted."""
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('5000.00'),
            estimated_days=20,
            status=ProposalStatus.ACCEPTED.value
        )
        self.assertTrue(proposal.is_accepted)

        proposal.status = ProposalStatus.PENDING.value
        proposal.save()
        self.assertFalse(proposal.is_accepted)

    def test_is_expired_property_with_expires_at(self):
        """Testa a propriedade is_expired quando expires_at está definido."""
        # Proposta com expires_at no futuro (não expirada)
        future_expires = timezone.now() + timedelta(days=7)
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('5000.00'),
            estimated_days=20,
            expires_at=future_expires
        )
        self.assertFalse(proposal.is_expired)

        # Proposta com expires_at no passado (expirada)
        past_expires = timezone.now() - timedelta(days=1)
        proposal.expires_at = past_expires
        proposal.save()
        self.assertTrue(proposal.is_expired)

    def test_is_expired_property_without_expires_at(self):
        """Testa a propriedade is_expired quando expires_at é None."""
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('5000.00'),
            estimated_days=20,
            expires_at=None
        )
        self.assertFalse(proposal.is_expired)

    def test_can_be_accepted_method(self):
        """Testa o método can_be_accepted."""
        # Proposta PENDING sem expires_at pode ser aceita
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('5000.00'),
            estimated_days=20,
            status=ProposalStatus.PENDING.value,
            expires_at=None
        )
        self.assertTrue(proposal.can_be_accepted())

        # Proposta PENDING com expires_at no futuro pode ser aceita
        future_expires = timezone.now() + timedelta(days=7)
        proposal.expires_at = future_expires
        proposal.save()
        self.assertTrue(proposal.can_be_accepted())

        # Proposta PENDING com expires_at no passado NÃO pode ser aceita
        past_expires = timezone.now() - timedelta(days=1)
        proposal.expires_at = past_expires
        proposal.save()
        self.assertFalse(proposal.can_be_accepted())

        # Proposta ACCEPTED não pode ser aceita novamente
        proposal.status = ProposalStatus.ACCEPTED.value
        proposal.expires_at = future_expires
        proposal.save()
        self.assertFalse(proposal.can_be_accepted())

        # Proposta DECLINED não pode ser aceita
        proposal.status = ProposalStatus.DECLINED.value
        proposal.save()
        self.assertFalse(proposal.can_be_accepted())

        # Proposta EXPIRED não pode ser aceita
        proposal.status = ProposalStatus.EXPIRED.value
        proposal.save()
        self.assertFalse(proposal.can_be_accepted())

    def test_can_be_declined_method(self):
        """Testa o método can_be_declined."""
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('5000.00'),
            estimated_days=20
        )

        # PENDING pode ser recusada
        proposal.status = ProposalStatus.PENDING.value
        proposal.save()
        self.assertTrue(proposal.can_be_declined())

        # ACCEPTED não pode ser recusada
        proposal.status = ProposalStatus.ACCEPTED.value
        proposal.save()
        self.assertFalse(proposal.can_be_declined())

        # DECLINED não pode ser recusada novamente
        proposal.status = ProposalStatus.DECLINED.value
        proposal.save()
        self.assertFalse(proposal.can_be_declined())

        # EXPIRED não pode ser recusada
        proposal.status = ProposalStatus.EXPIRED.value
        proposal.save()
        self.assertFalse(proposal.can_be_declined())

    def test_order_foreign_key_relationship(self):
        """Testa relacionamento ForeignKey com Order."""
        proposal1 = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Proposta 1',
            price=Decimal('5000.00'),
            estimated_days=20
        )
        proposal2 = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Proposta 2',
            price=Decimal('6000.00'),
            estimated_days=25
        )

        # Verifica relacionamento direto
        self.assertEqual(proposal1.order, self.order)
        self.assertEqual(proposal2.order, self.order)

        # Verifica relacionamento reverso
        proposals = self.order.proposals.all()
        self.assertEqual(proposals.count(), 2)
        self.assertIn(proposal1, proposals)
        self.assertIn(proposal2, proposals)

    def test_provider_foreign_key_relationship(self):
        """Testa relacionamento ForeignKey com ProviderProfile."""
        proposal1 = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Proposta 1',
            price=Decimal('5000.00'),
            estimated_days=20
        )
        proposal2 = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Proposta 2',
            price=Decimal('6000.00'),
            estimated_days=25
        )

        # Verifica relacionamento direto
        self.assertEqual(proposal1.provider, self.provider_profile)
        self.assertEqual(proposal2.provider, self.provider_profile)

        # Verifica relacionamento reverso
        proposals = self.provider_profile.proposals.all()
        self.assertEqual(proposals.count(), 2)
        self.assertIn(proposal1, proposals)
        self.assertIn(proposal2, proposals)

    def test_message_is_required(self):
        """Testa que message é obrigatório."""
        proposal = Proposal(
            order=self.order,
            provider=self.provider_profile,
            price=Decimal('5000.00'),
            estimated_days=20
        )
        with self.assertRaises(ValidationError):
            proposal.full_clean()

        # Com message, deve funcionar
        proposal.message = 'Mensagem da proposta'
        proposal.full_clean()  # Não deve levantar exceção

    def test_price_is_required(self):
        """Testa que price é obrigatório."""
        proposal = Proposal(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            estimated_days=20
        )
        with self.assertRaises(ValidationError):
            proposal.full_clean()

        # Com price, deve funcionar
        proposal.price = Decimal('5000.00')
        proposal.full_clean()  # Não deve levantar exceção

    def test_estimated_days_is_required(self):
        """Testa que estimated_days é obrigatório."""
        proposal = Proposal(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('5000.00')
        )
        with self.assertRaises(ValidationError):
            proposal.full_clean()

        # Com estimated_days, deve funcionar
        proposal.estimated_days = 20
        proposal.full_clean()  # Não deve levantar exceção

    def test_estimated_days_must_be_positive(self):
        """Testa que estimated_days deve ser positivo."""
        proposal = Proposal(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('5000.00'),
            estimated_days=-1
        )
        with self.assertRaises(ValidationError):
            proposal.full_clean()

        # Com estimated_days positivo, deve funcionar
        proposal.estimated_days = 20
        proposal.full_clean()  # Não deve levantar exceção

    def test_expires_at_is_optional(self):
        """Testa que expires_at é opcional."""
        # Proposta sem expires_at
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('5000.00'),
            estimated_days=20,
            expires_at=None
        )
        self.assertIsNone(proposal.expires_at)

        # Proposta com expires_at
        proposal.expires_at = self.future_expires_at
        proposal.save()
        self.assertIsNotNone(proposal.expires_at)

    def test_str_representation(self):
        """Testa a representação string do modelo."""
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('5000.00'),
            estimated_days=20,
            status=ProposalStatus.PENDING.value
        )
        expected = f"Proposta #{proposal.id} para Pedido #{self.order.id} ({ProposalStatus.PENDING.label})"
        self.assertEqual(str(proposal), expected)

    def test_created_at_auto_now_add(self):
        """Testa que created_at é preenchido automaticamente."""
        before = timezone.now()
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('5000.00'),
            estimated_days=20
        )
        after = timezone.now()

        self.assertIsNotNone(proposal.created_at)
        self.assertGreaterEqual(proposal.created_at, before)
        self.assertLessEqual(proposal.created_at, after)

    def test_updated_at_auto_now(self):
        """Testa que updated_at é atualizado automaticamente."""
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('5000.00'),
            estimated_days=20
        )
        original_updated_at = proposal.updated_at

        # Aguarda um pouco para garantir diferença de tempo
        time.sleep(0.01)

        proposal.message = 'Mensagem Atualizada'
        proposal.save()

        self.assertGreater(proposal.updated_at, original_updated_at)

    def test_soft_delete_functionality(self):
        """Testa funcionalidade de soft delete."""
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('5000.00'),
            estimated_days=20
        )

        # Proposta está ativa
        self.assertIsNone(proposal.deleted_at)
        self.assertTrue(proposal.is_alive)
        self.assertFalse(proposal.is_deleted)
        self.assertEqual(Proposal.objects.count(), 1)

        # Deleta (soft delete)
        proposal.delete()
        proposal.refresh_from_db()

        # Proposta está deletada
        self.assertIsNotNone(proposal.deleted_at)
        self.assertFalse(proposal.is_alive)
        self.assertTrue(proposal.is_deleted)
        self.assertEqual(Proposal.objects.count(), 0)
        self.assertEqual(Proposal.all_objects.count(), 1)
        self.assertEqual(Proposal.deleted_objects.count(), 1)

        # Restaura
        proposal.restore()
        proposal.refresh_from_db()

        # Proposta está ativa novamente
        self.assertIsNone(proposal.deleted_at)
        self.assertTrue(proposal.is_alive)
        self.assertFalse(proposal.is_deleted)
        self.assertEqual(Proposal.objects.count(), 1)

    def test_ordering_by_created_at_desc(self):
        """Testa que ordenação padrão é por created_at descendente."""
        proposal1 = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Proposta 1',
            price=Decimal('5000.00'),
            estimated_days=20
        )

        time.sleep(0.01)

        proposal2 = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Proposta 2',
            price=Decimal('6000.00'),
            estimated_days=25
        )

        proposals = list(Proposal.objects.all())

        # proposal2 é mais recente, deve aparecer primeiro
        self.assertEqual(proposals[0], proposal2)
        self.assertEqual(proposals[1], proposal1)

    def test_indexes_exist(self):
        """Testa que os índices foram criados corretamente."""
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('5000.00'),
            estimated_days=20
        )

        # Testa queries que usam os índices (verifica que não há erros)
        Proposal.objects.filter(order=self.order).first()
        Proposal.objects.filter(provider=self.provider_profile).first()
        Proposal.objects.filter(status=ProposalStatus.PENDING.value).first()
        Proposal.objects.filter(expires_at__isnull=True).first()
        Proposal.objects.filter(deleted_at__isnull=True).first()

        # Verifica que os índices estão definidos no Meta
        index_names = [idx.name for idx in Proposal._meta.indexes]
        self.assertIn('proposal_order_idx', index_names)
        self.assertIn('proposal_provider_idx', index_names)
        self.assertIn('proposal_status_idx', index_names)
        self.assertIn('proposal_expires_at_idx', index_names)
        self.assertIn('proposal_deleted_at_idx', index_names)

    def test_cascade_delete_when_order_hard_deleted(self):
        """Testa que propostas são deletadas quando pedido é hard deleted."""
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('5000.00'),
            estimated_days=20
        )
        proposal_id = proposal.id

        # Hard delete do pedido
        self.order.hard_delete()

        # A proposta também deve ser deletada (CASCADE)
        self.assertFalse(Proposal.all_objects.filter(id=proposal_id).exists())

    def test_cascade_delete_when_provider_hard_deleted(self):
        """Testa que propostas são deletadas quando prestador é hard deleted."""
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('5000.00'),
            estimated_days=20
        )
        proposal_id = proposal.id

        # Hard delete do prestador
        self.provider_profile.hard_delete()

        # A proposta também deve ser deletada (CASCADE)
        self.assertFalse(Proposal.all_objects.filter(id=proposal_id).exists())

    def test_price_decimal_precision(self):
        """Testa precisão decimal do campo price."""
        proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Mensagem',
            price=Decimal('1234.56'),
            estimated_days=20
        )

        # Verifica que o valor decimal é preservado
        self.assertEqual(proposal.price, Decimal('1234.56'))
