"""
Testes unitários para o app chat.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
import time
from datetime import timedelta
from api.chat.models import ChatRoom, Message
from api.chat.enums import MessageType
from api.orders.models import Order
from api.orders.enums import OrderStatus
from api.accounts.models import User, ClientProfile, ProviderProfile
from api.accounts.enums import UserType
from api.services.models import ServiceCategory, Service
from decimal import Decimal


class ChatRoomModelTestCase(TestCase):
    """Testes unitários para o modelo ChatRoom."""

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

    def test_create_chatroom_with_all_fields(self):
        """Testa criação de sala de chat com todos os campos."""
        last_message_at = timezone.now()
        chatroom = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user,
            last_message_at=last_message_at
        )

        self.assertEqual(chatroom.order, self.order)
        self.assertEqual(chatroom.client, self.client_user)
        self.assertEqual(chatroom.provider, self.provider_user)
        self.assertEqual(chatroom.last_message_at, last_message_at)
        self.assertIsNotNone(chatroom.created_at)
        self.assertIsNotNone(chatroom.updated_at)
        self.assertIsNone(chatroom.deleted_at)

    def test_create_chatroom_without_last_message_at(self):
        """Testa criação de sala de chat sem last_message_at."""
        chatroom = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user,
            last_message_at=None
        )

        self.assertIsNone(chatroom.last_message_at)
        self.assertIsNotNone(chatroom.created_at)

    def test_order_foreign_key_relationship(self):
        """Testa relacionamento ForeignKey com Order."""
        # Cria outro prestador para poder criar segunda sala
        provider_user2 = User.objects.create_user(  # type: ignore[call-arg]
            email='provider2@example.com',
            first_name='Provider2',
            last_name='User',
            password='testpass123',
            user_type=UserType.PROVIDER.value
        )
        ProviderProfile.objects.create(user=provider_user2)

        chatroom1 = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user
        )
        chatroom2 = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=provider_user2
        )

        # Verifica relacionamento direto
        self.assertEqual(chatroom1.order, self.order)
        self.assertEqual(chatroom2.order, self.order)

        # Verifica relacionamento reverso
        chatrooms = self.order.chat_rooms.all()
        self.assertEqual(chatrooms.count(), 2)
        self.assertIn(chatroom1, chatrooms)
        self.assertIn(chatroom2, chatrooms)

    def test_client_foreign_key_relationship(self):
        """Testa relacionamento ForeignKey com User (client)."""
        # Cria outro pedido para poder criar segunda sala
        order2 = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Outro Pedido',
            description='Outra descrição',
            budget_min=Decimal('3000.00'),
            budget_max=Decimal('5000.00'),
            deadline=self.future_deadline
        )

        chatroom1 = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user
        )
        chatroom2 = ChatRoom.objects.create(
            order=order2,
            client=self.client_user,
            provider=self.provider_user
        )

        # Verifica relacionamento direto
        self.assertEqual(chatroom1.client, self.client_user)
        self.assertEqual(chatroom2.client, self.client_user)

        # Verifica relacionamento reverso
        chatrooms = self.client_user.client_chat_rooms.all()
        self.assertEqual(chatrooms.count(), 2)
        self.assertIn(chatroom1, chatrooms)
        self.assertIn(chatroom2, chatrooms)

    def test_provider_foreign_key_relationship(self):
        """Testa relacionamento ForeignKey com User (provider)."""
        # Cria outro cliente para poder criar segunda sala
        client_user2 = User.objects.create_user(  # type: ignore[call-arg]
            email='client2@example.com',
            first_name='Client2',
            last_name='User',
            password='testpass123',
            user_type=UserType.CLIENT.value
        )
        ClientProfile.objects.create(user=client_user2)

        chatroom1 = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user
        )
        chatroom2 = ChatRoom.objects.create(
            order=self.order,
            client=client_user2,
            provider=self.provider_user
        )

        # Verifica relacionamento direto
        self.assertEqual(chatroom1.provider, self.provider_user)
        self.assertEqual(chatroom2.provider, self.provider_user)

        # Verifica relacionamento reverso
        chatrooms = self.provider_user.provider_chat_rooms.all()
        self.assertEqual(chatrooms.count(), 2)
        self.assertIn(chatroom1, chatrooms)
        self.assertIn(chatroom2, chatrooms)

    def test_unique_constraint_order_client_provider(self):
        """Testa constraint único: (order, client, provider)."""
        # Cria primeira sala de chat
        ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user
        )

        # Tenta criar outra sala com mesmo order, client e provider
        with self.assertRaises(IntegrityError):
            ChatRoom.objects.create(
                order=self.order,
                client=self.client_user,
                provider=self.provider_user
            )

    def test_unique_constraint_allows_different_combinations(self):
        """Testa que constraint único permite combinações diferentes."""
        # Cria outro cliente
        client_user2 = User.objects.create_user(  # type: ignore[call-arg]
            email='client2@example.com',
            first_name='Client2',
            last_name='User',
            password='testpass123',
            user_type=UserType.CLIENT.value
        )
        ClientProfile.objects.create(user=client_user2)

        # Cria outro prestador
        provider_user2 = User.objects.create_user(  # type: ignore[call-arg]
            email='provider2@example.com',
            first_name='Provider2',
            last_name='User',
            password='testpass123',
            user_type=UserType.PROVIDER.value
        )
        ProviderProfile.objects.create(user=provider_user2)

        # Cria outra ordem
        order2 = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            title='Outro Pedido',
            description='Outra descrição',
            budget_min=Decimal('3000.00'),
            budget_max=Decimal('5000.00'),
            deadline=self.future_deadline
        )

        # Todas essas combinações devem ser permitidas
        ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user
        )

        ChatRoom.objects.create(
            order=self.order,
            client=client_user2,
            provider=self.provider_user
        )

        ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=provider_user2
        )

        ChatRoom.objects.create(
            order=order2,
            client=self.client_user,
            provider=self.provider_user
        )

        self.assertEqual(ChatRoom.objects.count(), 4)

    def test_str_representation(self):
        """Testa a representação string do modelo."""
        chatroom = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user
        )
        expected = f"Chat #{chatroom.id} - Pedido #{self.order.id} ({self.client_user.email} <-> {self.provider_user.email})"
        self.assertEqual(str(chatroom), expected)

    def test_created_at_auto_now_add(self):
        """Testa que created_at é preenchido automaticamente."""
        before = timezone.now()
        chatroom = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user
        )
        after = timezone.now()

        self.assertIsNotNone(chatroom.created_at)
        self.assertGreaterEqual(chatroom.created_at, before)
        self.assertLessEqual(chatroom.created_at, after)

    def test_updated_at_auto_now(self):
        """Testa que updated_at é atualizado automaticamente."""
        chatroom = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user
        )
        original_updated_at = chatroom.updated_at

        # Aguarda um pouco para garantir diferença de tempo
        time.sleep(0.01)

        chatroom.last_message_at = timezone.now()
        chatroom.save()

        self.assertGreater(chatroom.updated_at, original_updated_at)

    def test_soft_delete_functionality(self):
        """Testa funcionalidade de soft delete."""
        chatroom = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user
        )

        # Sala está ativa
        self.assertIsNone(chatroom.deleted_at)
        self.assertTrue(chatroom.is_alive)
        self.assertFalse(chatroom.is_deleted)
        self.assertEqual(ChatRoom.objects.count(), 1)

        # Deleta (soft delete)
        chatroom.delete()
        chatroom.refresh_from_db()

        # Sala está deletada
        self.assertIsNotNone(chatroom.deleted_at)
        self.assertFalse(chatroom.is_alive)
        self.assertTrue(chatroom.is_deleted)
        self.assertEqual(ChatRoom.objects.count(), 0)
        self.assertEqual(ChatRoom.all_objects.count(), 1)
        self.assertEqual(ChatRoom.deleted_objects.count(), 1)

        # Restaura
        chatroom.restore()
        chatroom.refresh_from_db()

        # Sala está ativa novamente
        self.assertIsNone(chatroom.deleted_at)
        self.assertTrue(chatroom.is_alive)
        self.assertFalse(chatroom.is_deleted)
        self.assertEqual(ChatRoom.objects.count(), 1)

    def test_ordering_by_last_message_at_desc_then_created_at_desc(self):
        """Testa que ordenação padrão é por last_message_at descendente, depois created_at descendente."""
        # Cria outros usuários para poder criar múltiplas salas
        client_user2 = User.objects.create_user(  # type: ignore[call-arg]
            email='client2@example.com',
            first_name='Client2',
            last_name='User',
            password='testpass123',
            user_type=UserType.CLIENT.value
        )
        ClientProfile.objects.create(user=client_user2)

        provider_user2 = User.objects.create_user(  # type: ignore[call-arg]
            email='provider2@example.com',
            first_name='Provider2',
            last_name='User',
            password='testpass123',
            user_type=UserType.PROVIDER.value
        )
        ProviderProfile.objects.create(user=provider_user2)

        # Sala sem last_message_at
        chatroom1 = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user,
            last_message_at=None
        )

        time.sleep(0.01)

        # Sala com last_message_at mais antigo
        old_time = timezone.now() - timedelta(days=1)
        chatroom2 = ChatRoom.objects.create(
            order=self.order,
            client=client_user2,
            provider=self.provider_user,
            last_message_at=old_time
        )

        time.sleep(0.01)

        # Sala com last_message_at mais recente
        recent_time = timezone.now()
        chatroom3 = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=provider_user2,
            last_message_at=recent_time
        )

        chatrooms = list(ChatRoom.objects.all())

        # chatroom3 tem last_message_at mais recente, deve aparecer primeiro
        self.assertEqual(chatrooms[0], chatroom3)
        # chatroom2 tem last_message_at mais antigo, deve aparecer depois
        self.assertEqual(chatrooms[1], chatroom2)
        # chatroom1 não tem last_message_at, deve aparecer por último (ordenado por created_at desc)
        self.assertEqual(chatrooms[2], chatroom1)

    def test_indexes_exist(self):
        """Testa que os índices foram criados corretamente."""
        chatroom = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user
        )

        # Testa queries que usam os índices (verifica que não há erros)
        ChatRoom.objects.filter(order=self.order).first()
        ChatRoom.objects.filter(client=self.client_user).first()
        ChatRoom.objects.filter(provider=self.provider_user).first()
        ChatRoom.objects.filter(last_message_at__isnull=True).first()
        ChatRoom.objects.filter(deleted_at__isnull=True).first()

        # Verifica que os índices estão definidos no Meta
        index_names = [idx.name for idx in ChatRoom._meta.indexes]
        self.assertIn('chatroom_order_idx', index_names)
        self.assertIn('chatroom_client_idx', index_names)
        self.assertIn('chatroom_provider_idx', index_names)
        self.assertIn('chatroom_last_message_at_idx', index_names)
        self.assertIn('chatroom_deleted_at_idx', index_names)

    def test_unique_constraint_exists(self):
        """Testa que o constraint único está definido."""
        constraints = [c.name for c in ChatRoom._meta.constraints]
        self.assertIn('unique_chatroom_order_client_provider', constraints)

    def test_cascade_delete_when_order_hard_deleted(self):
        """Testa que salas de chat são deletadas quando pedido é hard deleted."""
        chatroom = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user
        )
        chatroom_id = chatroom.id

        # Hard delete do pedido
        self.order.hard_delete()

        # A sala também deve ser deletada (CASCADE)
        self.assertFalse(ChatRoom.all_objects.filter(id=chatroom_id).exists())

    def test_cascade_delete_when_client_hard_deleted(self):
        """Testa que salas de chat são deletadas quando cliente é hard deleted."""
        chatroom = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user
        )
        chatroom_id = chatroom.id

        # Hard delete do cliente
        self.client_user.hard_delete()

        # A sala também deve ser deletada (CASCADE)
        self.assertFalse(ChatRoom.all_objects.filter(id=chatroom_id).exists())

    def test_cascade_delete_when_provider_hard_deleted(self):
        """Testa que salas de chat são deletadas quando prestador é hard deleted."""
        chatroom = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user
        )
        chatroom_id = chatroom.id

        # Hard delete do prestador
        self.provider_user.hard_delete()

        # A sala também deve ser deletada (CASCADE)
        self.assertFalse(ChatRoom.all_objects.filter(id=chatroom_id).exists())

    def test_update_last_message_at_method(self):
        """Testa o método update_last_message_at."""
        chatroom = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user,
            last_message_at=None
        )

        self.assertIsNone(chatroom.last_message_at)

        # Atualiza last_message_at
        before = timezone.now()
        chatroom.update_last_message_at()
        after = timezone.now()
        chatroom.refresh_from_db()

        self.assertIsNotNone(chatroom.last_message_at)
        self.assertGreaterEqual(chatroom.last_message_at, before)
        self.assertLessEqual(chatroom.last_message_at, after)

    def test_update_last_message_at_updates_existing_value(self):
        """Testa que update_last_message_at atualiza valor existente."""
        old_time = timezone.now() - timedelta(days=1)
        chatroom = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user,
            last_message_at=old_time
        )

        self.assertEqual(chatroom.last_message_at, old_time)

        # Atualiza last_message_at
        chatroom.update_last_message_at()
        chatroom.refresh_from_db()

        self.assertGreater(chatroom.last_message_at, old_time)


class MessageModelTestCase(TestCase):
    """Testes unitários para o modelo Message."""

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

        # Cria sala de chat
        self.chatroom = ChatRoom.objects.create(
            order=self.order,
            client=self.client_user,
            provider=self.provider_user
        )

    def test_create_message_with_all_fields(self):
        """Testa criação de mensagem com todos os campos."""
        read_at = timezone.now()
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Olá, como vai?',
            message_type=MessageType.TEXT.value,
            is_read=True,
            read_at=read_at
        )

        self.assertEqual(message.room, self.chatroom)
        self.assertEqual(message.sender, self.client_user)
        self.assertEqual(message.content, 'Olá, como vai?')
        self.assertEqual(message.message_type, MessageType.TEXT.value)
        self.assertTrue(message.is_read)
        self.assertEqual(message.read_at, read_at)
        self.assertIsNotNone(message.created_at)
        self.assertIsNotNone(message.updated_at)
        self.assertIsNone(message.deleted_at)

    def test_message_type_default_is_text(self):
        """Testa que message_type padrão é TEXT."""
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem de texto'
        )
        self.assertEqual(message.message_type, MessageType.TEXT.value)
        self.assertTrue(message.is_text)

    def test_message_type_choices(self):
        """Testa que message_type aceita apenas valores válidos."""
        # TEXT
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem de texto',
            message_type=MessageType.TEXT.value
        )
        self.assertEqual(message.message_type, MessageType.TEXT.value)
        self.assertTrue(message.is_text)
        self.assertFalse(message.is_image)
        self.assertFalse(message.is_file)
        self.assertFalse(message.is_system)

        # IMAGE
        message.message_type = MessageType.IMAGE.value
        message.save()
        self.assertEqual(message.message_type, MessageType.IMAGE.value)
        self.assertFalse(message.is_text)
        self.assertTrue(message.is_image)
        self.assertFalse(message.is_file)
        self.assertFalse(message.is_system)

        # FILE
        message.message_type = MessageType.FILE.value
        message.save()
        self.assertEqual(message.message_type, MessageType.FILE.value)
        self.assertFalse(message.is_text)
        self.assertFalse(message.is_image)
        self.assertTrue(message.is_file)
        self.assertFalse(message.is_system)

        # SYSTEM
        message.message_type = MessageType.SYSTEM.value
        message.save()
        self.assertEqual(message.message_type, MessageType.SYSTEM.value)
        self.assertFalse(message.is_text)
        self.assertFalse(message.is_image)
        self.assertFalse(message.is_file)
        self.assertTrue(message.is_system)

    def test_is_text_property(self):
        """Testa a propriedade is_text."""
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem',
            message_type=MessageType.TEXT.value
        )
        self.assertTrue(message.is_text)

        message.message_type = MessageType.IMAGE.value
        message.save()
        self.assertFalse(message.is_text)

    def test_is_image_property(self):
        """Testa a propriedade is_image."""
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem',
            message_type=MessageType.IMAGE.value
        )
        self.assertTrue(message.is_image)

        message.message_type = MessageType.TEXT.value
        message.save()
        self.assertFalse(message.is_image)

    def test_is_file_property(self):
        """Testa a propriedade is_file."""
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem',
            message_type=MessageType.FILE.value
        )
        self.assertTrue(message.is_file)

        message.message_type = MessageType.TEXT.value
        message.save()
        self.assertFalse(message.is_file)

    def test_is_system_property(self):
        """Testa a propriedade is_system."""
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem',
            message_type=MessageType.SYSTEM.value
        )
        self.assertTrue(message.is_system)

        message.message_type = MessageType.TEXT.value
        message.save()
        self.assertFalse(message.is_system)

    def test_is_read_default_is_false(self):
        """Testa que is_read padrão é False."""
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem'
        )
        self.assertFalse(message.is_read)
        self.assertIsNone(message.read_at)

    def test_is_read_can_be_set_to_true(self):
        """Testa que is_read pode ser definido como True."""
        read_at = timezone.now()
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem',
            is_read=True,
            read_at=read_at
        )
        self.assertTrue(message.is_read)
        self.assertEqual(message.read_at, read_at)

    def test_read_at_is_optional(self):
        """Testa que read_at é opcional."""
        # Mensagem sem read_at
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem',
            is_read=False,
            read_at=None
        )
        self.assertIsNone(message.read_at)

        # Mensagem com read_at
        read_at = timezone.now()
        message.read_at = read_at
        message.save()
        self.assertIsNotNone(message.read_at)

    def test_mark_as_read_method(self):
        """Testa o método mark_as_read."""
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem',
            is_read=False,
            read_at=None
        )

        self.assertFalse(message.is_read)
        self.assertIsNone(message.read_at)

        # Marca como lida
        before = timezone.now()
        message.mark_as_read()
        after = timezone.now()
        message.refresh_from_db()

        self.assertTrue(message.is_read)
        self.assertIsNotNone(message.read_at)
        self.assertGreaterEqual(message.read_at, before)
        self.assertLessEqual(message.read_at, after)

    def test_mark_as_read_does_not_update_if_already_read(self):
        """Testa que mark_as_read não atualiza se já estiver lida."""
        original_read_at = timezone.now() - timedelta(hours=1)
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem',
            is_read=True,
            read_at=original_read_at
        )

        # Tenta marcar como lida novamente
        message.mark_as_read()
        message.refresh_from_db()

        # read_at não deve ter mudado
        self.assertEqual(message.read_at, original_read_at)

    def test_room_foreign_key_relationship(self):
        """Testa relacionamento ForeignKey com ChatRoom."""
        message1 = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem 1'
        )
        message2 = Message.objects.create(
            room=self.chatroom,
            sender=self.provider_user,
            content='Mensagem 2'
        )

        # Verifica relacionamento direto
        self.assertEqual(message1.room, self.chatroom)
        self.assertEqual(message2.room, self.chatroom)

        # Verifica relacionamento reverso
        messages = self.chatroom.messages.all()
        self.assertEqual(messages.count(), 2)
        self.assertIn(message1, messages)
        self.assertIn(message2, messages)

    def test_sender_foreign_key_relationship(self):
        """Testa relacionamento ForeignKey com User (sender)."""
        message1 = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem 1'
        )
        message2 = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem 2'
        )

        # Verifica relacionamento direto
        self.assertEqual(message1.sender, self.client_user)
        self.assertEqual(message2.sender, self.client_user)

        # Verifica relacionamento reverso
        messages = self.client_user.sent_messages.all()
        self.assertEqual(messages.count(), 2)
        self.assertIn(message1, messages)
        self.assertIn(message2, messages)

    def test_content_is_required(self):
        """Testa que content é obrigatório."""
        message = Message(
            room=self.chatroom,
            sender=self.client_user
        )
        with self.assertRaises(ValidationError):
            message.full_clean()

        # Com content, deve funcionar
        message.content = 'Conteúdo da mensagem'
        message.full_clean()  # Não deve levantar exceção

    def test_str_representation(self):
        """Testa a representação string do modelo."""
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem de teste'
        )
        expected = f"Mensagem #{message.id} de {self.client_user.email} em Chat #{self.chatroom.id}"
        self.assertEqual(str(message), expected)

    def test_created_at_auto_now_add(self):
        """Testa que created_at é preenchido automaticamente."""
        before = timezone.now()
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem'
        )
        after = timezone.now()

        self.assertIsNotNone(message.created_at)
        self.assertGreaterEqual(message.created_at, before)
        self.assertLessEqual(message.created_at, after)

    def test_updated_at_auto_now(self):
        """Testa que updated_at é atualizado automaticamente."""
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem'
        )
        original_updated_at = message.updated_at

        # Aguarda um pouco para garantir diferença de tempo
        time.sleep(0.01)

        message.content = 'Mensagem Atualizada'
        message.save()

        self.assertGreater(message.updated_at, original_updated_at)

    def test_soft_delete_functionality(self):
        """Testa funcionalidade de soft delete."""
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem'
        )

        # Mensagem está ativa
        self.assertIsNone(message.deleted_at)
        self.assertTrue(message.is_alive)
        self.assertFalse(message.is_deleted)
        self.assertEqual(Message.objects.count(), 1)

        # Deleta (soft delete)
        message.delete()
        message.refresh_from_db()

        # Mensagem está deletada
        self.assertIsNotNone(message.deleted_at)
        self.assertFalse(message.is_alive)
        self.assertTrue(message.is_deleted)
        self.assertEqual(Message.objects.count(), 0)
        self.assertEqual(Message.all_objects.count(), 1)
        self.assertEqual(Message.deleted_objects.count(), 1)

        # Restaura
        message.restore()
        message.refresh_from_db()

        # Mensagem está ativa novamente
        self.assertIsNone(message.deleted_at)
        self.assertTrue(message.is_alive)
        self.assertFalse(message.is_deleted)
        self.assertEqual(Message.objects.count(), 1)

    def test_ordering_by_created_at_asc(self):
        """Testa que ordenação padrão é por created_at ascendente."""
        message1 = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem 1'
        )

        time.sleep(0.01)

        message2 = Message.objects.create(
            room=self.chatroom,
            sender=self.provider_user,
            content='Mensagem 2'
        )

        messages = list(Message.objects.all())

        # message1 é mais antiga, deve aparecer primeiro
        self.assertEqual(messages[0], message1)
        self.assertEqual(messages[1], message2)

    def test_indexes_exist(self):
        """Testa que os índices foram criados corretamente."""
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem'
        )

        # Testa queries que usam os índices (verifica que não há erros)
        Message.objects.filter(room=self.chatroom).first()
        Message.objects.filter(sender=self.client_user).first()
        Message.objects.filter(created_at__gte=timezone.now() - timedelta(days=1)).first()
        Message.objects.filter(is_read=False).first()
        Message.objects.filter(deleted_at__isnull=True).first()

        # Verifica que os índices estão definidos no Meta
        index_names = [idx.name for idx in Message._meta.indexes]
        self.assertIn('message_room_idx', index_names)
        self.assertIn('message_sender_idx', index_names)
        self.assertIn('message_created_at_idx', index_names)
        self.assertIn('message_is_read_idx', index_names)
        self.assertIn('message_deleted_at_idx', index_names)

    def test_cascade_delete_when_room_hard_deleted(self):
        """Testa que mensagens são deletadas quando sala é hard deleted."""
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem'
        )
        message_id = message.id

        # Hard delete da sala
        self.chatroom.hard_delete()

        # A mensagem também deve ser deletada (CASCADE)
        self.assertFalse(Message.all_objects.filter(id=message_id).exists())

    def test_cascade_delete_when_sender_hard_deleted(self):
        """Testa que mensagens são deletadas quando remetente é hard deleted."""
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem'
        )
        message_id = message.id

        # Hard delete do remetente
        self.client_user.hard_delete()

        # A mensagem também deve ser deletada (CASCADE)
        self.assertFalse(Message.all_objects.filter(id=message_id).exists())

    def test_mark_as_read_updates_read_at(self):
        """Testa que mark_as_read atualiza read_at corretamente."""
        message = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem',
            is_read=False,
            read_at=None
        )

        self.assertIsNone(message.read_at)

        # Marca como lida
        message.mark_as_read()
        message.refresh_from_db()

        self.assertIsNotNone(message.read_at)
        self.assertTrue(message.is_read)

    def test_multiple_messages_in_same_room(self):
        """Testa criação de múltiplas mensagens na mesma sala."""
        message1 = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem 1',
            message_type=MessageType.TEXT.value
        )
        message2 = Message.objects.create(
            room=self.chatroom,
            sender=self.provider_user,
            content='Mensagem 2',
            message_type=MessageType.IMAGE.value
        )
        message3 = Message.objects.create(
            room=self.chatroom,
            sender=self.client_user,
            content='Mensagem 3',
            message_type=MessageType.FILE.value
        )

        messages = self.chatroom.messages.all()
        self.assertEqual(messages.count(), 3)
        self.assertIn(message1, messages)
        self.assertIn(message2, messages)
        self.assertIn(message3, messages)

        # Verifica tipos
        self.assertTrue(message1.is_text)
        self.assertTrue(message2.is_image)
        self.assertTrue(message3.is_file)
