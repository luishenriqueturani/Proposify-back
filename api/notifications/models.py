"""
Models para o app notifications (tokens de dispositivo para notificações push).
"""
from django.db import models
from api.utils.models import SoftDeleteMixin
from api.notifications.enums import DeviceType


class DeviceToken(SoftDeleteMixin, models.Model):
    """
    Token de dispositivo para notificações push via Firebase Cloud Messaging (FCM).
    Armazena tokens de dispositivos dos usuários para envio de notificações.
    Preparado para integração futura com Firebase Cloud Messaging.
    """
    user = models.ForeignKey(  # type: ignore
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='device_tokens',
        verbose_name='Usuário',
        help_text='Usuário proprietário do dispositivo'
    )

    token = models.CharField(  # type: ignore
        max_length=255,
        unique=True,
        verbose_name='Token',
        help_text='Token único do dispositivo para notificações push (FCM)'
    )

    device_type = models.CharField(  # type: ignore
        max_length=20,
        choices=DeviceType.choices(),
        verbose_name='Tipo de Dispositivo',
        help_text='Tipo do dispositivo: iOS, Android ou Web'
    )

    device_id = models.CharField(  # type: ignore
        max_length=255,
        blank=True,
        null=True,
        verbose_name='ID do Dispositivo',
        help_text='ID único do dispositivo (opcional)'
    )

    is_active = models.BooleanField(  # type: ignore
        default=True,
        verbose_name='Ativo',
        help_text='Indica se o token está ativo e pode receber notificações'
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
        verbose_name = 'Token de Dispositivo'
        verbose_name_plural = 'Tokens de Dispositivos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user'], name='device_token_user_idx'),
            models.Index(fields=['token'], name='device_token_token_idx'),
            models.Index(fields=['device_type'], name='device_token_type_idx'),
            models.Index(fields=['is_active'], name='device_token_active_idx'),
            models.Index(fields=['deleted_at'], name='device_token_deleted_idx'),
        ]

    def __str__(self):
        return f"Token #{self.id} - {self.user.email} ({self.get_device_type_display()})"  # type: ignore[attr-defined]

    @property
    def is_ios(self):
        """Retorna True se o dispositivo é iOS."""
        return self.device_type == DeviceType.IOS.value

    @property
    def is_android(self):
        """Retorna True se o dispositivo é Android."""
        return self.device_type == DeviceType.ANDROID.value

    @property
    def is_web(self):
        """Retorna True se o dispositivo é Web."""
        return self.device_type == DeviceType.WEB.value
