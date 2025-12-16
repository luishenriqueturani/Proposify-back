"""
Models para o app chat (salas de chat e mensagens).
"""
from django.db import models
from django.utils import timezone
from api.utils.models import SoftDeleteMixin
from api.chat.enums import MessageType


class ChatRoom(SoftDeleteMixin, models.Model):
    """
    Sala de chat entre cliente e prestador.
    Criada automaticamente quando uma proposta é aceita ou quando cliente/prestador iniciam conversa.
    """
    order = models.ForeignKey(  # type: ignore
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='chat_rooms',
        verbose_name='Pedido',
        help_text='Pedido relacionado a esta sala de chat'
    )

    client = models.ForeignKey(  # type: ignore
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='client_chat_rooms',
        verbose_name='Cliente',
        help_text='Cliente participante da conversa'
    )

    provider = models.ForeignKey(  # type: ignore
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='provider_chat_rooms',
        verbose_name='Prestador',
        help_text='Prestador participante da conversa'
    )

    # Campos de timestamp
    created_at = models.DateTimeField(  # type: ignore
        auto_now_add=True,
        verbose_name='Data de Criação'
    )

    updated_at = models.DateTimeField(  # type: ignore
        auto_now=True,
        verbose_name='Data de Atualização'
    )

    last_message_at = models.DateTimeField(  # type: ignore
        blank=True,
        null=True,
        verbose_name='Última Mensagem',
        help_text='Data e hora da última mensagem enviada na sala'
    )

    class Meta:
        verbose_name = 'Sala de Chat'
        verbose_name_plural = 'Salas de Chat'
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['order'], name='chatroom_order_idx'),
            models.Index(fields=['client'], name='chatroom_client_idx'),
            models.Index(fields=['provider'], name='chatroom_provider_idx'),
            models.Index(fields=['last_message_at'], name='chatroom_last_message_at_idx'),
            models.Index(fields=['deleted_at'], name='chatroom_deleted_at_idx'),
        ]
        # Índice único: (order, client, provider)
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'client', 'provider'],
                name='unique_chatroom_order_client_provider'
            )
        ]

    def __str__(self):
        return f"Chat #{self.id} - Pedido #{self.order.id} ({self.client.email} <-> {self.provider.email})"

    def update_last_message_at(self):
        """Atualiza o timestamp da última mensagem."""
        self.last_message_at = timezone.now()
        self.save(update_fields=['last_message_at'])


class Message(SoftDeleteMixin, models.Model):
    """
    Mensagem enviada em uma sala de chat.
    Suporta diferentes tipos: texto, imagem, arquivo e mensagens do sistema.
    """
    room = models.ForeignKey(  # type: ignore
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Sala de Chat',
        help_text='Sala de chat à qual esta mensagem pertence'
    )

    sender = models.ForeignKey(  # type: ignore
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Remetente',
        help_text='Usuário que enviou a mensagem'
    )

    content = models.TextField(  # type: ignore
        verbose_name='Conteúdo',
        help_text='Conteúdo da mensagem'
    )

    message_type = models.CharField(  # type: ignore
        max_length=20,
        choices=MessageType.choices(),
        default=MessageType.TEXT.value,
        verbose_name='Tipo de Mensagem',
        help_text='Tipo da mensagem: texto, imagem, arquivo ou sistema'
    )

    is_read = models.BooleanField(  # type: ignore
        default=False,
        verbose_name='Lida',
        help_text='Indica se a mensagem foi lida pelo destinatário'
    )

    read_at = models.DateTimeField(  # type: ignore
        blank=True,
        null=True,
        verbose_name='Data de Leitura',
        help_text='Data e hora em que a mensagem foi lida'
    )

    # Campos de timestamp
    created_at = models.DateTimeField(  # type: ignore
        auto_now_add=True,
        verbose_name='Data de Criação'
    )

    updated_at = models.DateTimeField(  # type: ignore
        auto_now=True,
        verbose_name='Data de Atualização'
    )

    class Meta:
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['room'], name='message_room_idx'),
            models.Index(fields=['sender'], name='message_sender_idx'),
            models.Index(fields=['created_at'], name='message_created_at_idx'),
            models.Index(fields=['is_read'], name='message_is_read_idx'),
            models.Index(fields=['deleted_at'], name='message_deleted_at_idx'),
        ]

    def __str__(self):
        return f"Mensagem #{self.id} de {self.sender.email} em Chat #{self.room.id}"

    def mark_as_read(self):
        """Marca a mensagem como lida."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    @property
    def is_text(self):
        """Retorna True se a mensagem é do tipo texto."""
        return self.message_type == MessageType.TEXT.value

    @property
    def is_image(self):
        """Retorna True se a mensagem é do tipo imagem."""
        return self.message_type == MessageType.IMAGE.value

    @property
    def is_file(self):
        """Retorna True se a mensagem é do tipo arquivo."""
        return self.message_type == MessageType.FILE.value

    @property
    def is_system(self):
        """Retorna True se a mensagem é do tipo sistema."""
        return self.message_type == MessageType.SYSTEM.value
