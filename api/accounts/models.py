"""
Models para o app accounts (usuários, perfis, autenticação).
"""
# pyright: reportIncompatibleVariableOverride=false
from django.contrib.auth.models import AbstractUser
from django.db import models
from api.utils.models import SoftDeleteMixin
from api.utils.managers import SoftDeleteManager


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
    phone = models.CharField(  # type: ignore
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Telefone',
        help_text='Número de telefone do usuário'
    )

    user_type = models.CharField(  # type: ignore
        max_length=10,
        choices=UserType.choices,
        default=UserType.CLIENT,
        verbose_name='Tipo de Usuário',
        help_text='Tipo de usuário: Cliente, Prestador ou Administrador'
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

    # Email como campo único e obrigatório (sobrescreve o campo do AbstractUser)
    email = models.EmailField(
        unique=True,
        verbose_name='Email',
        help_text='Endereço de email do usuário (usado para login)'
    )

    # Usar email como campo de autenticação ao invés de username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    # Redefinir objects para resolver conflito entre SoftDeleteMixin e AbstractUser
    # SoftDeleteManager é compatível em runtime, mas o type checker não reconhece
    # a compatibilidade com UserManager do AbstractUser
    objects = SoftDeleteManager()  # type: ignore[assignment]

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
        return f"{self.email} ({self.get_user_type_display()})"  # type: ignore[attr-defined]

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


class ProviderProfile(SoftDeleteMixin, models.Model):
    """
    Perfil do prestador de serviços.

    Relacionamento OneToOne com User.
    Armazena informações específicas de prestadores de serviços.
    """

    user = models.OneToOneField(  # type: ignore
        User,
        on_delete=models.CASCADE,
        related_name='provider_profile',
        verbose_name='Usuário',
        help_text='Usuário associado a este perfil de prestador'
    )

    bio = models.TextField(  # type: ignore
        blank=True,
        null=True,
        verbose_name='Biografia',
        help_text='Biografia ou descrição do prestador'
    )

    rating_avg = models.DecimalField(  # type: ignore
        max_digits=3,
        decimal_places=2,
        default=0.00,
        verbose_name='Avaliação Média',
        help_text='Média de avaliações recebidas (0.00 a 5.00)'
    )

    total_reviews = models.PositiveIntegerField(  # type: ignore
        default=0,
        verbose_name='Total de Avaliações',
        help_text='Número total de avaliações recebidas'
    )

    total_orders_completed = models.PositiveIntegerField(  # type: ignore
        default=0,
        verbose_name='Pedidos Completados',
        help_text='Número total de pedidos completados'
    )

    is_verified = models.BooleanField(  # type: ignore
        default=False,
        verbose_name='Verificado',
        help_text='Indica se o prestador foi verificado pela plataforma'
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
        verbose_name = 'Perfil de Prestador'
        verbose_name_plural = 'Perfis de Prestadores'
        ordering = ['-rating_avg', '-total_orders_completed']
        indexes = [
            models.Index(fields=['rating_avg'], name='provider_rating_avg_idx'),
            models.Index(fields=['is_verified'], name='provider_is_verified_idx'),
            models.Index(fields=['deleted_at'], name='provider_deleted_at_idx'),
        ]

    def __str__(self):
        return f"Perfil de {self.user.email}"

    def update_rating(self):
        """
        Atualiza a média de avaliações baseado nas reviews recebidas.
        Este método será implementado quando o modelo Review for criado.
        """
        # TODO: Implementar quando Review model estiver disponível
        pass


class ClientProfile(SoftDeleteMixin, models.Model):
    """
    Perfil do cliente.

    Relacionamento OneToOne com User.
    Armazena informações específicas de clientes.
    """

    user = models.OneToOneField(  # type: ignore
        User,
        on_delete=models.CASCADE,
        related_name='client_profile',
        verbose_name='Usuário',
        help_text='Usuário associado a este perfil de cliente'
    )

    address = models.CharField(  # type: ignore
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Endereço',
        help_text='Endereço completo do cliente'
    )

    city = models.CharField(  # type: ignore
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Cidade',
        help_text='Cidade do cliente'
    )

    state = models.CharField(  # type: ignore
        max_length=2,
        blank=True,
        null=True,
        verbose_name='Estado',
        help_text='Estado (UF) do cliente'
    )

    zip_code = models.CharField(  # type: ignore
        max_length=10,
        blank=True,
        null=True,
        verbose_name='CEP',
        help_text='CEP do cliente'
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
        verbose_name = 'Perfil de Cliente'
        verbose_name_plural = 'Perfis de Clientes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['city', 'state'], name='client_location_idx'),
            models.Index(fields=['deleted_at'], name='client_deleted_at_idx'),
        ]

    def __str__(self):
        return f"Perfil de {self.user.email}"
