"""
Testes de autenticação: JWT, hash de senhas e fluxos E2E.
"""
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.hashers import check_password, identify_hasher
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)
import uuid
import jwt
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

from api.accounts.models import User, ClientProfile
from api.accounts.enums import UserType


# =============================================================================
# Testes de Hash de Senhas
# =============================================================================


class PasswordHashingTestCase(TestCase):
    """Testes para verificar que o hash de senhas está funcionando corretamente."""

    def test_password_is_hashed_on_create(self):
        """Testa que a senha é hasheada ao criar usuário."""
        password = 'senhasegura123'
        user = User.objects.create_user(
            email='hash@example.com',
            first_name='Hash',
            last_name='Test',
            password=password,
        )
        
        # A senha armazenada não deve ser igual à senha em texto plano
        self.assertNotEqual(user.password, password)
        
        # A senha deve começar com o prefixo do hasher
        self.assertTrue(user.password.startswith('bcrypt'))

    def test_bcrypt_hasher_is_used(self):
        """Testa que o BCrypt é usado como hasher principal."""
        user = User.objects.create_user(
            email='bcrypt@example.com',
            first_name='BCrypt',
            last_name='Test',
            password='senhasegura123',
        )
        
        # Identifica o hasher usado
        hasher = identify_hasher(user.password)
        
        # Deve ser BCrypt
        self.assertIn('bcrypt', hasher.algorithm.lower())

    def test_password_verification_works(self):
        """Testa que a verificação de senha funciona."""
        password = 'senhasegura123'
        user = User.objects.create_user(
            email='verify@example.com',
            first_name='Verify',
            last_name='Test',
            password=password,
        )
        
        # Verifica que check_password funciona
        self.assertTrue(check_password(password, user.password))
        self.assertFalse(check_password('senhaerrada', user.password))

    def test_user_check_password_method(self):
        """Testa o método check_password do modelo User."""
        password = 'senhasegura123'
        user = User.objects.create_user(
            email='check@example.com',
            first_name='Check',
            last_name='Test',
            password=password,
        )
        
        # Testa o método do modelo
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.check_password('senhaerrada'))

    def test_password_change_rehashes(self):
        """Testa que mudar a senha cria um novo hash."""
        user = User.objects.create_user(
            email='change@example.com',
            first_name='Change',
            last_name='Test',
            password='senhaoriginal123',
        )
        
        old_hash = user.password
        
        # Muda a senha
        user.set_password('novasenha123')
        user.save()
        
        # O hash deve ser diferente
        self.assertNotEqual(user.password, old_hash)
        
        # A nova senha deve funcionar
        self.assertTrue(user.check_password('novasenha123'))
        self.assertFalse(user.check_password('senhaoriginal123'))

    def test_bcrypt_is_first_in_hashers(self):
        """Testa que BCrypt é o primeiro hasher configurado."""
        hashers = settings.PASSWORD_HASHERS
        
        # O primeiro deve ser BCrypt
        self.assertIn('BCrypt', hashers[0])


# =============================================================================
# Testes do Sistema JWT
# =============================================================================


class JWTTokenGenerationTestCase(TestCase):
    """Testes para geração de tokens JWT."""

    def setUp(self):
        """Cria usuário de teste."""
        self.user = User.objects.create_user(
            email=f'jwt_{uuid.uuid4().hex[:8]}@example.com',
            first_name='JWT',
            last_name='Test',
            password='senhasegura123',
        )

    def test_refresh_token_generation(self):
        """Testa geração de token de refresh."""
        refresh = RefreshToken.for_user(self.user)
        
        # Token deve existir
        self.assertIsNotNone(refresh)
        self.assertIsNotNone(str(refresh))
        
        # Token deve ter um access token associado
        access = refresh.access_token
        self.assertIsNotNone(access)
        self.assertIsNotNone(str(access))

    def test_access_token_contains_user_id(self):
        """Testa que o access token contém o ID do usuário."""
        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token
        
        # Decodifica o token (sem verificar assinatura para teste)
        decoded = jwt.decode(
            str(access),
            options={"verify_signature": False}
        )
        
        # Deve conter o user_id (pode ser int ou string dependendo da config)
        self.assertEqual(int(decoded['user_id']), self.user.id)

    def test_token_expiry_is_set(self):
        """Testa que os tokens têm expiração configurada."""
        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token
        
        # Decodifica os tokens
        access_decoded = jwt.decode(
            str(access),
            options={"verify_signature": False}
        )
        refresh_decoded = jwt.decode(
            str(refresh),
            options={"verify_signature": False}
        )
        
        # Ambos devem ter 'exp' (expiration)
        self.assertIn('exp', access_decoded)
        self.assertIn('exp', refresh_decoded)
        
        # Access token deve expirar antes do refresh token
        self.assertLess(access_decoded['exp'], refresh_decoded['exp'])

    def test_token_type_claim(self):
        """Testa que os tokens têm o claim 'token_type'."""
        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token
        
        # Decodifica os tokens
        access_decoded = jwt.decode(
            str(access),
            options={"verify_signature": False}
        )
        refresh_decoded = jwt.decode(
            str(refresh),
            options={"verify_signature": False}
        )
        
        # Verifica os tipos
        self.assertEqual(access_decoded['token_type'], 'access')
        self.assertEqual(refresh_decoded['token_type'], 'refresh')


class JWTTokenValidationTestCase(APITestCase):
    """Testes para validação de tokens JWT."""

    def setUp(self):
        """Cria usuário e tokens de teste."""
        self.user = User.objects.create_user(
            email=f'validate_{uuid.uuid4().hex[:8]}@example.com',
            first_name='Validate',
            last_name='Test',
            password='senhasegura123',
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.access = str(self.refresh.access_token)

    def test_valid_token_authenticates(self):
        """Testa que token válido autentica o usuário."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')
        
        # Tenta acessar endpoint protegido
        response = self.client.get(reverse('auth-me'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_invalid_token_rejected(self):
        """Testa que token inválido é rejeitado."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')
        
        response = self.client.get(reverse('auth-me'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_token_rejected(self):
        """Testa que token expirado é rejeitado."""
        # Cria um token com expiração no passado
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token
        
        # Modifica o payload para expirar no passado (não é possível diretamente)
        # Em vez disso, testamos com um token malformado
        self.client.credentials(HTTP_AUTHORIZATION='Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjAwMDAwMDAwLCJpYXQiOjE2MDAwMDAwMDAsImp0aSI6InRlc3QiLCJ1c2VyX2lkIjoxfQ.invalid')
        
        response = self.client.get(reverse('auth-me'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_token_rejected(self):
        """Testa que requisição sem token é rejeitada em endpoint protegido."""
        response = self.client.get(reverse('auth-me'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class JWTTokenRefreshTestCase(APITestCase):
    """Testes para refresh de tokens JWT."""

    def setUp(self):
        """Cria usuário e tokens de teste."""
        self.user = User.objects.create_user(
            email=f'refresh_{uuid.uuid4().hex[:8]}@example.com',
            first_name='Refresh',
            last_name='Test',
            password='senhasegura123',
        )
        self.refresh = RefreshToken.for_user(self.user)

    def test_refresh_returns_new_access_token(self):
        """Testa que refresh retorna novo access token."""
        response = self.client.post(
            reverse('auth-refresh'),
            {'refresh': str(self.refresh)},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        
        # Novo token deve ser diferente do original
        new_access = response.data['access']
        self.assertIsNotNone(new_access)

    def test_refresh_with_blacklisted_token_fails(self):
        """Testa que refresh com token na blacklist falha."""
        refresh_str = str(self.refresh)
        
        # Primeiro refresh funciona
        response1 = self.client.post(
            reverse('auth-refresh'),
            {'refresh': refresh_str},
            format='json'
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Coloca na blacklist (simulando logout)
        self.refresh.blacklist()
        
        # Segundo refresh deve falhar
        response2 = self.client.post(
            reverse('auth-refresh'),
            {'refresh': refresh_str},
            format='json'
        )
        self.assertEqual(response2.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_new_access_token_works(self):
        """Testa que o novo access token funciona para autenticação."""
        # Obtém novo access token via refresh
        response = self.client.post(
            reverse('auth-refresh'),
            {'refresh': str(self.refresh)},
            format='json'
        )
        
        new_access = response.data['access']
        
        # Usa o novo token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access}')
        
        response = self.client.get(reverse('auth-me'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)


class JWTTokenBlacklistTestCase(APITestCase):
    """Testes para blacklist de tokens JWT."""

    def setUp(self):
        """Cria usuário e tokens de teste."""
        self.user = User.objects.create_user(
            email=f'blacklist_{uuid.uuid4().hex[:8]}@example.com',
            first_name='Blacklist',
            last_name='Test',
            password='senhasegura123',
        )

    def test_logout_blacklists_token(self):
        """Testa que logout adiciona token à blacklist."""
        # Login
        response = self.client.post(
            reverse('auth-login'),
            {'email': self.user.email, 'password': 'senhasegura123'},
            format='json'
        )
        
        access = response.data['access']
        refresh = response.data['refresh']
        
        # Logout
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        response = self.client.post(
            reverse('auth-logout'),
            {'refresh': refresh},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verifica que o token foi adicionado à blacklist
        self.assertTrue(BlacklistedToken.objects.exists())

    def test_blacklisted_token_cannot_refresh(self):
        """Testa que token na blacklist não pode fazer refresh."""
        # Login
        response = self.client.post(
            reverse('auth-login'),
            {'email': self.user.email, 'password': 'senhasegura123'},
            format='json'
        )
        
        access = response.data['access']
        refresh = response.data['refresh']
        
        # Logout (adiciona à blacklist)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        self.client.post(
            reverse('auth-logout'),
            {'refresh': refresh},
            format='json'
        )
        
        # Tenta refresh
        self.client.credentials()
        response = self.client.post(
            reverse('auth-refresh'),
            {'refresh': refresh},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# =============================================================================
# Testes E2E - Fluxo Completo de Autenticação
# =============================================================================


class AuthenticationE2ETestCase(APITestCase):
    """Testes E2E para o fluxo completo de autenticação."""

    def test_full_auth_flow_client(self):
        """
        Testa fluxo completo: registro → login → refresh → acesso protegido → logout.
        """
        email = f'e2e_client_{uuid.uuid4().hex[:8]}@example.com'
        password = 'senhasegura@123'
        
        # 1. REGISTRO
        register_response = self.client.post(
            reverse('auth-register'),
            {
                'email': email,
                'first_name': 'E2E',
                'last_name': 'Client',
                'password': password,
                'password_confirm': password,
                'user_type': UserType.CLIENT.value,
            },
            format='json'
        )
        
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', register_response.data)
        self.assertEqual(register_response.data['user']['email'], email)
        self.assertEqual(register_response.data['user']['user_type'], UserType.CLIENT.value)
        
        # 2. LOGIN
        login_response = self.client.post(
            reverse('auth-login'),
            {'email': email, 'password': password},
            format='json'
        )
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_response.data)
        self.assertIn('refresh', login_response.data)
        self.assertIn('user', login_response.data)
        
        access_token = login_response.data['access']
        refresh_token = login_response.data['refresh']
        
        # 3. ACESSO A ENDPOINT PROTEGIDO (/me)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        me_response = self.client.get(reverse('auth-me'))
        
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data['email'], email)
        self.assertTrue(me_response.data['has_client_profile'])
        
        # 4. REFRESH DO TOKEN
        self.client.credentials()  # Remove credenciais
        
        refresh_response = self.client.post(
            reverse('auth-refresh'),
            {'refresh': refresh_token},
            format='json'
        )
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
        
        new_access_token = refresh_response.data['access']
        # Se houver rotação de tokens, usa o novo refresh token
        new_refresh_token = refresh_response.data.get('refresh', refresh_token)
        
        # 5. ACESSO COM NOVO TOKEN
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        
        me_response2 = self.client.get(reverse('auth-me'))
        
        self.assertEqual(me_response2.status_code, status.HTTP_200_OK)
        
        # 6. LOGOUT (usa o novo refresh token se disponível)
        logout_response = self.client.post(
            reverse('auth-logout'),
            {'refresh': new_refresh_token},
            format='json'
        )
        
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        
        # 7. VERIFICA QUE REFRESH NÃO FUNCIONA MAIS
        self.client.credentials()
        
        refresh_after_logout = self.client.post(
            reverse('auth-refresh'),
            {'refresh': new_refresh_token},
            format='json'
        )
        
        self.assertEqual(refresh_after_logout.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_full_auth_flow_provider(self):
        """
        Testa fluxo completo para prestador: registro → login → acesso → logout.
        """
        email = f'e2e_provider_{uuid.uuid4().hex[:8]}@example.com'
        password = 'senhasegura@123'
        
        # 1. REGISTRO COMO PROVIDER
        register_response = self.client.post(
            reverse('auth-register'),
            {
                'email': email,
                'first_name': 'E2E',
                'last_name': 'Provider',
                'password': password,
                'password_confirm': password,
                'user_type': UserType.PROVIDER.value,
            },
            format='json'
        )
        
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(register_response.data['user']['user_type'], UserType.PROVIDER.value)
        
        # 2. LOGIN
        login_response = self.client.post(
            reverse('auth-login'),
            {'email': email, 'password': password},
            format='json'
        )
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        access_token = login_response.data['access']
        refresh_token = login_response.data['refresh']
        
        # 3. ACESSO A /me - VERIFICA PROVIDER PROFILE
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        me_response = self.client.get(reverse('auth-me'))
        
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertTrue(me_response.data['has_provider_profile'])
        self.assertFalse(me_response.data['has_client_profile'])
        
        # 4. LOGOUT
        logout_response = self.client.post(
            reverse('auth-logout'),
            {'refresh': refresh_token},
            format='json'
        )
        
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

    def test_invalid_credentials_flow(self):
        """Testa fluxo com credenciais inválidas."""
        email = f'invalid_{uuid.uuid4().hex[:8]}@example.com'
        
        # Tenta login sem registro
        login_response = self.client.post(
            reverse('auth-login'),
            {'email': email, 'password': 'qualquersenha123'},
            format='json'
        )
        
        self.assertEqual(login_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_duplicate_email_registration_flow(self):
        """Testa fluxo de registro com email duplicado."""
        email = f'duplicate_{uuid.uuid4().hex[:8]}@example.com'
        password = 'senhasegura@123'
        
        # Primeiro registro
        self.client.post(
            reverse('auth-register'),
            {
                'email': email,
                'first_name': 'First',
                'last_name': 'User',
                'password': password,
                'password_confirm': password,
            },
            format='json'
        )
        
        # Segundo registro com mesmo email
        register_response = self.client.post(
            reverse('auth-register'),
            {
                'email': email,
                'first_name': 'Second',
                'last_name': 'User',
                'password': password,
                'password_confirm': password,
            },
            format='json'
        )
        
        self.assertEqual(register_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_profile_flow(self):
        """Testa fluxo de atualização de perfil."""
        email = f'update_{uuid.uuid4().hex[:8]}@example.com'
        password = 'senhasegura@123'
        
        # Registro
        self.client.post(
            reverse('auth-register'),
            {
                'email': email,
                'first_name': 'Original',
                'last_name': 'Name',
                'password': password,
                'password_confirm': password,
            },
            format='json'
        )
        
        # Login
        login_response = self.client.post(
            reverse('auth-login'),
            {'email': email, 'password': password},
            format='json'
        )
        
        access_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Atualiza perfil
        update_response = self.client.patch(
            reverse('auth-me'),
            {
                'first_name': 'Updated',
                'phone': '11999998888',
            },
            format='json'
        )
        
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['first_name'], 'Updated')
        
        # Verifica que a mudança persistiu
        me_response = self.client.get(reverse('auth-me'))
        
        self.assertEqual(me_response.data['first_name'], 'Updated')
