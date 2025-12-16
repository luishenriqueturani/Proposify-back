"""
Enums e constantes para o app notifications.
Centraliza valores de tipos de dispositivo e outras constantes para reutilização.
"""
from enum import Enum


class DeviceType(str, Enum):
    """
    Tipos possíveis de dispositivo para notificações push.
    
    Uso:
        DeviceType.IOS  # Retorna 'IOS'
        DeviceType.IOS.value  # Retorna 'IOS'
        DeviceType.IOS.label  # Retorna 'iOS'
    """
    IOS = 'IOS'
    ANDROID = 'ANDROID'
    WEB = 'WEB'

    @property
    def label(self):
        """Retorna o label legível do tipo de dispositivo."""
        labels = {
            'IOS': 'iOS',
            'ANDROID': 'Android',
            'WEB': 'Web',
        }
        return labels.get(self.value, self.value)

    @classmethod
    def choices(cls):
        """Retorna tuplas (value, label) para uso em Django choices."""
        return [(member.value, member.label) for member in cls]

