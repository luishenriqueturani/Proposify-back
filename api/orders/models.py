"""
Models para o app orders (pedidos e propostas).
"""
from django.db import models
from django.utils import timezone
from api.utils.models import SoftDeleteMixin


class Order(SoftDeleteMixin, models.Model):
    """
    Pedido de serviço feito pelo cliente.
    Representa uma solicitação de serviço que pode receber propostas de prestadores.
    """
    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        ACCEPTED = 'ACCEPTED', 'Aceito'
        IN_PROGRESS = 'IN_PROGRESS', 'Em Progresso'
        COMPLETED = 'COMPLETED', 'Completado'
        CANCELLED = 'CANCELLED', 'Cancelado'

    client = models.ForeignKey(  # type: ignore
        'accounts.ClientProfile',
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Cliente',
        help_text='Cliente que fez o pedido'
    )

    service = models.ForeignKey(  # type: ignore
        'services.Service',
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Serviço',
        help_text='Serviço solicitado'
    )

    title = models.CharField(  # type: ignore
        max_length=200,
        verbose_name='Título',
        help_text='Título do pedido'
    )

    description = models.TextField(  # type: ignore
        verbose_name='Descrição',
        help_text='Descrição detalhada do pedido'
    )

    budget_min = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        verbose_name='Orçamento Mínimo',
        help_text='Valor mínimo do orçamento'
    )

    budget_max = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        verbose_name='Orçamento Máximo',
        help_text='Valor máximo do orçamento'
    )

    deadline = models.DateTimeField(  # type: ignore
        verbose_name='Prazo',
        help_text='Data limite para conclusão do serviço'
    )

    status = models.CharField(  # type: ignore
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        verbose_name='Status',
        help_text='Status atual do pedido'
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
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client'], name='order_client_idx'),
            models.Index(fields=['service'], name='order_service_idx'),
            models.Index(fields=['status'], name='order_status_idx'),
            models.Index(fields=['deadline'], name='order_deadline_idx'),
            models.Index(fields=['deleted_at'], name='order_deleted_at_idx'),
        ]

    def __str__(self):
        return f"Pedido #{self.id}: {self.title} ({self.get_status_display()})"  # type: ignore[attr-defined]

    @property
    def is_pending(self):
        """Retorna True se o pedido está pendente."""
        return self.status == self.OrderStatus.PENDING

    @property
    def is_accepted(self):
        """Retorna True se o pedido foi aceito."""
        return self.status == self.OrderStatus.ACCEPTED

    @property
    def is_completed(self):
        """Retorna True se o pedido foi completado."""
        return self.status == self.OrderStatus.COMPLETED

    @property
    def is_cancelled(self):
        """Retorna True se o pedido foi cancelado."""
        return self.status == self.OrderStatus.CANCELLED

    def can_be_cancelled(self):
        """Retorna True se o pedido pode ser cancelado."""
        return self.status in [self.OrderStatus.PENDING, self.OrderStatus.ACCEPTED]


class Proposal(SoftDeleteMixin, models.Model):
    """
    Proposta feita por um prestador em resposta a um pedido.
    Representa uma oferta de serviço com preço e prazo estimado.
    """
    class ProposalStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        ACCEPTED = 'ACCEPTED', 'Aceita'
        DECLINED = 'DECLINED', 'Recusada'
        EXPIRED = 'EXPIRED', 'Expirada'

    order = models.ForeignKey(  # type: ignore
        Order,
        on_delete=models.CASCADE,
        related_name='proposals',
        verbose_name='Pedido',
        help_text='Pedido ao qual esta proposta se refere'
    )

    provider = models.ForeignKey(  # type: ignore
        'accounts.ProviderProfile',
        on_delete=models.CASCADE,
        related_name='proposals',
        verbose_name='Prestador',
        help_text='Prestador que fez a proposta'
    )

    message = models.TextField(  # type: ignore
        verbose_name='Mensagem',
        help_text='Mensagem explicativa da proposta'
    )

    price = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        verbose_name='Preço',
        help_text='Preço proposto para o serviço'
    )

    estimated_days = models.PositiveIntegerField(  # type: ignore
        verbose_name='Prazo Estimado (dias)',
        help_text='Número de dias estimados para conclusão do serviço'
    )

    status = models.CharField(  # type: ignore
        max_length=20,
        choices=ProposalStatus.choices,
        default=ProposalStatus.PENDING,
        verbose_name='Status',
        help_text='Status atual da proposta'
    )

    expires_at = models.DateTimeField(  # type: ignore
        blank=True,
        null=True,
        verbose_name='Data de Expiração',
        help_text='Data e hora em que a proposta expira (opcional)'
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
        verbose_name = 'Proposta'
        verbose_name_plural = 'Propostas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order'], name='proposal_order_idx'),
            models.Index(fields=['provider'], name='proposal_provider_idx'),
            models.Index(fields=['status'], name='proposal_status_idx'),
            models.Index(fields=['expires_at'], name='proposal_expires_at_idx'),
            models.Index(fields=['deleted_at'], name='proposal_deleted_at_idx'),
        ]

    def __str__(self):
        return f"Proposta #{self.id} para Pedido #{self.order.id} ({self.get_status_display()})"  # type: ignore[attr-defined]

    @property
    def is_pending(self):
        """Retorna True se a proposta está pendente."""
        return self.status == self.ProposalStatus.PENDING

    @property
    def is_accepted(self):
        """Retorna True se a proposta foi aceita."""
        return self.status == self.ProposalStatus.ACCEPTED

    @property
    def is_expired(self):
        """Retorna True se a proposta expirou."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def can_be_accepted(self):
        """Retorna True se a proposta pode ser aceita."""
        return self.status == self.ProposalStatus.PENDING and not self.is_expired

    def can_be_declined(self):
        """Retorna True se a proposta pode ser recusada."""
        return self.status == self.ProposalStatus.PENDING
