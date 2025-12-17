"""
Testes de integração para soft delete em todos os modelos.
Testa comportamento de soft delete, restore e relacionamentos.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from api.accounts.models import User, ClientProfile, ProviderProfile
from api.accounts.enums import UserType
from api.services.models import ServiceCategory, Service
from api.orders.models import Order, Proposal
from api.orders.enums import OrderStatus, ProposalStatus
from api.payments.models import Payment
from api.subscriptions.enums import PaymentStatus
from api.reviews.models import Review
from api.chat.models import ChatRoom, Message
from api.chat.enums import MessageType
from api.subscriptions.models import SubscriptionPlan, UserSubscription, SubscriptionPayment
from api.subscriptions.enums import SubscriptionStatus
from api.notifications.models import DeviceToken
from api.notifications.enums import DeviceType
from api.admin.models import AdminAction


class SoftDeleteIntegrationTestCase(TestCase):
    """Testes de integração para soft delete em todos os modelos."""

    def setUp(self):
        """Cria dados de teste."""
        # Cria usuários
        self.client_user = User.objects.create_user(  # type: ignore[call-arg]
            email='client@example.com',
            first_name='Client',
            last_name='User',
            password='testpass123',
            user_type=UserType.CLIENT.value
        )
        self.client_profile = ClientProfile.objects.create(user=self.client_user)

        self.provider_user = User.objects.create_user(  # type: ignore[call-arg]
            email='provider@example.com',
            first_name='Provider',
            last_name='User',
            password='testpass123',
            user_type=UserType.PROVIDER.value
        )
        self.provider_profile = ProviderProfile.objects.create(user=self.provider_user)

        # Cria categoria e serviço
        self.category = ServiceCategory.objects.create(name='Categoria Teste')
        self.service = Service.objects.create(
            category=self.category,
            name='Serviço Teste'
        )

        # Cria pedido
        self.order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=timezone.now() + timedelta(days=30)
        )

        # Cria proposta
        self.proposal = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Proposta',
            price=Decimal('1500.00'),
            estimated_days=10,
            expires_at=timezone.now() + timedelta(days=5)
        )

        # Cria pagamento
        self.payment = Payment.objects.create(
            order=self.order,
            proposal=self.proposal,
            amount=Decimal('1500.00')
        )

        # Cria avaliação
        self.review = Review.objects.create(
            order=self.order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )

        # Cria sala de chat
        self.chatroom = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user
        )

        # Cria mensagem
        self.message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem teste'
        )

        # Cria assinatura
        self.plan = SubscriptionPlan.objects.get(slug='free')
        self.subscription = UserSubscription.objects.create(
            user=self.client_user,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30)
        )

        # Cria pagamento de assinatura
        self.subscription_payment = SubscriptionPayment.objects.create(
            subscription=self.subscription,
            amount=Decimal('0.00'),
            due_date=timezone.now() + timedelta(days=30)
        )

        # Cria device token
        self.device_token = DeviceToken.objects.create(
            user=self.client_user,
            token='test_token_123',
            device_type=DeviceType.ANDROID.value
        )

        # Cria admin action
        self.admin_action = AdminAction.objects.create(
            admin_user=self.client_user,
            action_type='CREATE',
            target_model='User',
            target_id=1,
            description='Test action'
        )

    def test_soft_delete_user(self):
        """Testa soft delete em User."""
        user_id = self.client_user.id
        
        # Soft delete
        self.client_user.delete()
        
        # Verifica que não aparece em queries normais
        self.assertEqual(User.objects.filter(id=user_id).count(), 0)
        
        # Verifica que aparece em all_objects
        self.assertEqual(User.all_objects.filter(id=user_id).count(), 1)
        
        # Verifica que aparece em deleted_objects
        self.assertEqual(User.deleted_objects.filter(id=user_id).count(), 1)
        
        # Verifica propriedades
        user = User.all_objects.get(id=user_id)
        self.assertTrue(user.is_deleted)
        self.assertFalse(user.is_alive)
        self.assertIsNotNone(user.deleted_at)
        
        # Restore
        user.restore()
        self.assertEqual(User.objects.filter(id=user_id).count(), 1)
        self.assertFalse(user.is_deleted)
        self.assertTrue(user.is_alive)

    def test_soft_delete_client_profile(self):
        """Testa soft delete em ClientProfile."""
        profile_id = self.client_profile.id
        
        self.client_profile.delete()
        
        self.assertEqual(ClientProfile.objects.filter(id=profile_id).count(), 0)
        self.assertEqual(ClientProfile.all_objects.filter(id=profile_id).count(), 1)
        self.assertEqual(ClientProfile.deleted_objects.filter(id=profile_id).count(), 1)
        
        profile = ClientProfile.all_objects.get(id=profile_id)
        self.assertTrue(profile.is_deleted)
        profile.restore()
        self.assertEqual(ClientProfile.objects.filter(id=profile_id).count(), 1)

    def test_soft_delete_provider_profile(self):
        """Testa soft delete em ProviderProfile."""
        profile_id = self.provider_profile.id
        
        self.provider_profile.delete()
        
        self.assertEqual(ProviderProfile.objects.filter(id=profile_id).count(), 0)
        self.assertEqual(ProviderProfile.all_objects.filter(id=profile_id).count(), 1)
        self.assertEqual(ProviderProfile.deleted_objects.filter(id=profile_id).count(), 1)
        
        profile = ProviderProfile.all_objects.get(id=profile_id)
        self.assertTrue(profile.is_deleted)
        profile.restore()
        self.assertEqual(ProviderProfile.objects.filter(id=profile_id).count(), 1)

    def test_soft_delete_service_category(self):
        """Testa soft delete em ServiceCategory."""
        category_id = self.category.id
        
        self.category.delete()
        
        self.assertEqual(ServiceCategory.objects.filter(id=category_id).count(), 0)
        self.assertEqual(ServiceCategory.all_objects.filter(id=category_id).count(), 1)
        self.assertEqual(ServiceCategory.deleted_objects.filter(id=category_id).count(), 1)
        
        category = ServiceCategory.all_objects.get(id=category_id)
        self.assertTrue(category.is_deleted)
        category.restore()
        self.assertEqual(ServiceCategory.objects.filter(id=category_id).count(), 1)

    def test_soft_delete_service(self):
        """Testa soft delete em Service."""
        service_id = self.service.id
        
        self.service.delete()
        
        self.assertEqual(Service.objects.filter(id=service_id).count(), 0)
        self.assertEqual(Service.all_objects.filter(id=service_id).count(), 1)
        self.assertEqual(Service.deleted_objects.filter(id=service_id).count(), 1)
        
        service = Service.all_objects.get(id=service_id)
        self.assertTrue(service.is_deleted)
        service.restore()
        self.assertEqual(Service.objects.filter(id=service_id).count(), 1)

    def test_soft_delete_order(self):
        """Testa soft delete em Order."""
        order_id = self.order.id
        
        self.order.delete()
        
        self.assertEqual(Order.objects.filter(id=order_id).count(), 0)
        self.assertEqual(Order.all_objects.filter(id=order_id).count(), 1)
        self.assertEqual(Order.deleted_objects.filter(id=order_id).count(), 1)
        
        order = Order.all_objects.get(id=order_id)
        self.assertTrue(order.is_deleted)
        order.restore()
        self.assertEqual(Order.objects.filter(id=order_id).count(), 1)

    def test_soft_delete_proposal(self):
        """Testa soft delete em Proposal."""
        proposal_id = self.proposal.id
        
        self.proposal.delete()
        
        self.assertEqual(Proposal.objects.filter(id=proposal_id).count(), 0)
        self.assertEqual(Proposal.all_objects.filter(id=proposal_id).count(), 1)
        self.assertEqual(Proposal.deleted_objects.filter(id=proposal_id).count(), 1)
        
        proposal = Proposal.all_objects.get(id=proposal_id)
        self.assertTrue(proposal.is_deleted)
        proposal.restore()
        self.assertEqual(Proposal.objects.filter(id=proposal_id).count(), 1)

    def test_soft_delete_payment(self):
        """Testa soft delete em Payment."""
        payment_id = self.payment.id
        
        self.payment.delete()
        
        self.assertEqual(Payment.objects.filter(id=payment_id).count(), 0)
        self.assertEqual(Payment.all_objects.filter(id=payment_id).count(), 1)
        self.assertEqual(Payment.deleted_objects.filter(id=payment_id).count(), 1)
        
        payment = Payment.all_objects.get(id=payment_id)
        self.assertTrue(payment.is_deleted)
        payment.restore()
        self.assertEqual(Payment.objects.filter(id=payment_id).count(), 1)

    def test_soft_delete_review(self):
        """Testa soft delete em Review."""
        review_id = self.review.id
        
        self.review.delete()
        
        self.assertEqual(Review.objects.filter(id=review_id).count(), 0)
        self.assertEqual(Review.all_objects.filter(id=review_id).count(), 1)
        self.assertEqual(Review.deleted_objects.filter(id=review_id).count(), 1)
        
        review = Review.all_objects.get(id=review_id)
        self.assertTrue(review.is_deleted)
        review.restore()
        self.assertEqual(Review.objects.filter(id=review_id).count(), 1)

    def test_soft_delete_chatroom(self):
        """Testa soft delete em ChatRoom."""
        chatroom_id = self.chatroom.id
        
        self.chatroom.delete()
        
        self.assertEqual(ChatRoom.objects.filter(id=chatroom_id).count(), 0)
        self.assertEqual(ChatRoom.all_objects.filter(id=chatroom_id).count(), 1)
        self.assertEqual(ChatRoom.deleted_objects.filter(id=chatroom_id).count(), 1)
        
        chatroom = ChatRoom.all_objects.get(id=chatroom_id)
        self.assertTrue(chatroom.is_deleted)
        chatroom.restore()
        self.assertEqual(ChatRoom.objects.filter(id=chatroom_id).count(), 1)

    def test_soft_delete_message(self):
        """Testa soft delete em Message."""
        message_id = self.message.id
        
        self.message.delete()
        
        self.assertEqual(Message.objects.filter(id=message_id).count(), 0)
        self.assertEqual(Message.all_objects.filter(id=message_id).count(), 1)
        self.assertEqual(Message.deleted_objects.filter(id=message_id).count(), 1)
        
        message = Message.all_objects.get(id=message_id)
        self.assertTrue(message.is_deleted)
        message.restore()
        self.assertEqual(Message.objects.filter(id=message_id).count(), 1)

    def test_soft_delete_subscription_plan(self):
        """Testa soft delete em SubscriptionPlan."""
        plan_id = self.plan.id
        
        self.plan.delete()
        
        self.assertEqual(SubscriptionPlan.objects.filter(id=plan_id).count(), 0)
        self.assertEqual(SubscriptionPlan.all_objects.filter(id=plan_id).count(), 1)
        self.assertEqual(SubscriptionPlan.deleted_objects.filter(id=plan_id).count(), 1)
        
        plan = SubscriptionPlan.all_objects.get(id=plan_id)
        self.assertTrue(plan.is_deleted)
        plan.restore()
        self.assertEqual(SubscriptionPlan.objects.filter(id=plan_id).count(), 1)

    def test_soft_delete_user_subscription(self):
        """Testa soft delete em UserSubscription."""
        subscription_id = self.subscription.id
        
        self.subscription.delete()
        
        self.assertEqual(UserSubscription.objects.filter(id=subscription_id).count(), 0)
        self.assertEqual(UserSubscription.all_objects.filter(id=subscription_id).count(), 1)
        self.assertEqual(UserSubscription.deleted_objects.filter(id=subscription_id).count(), 1)
        
        subscription = UserSubscription.all_objects.get(id=subscription_id)
        self.assertTrue(subscription.is_deleted)
        subscription.restore()
        self.assertEqual(UserSubscription.objects.filter(id=subscription_id).count(), 1)

    def test_soft_delete_subscription_payment(self):
        """Testa soft delete em SubscriptionPayment."""
        payment_id = self.subscription_payment.id
        
        self.subscription_payment.delete()
        
        self.assertEqual(SubscriptionPayment.objects.filter(id=payment_id).count(), 0)
        self.assertEqual(SubscriptionPayment.all_objects.filter(id=payment_id).count(), 1)
        self.assertEqual(SubscriptionPayment.deleted_objects.filter(id=payment_id).count(), 1)
        
        payment = SubscriptionPayment.all_objects.get(id=payment_id)
        self.assertTrue(payment.is_deleted)
        payment.restore()
        self.assertEqual(SubscriptionPayment.objects.filter(id=payment_id).count(), 1)

    def test_soft_delete_device_token(self):
        """Testa soft delete em DeviceToken."""
        token_id = self.device_token.id
        
        self.device_token.delete()
        
        self.assertEqual(DeviceToken.objects.filter(id=token_id).count(), 0)
        self.assertEqual(DeviceToken.all_objects.filter(id=token_id).count(), 1)
        self.assertEqual(DeviceToken.deleted_objects.filter(id=token_id).count(), 1)
        
        token = DeviceToken.all_objects.get(id=token_id)
        self.assertTrue(token.is_deleted)
        token.restore()
        self.assertEqual(DeviceToken.objects.filter(id=token_id).count(), 1)

    def test_soft_delete_admin_action(self):
        """Testa soft delete em AdminAction."""
        action_id = self.admin_action.id
        
        self.admin_action.delete()
        
        self.assertEqual(AdminAction.objects.filter(id=action_id).count(), 0)
        self.assertEqual(AdminAction.all_objects.filter(id=action_id).count(), 1)
        self.assertEqual(AdminAction.deleted_objects.filter(id=action_id).count(), 1)
        
        action = AdminAction.all_objects.get(id=action_id)
        self.assertTrue(action.is_deleted)
        action.restore()
        self.assertEqual(AdminAction.objects.filter(id=action_id).count(), 1)

    def test_soft_delete_does_not_propagate_cascade(self):
        """Testa que soft delete NÃO propaga em cascata."""
        # Soft delete do pedido
        self.order.delete()
        
        # Objetos relacionados ainda devem existir (soft delete não propaga)
        self.assertTrue(Proposal.objects.filter(id=self.proposal.id).exists())
        self.assertTrue(Payment.objects.filter(id=self.payment.id).exists())
        self.assertTrue(Review.objects.filter(id=self.review.id).exists())
        self.assertTrue(ChatRoom.objects.filter(id=self.chatroom.id).exists())
        self.assertTrue(Message.objects.filter(id=self.message.id).exists())
        
        # Apenas o pedido está deletado
        self.assertFalse(Order.objects.filter(id=self.order.id).exists())
        self.assertTrue(Order.all_objects.filter(id=self.order.id).exists())

    def test_hard_delete_propagates_cascade(self):
        """Testa que hard delete propaga em cascata (diferente de soft delete)."""
        proposal_id = self.proposal.id
        payment_id = self.payment.id
        review_id = self.review.id
        chatroom_id = self.chatroom.id
        message_id = self.message.id
        
        # Hard delete do pedido
        self.order.hard_delete()
        
        # Objetos relacionados devem ser deletados (hard delete propaga)
        self.assertFalse(Proposal.all_objects.filter(id=proposal_id).exists())
        self.assertFalse(Payment.all_objects.filter(id=payment_id).exists())
        self.assertFalse(Review.all_objects.filter(id=review_id).exists())
        self.assertFalse(ChatRoom.all_objects.filter(id=chatroom_id).exists())
        self.assertFalse(Message.all_objects.filter(id=message_id).exists())

    def test_soft_delete_relationship_access(self):
        """Testa acesso a relacionamentos quando objeto está soft deleted."""
        # Soft delete do pedido
        self.order.delete()
        
        # Ainda deve ser possível acessar relacionamentos via all_objects
        order = Order.all_objects.get(id=self.order.id)
        self.assertEqual(order.client, self.client_profile)
        self.assertEqual(order.service, self.service)
        
        # Mas não via objects (objeto não existe mais em queries normais)
        self.assertFalse(Order.objects.filter(id=self.order.id).exists())

    def test_restore_restores_object(self):
        """Testa que restore() restaura objeto corretamente."""
        # Soft delete
        self.order.delete()
        self.assertFalse(Order.objects.filter(id=self.order.id).exists())
        self.assertTrue(Order.all_objects.filter(id=self.order.id).exists())
        
        # Restore
        order = Order.all_objects.get(id=self.order.id)
        order.restore()
        
        # Objeto deve aparecer em queries normais novamente
        self.assertTrue(Order.objects.filter(id=self.order.id).exists())
        self.assertFalse(order.is_deleted)
        self.assertTrue(order.is_alive)
        self.assertIsNone(order.deleted_at)

    def test_restore_returns_false_if_not_deleted(self):
        """Testa que restore() retorna False se objeto não está deletado."""
        result = self.order.restore()
        self.assertFalse(result)
        self.assertTrue(self.order.is_alive)

    def test_multiple_soft_deletes(self):
        """Testa múltiplos soft deletes."""
        # Soft delete de vários objetos
        self.order.delete()
        self.proposal.delete()
        self.payment.delete()
        self.review.delete()
        
        # Verifica que todos estão deletados
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Proposal.objects.count(), 0)
        self.assertEqual(Payment.objects.count(), 0)
        self.assertEqual(Review.objects.count(), 0)
        
        # Verifica que todos aparecem em all_objects
        self.assertEqual(Order.all_objects.count(), 1)
        self.assertEqual(Proposal.all_objects.count(), 1)
        self.assertEqual(Payment.all_objects.count(), 1)
        self.assertEqual(Review.all_objects.count(), 1)
        
        # Verifica que todos aparecem em deleted_objects
        self.assertEqual(Order.deleted_objects.count(), 1)
        self.assertEqual(Proposal.deleted_objects.count(), 1)
        self.assertEqual(Payment.deleted_objects.count(), 1)
        self.assertEqual(Review.deleted_objects.count(), 1)

    def test_soft_delete_preserves_data(self):
        """Testa que soft delete preserva todos os dados do objeto."""
        # Salva dados antes do delete
        order_id = self.order.id
        order_title = self.order.title
        order_description = self.order.description
        order_status = self.order.status
        
        # Soft delete
        self.order.delete()
        
        # Recupera via all_objects
        order = Order.all_objects.get(id=order_id)
        
        # Verifica que todos os dados foram preservados
        self.assertEqual(order.id, order_id)
        self.assertEqual(order.title, order_title)
        self.assertEqual(order.description, order_description)
        self.assertEqual(order.status, order_status)
        self.assertEqual(order.client, self.client_profile)
        self.assertEqual(order.service, self.service)

    def test_soft_delete_timestamp(self):
        """Testa que soft delete define deleted_at corretamente."""
        before = timezone.now()
        self.order.delete()
        after = timezone.now()
        
        order = Order.all_objects.get(id=self.order.id)
        self.assertIsNotNone(order.deleted_at)
        self.assertGreaterEqual(order.deleted_at, before)
        self.assertLessEqual(order.deleted_at, after)

    def test_soft_delete_restore_cycle(self):
        """Testa múltiplos ciclos de soft delete e restore."""
        order_id = self.order.id
        
        # Primeiro ciclo
        self.order.delete()
        self.assertFalse(Order.objects.filter(id=order_id).exists())
        
        order = Order.all_objects.get(id=order_id)
        order.restore()
        self.assertTrue(Order.objects.filter(id=order_id).exists())
        
        # Segundo ciclo
        order = Order.objects.get(id=order_id)
        order.delete()
        self.assertFalse(Order.objects.filter(id=order_id).exists())
        
        order = Order.all_objects.get(id=order_id)
        order.restore()
        self.assertTrue(Order.objects.filter(id=order_id).exists())

    def test_soft_delete_with_related_objects(self):
        """Testa soft delete quando há objetos relacionados."""
        # Cria mais objetos relacionados
        proposal2 = Proposal.objects.create(
            order=self.order,
            provider=self.provider_profile,
            message='Segunda proposta',
            price=Decimal('2000.00'),
            estimated_days=15,
            expires_at=timezone.now() + timedelta(days=5)
        )
        
        payment2 = Payment.objects.create(
            order=self.order,
            proposal=proposal2,
            amount=Decimal('2000.00')
        )
        
        # Soft delete do pedido
        self.order.delete()
        
        # Objetos relacionados ainda existem
        self.assertTrue(Proposal.objects.filter(id=proposal2.id).exists())
        self.assertTrue(Payment.objects.filter(id=payment2.id).exists())
        
        # Mas o pedido está deletado
        self.assertFalse(Order.objects.filter(id=self.order.id).exists())
        
        # Ainda é possível acessar relacionamentos via all_objects
        order = Order.all_objects.get(id=self.order.id)
        self.assertEqual(order.proposals.count(), 2)  # Inclui deletados e não deletados
        self.assertEqual(order.proposals.filter(deleted_at__isnull=True).count(), 2)

