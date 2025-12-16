"""
Models para o app accounts (usuários, perfis, autenticação).
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from api.utils.models import SoftDeleteMixin


class User(SoftDeleteMixin, AbstractUser):
    """
    Modelo de usuário customizado.
    
    Estende AbstractUser e adiciona:
    - Soft Delete (deleted_at)
    - Campos de timestamp (created_at, updated_at)
    - Campo phone
    - Tipo de usuário (CLIENT, PROVIDER, ADMIN)
    """
    
    class UserType(models.TextChoices):
        CLIENT = 'CLIENT', 'Cliente'
        PROVIDER = 'PROVIDER', 'Prestador'
        ADMIN = 'ADMIN', 'Administrador'
    
    # Campos adicionais
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Telefone',
        help_text='Número de telefone do usuário'
    )
    
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.CLIENT,
        verbose_name='Tipo de Usuário',
        help_text='Tipo de usuário: Cliente, Prestador ou Administrador'
    )
    
    # Campos de timestamp
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Criação'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Data de Atualização'
    )
    
    # Email como campo único e obrigatório (sobrescreve o campo do AbstractUser)
    email = models.EmailField(
        unique=True,
        verbose_name='Email',
        help_text='Endereço de email do usuário (usado para login)'
    )
    
    # Usar email como campo de autenticação ao invés de username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email'], name='user_email_idx'),
            models.Index(fields=['user_type'], name='user_type_idx'),
            models.Index(fields=['deleted_at'], name='user_deleted_at_idx'),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.get_user_type_display()})"
    
    @property
    def is_client(self):
        """Retorna True se o usuário é um cliente."""
        return self.user_type == self.UserType.CLIENT
    
    @property
    def is_provider(self):
        """Retorna True se o usuário é um prestador."""
        return self.user_type == self.UserType.PROVIDER
    
    @property
    def is_admin_user(self):
        """Retorna True se o usuário é um administrador."""
        return self.user_type == self.UserType.ADMIN or self.is_staff or self.is_superuser
