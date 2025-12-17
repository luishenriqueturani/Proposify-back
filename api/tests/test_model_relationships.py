"""
Testes de integração para relacionamentos entre modelos.
Testa fluxos completos e relacionamentos complexos entre múltiplos modelos.
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


class ModelRelationshipsIntegrationTestCase(TestCase):
    """Testes de integração para relacionamentos entre modelos."""

    def setUp(self):
        """Cria dados de teste para os relacionamentos."""
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
        self.category = ServiceCategory.objects.create(name='Desenvolvimento Web')
        self.service = Service.objects.create(
            category=self.category,
            name='Desenvolvimento de Site'
        )

        # Cria plano de assinatura
        self.plan = SubscriptionPlan.objects.get(slug='free')  # Plano criado pela migration

    def test_complete_order_flow(self):
        """Testa fluxo completo: User -> ClientProfile -> Order -> Proposal -> Payment -> Review."""
        # 1. Cliente cria pedido
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Desenvolvimento de E-commerce',
            description='Preciso de um e-commerce completo',
            budget_min=Decimal('5000.00'),
            budget_max=Decimal('10000.00'),
            deadline=timezone.now() + timedelta(days=30)
        )

        # Verifica relacionamento User -> ClientProfile -> Order
        self.assertEqual(order.client.user, self.client_user)
        self.assertIn(order, self.client_profile.orders.all())
        self.assertIn(order, self.client_user.client_profile.orders.all())

        # 2. Prestador cria proposta
        proposal = Proposal.objects.create(
            order=order,
            provider=self.provider_profile,
            message='Minha proposta para o serviço.',
            price=Decimal('7500.00'),
            estimated_days=30,
            expires_at=timezone.now() + timedelta(days=5)
        )

        # Verifica relacionamento Order -> Proposal
        self.assertEqual(proposal.order, order)
        self.assertIn(proposal, order.proposals.all())
        self.assertIn(proposal, self.provider_profile.proposals.all())

        # 3. Cliente aceita proposta
        proposal.status = ProposalStatus.ACCEPTED.value
        proposal.save()
        order.status = OrderStatus.ACCEPTED.value
        order.save()

        # 4. Cria pagamento
        payment = Payment.objects.create(
            order=order,
            proposal=proposal,
            amount=Decimal('7500.00'),
            payment_method='credit_card',
            payment_status=PaymentStatus.PAID.value,
            transaction_id='txn_123456',
            payment_date=timezone.now()
        )

        # Verifica relacionamentos Payment
        self.assertEqual(payment.order, order)
        self.assertEqual(payment.proposal, proposal)
        self.assertIn(payment, order.payments.all())
        self.assertIn(payment, proposal.payments.all())

        # 5. Pedido é concluído
        order.status = OrderStatus.COMPLETED.value
        order.save()

        # 6. Cliente avalia prestador
        review_client = Review.objects.create(
            order=order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5,
            comment='Excelente trabalho!'
        )

        # 7. Prestador avalia cliente
        review_provider = Review.objects.create(
            order=order,
            reviewer=self.provider_user,
            reviewed_user=self.client_user,
            rating=4,
            comment='Cliente muito profissional.'
        )

        # Verifica relacionamentos Review
        self.assertEqual(review_client.order, order)
        self.assertEqual(review_client.reviewer, self.client_user)
        self.assertEqual(review_client.reviewed_user, self.provider_user)
        self.assertIn(review_client, order.reviews.all())
        self.assertIn(review_client, self.client_user.reviews_given.all())
        self.assertIn(review_client, self.provider_user.reviews_received.all())

        # Verifica que todos os relacionamentos estão corretos
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Proposal.objects.count(), 1)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(Review.objects.count(), 2)

    def test_chat_room_and_messages_flow(self):
        """Testa fluxo: Order -> ChatRoom -> Message."""
        # Cria pedido
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Desenvolvimento de E-commerce',
            description='Preciso de um e-commerce completo',
            budget_min=Decimal('5000.00'),
            budget_max=Decimal('10000.00'),
            deadline=timezone.now() + timedelta(days=30)
        )

        # Cria sala de chat
        chatroom = ChatRoom.objects.create(
            order=order,
            client=self.client_user,
            provider=self.provider_user
        )

        # Verifica relacionamento Order -> ChatRoom
        self.assertEqual(chatroom.order, order)
        self.assertIn(chatroom, order.chat_rooms.all())

        # Cliente envia mensagem
        message1 = Message.objects.create(
            room=chatroom,
            sender=self.client_user,
            content='Olá, gostaria de mais informações sobre o serviço.',
            message_type=MessageType.TEXT.value
        )

        # Prestador responde
        message2 = Message.objects.create(
            room=chatroom,
            sender=self.provider_user,
            content='Claro! Posso ajudar com o que precisar.',
            message_type=MessageType.TEXT.value
        )

        # Verifica relacionamentos Message
        self.assertEqual(message1.room, chatroom)
        self.assertEqual(message1.sender, self.client_user)
        self.assertIn(message1, chatroom.messages.all())
        self.assertIn(message1, self.client_user.sent_messages.all())

        self.assertEqual(message2.room, chatroom)
        self.assertEqual(message2.sender, self.provider_user)
        self.assertIn(message2, chatroom.messages.all())
        self.assertIn(message2, self.provider_user.sent_messages.all())

        # Verifica que todos os relacionamentos estão corretos
        self.assertEqual(ChatRoom.objects.count(), 1)
        self.assertEqual(Message.objects.count(), 2)

    def test_subscription_flow(self):
        """Testa fluxo: User -> UserSubscription -> SubscriptionPayment."""
        # Cria assinatura
        start_date = timezone.now()
        end_date = start_date + timedelta(days=30)
        subscription = UserSubscription.objects.create(
            user=self.client_user,
            plan=self.plan,
            status=SubscriptionStatus.ACTIVE.value,
            start_date=start_date,
            end_date=end_date,
            auto_renew=True
        )

        # Verifica relacionamento User -> UserSubscription
        self.assertEqual(subscription.user, self.client_user)
        self.assertEqual(subscription.plan, self.plan)
        self.assertIn(subscription, self.client_user.subscriptions.all())
        self.assertIn(subscription, self.plan.user_subscriptions.all())

        # Cria pagamento de assinatura
        payment = SubscriptionPayment.objects.create(
            subscription=subscription,
            amount=Decimal('0.00'),  # Plano FREE
            payment_method='credit_card',
            payment_status=PaymentStatus.PAID.value,
            transaction_id='sub_txn_123',
            payment_date=timezone.now(),
            due_date=end_date
        )

        # Verifica relacionamento UserSubscription -> SubscriptionPayment
        self.assertEqual(payment.subscription, subscription)
        self.assertIn(payment, subscription.payments.all())

        # Verifica que todos os relacionamentos estão corretos
        self.assertEqual(UserSubscription.objects.count(), 1)
        self.assertEqual(SubscriptionPayment.objects.count(), 1)

    def test_service_category_hierarchy(self):
        """Testa relacionamento hierárquico: ServiceCategory -> ServiceCategory (self)."""
        # Cria categoria pai
        parent_category = ServiceCategory.objects.create(name='Tecnologia Avançada')

        # Cria subcategorias
        subcategory1 = ServiceCategory.objects.create(
            name='Desenvolvimento Web Avançado',
            parent=parent_category
        )
        subcategory2 = ServiceCategory.objects.create(
            name='Desenvolvimento Mobile Avançado',
            parent=parent_category
        )

        # Verifica relacionamento self
        self.assertEqual(subcategory1.parent, parent_category)
        self.assertEqual(subcategory2.parent, parent_category)
        self.assertIn(subcategory1, parent_category.children.all())
        self.assertIn(subcategory2, parent_category.children.all())

        # Cria serviços nas subcategorias
        service1 = Service.objects.create(
            category=subcategory1,
            name='Desenvolvimento de Site'
        )
        service2 = Service.objects.create(
            category=subcategory2,
            name='Desenvolvimento de App'
        )

        # Verifica relacionamento ServiceCategory -> Service
        self.assertEqual(service1.category, subcategory1)
        self.assertEqual(service2.category, subcategory2)
        self.assertIn(service1, subcategory1.services.all())
        self.assertIn(service2, subcategory2.services.all())

    def test_cascade_delete_order_flow(self):
        """Testa CASCADE delete: deletar Order deve deletar Proposal, Payment, Review, ChatRoom."""
        # Cria fluxo completo
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=timezone.now() + timedelta(days=30)
        )

        proposal = Proposal.objects.create(
            order=order,
            provider=self.provider_profile,
            message='Proposta',
            price=Decimal('1500.00'),
            estimated_days=10,
            expires_at=timezone.now() + timedelta(days=5)
        )

        payment = Payment.objects.create(
            order=order,
            proposal=proposal,
            amount=Decimal('1500.00')
        )

        review = Review.objects.create(
            order=order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )

        chatroom = ChatRoom.objects.create(
            order=order,
            client=self.client_user,
            provider=self.provider_user
        )

        message = Message.objects.create(
            room=chatroom,
            sender=self.client_user,
            content='Mensagem'
        )

        # Salva IDs antes do delete
        proposal_id = proposal.id
        payment_id = payment.id
        review_id = review.id
        chatroom_id = chatroom.id
        message_id = message.id

        # Hard delete do pedido
        order.hard_delete()

        # Verifica CASCADE delete
        self.assertFalse(Proposal.all_objects.filter(id=proposal_id).exists())
        self.assertFalse(Payment.all_objects.filter(id=payment_id).exists())
        self.assertFalse(Review.all_objects.filter(id=review_id).exists())
        self.assertFalse(ChatRoom.all_objects.filter(id=chatroom_id).exists())
        self.assertFalse(Message.all_objects.filter(id=message_id).exists())

    def test_cascade_delete_user_flow(self):
        """Testa CASCADE delete: deletar User deve deletar Profile, Orders, Reviews, etc."""
        # Cria dados
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=timezone.now() + timedelta(days=30)
        )

        review = Review.objects.create(
            order=order,
            reviewer=self.client_user,
            reviewed_user=self.provider_user,
            rating=5
        )

        subscription = UserSubscription.objects.create(
            user=self.client_user,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30)
        )

        # Salva IDs
        client_profile_id = self.client_profile.id
        order_id = order.id
        review_id = review.id
        subscription_id = subscription.id

        # Hard delete do usuário
        self.client_user.hard_delete()

        # Verifica CASCADE delete
        self.assertFalse(ClientProfile.all_objects.filter(id=client_profile_id).exists())
        self.assertFalse(Order.all_objects.filter(id=order_id).exists())
        self.assertFalse(Review.all_objects.filter(id=review_id).exists())
        self.assertFalse(UserSubscription.all_objects.filter(id=subscription_id).exists())

    def test_protect_delete_subscription_plan(self):
        """Testa PROTECT delete: não pode deletar SubscriptionPlan se houver UserSubscription."""
        # Cria assinatura
        subscription = UserSubscription.objects.create(
            user=self.client_user,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30)
        )

        # Tenta hard delete do plano (deve falhar)
        from django.db.models.deletion import ProtectedError
        with self.assertRaises(ProtectedError):
            self.plan.hard_delete()

        # A assinatura ainda deve existir
        self.assertTrue(UserSubscription.objects.filter(id=subscription.id).exists())

    def test_multiple_orders_same_client(self):
        """Testa que um cliente pode ter múltiplos pedidos."""
        order1 = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido 1',
            description='Descrição 1',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=timezone.now() + timedelta(days=30)
        )

        order2 = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido 2',
            description='Descrição 2',
            budget_min=Decimal('2000.00'),
            budget_max=Decimal('3000.00'),
            deadline=timezone.now() + timedelta(days=30)
        )

        # Verifica que ambos os pedidos pertencem ao mesmo cliente
        self.assertEqual(order1.client, self.client_profile)
        self.assertEqual(order2.client, self.client_profile)
        self.assertEqual(self.client_profile.orders.count(), 2)
        self.assertIn(order1, self.client_profile.orders.all())
        self.assertIn(order2, self.client_profile.orders.all())

    def test_multiple_proposals_same_order(self):
        """Testa que um pedido pode ter múltiplas propostas."""
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=timezone.now() + timedelta(days=30)
        )

        # Cria outro prestador
        provider_user2 = User.objects.create_user(  # type: ignore[call-arg]
            email='provider2@example.com',
            first_name='Provider',
            last_name='User2',
            password='testpass123',
            user_type=UserType.PROVIDER.value
        )
        provider_profile2 = ProviderProfile.objects.create(user=provider_user2)

        proposal1 = Proposal.objects.create(
            order=order,
            provider=self.provider_profile,
            message='Proposta 1',
            price=Decimal('1500.00'),
            estimated_days=10,
            expires_at=timezone.now() + timedelta(days=5)
        )

        proposal2 = Proposal.objects.create(
            order=order,
            provider=provider_profile2,
            message='Proposta 2',
            price=Decimal('1800.00'),
            estimated_days=15,
            expires_at=timezone.now() + timedelta(days=5)
        )

        # Verifica que ambas as propostas pertencem ao mesmo pedido
        self.assertEqual(proposal1.order, order)
        self.assertEqual(proposal2.order, order)
        self.assertEqual(order.proposals.count(), 2)
        self.assertIn(proposal1, order.proposals.all())
        self.assertIn(proposal2, order.proposals.all())

    def test_soft_delete_cascade_behavior(self):
        """Testa que soft delete não propaga em cascata, apenas hard delete."""
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=timezone.now() + timedelta(days=30)
        )

        proposal = Proposal.objects.create(
            order=order,
            provider=self.provider_profile,
            message='Proposta',
            price=Decimal('1500.00'),
            estimated_days=10,
            expires_at=timezone.now() + timedelta(days=5)
        )

        # Soft delete do pedido
        order.delete()

        # A proposta ainda deve existir (soft delete não propaga)
        self.assertTrue(Proposal.objects.filter(id=proposal.id).exists())
        self.assertFalse(Order.objects.filter(id=order.id).exists())
        self.assertTrue(Order.all_objects.filter(id=order.id).exists())

    def test_reverse_relationships(self):
        """Testa relacionamentos reversos em todos os modelos."""
        # Cria dados
        order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Pedido Teste',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=timezone.now() + timedelta(days=30)
        )

        proposal = Proposal.objects.create(
            order=order,
            provider=self.provider_profile,
            message='Proposta',
            price=Decimal('1500.00'),
            estimated_days=10,
            expires_at=timezone.now() + timedelta(days=5)
        )

        # Verifica relacionamentos reversos
        self.assertIn(order, self.client_profile.orders.all())
        self.assertIn(order, self.service.orders.all())
        self.assertIn(proposal, order.proposals.all())
        self.assertIn(proposal, self.provider_profile.proposals.all())

    def test_user_can_be_both_client_and_provider(self):
        """Testa que um usuário pode ser cliente e prestador ao mesmo tempo."""
        # Cria usuário que é ambos
        user = User.objects.create_user(  # type: ignore[call-arg]
            email='both@example.com',
            first_name='Both',
            last_name='User',
            password='testpass123',
            user_type=UserType.CLIENT.value  # Inicia como cliente
        )
        client_profile = ClientProfile.objects.create(user=user)
        provider_profile = ProviderProfile.objects.create(user=user)

        # Cria pedido como cliente
        order = Order.objects.create(
            client=client_profile,
            service=self.service,
            title='Pedido como Cliente',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=timezone.now() + timedelta(days=30)
        )

        # Cria proposta como prestador (para outro pedido)
        order2 = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Outro Pedido',
            description='Descrição',
            budget_min=Decimal('1000.00'),
            budget_max=Decimal('2000.00'),
            deadline=timezone.now() + timedelta(days=30)
        )

        proposal = Proposal.objects.create(
            order=order2,
            provider=provider_profile,
            message='Proposta como Prestador',
            price=Decimal('1500.00'),
            estimated_days=10,
            expires_at=timezone.now() + timedelta(days=5)
        )

        # Verifica que o usuário tem ambos os perfis
        self.assertEqual(user.client_profile, client_profile)
        self.assertEqual(user.provider_profile, provider_profile)
        self.assertIn(order, client_profile.orders.all())
        self.assertIn(proposal, provider_profile.proposals.all())

