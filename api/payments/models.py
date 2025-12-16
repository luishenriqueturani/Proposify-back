"""
Models para o app payments (pagamentos de serviços).
"""
from django.db import models
from django.utils import timezone
from api.utils.models import SoftDeleteMixin
from api.subscriptions.enums import PaymentStatus


class Payment(SoftDeleteMixin, models.Model):
    """
    Pagamento de um serviço.
    Representa o pagamento realizado para um pedido/proposta aceita.
    Armazena informações de transação e metadados do gateway de pagamento.
    """
    order = models.ForeignKey(  # type: ignore
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Pedido',
        help_text='Pedido ao qual este pagamento se refere'
    )

    proposal = models.ForeignKey(  # type: ignore
        'orders.Proposal',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Proposta',
        help_text='Proposta aceita que gerou este pagamento'
    )

    amount = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor',
        help_text='Valor do pagamento'
    )

    payment_method = models.CharField(  # type: ignore
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Método de Pagamento',
        help_text='Método utilizado para o pagamento (ex: credit_card, pix, boleto)'
    )

    payment_status = models.CharField(  # type: ignore
        max_length=20,
        choices=PaymentStatus.choices(),
        default=PaymentStatus.PENDING.value,
        verbose_name='Status do Pagamento',
        help_text='Status atual do pagamento'
    )

    transaction_id = models.CharField(  # type: ignore
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        verbose_name='ID da Transação',
        help_text='ID único da transação no gateway de pagamento'
    )

    payment_date = models.DateTimeField(  # type: ignore
        blank=True,
        null=True,
        verbose_name='Data de Pagamento',
        help_text='Data e hora em que o pagamento foi realizado'
    )

    metadata = models.JSONField(  # type: ignore
        default=dict,
        blank=True,
        verbose_name='Metadados',
        help_text='Informações adicionais do pagamento em formato JSON (dados do gateway, etc.)'
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
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order'], name='svc_payment_order_idx'),
            models.Index(fields=['proposal'], name='svc_payment_proposal_idx'),
            models.Index(fields=['payment_status'], name='svc_payment_status_idx'),
            models.Index(fields=['transaction_id'], name='svc_payment_txn_id_idx'),
            models.Index(fields=['payment_date'], name='svc_payment_date_idx'),
            models.Index(fields=['deleted_at'], name='svc_payment_deleted_idx'),
        ]

    def __str__(self):
        return f"Pagamento #{self.id} - R$ {self.amount} ({self.get_payment_status_display()})"  # type: ignore[attr-defined]

    @property
    def is_paid(self):
        """Retorna True se o pagamento foi realizado."""
        return self.payment_status == PaymentStatus.PAID.value

    @property
    def is_pending(self):
        """Retorna True se o pagamento está pendente."""
        return self.payment_status == PaymentStatus.PENDING.value

    @property
    def is_failed(self):
        """Retorna True se o pagamento falhou."""
        return self.payment_status == PaymentStatus.FAILED.value

    @property
    def is_refunded(self):
        """Retorna True se o pagamento foi reembolsado."""
        return self.payment_status == PaymentStatus.REFUNDED.value

    def mark_as_paid(self, transaction_id=None, payment_date=None):
        """
        Marca o pagamento como pago.
        
        Args:
            transaction_id: ID da transação no gateway (opcional)
            payment_date: Data do pagamento (opcional, usa agora se não fornecido)
        """
        self.payment_status = PaymentStatus.PAID.value
        if transaction_id:
            self.transaction_id = transaction_id
        if payment_date:
            self.payment_date = payment_date
        else:
            self.payment_date = timezone.now()
        self.save(update_fields=['payment_status', 'transaction_id', 'payment_date'])

    def mark_as_failed(self, reason=None):
        """
        Marca o pagamento como falhou.
        
        Args:
            reason: Motivo da falha (opcional, será salvo em metadata)
        """
        self.payment_status = PaymentStatus.FAILED.value
        if reason:
            if not self.metadata:
                self.metadata = {}
            self.metadata['failure_reason'] = reason
        self.save(update_fields=['payment_status', 'metadata'])

    def mark_as_refunded(self, refund_transaction_id=None):
        """
        Marca o pagamento como reembolsado.
        
        Args:
            refund_transaction_id: ID da transação de reembolso (opcional)
        """
        self.payment_status = PaymentStatus.REFUNDED.value
        if refund_transaction_id:
            if not self.metadata:
                self.metadata = {}
            self.metadata['refund_transaction_id'] = refund_transaction_id
        self.save(update_fields=['payment_status', 'metadata'])
