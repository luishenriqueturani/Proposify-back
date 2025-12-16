"""
Enums e constantes para o app subscriptions.
Centraliza valores de status e outras constantes para reutilização.
"""
from enum import Enum


class SubscriptionStatus(str, Enum):
    """
    Status possíveis para uma assinatura de usuário.
    
    Uso:
        SubscriptionStatus.ACTIVE  # Retorna 'ACTIVE'
        SubscriptionStatus.ACTIVE.value  # Retorna 'ACTIVE'
        SubscriptionStatus.ACTIVE.label  # Retorna 'Ativa'
    """
    ACTIVE = 'ACTIVE'
    CANCELLED = 'CANCELLED'
    EXPIRED = 'EXPIRED'
    SUSPENDED = 'SUSPENDED'

    @property
    def label(self):
        """Retorna o label legível do status."""
        labels = {
            'ACTIVE': 'Ativa',
            'CANCELLED': 'Cancelada',
            'EXPIRED': 'Expirada',
            'SUSPENDED': 'Suspensa',
        }
        return labels.get(self.value, self.value)

    @classmethod
    def choices(cls):
        """Retorna tuplas (value, label) para uso em Django choices."""
        return [(member.value, member.label) for member in cls]


class PaymentStatus(str, Enum):
    """
    Status possíveis para um pagamento.
    
    Uso:
        PaymentStatus.PENDING  # Retorna 'PENDING'
        PaymentStatus.PENDING.value  # Retorna 'PENDING'
        PaymentStatus.PENDING.label  # Retorna 'Pendente'
    """
    PENDING = 'PENDING'
    PAID = 'PAID'
    FAILED = 'FAILED'
    REFUNDED = 'REFUNDED'

    @property
    def label(self):
        """Retorna o label legível do status."""
        labels = {
            'PENDING': 'Pendente',
            'PAID': 'Pago',
            'FAILED': 'Falhou',
            'REFUNDED': 'Reembolsado',
        }
        return labels.get(self.value, self.value)

    @classmethod
    def choices(cls):
        """Retorna tuplas (value, label) para uso em Django choices."""
        return [(member.value, member.label) for member in cls]

