"""
Testes de integração para os endpoints de autenticação do app accounts.
"""
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
import uuid

from api.accounts.models import User, ClientProfile
from api.accounts.enums import UserType


class RegisterViewTestCase(APITestCase):
    """Testes para o endpoint de registro."""

    def test_register_client_success(self):
        """Testa registro de cliente com sucesso."""
        data = {
            'email': f'newuser_{uuid.uuid4().hex[:8]}@example.com',
            'first_name': 'João',
            'last_name': 'Silva',
            'password': 'senha@segura123',
            'password_confirm': 'senha@segura123',
            'user_type': UserType.CLIENT.value,
        }
        response = self.client.post(reverse('auth-register'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['user_type'], UserType.CLIENT.value)

    def test_register_provider_success(self):
        """Testa registro de prestador com sucesso."""
        data = {
            'email': f'provider_{uuid.uuid4().hex[:8]}@example.com',
            'first_name': 'Maria',
            'last_name': 'Santos',
            'password': 'senha@segura123',
            'password_confirm': 'senha@segura123',
            'user_type': UserType.PROVIDER.value,
        }
        response = self.client.post(reverse('auth-register'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['user_type'], UserType.PROVIDER.value)

    def test_register_invalid_data(self):
        """Testa registro com dados inválidos."""
        data = {
            'email': 'invalid-email',
            'first_name': '',
            'password': '123',  # Muito curta
            'password_confirm': '456',
        }
        response = self.client.post(reverse('auth-register'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        """Testa registro com email duplicado."""
        email = f'duplicate_{uuid.uuid4().hex[:8]}@example.com'
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
        response = self.client.post(reverse('auth-register'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTestCase(APITestCase):
    """Testes para o endpoint de login."""

    def setUp(self):
        """Cria usuário de teste."""
        self.email = f'login_{uuid.uuid4().hex[:8]}@example.com'
        self.password = 'senha@segura123'
        self.user = User.objects.create_user(
            email=self.email,
            first_name='João',
            last_name='Silva',
            password=self.password,
        )

    def test_login_success(self):
        """Testa login com credenciais válidas."""
        data = {'email': self.email, 'password': self.password}
        response = self.client.post(reverse('auth-login'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_login_invalid_credentials(self):
        """Testa login com credenciais inválidas."""
        data = {'email': self.email, 'password': 'wrongpassword'}
        response = self.client.post(reverse('auth-login'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_inactive_user(self):
        """Testa login de usuário inativo."""
        self.user.is_active = False
        self.user.save()
        
        data = {'email': self.email, 'password': self.password}
        response = self.client.post(reverse('auth-login'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutViewTestCase(APITestCase):
    """Testes para o endpoint de logout."""

    def setUp(self):
        """Cria usuário e obtém tokens."""
        self.email = f'logout_{uuid.uuid4().hex[:8]}@example.com'
        self.password = 'senha@segura123'
        self.user = User.objects.create_user(
            email=self.email,
            first_name='João',
            last_name='Silva',
            password=self.password,
        )
        # Faz login para obter tokens
        response = self.client.post(
            reverse('auth-login'),
            {'email': self.email, 'password': self.password},
            format='json'
        )
        self.access_token = response.data['access']
        self.refresh_token = response.data['refresh']

    def test_logout_success(self):
        """Testa logout com token válido."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(
            reverse('auth-logout'),
            {'refresh': self.refresh_token},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_logout_without_refresh_token(self):
        """Testa logout sem token de refresh."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(reverse('auth-logout'), {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_unauthenticated(self):
        """Testa logout sem autenticação."""
        response = self.client.post(
            reverse('auth-logout'),
            {'refresh': self.refresh_token},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RefreshViewTestCase(APITestCase):
    """Testes para o endpoint de refresh de token."""

    def setUp(self):
        """Cria usuário e obtém tokens."""
        self.email = f'refresh_{uuid.uuid4().hex[:8]}@example.com'
        self.password = 'senha@segura123'
        self.user = User.objects.create_user(
            email=self.email,
            first_name='João',
            last_name='Silva',
            password=self.password,
        )
        # Faz login para obter tokens
        response = self.client.post(
            reverse('auth-login'),
            {'email': self.email, 'password': self.password},
            format='json'
        )
        self.refresh_token = response.data['refresh']

    def test_refresh_success(self):
        """Testa refresh de token com sucesso."""
        response = self.client.post(
            reverse('auth-refresh'),
            {'refresh': self.refresh_token},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_invalid_token(self):
        """Testa refresh com token inválido."""
        response = self.client.post(
            reverse('auth-refresh'),
            {'refresh': 'invalid-token'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MeViewTestCase(APITestCase):
    """Testes para o endpoint /auth/me/."""

    def setUp(self):
        """Cria usuário e autentica."""
        self.email = f'me_{uuid.uuid4().hex[:8]}@example.com'
        self.password = 'senha@segura123'
        self.user = User.objects.create_user(
            email=self.email,
            first_name='João',
            last_name='Silva',
            password=self.password,
        )
        ClientProfile.objects.create(user=self.user)
        # Faz login para obter token
        response = self.client.post(
            reverse('auth-login'),
            {'email': self.email, 'password': self.password},
            format='json'
        )
        self.access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_get_me_success(self):
        """Testa GET /auth/me/ com sucesso."""
        response = self.client.get(reverse('auth-me'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.email)
        self.assertEqual(response.data['first_name'], 'João')
        self.assertTrue(response.data['has_client_profile'])

    def test_patch_me_success(self):
        """Testa PATCH /auth/me/ com sucesso."""
        response = self.client.patch(
            reverse('auth-me'),
            {'first_name': 'José', 'phone': '11999998888'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'José')
        
        # Verifica que foi salvo no banco
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'José')
        self.assertEqual(self.user.phone, '11999998888')

    def test_me_unauthenticated(self):
        """Testa acesso sem autenticação."""
        self.client.credentials()  # Remove credenciais
        response = self.client.get(reverse('auth-me'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordResetViewTestCase(APITestCase):
    """Testes para os endpoints de reset de senha."""

    def setUp(self):
        """Cria usuário de teste."""
        self.email = f'reset_{uuid.uuid4().hex[:8]}@example.com'
        self.user = User.objects.create_user(
            email=self.email,
            first_name='João',
            last_name='Silva',
            password='senha@segura123',
        )

    def test_password_reset_request_existing_email(self):
        """Testa solicitação de reset para email existente."""
        response = self.client.post(
            reverse('auth-password-reset'),
            {'email': self.email},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_password_reset_request_nonexistent_email(self):
        """Testa solicitação de reset para email inexistente (deve retornar sucesso por segurança)."""
        response = self.client.post(
            reverse('auth-password-reset'),
            {'email': 'nonexistent@example.com'},
            format='json'
        )
        
        # Sempre retorna sucesso por segurança
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_confirm_success(self):
        """Testa confirmação de reset de senha com sucesso."""
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from django.contrib.auth.tokens import default_token_generator
        
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        
        response = self.client.post(
            reverse('auth-password-reset-confirm'),
            {
                'uid': uid,
                'token': token,
                'new_password': 'novasenha@segura123',
                'new_password_confirm': 'novasenha@segura123',
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verifica que a senha foi alterada
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('novasenha@segura123'))

    def test_password_reset_confirm_invalid_token(self):
        """Testa confirmação com token inválido."""
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        response = self.client.post(
            reverse('auth-password-reset-confirm'),
            {
                'uid': uid,
                'token': 'invalid-token',
                'new_password': 'novasenha@segura123',
                'new_password_confirm': 'novasenha@segura123',
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_password_mismatch(self):
        """Testa confirmação com senhas diferentes."""
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        from django.contrib.auth.tokens import default_token_generator
        
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        
        response = self.client.post(
            reverse('auth-password-reset-confirm'),
            {
                'uid': uid,
                'token': token,
                'new_password': 'novasenha@segura123',
                'new_password_confirm': 'outrasenha@123',
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
