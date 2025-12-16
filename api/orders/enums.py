"""
Enums e constantes para o app orders.
Centraliza valores de status e outras constantes para reutilização.
"""
from enum import Enum


class OrderStatus(str, Enum):
    """
    Status possíveis para um pedido.
    
    Uso:
        OrderStatus.PENDING  # Retorna 'PENDING'
        OrderStatus.PENDING.value  # Retorna 'PENDING'
        OrderStatus.PENDING.label  # Retorna 'Pendente'
    """
    PENDING = 'PENDING'
    ACCEPTED = 'ACCEPTED'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'

    @property
    def label(self):
        """Retorna o label legível do status."""
        labels = {
            'PENDING': 'Pendente',
            'ACCEPTED': 'Aceito',
            'IN_PROGRESS': 'Em Progresso',
            'COMPLETED': 'Completado',
            'CANCELLED': 'Cancelado',
        }
        return labels.get(self.value, self.value)

    @classmethod
    def choices(cls):
        """Retorna tuplas (value, label) para uso em Django choices."""
        return [(member.value, member.label) for member in cls]


class ProposalStatus(str, Enum):
    """
    Status possíveis para uma proposta.
    
    Uso:
        ProposalStatus.PENDING  # Retorna 'PENDING'
        ProposalStatus.PENDING.value  # Retorna 'PENDING'
        ProposalStatus.PENDING.label  # Retorna 'Pendente'
    """
    PENDING = 'PENDING'
    ACCEPTED = 'ACCEPTED'
    DECLINED = 'DECLINED'
    EXPIRED = 'EXPIRED'

    @property
    def label(self):
        """Retorna o label legível do status."""
        labels = {
            'PENDING': 'Pendente',
            'ACCEPTED': 'Aceita',
            'DECLINED': 'Recusada',
            'EXPIRED': 'Expirada',
        }
        return labels.get(self.value, self.value)

    @classmethod
    def choices(cls):
        """Retorna tuplas (value, label) para uso em Django choices."""
        return [(member.value, member.label) for member in cls]

