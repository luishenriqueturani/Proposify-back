"""
Testes unitários para o app payments.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
import time
from datetime import timedelta
from decimal import Decimal
from api.payments.models import Payment
from api.subscriptions.enums import PaymentStatus
from api.accounts.models import User, ClientProfile, ProviderProfile
from api.accounts.enums import UserType
from api.services.models import ServiceCategory, Service
from api.orders.models import Order, Proposal
from api.orders.enums import OrderStatus, ProposalStatus


class PaymentModelTestCase(TestCase):
    """Testes unitários para o modelo Payment."""

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

        # Cria proposta
        self.future_expires_at = timezone.now() + timedelta(days=5)
        self.proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Minha proposta para o serviço.',
            price=Decimal('7500.00'),
            estimated_days=30,
            status=ProposalStatus.ACCEPTED.value,
            expires_at=self.future_expires_at
        )

    def test_create_payment_with_minimal_fields(self):
        """Testa criação de pagamento com campos mínimos."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00')
        )
        self.assertEqual(payment.order, self.order)
        self.assertEqual(payment.proposal, self.proposal)
        self.assertEqual(payment.amount, Decimal('7500.00'))
        self.assertEqual(payment.payment_status, PaymentStatus.PENDING.value)
        self.assertIsNone(payment.payment_method)
        self.assertIsNone(payment.transaction_id)
        self.assertIsNone(payment.payment_date)
        self.assertEqual(payment.metadata, {})
        self.assertIsNotNone(payment.created_at)
        self.assertIsNone(payment.deleted_at)

    def test_create_payment_with_all_fields(self):
        """Testa criação de pagamento com todos os campos."""
        payment_date = timezone.now()
        metadata = {'gateway': 'stripe', 'customer_id': 'cus_123'}
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_method='credit_card',
            payment_status=PaymentStatus.PAID.value,
            transaction_id='txn_123456',
            payment_date=payment_date,
            metadata=metadata
        )
        self.assertEqual(payment.order, self.order)
        self.assertEqual(payment.proposal, self.proposal)
        self.assertEqual(payment.amount, Decimal('7500.00'))
        self.assertEqual(payment.payment_method, 'credit_card')
        self.assertEqual(payment.payment_status, PaymentStatus.PAID.value)
        self.assertEqual(payment.transaction_id, 'txn_123456')
        self.assertEqual(payment.payment_date, payment_date)
        self.assertEqual(payment.metadata, metadata)
        self.assertIsNotNone(payment.created_at)
        self.assertIsNotNone(payment.updated_at)
        self.assertIsNone(payment.deleted_at)

    def test_order_is_required(self):
        """Testa que order é obrigatório."""
        payment = Payment(
            proposal=self.proposal,
            amount=Decimal('7500.00')
        )
        with self.assertRaises(ValidationError):
            payment.full_clean()

    def test_proposal_is_required(self):
        """Testa que proposal é obrigatório."""
        payment = Payment(
            order=self.order,
            amount=Decimal('7500.00')
        )
        with self.assertRaises(ValidationError):
            payment.full_clean()

    def test_amount_is_required(self):
        """Testa que amount é obrigatório."""
        payment = Payment(
            order=self.order,
            proposal=self.proposal
        )
        with self.assertRaises(ValidationError):
            payment.full_clean()

    def test_payment_status_default_is_pending(self):
        """Testa que payment_status padrão é PENDING."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00')
        )
        self.assertEqual(payment.payment_status, PaymentStatus.PENDING.value)
        self.assertTrue(payment.is_pending)

    def test_payment_status_choices(self):
        """Testa que payment_status aceita apenas valores válidos."""
        # PENDING
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_status=PaymentStatus.PENDING.value
        )
        self.assertEqual(payment.payment_status, PaymentStatus.PENDING.value)
        self.assertTrue(payment.is_pending)
        self.assertFalse(payment.is_paid)
        self.assertFalse(payment.is_failed)
        self.assertFalse(payment.is_refunded)

        # PAID
        payment.payment_status = PaymentStatus.PAID.value
        payment.save()
        self.assertEqual(payment.payment_status, PaymentStatus.PAID.value)
        self.assertFalse(payment.is_pending)
        self.assertTrue(payment.is_paid)
        self.assertFalse(payment.is_failed)
        self.assertFalse(payment.is_refunded)

        # FAILED
        payment.payment_status = PaymentStatus.FAILED.value
        payment.save()
        self.assertEqual(payment.payment_status, PaymentStatus.FAILED.value)
        self.assertFalse(payment.is_pending)
        self.assertFalse(payment.is_paid)
        self.assertTrue(payment.is_failed)
        self.assertFalse(payment.is_refunded)

        # REFUNDED
        payment.payment_status = PaymentStatus.REFUNDED.value
        payment.save()
        self.assertEqual(payment.payment_status, PaymentStatus.REFUNDED.value)
        self.assertFalse(payment.is_pending)
        self.assertFalse(payment.is_paid)
        self.assertFalse(payment.is_failed)
        self.assertTrue(payment.is_refunded)

    def test_is_paid_property(self):
        """Testa a propriedade is_paid."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_status=PaymentStatus.PAID.value
        )
        self.assertTrue(payment.is_paid)

        payment.payment_status = PaymentStatus.PENDING.value
        payment.save()
        self.assertFalse(payment.is_paid)

    def test_is_pending_property(self):
        """Testa a propriedade is_pending."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_status=PaymentStatus.PENDING.value
        )
        self.assertTrue(payment.is_pending)

        payment.payment_status = PaymentStatus.PAID.value
        payment.save()
        self.assertFalse(payment.is_pending)

    def test_is_failed_property(self):
        """Testa a propriedade is_failed."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_status=PaymentStatus.FAILED.value
        )
        self.assertTrue(payment.is_failed)

        payment.payment_status = PaymentStatus.PENDING.value
        payment.save()
        self.assertFalse(payment.is_failed)

    def test_is_refunded_property(self):
        """Testa a propriedade is_refunded."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_status=PaymentStatus.REFUNDED.value
        )
        self.assertTrue(payment.is_refunded)

        payment.payment_status = PaymentStatus.PENDING.value
        payment.save()
        self.assertFalse(payment.is_refunded)

    def test_payment_method_is_optional(self):
        """Testa que payment_method é opcional."""
        # Sem payment_method
        payment1 = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_method=None
        )
        self.assertIsNone(payment1.payment_method)

        # Com payment_method
        payment2 = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_method='pix'
        )
        self.assertEqual(payment2.payment_method, 'pix')

    def test_transaction_id_is_optional(self):
        """Testa que transaction_id é opcional."""
        # Sem transaction_id
        payment1 = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            transaction_id=None
        )
        self.assertIsNone(payment1.transaction_id)

        # Com transaction_id
        payment2 = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            transaction_id='txn_123456'
        )
        self.assertEqual(payment2.transaction_id, 'txn_123456')

    def test_transaction_id_is_unique(self):
        """Testa que transaction_id deve ser único."""
        Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            transaction_id='txn_unique'
        )

        # Tentar criar outro com mesmo transaction_id deve falhar
        with self.assertRaises(IntegrityError):
            Payment.objects.create(
                order=self.order,
                proposal=self.proposal,
                amount=Decimal('8000.00'),
                transaction_id='txn_unique'
            )

    def test_payment_date_is_optional(self):
        """Testa que payment_date é opcional."""
        # Sem payment_date
        payment1 = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_date=None
        )
        self.assertIsNone(payment1.payment_date)

        # Com payment_date
        payment_date = timezone.now()
        payment2 = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_date=payment_date
        )
        self.assertEqual(payment2.payment_date, payment_date)

    def test_metadata_default_is_empty_dict(self):
        """Testa que metadata padrão é um dicionário vazio."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00')
        )
        self.assertEqual(payment.metadata, {})

    def test_metadata_can_be_set(self):
        """Testa que metadata pode ser definido."""
        metadata = {
            'gateway': 'stripe',
            'customer_id': 'cus_123',
            'charge_id': 'ch_123'
        }
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            metadata=metadata
        )
        self.assertEqual(payment.metadata, metadata)

    def test_mark_as_paid_method(self):
        """Testa o método mark_as_paid()."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_status=PaymentStatus.PENDING.value
        )

        self.assertFalse(payment.is_paid)
        self.assertIsNone(payment.transaction_id)
        self.assertIsNone(payment.payment_date)

        # Marca como pago
        before = timezone.now()
        payment.mark_as_paid()
        after = timezone.now()
        payment.refresh_from_db()

        self.assertTrue(payment.is_paid)
        self.assertEqual(payment.payment_status, PaymentStatus.PAID.value)
        self.assertIsNotNone(payment.payment_date)
        self.assertGreaterEqual(payment.payment_date, before)
        self.assertLessEqual(payment.payment_date, after)

    def test_mark_as_paid_with_transaction_id(self):
        """Testa o método mark_as_paid() com transaction_id."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_status=PaymentStatus.PENDING.value
        )

        payment.mark_as_paid(transaction_id='txn_123456')
        payment.refresh_from_db()

        self.assertTrue(payment.is_paid)
        self.assertEqual(payment.transaction_id, 'txn_123456')
        self.assertIsNotNone(payment.payment_date)

    def test_mark_as_paid_with_payment_date(self):
        """Testa o método mark_as_paid() com payment_date."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_status=PaymentStatus.PENDING.value
        )

        custom_date = timezone.now() - timedelta(days=1)
        payment.mark_as_paid(payment_date=custom_date)
        payment.refresh_from_db()

        self.assertTrue(payment.is_paid)
        self.assertEqual(payment.payment_date, custom_date)

    def test_mark_as_paid_with_both_parameters(self):
        """Testa o método mark_as_paid() com transaction_id e payment_date."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_status=PaymentStatus.PENDING.value
        )

        custom_date = timezone.now() - timedelta(days=1)
        payment.mark_as_paid(transaction_id='txn_789', payment_date=custom_date)
        payment.refresh_from_db()

        self.assertTrue(payment.is_paid)
        self.assertEqual(payment.transaction_id, 'txn_789')
        self.assertEqual(payment.payment_date, custom_date)

    def test_mark_as_failed_method(self):
        """Testa o método mark_as_failed()."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_status=PaymentStatus.PENDING.value
        )

        self.assertFalse(payment.is_failed)

        # Marca como falhou
        payment.mark_as_failed()
        payment.refresh_from_db()

        self.assertTrue(payment.is_failed)
        self.assertEqual(payment.payment_status, PaymentStatus.FAILED.value)

    def test_mark_as_failed_with_reason(self):
        """Testa o método mark_as_failed() com motivo."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_status=PaymentStatus.PENDING.value
        )

        payment.mark_as_failed(reason='Cartão recusado')
        payment.refresh_from_db()

        self.assertTrue(payment.is_failed)
        self.assertEqual(payment.payment_status, PaymentStatus.FAILED.value)
        self.assertEqual(payment.metadata['failure_reason'], 'Cartão recusado')

    def test_mark_as_failed_preserves_existing_metadata(self):
        """Testa que mark_as_failed() preserva metadata existente."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_status=PaymentStatus.PENDING.value,
            metadata={'gateway': 'stripe', 'customer_id': 'cus_123'}
        )

        payment.mark_as_failed(reason='Cartão recusado')
        payment.refresh_from_db()

        self.assertEqual(payment.metadata['gateway'], 'stripe')
        self.assertEqual(payment.metadata['customer_id'], 'cus_123')
        self.assertEqual(payment.metadata['failure_reason'], 'Cartão recusado')

    def test_mark_as_refunded_method(self):
        """Testa o método mark_as_refunded()."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_status=PaymentStatus.PAID.value
        )

        self.assertFalse(payment.is_refunded)

        # Marca como reembolsado
        payment.mark_as_refunded()
        payment.refresh_from_db()

        self.assertTrue(payment.is_refunded)
        self.assertEqual(payment.payment_status, PaymentStatus.REFUNDED.value)

    def test_mark_as_refunded_with_transaction_id(self):
        """Testa o método mark_as_refunded() com refund_transaction_id."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_status=PaymentStatus.PAID.value
        )

        payment.mark_as_refunded(refund_transaction_id='refund_123456')
        payment.refresh_from_db()

        self.assertTrue(payment.is_refunded)
        self.assertEqual(payment.payment_status, PaymentStatus.REFUNDED.value)
        self.assertEqual(payment.metadata['refund_transaction_id'], 'refund_123456')

    def test_mark_as_refunded_preserves_existing_metadata(self):
        """Testa que mark_as_refunded() preserva metadata existente."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_status=PaymentStatus.PAID.value,
            metadata={'gateway': 'stripe', 'charge_id': 'ch_123'}
        )

        payment.mark_as_refunded(refund_transaction_id='refund_789')
        payment.refresh_from_db()

        self.assertEqual(payment.metadata['gateway'], 'stripe')
        self.assertEqual(payment.metadata['charge_id'], 'ch_123')
        self.assertEqual(payment.metadata['refund_transaction_id'], 'refund_789')

    def test_order_foreign_key_relationship(self):
        """Testa relacionamento ForeignKey com Order."""
        payment1 = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00')
        )

        # Cria outra proposta para o mesmo pedido
        proposal2 = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Segunda proposta',
            price=Decimal('8000.00'),
            estimated_days=35,
            status=ProposalStatus.ACCEPTED.value,
            expires_at=self.future_expires_at
        )

        payment2 = Payment.objects.create(
            order=self.order,
            proposal=proposal2,
            amount=Decimal('8000.00')
        )

        # Verifica relacionamento direto
        self.assertEqual(payment1.order, self.order)
        self.assertEqual(payment2.order, self.order)

        # Verifica relacionamento reverso
        payments = self.order.payments.all()
        self.assertEqual(payments.count(), 2)
        self.assertIn(payment1, payments)
        self.assertIn(payment2, payments)

    def test_proposal_foreign_key_relationship(self):
        """Testa relacionamento ForeignKey com Proposal."""
        payment1 = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00')
        )

        # Cria outro pedido e proposta
        order2 = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Segundo Pedido',
            description='Outro pedido',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=self.future_deadline
        )

        proposal2 = Proposal.objects.create(
            order=order2,
            provider=self.provider_profile,
            message='Proposta para segundo pedido',
            price=Decimal('1500.00'),
            estimated_days=10,
            status=ProposalStatus.ACCEPTED.value,
            expires_at=self.future_expires_at
        )

        payment2 = Payment.objects.create(
            order=order2,
            proposal=proposal2,
            amount=Decimal('1500.00')
        )

        # Verifica relacionamento direto
        self.assertEqual(payment1.proposal, self.proposal)
        self.assertEqual(payment2.proposal, proposal2)

        # Verifica relacionamento reverso
        payments = self.proposal.payments.all()
        self.assertEqual(payments.count(), 1)
        self.assertIn(payment1, payments)

    def test_str_representation(self):
        """Testa a representação string do modelo."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_status=PaymentStatus.PAID.value
        )
        expected = f"Pagamento #{payment.id} - R$ 7500.00 (Pago)"
        self.assertEqual(str(payment), expected)

    def test_created_at_auto_now_add(self):
        """Testa que created_at é preenchido automaticamente."""
        before = timezone.now()
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00')
        )
        after = timezone.now()

        self.assertIsNotNone(payment.created_at)
        self.assertGreaterEqual(payment.created_at, before)
        self.assertLessEqual(payment.created_at, after)

    def test_updated_at_auto_now(self):
        """Testa que updated_at é atualizado automaticamente."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00')
        )
        original_updated_at = payment.updated_at

        # Aguarda um pouco para garantir diferença de tempo
        time.sleep(0.01)

        payment.amount = Decimal('8000.00')
        payment.save()

        self.assertGreater(payment.updated_at, original_updated_at)

    def test_soft_delete_functionality(self):
        """Testa funcionalidade de soft delete."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00')
        )

        # Pagamento está ativo
        self.assertIsNone(payment.deleted_at)
        self.assertTrue(payment.is_alive)
        self.assertFalse(payment.is_deleted)
        self.assertEqual(Payment.objects.count(), 1)

        # Deleta (soft delete)
        payment.delete()
        payment.refresh_from_db()

        # Pagamento está deletado
        self.assertIsNotNone(payment.deleted_at)
        self.assertFalse(payment.is_alive)
        self.assertTrue(payment.is_deleted)
        self.assertEqual(Payment.objects.count(), 0)
        self.assertEqual(Payment.all_objects.count(), 1)
        self.assertEqual(Payment.deleted_objects.count(), 1)

        # Restaura
        payment.restore()
        payment.refresh_from_db()

        # Pagamento está ativo novamente
        self.assertIsNone(payment.deleted_at)
        self.assertTrue(payment.is_alive)
        self.assertFalse(payment.is_deleted)
        self.assertEqual(Payment.objects.count(), 1)

    def test_ordering_by_created_at_desc(self):
        """Testa que ordenação padrão é por created_at descendente."""
        payment1 = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00')
        )

        time.sleep(0.01)

        payment2 = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('8000.00')
        )

        payments = list(Payment.objects.all())

        # payment2 é mais recente, deve aparecer primeiro
        self.assertEqual(payments[0], payment2)
        self.assertEqual(payments[1], payment1)

    def test_indexes_exist(self):
        """Testa que os índices foram criados corretamente."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00')
        )

        # Testa queries que usam os índices (verifica que não há erros)
        Payment.objects.filter(order=self.order).first()
        Payment.objects.filter(proposal=self.proposal).first()
        Payment.objects.filter(payment_status=PaymentStatus.PENDING.value).first()
        Payment.objects.filter(transaction_id='txn_123').first()
        Payment.objects.filter(payment_date__isnull=False).first()
        Payment.objects.filter(deleted_at__isnull=True).first()

        # Verifica que os índices estão definidos no Meta
        index_names = [idx.name for idx in Payment._meta.indexes]
        self.assertIn('svc_payment_order_idx', index_names)
        self.assertIn('svc_payment_proposal_idx', index_names)
        self.assertIn('svc_payment_status_idx', index_names)
        self.assertIn('svc_payment_txn_id_idx', index_names)
        self.assertIn('svc_payment_date_idx', index_names)
        self.assertIn('svc_payment_deleted_idx', index_names)

    def test_cascade_delete_when_order_hard_deleted(self):
        """Testa que pagamentos são deletados quando pedido é hard deleted."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00')
        )
        payment_id = payment.id

        # Hard delete do pedido
        self.order.hard_delete()

        # O pagamento também deve ser deletado (CASCADE)
        self.assertFalse(Payment.all_objects.filter(id=payment_id).exists())

    def test_cascade_delete_when_proposal_hard_deleted(self):
        """Testa que pagamentos são deletados quando proposta é hard deleted."""
        payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00')
        )
        payment_id = payment.id

        # Hard delete da proposta
        self.proposal.hard_delete()

        # O pagamento também deve ser deletado (CASCADE)
        self.assertFalse(Payment.all_objects.filter(id=payment_id).exists())

    def test_multiple_payments_for_same_order(self):
        """Testa criação de múltiplos pagamentos para o mesmo pedido."""
        payment1 = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('7500.00'),
            payment_status=PaymentStatus.PAID.value
        )

        # Cria outra proposta e pagamento para o mesmo pedido
        proposal2 = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Segunda proposta',
            price=Decimal('8000.00'),
            estimated_days=35,
            status=ProposalStatus.ACCEPTED.value,
            expires_at=self.future_expires_at
        )

        payment2 = Payment.objects.create(
            order=self.order,
            proposal=proposal2,
            amount=Decimal('8000.00'),
            payment_status=PaymentStatus.PENDING.value
        )

        payments = self.order.payments.all()
        self.assertEqual(payments.count(), 2)
        self.assertIn(payment1, payments)
        self.assertIn(payment2, payments)
