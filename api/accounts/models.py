"""
Models para o app accounts (usuários, perfis, autenticação).
"""
# pyright: reportIncompatibleVariableOverride=false
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from api.utils.models import SoftDeleteMixin
from api.utils.managers import SoftDeleteQuerySet
from api.accounts.enums import UserType


class UserQuerySet(SoftDeleteQuerySet):
    """QuerySet customizado para User com funcionalidades de soft delete."""


class UserManager(UserManager):
    """
    Manager customizado que combina UserManager do Django com Soft Delete.
    
    Sobrescreve create_user e create_superuser para usar email ao invés de username.
    Adiciona funcionalidades de soft delete.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Cria e salva um usuário com o email e senha fornecidos.
        
        Args:
            email: Email do usuário (usado como USERNAME_FIELD)
            password: Senha do usuário
            **extra_fields: Campos extras do modelo User
            
        Returns:
            User: Instância do usuário criado
        """
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        # Usa email como username também (para compatibilidade com AbstractUser)
        extra_fields.setdefault('username', email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Cria e salva um superusuário com o email e senha fornecidos.
        
        Args:
            email: Email do superusuário (usado como USERNAME_FIELD)
            password: Senha do superusuário
            **extra_fields: Campos extras do modelo User
            
        Returns:
            User: Instância do superusuário criado
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superusuário deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusuário deve ter is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

    def get_queryset(self):
        """Retorna queryset filtrando registros deletados."""
        return UserQuerySet(self.model, using=self._db).filter(
            deleted_at__isnull=True
        )

    def all_objects(self):
        """Retorna todos os registros, incluindo deletados."""
        return UserQuerySet(self.model, using=self._db)

    def deleted_objects(self):
        """Retorna apenas registros deletados."""
        return UserQuerySet(self.model, using=self._db).filter(
            deleted_at__isnull=False
        )

    def alive(self):
        """Retorna apenas registros não deletados (alias para get_queryset)."""
        return self.get_queryset()

    def dead(self):
        """Retorna apenas registros deletados."""
        return self.deleted_objects()


class User(SoftDeleteMixin, AbstractUser):
    """
    Modelo de usuário customizado do sistema.
    
    Estende AbstractUser do Django e adiciona funcionalidades específicas:
    - Soft Delete (deleted_at) para exclusão lógica
    - Campos de timestamp (created_at, updated_at)
    - Campo phone para telefone do usuário
    - Tipo de usuário (CLIENT, PROVIDER, ADMIN)
    - Email como USERNAME_FIELD (ao invés de username)
    
    Relacionamentos:
        - provider_profile: Perfil de prestador (OneToOne, opcional)
        - client_profile: Perfil de cliente (OneToOne, opcional)
        - subscriptions: Assinaturas do usuário (relacionamento reverso)
        - orders: Pedidos feitos (através de client_profile)
        - proposals: Propostas feitas (através de provider_profile)
        - reviews_given: Avaliações feitas pelo usuário (relacionamento reverso)
        - reviews_received: Avaliações recebidas pelo usuário (relacionamento reverso)
        - client_chat_rooms: Salas de chat como cliente (relacionamento reverso)
        - provider_chat_rooms: Salas de chat como prestador (relacionamento reverso)
        - sent_messages: Mensagens enviadas (relacionamento reverso)
        - device_tokens: Tokens FCM para notificações push (relacionamento reverso)
        - admin_actions: Ações administrativas (se for admin, relacionamento reverso)
    
    Tipos de usuário:
        - CLIENT: Cliente (padrão)
        - PROVIDER: Prestador de serviços
        - ADMIN: Administrador
    
    Nota: Um usuário pode ser CLIENT e PROVIDER ao mesmo tempo, tendo ambos os perfis.
    
    Exemplo:
        >>> user = User.objects.create_user(
        ...     email='user@example.com',
        ...     first_name='João',
        ...     last_name='Silva',
        ...     password='senha123',
        ...     user_type=UserType.CLIENT.value
        ... )
    """

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
        choices=UserType.choices(),
        default=UserType.CLIENT.value,
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

    # Manager customizado que combina UserManager com Soft Delete
    objects = UserManager()  # type: ignore[assignment]

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
        return self.user_type == UserType.CLIENT.value

    @property
    def is_provider(self):
        """Retorna True se o usuário é um prestador."""
        return self.user_type == UserType.PROVIDER.value

    @property
    def is_admin_user(self):
        """Retorna True se o usuário é um administrador."""
        return self.user_type == UserType.ADMIN.value or self.is_staff or self.is_superuser


class ProviderProfile(SoftDeleteMixin, models.Model):
    """
    Perfil do prestador de serviços.
    
    Relacionamento OneToOne com User.
    Armazena informações específicas de prestadores de serviços, incluindo:
    - Biografia do prestador
    - Avaliação média e total de avaliações
    - Total de pedidos completados
    - Status de verificação pela plataforma
    
    Relacionamentos:
        - user: Usuário associado (OneToOne com User)
        - proposals: Propostas feitas pelo prestador (relacionamento reverso)
    
    Campos calculados:
        - rating_avg: Média de avaliações (0.00 a 5.00)
        - total_reviews: Número total de avaliações recebidas
        - total_orders_completed: Número de pedidos completados
    
    Exemplo:
        >>> profile = ProviderProfile.objects.create(
        ...     user=user,
        ...     bio='Desenvolvedor Full Stack com 10 anos de experiência',
        ...     rating_avg=Decimal('4.8'),
        ...     total_reviews=50,
        ...     total_orders_completed=30,
        ...     is_verified=True
        ... )
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
    Armazena informações específicas de clientes, incluindo endereço completo.
    
    Relacionamentos:
        - user: Usuário associado (OneToOne com User)
        - orders: Pedidos feitos pelo cliente (relacionamento reverso)
    
    Campos de endereço:
        - address: Endereço completo
        - city: Cidade
        - state: Estado (UF)
        - zip_code: CEP
    
    Exemplo:
        >>> profile = ClientProfile.objects.create(
        ...     user=user,
        ...     address='Rua das Flores, 123',
        ...     city='São Paulo',
        ...     state='SP',
        ...     zip_code='01234-567'
        ... )
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
