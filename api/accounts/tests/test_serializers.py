"""
Testes unitários para os serializers do app accounts.
"""
from django.test import TestCase
from decimal import Decimal
import uuid

from api.accounts.models import User, ClientProfile, ProviderProfile
from api.accounts.enums import UserType
from api.accounts.serializers import (
    UserRegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
    ProviderProfileSerializer,
    ProviderProfileUpdateSerializer,
    ClientProfileSerializer,
    ClientProfileUpdateSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
)


class UserRegisterSerializerTestCase(TestCase):
    """Testes para o UserRegisterSerializer."""

    def test_valid_registration_data(self):
        """Testa registro com dados válidos."""
        data = {
            'email': f'test_{uuid.uuid4().hex[:8]}@example.com',
            'first_name': 'João',
            'last_name': 'Silva',
            'password': 'senha@segura123',
            'password_confirm': 'senha@segura123',
            'user_type': UserType.CLIENT.value,
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_password_mismatch(self):
        """Testa que senhas diferentes geram erro."""
        data = {
            'email': f'test_{uuid.uuid4().hex[:8]}@example.com',
            'first_name': 'João',
            'last_name': 'Silva',
            'password': 'senha@segura123',
            'password_confirm': 'outrasenha123',
            'user_type': UserType.CLIENT.value,
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password_confirm', serializer.errors)

    def test_duplicate_email(self):
        """Testa que email duplicado gera erro."""
        email = f'test_{uuid.uuid4().hex[:8]}@example.com'
        User.objects.create_user(
            email=email,
            first_name='Existing',
            last_name='User',
            password='testpass123'
        )
        data = {
            'email': email,
            'first_name': 'João',
            'last_name': 'Silva',
            'password': 'senha@segura123',
            'password_confirm': 'senha@segura123',
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_cannot_register_as_admin(self):
        """Testa que não é possível registrar como ADMIN."""
        data = {
            'email': f'test_{uuid.uuid4().hex[:8]}@example.com',
            'first_name': 'João',
            'last_name': 'Silva',
            'password': 'senha@segura123',
            'password_confirm': 'senha@segura123',
            'user_type': UserType.ADMIN.value,
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('user_type', serializer.errors)

    def test_creates_client_profile(self):
        """Testa que perfil de cliente é criado automaticamente."""
        data = {
            'email': f'test_{uuid.uuid4().hex[:8]}@example.com',
            'first_name': 'João',
            'last_name': 'Silva',
            'password': 'senha@segura123',
            'password_confirm': 'senha@segura123',
            'user_type': UserType.CLIENT.value,
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertTrue(hasattr(user, 'client_profile'))

    def test_creates_provider_profile(self):
        """Testa que perfil de prestador é criado automaticamente."""
        data = {
            'email': f'test_{uuid.uuid4().hex[:8]}@example.com',
            'first_name': 'João',
            'last_name': 'Silva',
            'password': 'senha@segura123',
            'password_confirm': 'senha@segura123',
            'user_type': UserType.PROVIDER.value,
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertTrue(hasattr(user, 'provider_profile'))


class UserSerializerTestCase(TestCase):
    """Testes para o UserSerializer."""

    def setUp(self):
        """Cria usuário de teste."""
        self.user = User.objects.create_user(
            email=f'test_{uuid.uuid4().hex[:8]}@example.com',
            first_name='João',
            last_name='Silva',
            password='testpass123',
        )
        ClientProfile.objects.create(user=self.user)

    def test_serializes_user_data(self):
        """Testa serialização de dados do usuário."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['first_name'], 'João')
        self.assertEqual(data['last_name'], 'Silva')
        self.assertEqual(data['full_name'], 'João Silva')
        self.assertTrue(data['has_client_profile'])
        self.assertFalse(data['has_provider_profile'])

    def test_read_only_fields(self):
        """Testa que campos read_only não podem ser alterados."""
        serializer = UserSerializer(self.user, data={'email': 'new@example.com'}, partial=True)
        self.assertTrue(serializer.is_valid())
        # email não deve estar nos validated_data pois é read_only
        self.assertNotIn('email', serializer.validated_data)


class UserUpdateSerializerTestCase(TestCase):
    """Testes para o UserUpdateSerializer."""

    def setUp(self):
        """Cria usuário de teste."""
        self.user = User.objects.create_user(
            email=f'test_{uuid.uuid4().hex[:8]}@example.com',
            first_name='João',
            last_name='Silva',
            password='testpass123',
        )

    def test_update_user_data(self):
        """Testa atualização de dados do usuário."""
        serializer = UserUpdateSerializer(
            self.user,
            data={'first_name': 'José', 'phone': '11999998888'},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.first_name, 'José')
        self.assertEqual(user.phone, '11999998888')

    def test_phone_validation_strips_non_numeric(self):
        """Testa que telefone mantém apenas números."""
        serializer = UserUpdateSerializer(
            self.user,
            data={'phone': '(11) 99999-8888'},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['phone'], '11999998888')


# =============================================================================
# Testes de Serializers de Perfil
# =============================================================================


class ProviderProfileSerializerTestCase(TestCase):
    """Testes para o ProviderProfileSerializer."""

    def setUp(self):
        """Cria usuário e perfil de teste."""
        self.user = User.objects.create_user(
            email=f'provider_{uuid.uuid4().hex[:8]}@example.com',
            first_name='João',
            last_name='Prestador',
            password='testpass123',
            user_type=UserType.PROVIDER.value,
        )
        self.profile = ProviderProfile.objects.create(
            user=self.user,
            bio='Desenvolvedor Full Stack',
            rating_avg=Decimal('4.50'),
            total_reviews=10,
            total_orders_completed=25,
            is_verified=True
        )

    def test_serializes_provider_profile(self):
        """Testa serialização do perfil de prestador."""
        serializer = ProviderProfileSerializer(self.profile)
        data = serializer.data
        
        self.assertEqual(data['id'], self.profile.id)
        self.assertEqual(data['user_email'], self.user.email)
        self.assertEqual(data['user_name'], 'João Prestador')
        self.assertEqual(data['bio'], 'Desenvolvedor Full Stack')
        self.assertEqual(Decimal(data['rating_avg']), Decimal('4.50'))
        self.assertEqual(data['total_reviews'], 10)
        self.assertEqual(data['total_orders_completed'], 25)
        self.assertTrue(data['is_verified'])

    def test_read_only_fields(self):
        """Testa que campos calculados são read-only."""
        serializer = ProviderProfileSerializer(
            self.profile,
            data={'rating_avg': '5.00', 'total_reviews': 100},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        # Campos read-only não devem estar nos validated_data
        self.assertNotIn('rating_avg', serializer.validated_data)
        self.assertNotIn('total_reviews', serializer.validated_data)


class ProviderProfileUpdateSerializerTestCase(TestCase):
    """Testes para o ProviderProfileUpdateSerializer."""

    def setUp(self):
        """Cria usuário e perfil de teste."""
        self.user = User.objects.create_user(
            email=f'provider_{uuid.uuid4().hex[:8]}@example.com',
            first_name='João',
            last_name='Prestador',
            password='testpass123',
            user_type=UserType.PROVIDER.value,
        )
        self.profile = ProviderProfile.objects.create(user=self.user)

    def test_update_bio(self):
        """Testa atualização da bio."""
        serializer = ProviderProfileUpdateSerializer(
            self.profile,
            data={'bio': 'Nova biografia do prestador'},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        profile = serializer.save()
        self.assertEqual(profile.bio, 'Nova biografia do prestador')


class ClientProfileSerializerTestCase(TestCase):
    """Testes para o ClientProfileSerializer."""

    def setUp(self):
        """Cria usuário e perfil de teste."""
        self.user = User.objects.create_user(
            email=f'client_{uuid.uuid4().hex[:8]}@example.com',
            first_name='Maria',
            last_name='Cliente',
            password='testpass123',
            user_type=UserType.CLIENT.value,
        )
        self.profile = ClientProfile.objects.create(
            user=self.user,
            address='Rua das Flores, 123',
            city='São Paulo',
            state='SP',
            zip_code='01234-567'
        )

    def test_serializes_client_profile(self):
        """Testa serialização do perfil de cliente."""
        serializer = ClientProfileSerializer(self.profile)
        data = serializer.data
        
        self.assertEqual(data['id'], self.profile.id)
        self.assertEqual(data['user_email'], self.user.email)
        self.assertEqual(data['user_name'], 'Maria Cliente')
        self.assertEqual(data['address'], 'Rua das Flores, 123')
        self.assertEqual(data['city'], 'São Paulo')
        self.assertEqual(data['state'], 'SP')
        self.assertEqual(data['zip_code'], '01234-567')

    def test_full_address_formatted(self):
        """Testa que full_address é formatado corretamente."""
        serializer = ClientProfileSerializer(self.profile)
        data = serializer.data
        
        self.assertIn('Rua das Flores, 123', data['full_address'])
        self.assertIn('São Paulo', data['full_address'])
        self.assertIn('SP', data['full_address'])
        self.assertIn('CEP: 01234-567', data['full_address'])

    def test_full_address_with_partial_data(self):
        """Testa full_address com dados parciais."""
        profile = ClientProfile.objects.create(
            user=User.objects.create_user(
                email=f'partial_{uuid.uuid4().hex[:8]}@example.com',
                first_name='Parcial',
                last_name='User',
                password='testpass123',
            ),
            city='Rio de Janeiro'
        )
        serializer = ClientProfileSerializer(profile)
        
        self.assertEqual(serializer.data['full_address'], 'Rio de Janeiro')


class ClientProfileUpdateSerializerTestCase(TestCase):
    """Testes para o ClientProfileUpdateSerializer."""

    def setUp(self):
        """Cria usuário e perfil de teste."""
        self.user = User.objects.create_user(
            email=f'client_{uuid.uuid4().hex[:8]}@example.com',
            first_name='Maria',
            last_name='Cliente',
            password='testpass123',
        )
        self.profile = ClientProfile.objects.create(user=self.user)

    def test_update_address(self):
        """Testa atualização de endereço."""
        serializer = ClientProfileUpdateSerializer(
            self.profile,
            data={
                'address': 'Rua Nova, 456',
                'city': 'Curitiba',
                'state': 'pr',
                'zip_code': '80000000'
            }
        )
        self.assertTrue(serializer.is_valid())
        profile = serializer.save()
        
        self.assertEqual(profile.address, 'Rua Nova, 456')
        self.assertEqual(profile.city, 'Curitiba')
        self.assertEqual(profile.state, 'PR')  # Deve ser uppercase
        self.assertEqual(profile.zip_code, '80000-000')  # Deve ser formatado

    def test_state_validation(self):
        """Testa validação de estado (deve ter 2 caracteres)."""
        serializer = ClientProfileUpdateSerializer(
            self.profile,
            data={'state': 'São Paulo'},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('state', serializer.errors)

    def test_zip_code_validation(self):
        """Testa validação de CEP (deve ter 8 dígitos)."""
        serializer = ClientProfileUpdateSerializer(
            self.profile,
            data={'zip_code': '123'},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('zip_code', serializer.errors)


class UserProfileSerializerTestCase(TestCase):
    """Testes para o UserProfileSerializer (combinado)."""

    def setUp(self):
        """Cria usuário com ambos os perfis."""
        self.user = User.objects.create_user(
            email=f'combined_{uuid.uuid4().hex[:8]}@example.com',
            first_name='João',
            last_name='Completo',
            password='testpass123',
            user_type=UserType.PROVIDER.value,
        )
        self.client_profile = ClientProfile.objects.create(
            user=self.user,
            city='São Paulo',
            state='SP'
        )
        self.provider_profile = ProviderProfile.objects.create(
            user=self.user,
            bio='Prestador experiente',
            rating_avg=Decimal('4.80')
        )

    def test_serializes_user_with_profiles(self):
        """Testa serialização de usuário com ambos os perfis."""
        serializer = UserProfileSerializer(self.user)
        data = serializer.data
        
        # Dados do usuário
        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['full_name'], 'João Completo')
        
        # Perfil de cliente
        self.assertIsNotNone(data['client_profile'])
        self.assertEqual(data['client_profile']['city'], 'São Paulo')
        
        # Perfil de prestador
        self.assertIsNotNone(data['provider_profile'])
        self.assertEqual(data['provider_profile']['bio'], 'Prestador experiente')

    def test_serializes_user_without_profiles(self):
        """Testa serialização de usuário sem perfis."""
        user = User.objects.create_user(
            email=f'no_profile_{uuid.uuid4().hex[:8]}@example.com',
            first_name='Sem',
            last_name='Perfil',
            password='testpass123',
        )
        serializer = UserProfileSerializer(user)
        data = serializer.data
        
        self.assertIsNone(data['client_profile'])
        self.assertIsNone(data['provider_profile'])


class UserProfileUpdateSerializerTestCase(TestCase):
    """Testes para o UserProfileUpdateSerializer."""

    def setUp(self):
        """Cria usuário com perfis."""
        self.user = User.objects.create_user(
            email=f'update_{uuid.uuid4().hex[:8]}@example.com',
            first_name='João',
            last_name='Original',
            password='testpass123',
        )
        self.client_profile = ClientProfile.objects.create(user=self.user)
        self.provider_profile = ProviderProfile.objects.create(user=self.user)

    def test_update_user_and_profiles(self):
        """Testa atualização combinada de usuário e perfis."""
        serializer = UserProfileUpdateSerializer(
            self.user,
            data={
                'first_name': 'José',
                'phone': '11999998888',
                'client_city': 'São Paulo',
                'client_state': 'SP',
                'provider_bio': 'Nova biografia',
            }
        )
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        
        # Verifica usuário
        self.assertEqual(user.first_name, 'José')
        self.assertEqual(user.phone, '11999998888')
        
        # Verifica perfil de cliente
        user.client_profile.refresh_from_db()
        self.assertEqual(user.client_profile.city, 'São Paulo')
        self.assertEqual(user.client_profile.state, 'SP')
        
        # Verifica perfil de prestador
        user.provider_profile.refresh_from_db()
        self.assertEqual(user.provider_profile.bio, 'Nova biografia')

    def test_partial_update(self):
        """Testa atualização parcial (apenas alguns campos)."""
        serializer = UserProfileUpdateSerializer(
            self.user,
            data={'first_name': 'Parcial'},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        
        self.assertEqual(user.first_name, 'Parcial')
        self.assertEqual(user.last_name, 'Original')  # Não alterado

    def test_phone_validation(self):
        """Testa validação de telefone."""
        serializer = UserProfileUpdateSerializer(
            self.user,
            data={'phone': '(11) 99999-8888'}
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['phone'], '11999998888')
