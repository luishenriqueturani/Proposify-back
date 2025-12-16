"""
Models para o app subscriptions (planos, assinaturas e pagamentos de assinatura).
"""
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from api.utils.models import SoftDeleteMixin
from api.subscriptions.enums import SubscriptionStatus, PaymentStatus


class SubscriptionPlan(SoftDeleteMixin, models.Model):
    """
    Plano de assinatura disponível na plataforma.
    Define limites e recursos para cada tipo de plano.
    """
    name = models.CharField(  # type: ignore
        max_length=100,
        unique=True,
        verbose_name='Nome',
        help_text='Nome do plano de assinatura'
    )

    slug = models.SlugField(  # type: ignore
        max_length=100,
        unique=True,
        blank=True,
        verbose_name='Slug',
        help_text='Slug único para o plano (gerado automaticamente se não fornecido)'
    )

    description = models.TextField(  # type: ignore
        blank=True,
        null=True,
        verbose_name='Descrição',
        help_text='Descrição detalhada do plano'
    )

    price_monthly = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name='Preço Mensal',
        help_text='Preço do plano para assinatura mensal'
    )

    price_yearly = models.DecimalField(  # type: ignore
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name='Preço Anual',
        help_text='Preço do plano para assinatura anual'
    )

    features = models.JSONField(  # type: ignore
        default=dict,
        blank=True,
        verbose_name='Recursos',
        help_text='Recursos do plano em formato JSON (ex: {"feature1": true, "feature2": false})'
    )

    max_orders_per_month = models.PositiveIntegerField(  # type: ignore
        default=0,
        verbose_name='Máximo de Pedidos por Mês',
        help_text='Número máximo de pedidos que o usuário pode fazer por mês (0 = ilimitado)'
    )

    max_proposals_per_order = models.PositiveIntegerField(  # type: ignore
        default=0,
        verbose_name='Máximo de Propostas por Pedido',
        help_text='Número máximo de propostas que o prestador pode fazer por pedido (0 = ilimitado)'
    )

    is_active = models.BooleanField(  # type: ignore
        default=True,
        verbose_name='Ativo',
        help_text='Indica se o plano está ativo e disponível para assinatura'
    )

    is_default = models.BooleanField(  # type: ignore
        default=False,
        verbose_name='Plano Padrão',
        help_text='Indica se este é o plano padrão atribuído a novos usuários'
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
        verbose_name = 'Plano de Assinatura'
        verbose_name_plural = 'Planos de Assinatura'
        ordering = ['price_monthly', 'name']
        indexes = [
            models.Index(fields=['slug'], name='plan_slug_idx'),
            models.Index(fields=['is_active'], name='plan_is_active_idx'),
            models.Index(fields=['is_default'], name='plan_is_default_idx'),
            models.Index(fields=['deleted_at'], name='plan_deleted_at_idx'),
        ]

    def __str__(self):
        return f"{self.name} (R$ {self.price_monthly}/mês)"

    def save(self, *args, **kwargs):
        """Gera slug automaticamente se não fornecido."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class UserSubscription(SoftDeleteMixin, models.Model):
    """
    Assinatura de um usuário em um plano.
    Armazena o histórico de assinaturas do usuário.
    """
    user = models.ForeignKey(  # type: ignore
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Usuário',
        help_text='Usuário que possui esta assinatura'
    )

    plan = models.ForeignKey(  # type: ignore
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='user_subscriptions',
        verbose_name='Plano',
        help_text='Plano de assinatura'
    )

    status = models.CharField(  # type: ignore
        max_length=20,
        choices=SubscriptionStatus.choices(),
        default=SubscriptionStatus.ACTIVE.value,
        verbose_name='Status',
        help_text='Status atual da assinatura'
    )

    start_date = models.DateTimeField(  # type: ignore
        verbose_name='Data de Início',
        help_text='Data e hora de início da assinatura'
    )

    end_date = models.DateTimeField(  # type: ignore
        blank=True,
        null=True,
        verbose_name='Data de Término',
        help_text='Data e hora de término da assinatura (NULL = sem término)'
    )

    auto_renew = models.BooleanField(  # type: ignore
        default=True,
        verbose_name='Renovação Automática',
        help_text='Indica se a assinatura deve ser renovada automaticamente'
    )

    cancelled_at = models.DateTimeField(  # type: ignore
        blank=True,
        null=True,
        verbose_name='Data de Cancelamento',
        help_text='Data e hora em que a assinatura foi cancelada'
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
        verbose_name = 'Assinatura de Usuário'
        verbose_name_plural = 'Assinaturas de Usuários'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user'], name='subscription_user_idx'),
            models.Index(fields=['plan'], name='subscription_plan_idx'),
            models.Index(fields=['status'], name='subscription_status_idx'),
            models.Index(fields=['end_date'], name='subscription_end_date_idx'),
            models.Index(fields=['deleted_at'], name='subscription_deleted_at_idx'),
        ]

    def __str__(self):
        return f"Assinatura #{self.id} - {self.user.email} ({self.plan.name})"

    @property
    def is_active(self):
        """Retorna True se a assinatura está ativa."""
        return self.status == SubscriptionStatus.ACTIVE.value

    @property
    def is_expired(self):
        """Retorna True se a assinatura expirou."""
        if self.end_date:
            return timezone.now() > self.end_date
        return False

    def cancel(self):
        """Cancela a assinatura."""
        if self.status == SubscriptionStatus.ACTIVE.value:
            self.status = SubscriptionStatus.CANCELLED.value
            self.cancelled_at = timezone.now()
            self.auto_renew = False
            self.save(update_fields=['status', 'cancelled_at', 'auto_renew'])


class SubscriptionPayment(SoftDeleteMixin, models.Model):
    """
    Pagamento de uma assinatura.
    Armazena o histórico de pagamentos de assinaturas.
    """
    subscription = models.ForeignKey(  # type: ignore
        UserSubscription,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Assinatura',
        help_text='Assinatura à qual este pagamento pertence'
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

    due_date = models.DateTimeField(  # type: ignore
        verbose_name='Data de Vencimento',
        help_text='Data e hora de vencimento do pagamento'
    )

    metadata = models.JSONField(  # type: ignore
        default=dict,
        blank=True,
        verbose_name='Metadados',
        help_text='Informações adicionais do pagamento em formato JSON'
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
        verbose_name = 'Pagamento de Assinatura'
        verbose_name_plural = 'Pagamentos de Assinatura'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subscription'], name='payment_subscription_idx'),
            models.Index(fields=['payment_status'], name='payment_status_idx'),
            models.Index(fields=['due_date'], name='payment_due_date_idx'),
            models.Index(fields=['transaction_id'], name='payment_transaction_id_idx'),
            models.Index(fields=['deleted_at'], name='payment_deleted_at_idx'),
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
    def is_overdue(self):
        """Retorna True se o pagamento está vencido."""
        if self.due_date and self.payment_status == PaymentStatus.PENDING.value:
            return timezone.now() > self.due_date
        return False
