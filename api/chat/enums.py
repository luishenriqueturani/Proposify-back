"""
Enums e constantes para o app chat.
Centraliza valores de tipos de mensagem e outras constantes para reutilização.
"""
from enum import Enum


class MessageType(str, Enum):
    """
    Tipos possíveis de mensagem no chat.
    
    Uso:
        MessageType.TEXT  # Retorna 'TEXT'
        MessageType.TEXT.value  # Retorna 'TEXT'
        MessageType.TEXT.label  # Retorna 'Texto'
    """
    TEXT = 'TEXT'
    IMAGE = 'IMAGE'
    FILE = 'FILE'
    SYSTEM = 'SYSTEM'

    @property
    def label(self):
        """Retorna o label legível do tipo de mensagem."""
        labels = {
            'TEXT': 'Texto',
            'IMAGE': 'Imagem',
            'FILE': 'Arquivo',
            'SYSTEM': 'Sistema',
        }
        return labels.get(self.value, self.value)

    @classmethod
    def choices(cls):
        """Retorna tuplas (value, label) para uso em Django choices."""
        return [(member.value, member.label) for member in cls]

