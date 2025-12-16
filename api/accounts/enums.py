"""
Enums e constantes para o app accounts.
Centraliza valores de tipos de usuário e outras constantes para reutilização.
"""
from enum import Enum


class UserType(str, Enum):
    """
    Tipos possíveis de usuário no sistema.
    
    Uso:
        UserType.CLIENT  # Retorna 'CLIENT'
        UserType.CLIENT.value  # Retorna 'CLIENT'
        UserType.CLIENT.label  # Retorna 'Cliente'
    """
    CLIENT = 'CLIENT'
    PROVIDER = 'PROVIDER'
    ADMIN = 'ADMIN'

    @property
    def label(self):
        """Retorna o label legível do tipo de usuário."""
        labels = {
            'CLIENT': 'Cliente',
            'PROVIDER': 'Prestador',
            'ADMIN': 'Administrador',
        }
        return labels.get(self.value, self.value)

    @classmethod
    def choices(cls):
        """Retorna tuplas (value, label) para uso em Django choices."""
        return [(member.value, member.label) for member in cls]

