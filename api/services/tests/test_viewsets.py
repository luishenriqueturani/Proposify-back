"""
Testes de integração para os ViewSets do app services.
"""
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status as http_status
import uuid

from api.accounts.models import User
from api.accounts.enums import UserType
from api.services.models import ServiceCategory, Service


class ServiceCategoryViewSetTestCase(APITestCase):
    """Testes de integração para ServiceCategoryViewSet."""

    def setUp(self):
        """Cria dados de teste."""
        self.unique_id = str(uuid.uuid4())[:8]
        
        # Admin
        self.admin = User.objects.create_user(
            email=f'admin-{self.unique_id}@example.com',
            first_name='Admin',
            last_name='User',
            password='testpass123',
            user_type=UserType.ADMIN.value,
        )
        
        # Cliente
        self.client_user = User.objects.create_user(
            email=f'client-{self.unique_id}@example.com',
            first_name='Client',
            last_name='User',
            password='testpass123',
            user_type=UserType.CLIENT.value,
        )
        
        # Categorias
        self.category1 = ServiceCategory.objects.create(name=f'Tecnologia-{self.unique_id}')
        self.category2 = ServiceCategory.objects.create(
            name=f'Web-{self.unique_id}',
            parent=self.category1
        )

    def get_access_token(self, user):
        """Obtém token de acesso para um usuário."""
        response = self.client.post(
            reverse('auth-login'),
            {'email': user.email, 'password': 'testpass123'},
            format='json'
        )
        return response.data['access']

    def get_results(self, response):
        """Extrai resultados da resposta (suporta paginação)."""
        if isinstance(response.data, dict) and 'results' in response.data:
            return response.data['results']
        return response.data

    def test_list_categories_authenticated(self):
        """Testa que usuário autenticado pode listar categorias."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(reverse('service-categories-list'))
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        results = self.get_results(response)
        self.assertGreaterEqual(len(results), 2)

    def test_list_categories_unauthenticated(self):
        """Testa que usuário não autenticado não pode listar."""
        response = self.client.get(reverse('service-categories-list'))
        self.assertEqual(response.status_code, http_status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_category(self):
        """Testa obter detalhes de uma categoria."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('service-categories-detail', kwargs={'pk': self.category1.pk})
        )
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn('full_path', response.data)
        self.assertIn('children_count', response.data)

    def test_create_category_admin_only(self):
        """Testa que apenas admin pode criar categoria."""
        # Cliente tenta criar
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.post(
            reverse('service-categories-list'),
            {'name': 'Nova Categoria', 'is_active': True},
            format='json'
        )
        self.assertEqual(response.status_code, http_status.HTTP_403_FORBIDDEN)
        
        # Admin cria com sucesso
        token = self.get_access_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.post(
            reverse('service-categories-list'),
            {'name': f'Nova Categoria-{self.unique_id}', 'is_active': True},
            format='json'
        )
        self.assertEqual(response.status_code, http_status.HTTP_201_CREATED)
        self.assertIn('id', response.data)

    def test_update_category_admin_only(self):
        """Testa que apenas admin pode atualizar categoria."""
        # Cliente tenta atualizar
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.patch(
            reverse('service-categories-detail', kwargs={'pk': self.category1.pk}),
            {'name': 'Nome Atualizado'},
            format='json'
        )
        self.assertEqual(response.status_code, http_status.HTTP_403_FORBIDDEN)
        
        # Admin atualiza com sucesso
        token = self.get_access_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.patch(
            reverse('service-categories-detail', kwargs={'pk': self.category1.pk}),
            {'description': 'Nova descrição'},
            format='json'
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

    def test_delete_category_admin_only(self):
        """Testa que apenas admin pode deletar categoria."""
        category = ServiceCategory.objects.create(name=f'ToDelete-{uuid.uuid4().hex[:8]}')
        
        # Cliente tenta deletar
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.delete(
            reverse('service-categories-detail', kwargs={'pk': category.pk})
        )
        self.assertEqual(response.status_code, http_status.HTTP_403_FORBIDDEN)
        
        # Admin deleta com sucesso
        token = self.get_access_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.delete(
            reverse('service-categories-detail', kwargs={'pk': category.pk})
        )
        self.assertEqual(response.status_code, http_status.HTTP_204_NO_CONTENT)

    def test_tree_action(self):
        """Testa action de árvore de categorias."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(reverse('service-categories-tree'))
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        for item in response.data:
            self.assertIn('children', item)

    def test_root_action(self):
        """Testa action de categorias raiz."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(reverse('service-categories-root'))
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        for item in response.data:
            self.assertIsNone(item['parent'])

    def test_filter_by_is_active(self):
        """Testa filtro por is_active."""
        ServiceCategory.objects.create(
            name=f'Inactive-{uuid.uuid4().hex[:8]}',
            is_active=False
        )
        
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('service-categories-list'),
            {'is_active': 'true'}
        )
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        results = self.get_results(response)
        for item in results:
            self.assertTrue(item['is_active'])

    def test_search_categories(self):
        """Testa busca por nome."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('service-categories-list'),
            {'search': self.unique_id}
        )
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        results = self.get_results(response)
        self.assertGreaterEqual(len(results), 1)


class ServiceViewSetTestCase(APITestCase):
    """Testes de integração para ServiceViewSet."""

    def setUp(self):
        """Cria dados de teste."""
        self.unique_id = str(uuid.uuid4())[:8]
        
        # Admin
        self.admin = User.objects.create_user(
            email=f'admin-{self.unique_id}@example.com',
            first_name='Admin',
            last_name='User',
            password='testpass123',
            user_type=UserType.ADMIN.value,
        )
        
        # Cliente
        self.client_user = User.objects.create_user(
            email=f'client-{self.unique_id}@example.com',
            first_name='Client',
            last_name='User',
            password='testpass123',
            user_type=UserType.CLIENT.value,
        )
        
        # Categoria e serviços
        self.category = ServiceCategory.objects.create(name=f'Web-{self.unique_id}')
        self.service1 = Service.objects.create(
            category=self.category,
            name=f'Site Institucional-{self.unique_id}'
        )
        self.service2 = Service.objects.create(
            category=self.category,
            name=f'E-commerce-{self.unique_id}'
        )

    def get_access_token(self, user):
        """Obtém token de acesso para um usuário."""
        response = self.client.post(
            reverse('auth-login'),
            {'email': user.email, 'password': 'testpass123'},
            format='json'
        )
        return response.data['access']

    def get_results(self, response):
        """Extrai resultados da resposta (suporta paginação)."""
        if isinstance(response.data, dict) and 'results' in response.data:
            return response.data['results']
        return response.data

    def test_list_services_authenticated(self):
        """Testa que usuário autenticado pode listar serviços."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(reverse('services-list'))
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        results = self.get_results(response)
        self.assertGreaterEqual(len(results), 2)

    def test_list_services_unauthenticated(self):
        """Testa que usuário não autenticado não pode listar."""
        response = self.client.get(reverse('services-list'))
        self.assertEqual(response.status_code, http_status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_service(self):
        """Testa obter detalhes de um serviço."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('services-detail', kwargs={'pk': self.service1.pk})
        )
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn('category_name', response.data)
        self.assertIn('category_full_path', response.data)

    def test_create_service_admin_only(self):
        """Testa que apenas admin pode criar serviço."""
        # Cliente tenta criar
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.post(
            reverse('services-list'),
            {'name': 'Novo Serviço', 'category': self.category.pk},
            format='json'
        )
        self.assertEqual(response.status_code, http_status.HTTP_403_FORBIDDEN)
        
        # Admin cria com sucesso
        token = self.get_access_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.post(
            reverse('services-list'),
            {'name': f'Novo Serviço-{self.unique_id}', 'category': self.category.pk},
            format='json'
        )
        self.assertEqual(response.status_code, http_status.HTTP_201_CREATED)

    def test_update_service_admin_only(self):
        """Testa que apenas admin pode atualizar serviço."""
        # Cliente tenta atualizar
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.patch(
            reverse('services-detail', kwargs={'pk': self.service1.pk}),
            {'name': 'Nome Atualizado'},
            format='json'
        )
        self.assertEqual(response.status_code, http_status.HTTP_403_FORBIDDEN)
        
        # Admin atualiza com sucesso
        token = self.get_access_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.patch(
            reverse('services-detail', kwargs={'pk': self.service1.pk}),
            {'description': 'Nova descrição'},
            format='json'
        )
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)

    def test_delete_service_admin_only(self):
        """Testa que apenas admin pode deletar serviço."""
        service = Service.objects.create(
            category=self.category,
            name=f'ToDelete-{uuid.uuid4().hex[:8]}'
        )
        
        # Cliente tenta deletar
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.delete(
            reverse('services-detail', kwargs={'pk': service.pk})
        )
        self.assertEqual(response.status_code, http_status.HTTP_403_FORBIDDEN)
        
        # Admin deleta com sucesso
        token = self.get_access_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.delete(
            reverse('services-detail', kwargs={'pk': service.pk})
        )
        self.assertEqual(response.status_code, http_status.HTTP_204_NO_CONTENT)

    def test_filter_by_category(self):
        """Testa filtro por categoria."""
        other_category = ServiceCategory.objects.create(name=f'Other-{uuid.uuid4().hex[:8]}')
        Service.objects.create(category=other_category, name=f'Other Service-{uuid.uuid4().hex[:8]}')
        
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('services-list'),
            {'category': self.category.pk}
        )
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        results = self.get_results(response)
        for item in results:
            self.assertEqual(item['category'], self.category.pk)

    def test_filter_by_is_active(self):
        """Testa filtro por is_active."""
        Service.objects.create(
            category=self.category,
            name=f'Inactive-{uuid.uuid4().hex[:8]}',
            is_active=False
        )
        
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('services-list'),
            {'is_active': 'true'}
        )
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        results = self.get_results(response)
        for item in results:
            self.assertTrue(item['is_active'])

    def test_search_services(self):
        """Testa busca por nome."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('services-list'),
            {'search': self.unique_id}
        )
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        results = self.get_results(response)
        self.assertGreaterEqual(len(results), 1)
