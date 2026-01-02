"""
Serializers para o app accounts (autenticação e usuários).
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from api.accounts.models import User, ClientProfile, ProviderProfile
from api.accounts.enums import UserType


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de novos usuários.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text='Senha do usuário (mínimo 8 caracteres)'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Confirmação da senha'
    )
    user_type = serializers.ChoiceField(
        choices=UserType.choices(),
        default=UserType.CLIENT.value,
        help_text='Tipo de usuário: CLIENT ou PROVIDER'
    )

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone',
            'password', 'password_confirm', 'user_type'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        """Valida que as senhas coincidem."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'As senhas não coincidem.'
            })
        return attrs

    def validate_email(self, value):
        """Valida que o email não está em uso."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este email já está em uso.')
        return value.lower()

    def validate_user_type(self, value):
        """Valida que o tipo de usuário é válido (não pode ser ADMIN)."""
        if value == UserType.ADMIN.value:
            raise serializers.ValidationError(
                'Não é possível criar um usuário administrador por este endpoint.'
            )
        return value

    def create(self, validated_data):
        """Cria o usuário e o perfil correspondente."""
        validated_data.pop('password_confirm')
        user_type = validated_data.get('user_type', UserType.CLIENT.value)
        
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data.get('phone'),
            user_type=user_type,
        )
        
        # Cria o perfil correspondente ao tipo de usuário
        if user_type == UserType.CLIENT.value:
            ClientProfile.objects.create(user=user)
        elif user_type == UserType.PROVIDER.value:
            ProviderProfile.objects.create(user=user)
        
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer customizado para login que inclui dados do usuário na resposta.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Adiciona claims customizados ao token
        token['email'] = user.email
        token['user_type'] = user.user_type
        token['full_name'] = user.get_full_name()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Adiciona dados do usuário na resposta
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'user_type': self.user.user_type,
            'is_active': self.user.is_active,
        }
        return data


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para dados do usuário logado.
    """
    full_name = serializers.SerializerMethodField()
    has_client_profile = serializers.SerializerMethodField()
    has_provider_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'user_type', 'is_active', 'date_joined',
            'last_login', 'has_client_profile', 'has_provider_profile',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'email', 'is_active', 'date_joined', 'last_login',
            'created_at', 'updated_at'
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_has_client_profile(self, obj):
        return hasattr(obj, 'client_profile') and obj.client_profile is not None

    def get_has_provider_profile(self, obj):
        return hasattr(obj, 'provider_profile') and obj.provider_profile is not None


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização de dados do usuário logado.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone']

    def validate_phone(self, value):
        """Remove caracteres não numéricos do telefone."""
        if value:
            # Mantém apenas números
            return ''.join(filter(str.isdigit, value))
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer para solicitação de reset de senha.
    """
    email = serializers.EmailField(
        required=True,
        help_text='Email do usuário para reset de senha'
    )

    def validate_email(self, value):
        """Valida e normaliza o email."""
        return value.lower()

    def get_user(self):
        """Retorna o usuário pelo email, ou None se não existir."""
        email = self.validated_data['email']
        try:
            return User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            return None

    def generate_reset_token(self, user):
        """Gera token e UID para reset de senha."""
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return uid, token


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer para confirmação de reset de senha.
    """
    uid = serializers.CharField(
        required=True,
        help_text='UID do usuário (base64)'
    )
    token = serializers.CharField(
        required=True,
        help_text='Token de reset de senha'
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text='Nova senha'
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Confirmação da nova senha'
    )

    def validate_uid(self, value):
        """Valida e decodifica o UID."""
        try:
            user_id = urlsafe_base64_decode(value).decode()
            self.user = User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, User.DoesNotExist):
            raise serializers.ValidationError('UID inválido.')
        return value

    def validate(self, attrs):
        """Valida o token com o usuário e que as senhas coincidem."""
        # Valida que as senhas coincidem
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'As senhas não coincidem.'
            })
        
        # Valida UID e token
        if not hasattr(self, 'user'):
            raise serializers.ValidationError({'uid': 'UID inválido.'})
        
        if not default_token_generator.check_token(self.user, attrs['token']):
            raise serializers.ValidationError({
                'token': 'Token inválido ou expirado.'
            })
        
        return attrs

    def save(self):
        """Salva a nova senha."""
        self.user.set_password(self.validated_data['new_password'])
        self.user.save(update_fields=['password'])
        return self.user


# =============================================================================
# Serializers de Perfil
# =============================================================================


class ProviderProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para perfil de prestador de serviços.
    
    Campos read-only (calculados pelo sistema):
    - rating_avg, total_reviews, total_orders_completed
    
    Campos editáveis:
    - bio
    
    Campos admin-only:
    - is_verified
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = ProviderProfile
        fields = [
            'id', 'user_email', 'user_name', 'bio',
            'rating_avg', 'total_reviews', 'total_orders_completed',
            'is_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'user_name',
            'rating_avg', 'total_reviews', 'total_orders_completed',
            'is_verified', 'created_at', 'updated_at'
        ]

    def get_user_name(self, obj):
        """Retorna o nome completo do usuário."""
        return obj.user.get_full_name()


class ProviderProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização de perfil de prestador.
    """
    class Meta:
        model = ProviderProfile
        fields = ['bio']


class ClientProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para perfil de cliente.
    
    Campos editáveis:
    - address, city, state, zip_code
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    full_address = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = [
            'id', 'user_email', 'user_name',
            'address', 'city', 'state', 'zip_code', 'full_address',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_email', 'user_name', 'full_address', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        """Retorna o nome completo do usuário."""
        return obj.user.get_full_name()

    def get_full_address(self, obj):
        """Retorna o endereço completo formatado."""
        parts = []
        if obj.address:
            parts.append(obj.address)
        if obj.city:
            parts.append(obj.city)
        if obj.state:
            parts.append(obj.state)
        if obj.zip_code:
            parts.append(f"CEP: {obj.zip_code}")
        return ' - '.join(parts) if parts else None


class ClientProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização de perfil de cliente.
    """
    class Meta:
        model = ClientProfile
        fields = ['address', 'city', 'state', 'zip_code']

    def validate_state(self, value):
        """Valida que o estado tem exatamente 2 caracteres (UF)."""
        if value and len(value) != 2:
            raise serializers.ValidationError(
                'O estado deve ter exatamente 2 caracteres (UF).'
            )
        return value.upper() if value else value

    def validate_zip_code(self, value):
        """Valida e formata o CEP."""
        if value:
            # Remove caracteres não numéricos
            digits = ''.join(filter(str.isdigit, value))
            if len(digits) != 8:
                raise serializers.ValidationError(
                    'O CEP deve ter 8 dígitos.'
                )
            # Formata como 00000-000
            return f"{digits[:5]}-{digits[5:]}"
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer combinado: dados do usuário + perfis (cliente e/ou prestador).
    
    Útil para endpoints que precisam retornar todos os dados do usuário
    junto com seus perfis em uma única requisição.
    """
    full_name = serializers.SerializerMethodField()
    client_profile = ClientProfileSerializer(read_only=True)
    provider_profile = ProviderProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'user_type', 'is_active',
            'client_profile', 'provider_profile',
            'date_joined', 'last_login', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'email', 'is_active', 'date_joined', 'last_login',
            'created_at', 'updated_at'
        ]

    def get_full_name(self, obj):
        """Retorna o nome completo do usuário."""
        return obj.get_full_name()


class UserProfileUpdateSerializer(serializers.Serializer):
    """
    Serializer para atualização combinada de usuário + perfil.
    
    Permite atualizar dados do usuário e do perfil em uma única requisição.
    """
    # Dados do usuário
    first_name = serializers.CharField(required=False, max_length=150)
    last_name = serializers.CharField(required=False, max_length=150)
    phone = serializers.CharField(required=False, max_length=20, allow_blank=True)
    
    # Dados do perfil de cliente
    client_address = serializers.CharField(
        required=False, max_length=255, allow_blank=True,
        help_text='Endereço do cliente'
    )
    client_city = serializers.CharField(
        required=False, max_length=100, allow_blank=True,
        help_text='Cidade do cliente'
    )
    client_state = serializers.CharField(
        required=False, max_length=2, allow_blank=True,
        help_text='Estado (UF) do cliente'
    )
    client_zip_code = serializers.CharField(
        required=False, max_length=10, allow_blank=True,
        help_text='CEP do cliente'
    )
    
    # Dados do perfil de prestador
    provider_bio = serializers.CharField(
        required=False, allow_blank=True,
        help_text='Biografia do prestador'
    )

    def validate_phone(self, value):
        """Remove caracteres não numéricos do telefone."""
        if value:
            return ''.join(filter(str.isdigit, value))
        return value

    def validate_client_state(self, value):
        """Valida que o estado tem 2 caracteres."""
        if value and len(value) != 2:
            raise serializers.ValidationError(
                'O estado deve ter exatamente 2 caracteres (UF).'
            )
        return value.upper() if value else value

    def validate_client_zip_code(self, value):
        """Valida e formata o CEP."""
        if value:
            digits = ''.join(filter(str.isdigit, value))
            if len(digits) != 8:
                raise serializers.ValidationError(
                    'O CEP deve ter 8 dígitos.'
                )
            return f"{digits[:5]}-{digits[5:]}"
        return value

    def update(self, instance, validated_data):
        """Atualiza usuário e perfis."""
        # Atualiza dados do usuário
        user_fields = ['first_name', 'last_name', 'phone']
        user_updated = False
        for field in user_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
                user_updated = True
        
        if user_updated:
            instance.save()
        
        # Atualiza perfil de cliente
        client_fields = {
            'client_address': 'address',
            'client_city': 'city',
            'client_state': 'state',
            'client_zip_code': 'zip_code',
        }
        if hasattr(instance, 'client_profile') and instance.client_profile:
            profile = instance.client_profile
            profile_updated = False
            for input_field, model_field in client_fields.items():
                if input_field in validated_data:
                    setattr(profile, model_field, validated_data[input_field])
                    profile_updated = True
            if profile_updated:
                profile.save()
        
        # Atualiza perfil de prestador
        if 'provider_bio' in validated_data:
            if hasattr(instance, 'provider_profile') and instance.provider_profile:
                instance.provider_profile.bio = validated_data['provider_bio']
                instance.provider_profile.save()
        
        return instance
