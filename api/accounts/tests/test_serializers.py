"""
Testes unitários para os serializers do app accounts.
"""
from django.test import TestCase
import uuid

from api.accounts.models import User, ClientProfile
from api.accounts.enums import UserType
from api.accounts.serializers import (
    UserRegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
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
