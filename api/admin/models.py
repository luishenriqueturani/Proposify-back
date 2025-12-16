"""
Models para o app admin (auditoria de ações administrativas).
"""
from django.db import models
from api.utils.models import SoftDeleteMixin


class AdminAction(SoftDeleteMixin, models.Model):
    """
    Registro de auditoria de ações administrativas.
    Armazena histórico de ações realizadas por administradores no sistema.
    Nota: Logs de auditoria raramente são deletados, apenas em casos específicos.
    """
    admin_user = models.ForeignKey(  # type: ignore
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='admin_actions',
        verbose_name='Administrador',
        help_text='Usuário administrador que realizou a ação'
    )

    action_type = models.CharField(  # type: ignore
        max_length=100,
        verbose_name='Tipo de Ação',
        help_text='Tipo da ação realizada (ex: USER_DELETE, ORDER_CANCEL, PLAN_UPDATE)'
    )

    target_model = models.CharField(  # type: ignore
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Modelo Alvo',
        help_text='Nome do modelo Django afetado pela ação (ex: User, Order)'
    )

    target_id = models.BigIntegerField(  # type: ignore
        blank=True,
        null=True,
        verbose_name='ID do Alvo',
        help_text='ID do objeto afetado pela ação'
    )

    description = models.TextField(  # type: ignore
        verbose_name='Descrição',
        help_text='Descrição detalhada da ação realizada'
    )

    metadata = models.JSONField(  # type: ignore
        default=dict,
        blank=True,
        verbose_name='Metadados',
        help_text='Informações adicionais da ação em formato JSON'
    )

    ip_address = models.GenericIPAddressField(  # type: ignore
        blank=True,
        null=True,
        verbose_name='Endereço IP',
        help_text='Endereço IP de onde a ação foi realizada'
    )

    # Campos de timestamp
    created_at = models.DateTimeField(  # type: ignore
        auto_now_add=True,
        verbose_name='Data de Criação'
    )

    class Meta:
        verbose_name = 'Ação Administrativa'
        verbose_name_plural = 'Ações Administrativas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin_user'], name='admin_action_user_idx'),
            models.Index(fields=['action_type'], name='admin_action_type_idx'),
            models.Index(fields=['target_model', 'target_id'], name='admin_action_target_idx'),
            models.Index(fields=['created_at'], name='admin_action_created_at_idx'),
            models.Index(fields=['deleted_at'], name='admin_action_deleted_at_idx'),
        ]

    def __str__(self):
        return f"Ação #{self.id} - {self.action_type} por {self.admin_user.email}"
