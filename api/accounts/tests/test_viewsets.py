"""
Testes de integração para os ViewSets do app accounts.
"""
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
import uuid

from api.accounts.models import User, ClientProfile, ProviderProfile
from api.accounts.enums import UserType


class UserViewSetTestCase(APITestCase):
    """Testes para o UserViewSet."""

    def setUp(self):
        """Cria usuários de teste."""
        self.unique_id = str(uuid.uuid4())[:8]
        
        # Admin
        self.admin = User.objects.create_user(
            email=f'admin-{self.unique_id}@example.com',
            first_name='Admin',
            last_name='User',
            password='testpass123',
            user_type=UserType.ADMIN.value,
        )
        
        # Cliente comum
        self.client_user = User.objects.create_user(
            email=f'client-{self.unique_id}@example.com',
            first_name='Client',
            last_name='User',
            password='testpass123',
            user_type=UserType.CLIENT.value,
        )
        ClientProfile.objects.create(user=self.client_user)
        
        # Prestador
        self.provider = User.objects.create_user(
            email=f'provider-{self.unique_id}@example.com',
            first_name='Provider',
            last_name='User',
            password='testpass123',
            user_type=UserType.PROVIDER.value,
        )
        ProviderProfile.objects.create(user=self.provider)

    def get_access_token(self, user):
        """Obtém token de acesso para um usuário."""
        response = self.client.post(
            reverse('auth-login'),
            {'email': user.email, 'password': 'testpass123'},
            format='json'
        )
        return response.data['access']

    # Testes de listagem
    def test_admin_can_list_users(self):
        """Testa que admin pode listar todos os usuários."""
        token = self.get_access_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(reverse('users-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Deve listar todos os usuários
        self.assertGreaterEqual(len(response.data), 3)

    def test_client_cannot_list_users(self):
        """Testa que cliente não pode listar todos os usuários."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(reverse('users-list'))
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Testes de retrieve
    def test_user_can_view_own_profile(self):
        """Testa que usuário pode ver seu próprio perfil."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('users-detail', kwargs={'pk': self.client_user.pk})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.client_user.email)

    def test_user_cannot_view_other_profile(self):
        """Testa que usuário não pode ver perfil de outro."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('users-detail', kwargs={'pk': self.provider.pk})
        )
        
        # Não encontra porque queryset filtra
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_view_any_profile(self):
        """Testa que admin pode ver qualquer perfil."""
        token = self.get_access_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('users-detail', kwargs={'pk': self.client_user.pk})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Testes de update
    def test_user_can_update_own_profile(self):
        """Testa que usuário pode atualizar seu próprio perfil."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.patch(
            reverse('users-detail', kwargs={'pk': self.client_user.pk}),
            {'first_name': 'Updated'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client_user.refresh_from_db()
        self.assertEqual(self.client_user.first_name, 'Updated')

    # Testes de profile action
    def test_get_user_profile(self):
        """Testa action de perfil completo."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('users-profile', kwargs={'pk': self.client_user.pk})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('client_profile', response.data)


class ProviderProfileViewSetTestCase(APITestCase):
    """Testes para o ProviderProfileViewSet."""

    def setUp(self):
        """Cria usuários e perfis de teste."""
        self.unique_id = str(uuid.uuid4())[:8]
        
        # Admin
        self.admin = User.objects.create_user(
            email=f'admin-{self.unique_id}@example.com',
            first_name='Admin',
            last_name='User',
            password='testpass123',
            user_type=UserType.ADMIN.value,
        )
        
        # Prestador 1
        self.provider1 = User.objects.create_user(
            email=f'provider1-{self.unique_id}@example.com',
            first_name='Provider',
            last_name='One',
            password='testpass123',
            user_type=UserType.PROVIDER.value,
        )
        self.profile1 = ProviderProfile.objects.create(
            user=self.provider1,
            bio='Desenvolvedor Full Stack',
            rating_avg=Decimal('4.50'),
            is_verified=True
        )
        
        # Prestador 2
        self.provider2 = User.objects.create_user(
            email=f'provider2-{self.unique_id}@example.com',
            first_name='Provider',
            last_name='Two',
            password='testpass123',
            user_type=UserType.PROVIDER.value,
        )
        self.profile2 = ProviderProfile.objects.create(
            user=self.provider2,
            bio='Designer UI/UX'
        )
        
        # Cliente
        self.client_user = User.objects.create_user(
            email=f'client-{self.unique_id}@example.com',
            first_name='Client',
            last_name='User',
            password='testpass123',
            user_type=UserType.CLIENT.value,
        )

    def get_access_token(self, user):
        """Obtém token de acesso para um usuário."""
        response = self.client.post(
            reverse('auth-login'),
            {'email': user.email, 'password': 'testpass123'},
            format='json'
        )
        return response.data['access']

    # Testes de listagem
    def test_authenticated_user_can_list_providers(self):
        """Testa que usuário autenticado pode listar prestadores."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(reverse('provider-profiles-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_unauthenticated_cannot_list_providers(self):
        """Testa que usuário não autenticado não pode listar."""
        response = self.client.get(reverse('provider-profiles-list'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Testes de retrieve
    def test_can_view_provider_details(self):
        """Testa que pode ver detalhes de um prestador."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('provider-profiles-detail', kwargs={'pk': self.profile1.pk})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], 'Desenvolvedor Full Stack')
        self.assertEqual(response.data['user_name'], 'Provider One')

    # Testes de update
    def test_provider_can_update_own_profile(self):
        """Testa que prestador pode atualizar seu próprio perfil."""
        token = self.get_access_token(self.provider1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.patch(
            reverse('provider-profiles-detail', kwargs={'pk': self.profile1.pk}),
            {'bio': 'Nova biografia atualizada'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile1.refresh_from_db()
        self.assertEqual(self.profile1.bio, 'Nova biografia atualizada')

    def test_provider_cannot_update_other_profile(self):
        """Testa que prestador não pode atualizar perfil de outro."""
        token = self.get_access_token(self.provider1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.patch(
            reverse('provider-profiles-detail', kwargs={'pk': self.profile2.pk}),
            {'bio': 'Tentativa de alteração'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_any_profile(self):
        """Testa que admin pode atualizar qualquer perfil."""
        token = self.get_access_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.patch(
            reverse('provider-profiles-detail', kwargs={'pk': self.profile1.pk}),
            {'bio': 'Atualizado pelo admin'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ClientProfileViewSetTestCase(APITestCase):
    """Testes para o ClientProfileViewSet."""

    def setUp(self):
        """Cria usuários e perfis de teste."""
        self.unique_id = str(uuid.uuid4())[:8]
        
        # Admin
        self.admin = User.objects.create_user(
            email=f'admin-{self.unique_id}@example.com',
            first_name='Admin',
            last_name='User',
            password='testpass123',
            user_type=UserType.ADMIN.value,
        )
        
        # Cliente 1
        self.client1 = User.objects.create_user(
            email=f'client1-{self.unique_id}@example.com',
            first_name='Client',
            last_name='One',
            password='testpass123',
            user_type=UserType.CLIENT.value,
        )
        self.profile1 = ClientProfile.objects.create(
            user=self.client1,
            address='Rua das Flores, 123',
            city='São Paulo',
            state='SP',
            zip_code='01234-567'
        )
        
        # Cliente 2
        self.client2 = User.objects.create_user(
            email=f'client2-{self.unique_id}@example.com',
            first_name='Client',
            last_name='Two',
            password='testpass123',
            user_type=UserType.CLIENT.value,
        )
        self.profile2 = ClientProfile.objects.create(
            user=self.client2,
            city='Rio de Janeiro',
            state='RJ'
        )

    def get_access_token(self, user):
        """Obtém token de acesso para um usuário."""
        response = self.client.post(
            reverse('auth-login'),
            {'email': user.email, 'password': 'testpass123'},
            format='json'
        )
        return response.data['access']

    # Testes de listagem
    def test_admin_can_list_clients(self):
        """Testa que admin pode listar todos os clientes."""
        token = self.get_access_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(reverse('client-profiles-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_client_cannot_list_all_clients(self):
        """Testa que cliente não pode listar todos os clientes."""
        token = self.get_access_token(self.client1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(reverse('client-profiles-list'))
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Testes de retrieve
    def test_client_can_view_own_profile(self):
        """Testa que cliente pode ver seu próprio perfil."""
        token = self.get_access_token(self.client1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('client-profiles-detail', kwargs={'pk': self.profile1.pk})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['city'], 'São Paulo')

    def test_client_cannot_view_other_profile(self):
        """Testa que cliente não pode ver perfil de outro."""
        token = self.get_access_token(self.client1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('client-profiles-detail', kwargs={'pk': self.profile2.pk})
        )
        
        # Não encontra porque queryset filtra
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Testes de update
    def test_client_can_update_own_profile(self):
        """Testa que cliente pode atualizar seu próprio perfil."""
        token = self.get_access_token(self.client1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.patch(
            reverse('client-profiles-detail', kwargs={'pk': self.profile1.pk}),
            {'city': 'Campinas', 'state': 'SP'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile1.refresh_from_db()
        self.assertEqual(self.profile1.city, 'Campinas')

    def test_admin_can_view_any_profile(self):
        """Testa que admin pode ver qualquer perfil."""
        token = self.get_access_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('client-profiles-detail', kwargs={'pk': self.profile2.pk})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['city'], 'Rio de Janeiro')


class PermissionsIntegrationTestCase(APITestCase):
    """
    Testes de integração para verificar permissões IsClient e IsProvider
    em cenários reais de API.
    """

    def setUp(self):
        """Cria usuários de teste."""
        self.unique_id = str(uuid.uuid4())[:8]
        
        # Cliente
        self.client_user = User.objects.create_user(
            email=f'client-{self.unique_id}@example.com',
            first_name='Client',
            last_name='User',
            password='testpass123',
            user_type=UserType.CLIENT.value,
        )
        ClientProfile.objects.create(user=self.client_user, city='São Paulo', state='SP')
        
        # Prestador
        self.provider = User.objects.create_user(
            email=f'provider-{self.unique_id}@example.com',
            first_name='Provider',
            last_name='User',
            password='testpass123',
            user_type=UserType.PROVIDER.value,
        )
        ProviderProfile.objects.create(user=self.provider, bio='Desenvolvedor')
        
        # Admin
        self.admin = User.objects.create_user(
            email=f'admin-{self.unique_id}@example.com',
            first_name='Admin',
            last_name='User',
            password='testpass123',
            user_type=UserType.ADMIN.value,
        )

    def get_access_token(self, user):
        """Obtém token de acesso para um usuário."""
        response = self.client.post(
            reverse('auth-login'),
            {'email': user.email, 'password': 'testpass123'},
            format='json'
        )
        return response.data['access']

    # Testes de permissão IsClient via endpoints
    def test_client_can_view_providers_list(self):
        """Cliente pode listar prestadores para contratar."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(reverse('provider-profiles-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_client_cannot_access_admin_users_list(self):
        """Cliente não pode acessar lista de usuários (admin only)."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(reverse('users-list'))
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Testes de permissão IsProvider via endpoints
    def test_provider_can_view_own_profile(self):
        """Prestador pode ver seu próprio perfil."""
        token = self.get_access_token(self.provider)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        provider_profile = ProviderProfile.objects.get(user=self.provider)
        response = self.client.get(
            reverse('provider-profiles-detail', kwargs={'pk': provider_profile.pk})
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], 'Desenvolvedor')

    def test_provider_can_update_own_bio(self):
        """Prestador pode atualizar sua bio."""
        token = self.get_access_token(self.provider)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        provider_profile = ProviderProfile.objects.get(user=self.provider)
        response = self.client.patch(
            reverse('provider-profiles-detail', kwargs={'pk': provider_profile.pk}),
            {'bio': 'Nova biografia do prestador'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        provider_profile.refresh_from_db()
        self.assertEqual(provider_profile.bio, 'Nova biografia do prestador')

    def test_provider_cannot_access_clients_list(self):
        """Prestador não pode acessar lista de clientes (admin only)."""
        token = self.get_access_token(self.provider)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(reverse('client-profiles-list'))
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Testes de permissão cruzada
    def test_client_cannot_update_provider_profile(self):
        """Cliente não pode atualizar perfil de prestador."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        provider_profile = ProviderProfile.objects.get(user=self.provider)
        response = self.client.patch(
            reverse('provider-profiles-detail', kwargs={'pk': provider_profile.pk}),
            {'bio': 'Tentativa de alteração'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_all_resources(self):
        """Admin pode acessar todos os recursos."""
        token = self.get_access_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Pode listar usuários
        users_response = self.client.get(reverse('users-list'))
        self.assertEqual(users_response.status_code, status.HTTP_200_OK)
        
        # Pode listar clientes
        clients_response = self.client.get(reverse('client-profiles-list'))
        self.assertEqual(clients_response.status_code, status.HTTP_200_OK)
        
        # Pode listar prestadores
        providers_response = self.client.get(reverse('provider-profiles-list'))
        self.assertEqual(providers_response.status_code, status.HTTP_200_OK)


class ProfileCreationE2ETestCase(APITestCase):
    """
    Testes E2E para fluxo completo de criação de perfil de cliente e prestador.
    """

    def test_e2e_create_client_profile(self):
        """
        Teste E2E: Registro de cliente -> Login -> Verificar perfil criado
        -> Atualizar perfil -> Verificar atualização
        """
        unique_id = str(uuid.uuid4())[:8]
        
        # 1. Registro do cliente
        register_data = {
            'email': f'e2e_client_{unique_id}@example.com',
            'first_name': 'E2E',
            'last_name': 'Client',
            'password': 'e2e_password123',
            'password_confirm': 'e2e_password123',
            'user_type': UserType.CLIENT.value,
        }
        register_response = self.client.post(
            reverse('auth-register'),
            register_data,
            format='json'
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        user_id = register_response.data['user']['id']
        
        # 2. Login
        login_data = {
            'email': register_data['email'],
            'password': register_data['password'],
        }
        login_response = self.client.post(
            reverse('auth-login'),
            login_data,
            format='json'
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data['access']
        
        # 3. Verificar que perfil de cliente foi criado automaticamente
        user = User.objects.get(id=user_id)
        self.assertTrue(hasattr(user, 'client_profile'))
        client_profile = user.client_profile
        
        # 4. Atualizar perfil via endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        update_data = {
            'city': 'São Paulo',
            'state': 'SP',
            'zip_code': '01234567',
        }
        update_response = self.client.patch(
            reverse('client-profiles-detail', kwargs={'pk': client_profile.pk}),
            update_data,
            format='json'
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        
        # 5. Verificar atualização
        client_profile.refresh_from_db()
        self.assertEqual(client_profile.city, 'São Paulo')
        self.assertEqual(client_profile.state, 'SP')
        self.assertEqual(client_profile.zip_code, '01234-567')  # Formatado

    def test_e2e_create_provider_profile(self):
        """
        Teste E2E: Registro de prestador -> Login -> Verificar perfil criado
        -> Atualizar bio -> Verificar atualização
        """
        unique_id = str(uuid.uuid4())[:8]
        
        # 1. Registro do prestador
        register_data = {
            'email': f'e2e_provider_{unique_id}@example.com',
            'first_name': 'E2E',
            'last_name': 'Provider',
            'password': 'e2e_password123',
            'password_confirm': 'e2e_password123',
            'user_type': UserType.PROVIDER.value,
        }
        register_response = self.client.post(
            reverse('auth-register'),
            register_data,
            format='json'
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        user_id = register_response.data['user']['id']
        
        # 2. Login
        login_data = {
            'email': register_data['email'],
            'password': register_data['password'],
        }
        login_response = self.client.post(
            reverse('auth-login'),
            login_data,
            format='json'
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data['access']
        
        # 3. Verificar que perfil de prestador foi criado automaticamente
        user = User.objects.get(id=user_id)
        self.assertTrue(hasattr(user, 'provider_profile'))
        provider_profile = user.provider_profile
        
        # Valores padrão
        self.assertEqual(provider_profile.rating_avg, Decimal('0.00'))
        self.assertEqual(provider_profile.total_reviews, 0)
        self.assertFalse(provider_profile.is_verified)
        
        # 4. Atualizar bio via endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        update_data = {
            'bio': 'Desenvolvedor Full Stack com 5 anos de experiência',
        }
        update_response = self.client.patch(
            reverse('provider-profiles-detail', kwargs={'pk': provider_profile.pk}),
            update_data,
            format='json'
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        
        # 5. Verificar atualização
        provider_profile.refresh_from_db()
        self.assertEqual(
            provider_profile.bio,
            'Desenvolvedor Full Stack com 5 anos de experiência'
        )

    def test_e2e_get_complete_user_profile(self):
        """
        Teste E2E: Registro -> Login -> Obter perfil completo via /users/{id}/profile/
        """
        unique_id = str(uuid.uuid4())[:8]
        
        # 1. Registro
        register_data = {
            'email': f'e2e_complete_{unique_id}@example.com',
            'first_name': 'Complete',
            'last_name': 'Profile',
            'password': 'e2e_password123',
            'password_confirm': 'e2e_password123',
            'user_type': UserType.CLIENT.value,
        }
        register_response = self.client.post(
            reverse('auth-register'),
            register_data,
            format='json'
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        user_id = register_response.data['user']['id']
        
        # 2. Login
        login_response = self.client.post(
            reverse('auth-login'),
            {'email': register_data['email'], 'password': register_data['password']},
            format='json'
        )
        access_token = login_response.data['access']
        
        # 3. Obter perfil completo
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        profile_response = self.client.get(
            reverse('users-profile', kwargs={'pk': user_id})
        )
        
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data['email'], register_data['email'])
        self.assertEqual(profile_response.data['first_name'], 'Complete')
        self.assertEqual(profile_response.data['last_name'], 'Profile')
        self.assertEqual(profile_response.data['full_name'], 'Complete Profile')
        self.assertIn('client_profile', profile_response.data)
        self.assertIsNotNone(profile_response.data['client_profile'])

    def test_e2e_update_user_and_profile_together(self):
        """
        Teste E2E: Atualizar dados do usuário e perfil em requisições separadas.
        """
        unique_id = str(uuid.uuid4())[:8]
        
        # Registro
        register_data = {
            'email': f'e2e_update_{unique_id}@example.com',
            'first_name': 'Original',
            'last_name': 'Name',
            'password': 'e2e_password123',
            'password_confirm': 'e2e_password123',
            'user_type': UserType.CLIENT.value,
        }
        register_response = self.client.post(
            reverse('auth-register'),
            register_data,
            format='json'
        )
        user_id = register_response.data['user']['id']
        
        # Login
        login_response = self.client.post(
            reverse('auth-login'),
            {'email': register_data['email'], 'password': register_data['password']},
            format='json'
        )
        access_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Atualizar dados do usuário
        user_update_response = self.client.patch(
            reverse('users-detail', kwargs={'pk': user_id}),
            {'first_name': 'Updated', 'last_name': 'Username', 'phone': '11999998888'},
            format='json'
        )
        self.assertEqual(user_update_response.status_code, status.HTTP_200_OK)
        
        # Atualizar perfil de cliente
        user = User.objects.get(id=user_id)
        profile_update_response = self.client.patch(
            reverse('client-profiles-detail', kwargs={'pk': user.client_profile.pk}),
            {'city': 'Campinas', 'state': 'SP'},
            format='json'
        )
        self.assertEqual(profile_update_response.status_code, status.HTTP_200_OK)
        
        # Verificar todas as atualizações
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.last_name, 'Username')
        self.assertEqual(user.phone, '11999998888')
        self.assertEqual(user.client_profile.city, 'Campinas')
        self.assertEqual(user.client_profile.state, 'SP')
