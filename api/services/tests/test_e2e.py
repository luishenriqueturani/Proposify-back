"""
Testes E2E (End-to-End) para o app services.
"""
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status as http_status
import uuid

from api.accounts.models import User
from api.accounts.enums import UserType
from api.services.models import ServiceCategory, Service


class CategoryServicesEndpointTestCase(APITestCase):
    """Testes para o endpoint /categories/{id}/services/."""

    def setUp(self):
        """Cria dados de teste."""
        self.unique_id = str(uuid.uuid4())[:8]
        
        # Cliente
        self.client_user = User.objects.create_user(
            email=f'client-{self.unique_id}@example.com',
            first_name='Client',
            last_name='User',
            password='testpass123',
            user_type=UserType.CLIENT.value,
        )
        
        # Categoria com serviços
        self.category = ServiceCategory.objects.create(name=f'Web-{self.unique_id}')
        self.service1 = Service.objects.create(
            category=self.category,
            name=f'Serviço Ativo 1-{self.unique_id}',
            is_active=True
        )
        self.service2 = Service.objects.create(
            category=self.category,
            name=f'Serviço Ativo 2-{self.unique_id}',
            is_active=True
        )
        self.service_inactive = Service.objects.create(
            category=self.category,
            name=f'Serviço Inativo-{self.unique_id}',
            is_active=False
        )

    def get_access_token(self, user):
        """Obtém token de acesso para um usuário."""
        response = self.client.post(
            reverse('auth-login'),
            {'email': user.email, 'password': 'testpass123'},
            format='json'
        )
        return response.data['access']

    def test_get_services_of_category(self):
        """Testa obter serviços de uma categoria."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('service-categories-services', kwargs={'pk': self.category.pk})
        )
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        # Deve retornar apenas serviços ativos
        self.assertEqual(len(response.data), 2)
        for item in response.data:
            self.assertTrue(item['is_active'])

    def test_get_services_empty_category(self):
        """Testa categoria sem serviços."""
        empty_category = ServiceCategory.objects.create(name=f'Empty-{uuid.uuid4().hex[:8]}')
        
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('service-categories-services', kwargs={'pk': empty_category.pk})
        )
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_get_services_nonexistent_category(self):
        """Testa categoria inexistente."""
        token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(
            reverse('service-categories-services', kwargs={'pk': 99999})
        )
        
        self.assertEqual(response.status_code, http_status.HTTP_404_NOT_FOUND)


class ServicesE2ETestCase(APITestCase):
    """Testes E2E para fluxo completo de criação de categorias e serviços."""

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

    def test_e2e_create_category_and_services(self):
        """Teste E2E: Admin cria categoria -> cria serviços -> cliente lista."""
        unique = uuid.uuid4().hex[:8]
        
        # 1. Admin faz login
        admin_token = self.get_access_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        
        # 2. Admin cria categoria
        category_response = self.client.post(
            reverse('service-categories-list'),
            {'name': f'Desenvolvimento-{unique}', 'description': 'Serviços de desenvolvimento'},
            format='json'
        )
        self.assertEqual(category_response.status_code, http_status.HTTP_201_CREATED)
        category_id = category_response.data['id']
        
        # 3. Admin cria serviços na categoria
        service1_response = self.client.post(
            reverse('services-list'),
            {
                'name': f'Criação de Sites-{unique}',
                'description': 'Desenvolvimento de sites institucionais',
                'category': category_id
            },
            format='json'
        )
        self.assertEqual(service1_response.status_code, http_status.HTTP_201_CREATED)
        
        service2_response = self.client.post(
            reverse('services-list'),
            {
                'name': f'E-commerce-{unique}',
                'description': 'Lojas virtuais completas',
                'category': category_id
            },
            format='json'
        )
        self.assertEqual(service2_response.status_code, http_status.HTTP_201_CREATED)
        
        # 4. Cliente faz login
        client_token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {client_token}')
        
        # 5. Cliente lista serviços da categoria
        services_response = self.client.get(
            reverse('service-categories-services', kwargs={'pk': category_id})
        )
        self.assertEqual(services_response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(len(services_response.data), 2)
        
        # 6. Cliente busca serviços por nome
        search_response = self.client.get(
            reverse('services-list'),
            {'search': unique}
        )
        self.assertEqual(search_response.status_code, http_status.HTTP_200_OK)
        results = self.get_results(search_response)
        self.assertEqual(len(results), 2)

    def test_e2e_category_hierarchy(self):
        """Teste E2E: Admin cria hierarquia de categorias -> cliente visualiza árvore."""
        unique = uuid.uuid4().hex[:8]
        
        # Admin faz login
        admin_token = self.get_access_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        
        # Cria categoria raiz
        root_response = self.client.post(
            reverse('service-categories-list'),
            {'name': f'Tecnologia-{unique}'},
            format='json'
        )
        self.assertEqual(root_response.status_code, http_status.HTTP_201_CREATED)
        root_id = root_response.data['id']
        
        # Cria subcategoria
        sub_response = self.client.post(
            reverse('service-categories-list'),
            {'name': f'Desenvolvimento Web-{unique}', 'parent': root_id},
            format='json'
        )
        self.assertEqual(sub_response.status_code, http_status.HTTP_201_CREATED)
        sub_id = sub_response.data['id']
        
        # Verifica que é subcategoria
        self.assertEqual(sub_response.data['parent'], root_id)
        self.assertTrue(sub_response.data['is_subcategory'])
        
        # Cria serviço na subcategoria
        service_response = self.client.post(
            reverse('services-list'),
            {'name': f'Criação de Site-{unique}', 'category': sub_id},
            format='json'
        )
        self.assertEqual(service_response.status_code, http_status.HTTP_201_CREATED)
        
        # Cliente visualiza árvore
        client_token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {client_token}')
        
        tree_response = self.client.get(reverse('service-categories-tree'))
        self.assertEqual(tree_response.status_code, http_status.HTTP_200_OK)
        
        # Encontra a categoria raiz criada
        root_in_tree = None
        for item in tree_response.data:
            if item['id'] == root_id:
                root_in_tree = item
                break
        
        self.assertIsNotNone(root_in_tree)
        self.assertGreaterEqual(len(root_in_tree['children']), 1)

    def test_e2e_permission_denied_for_client(self):
        """Teste E2E: Cliente não pode criar/editar/deletar categorias e serviços."""
        unique = uuid.uuid4().hex[:8]
        
        # Admin cria categoria
        admin_token = self.get_access_token(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        
        category_response = self.client.post(
            reverse('service-categories-list'),
            {'name': f'TestCategory-{unique}'},
            format='json'
        )
        category_id = category_response.data['id']
        
        service_response = self.client.post(
            reverse('services-list'),
            {'name': f'TestService-{unique}', 'category': category_id},
            format='json'
        )
        service_id = service_response.data['id']
        
        # Cliente tenta operações restritas
        client_token = self.get_access_token(self.client_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {client_token}')
        
        # Tentar criar categoria
        create_cat = self.client.post(
            reverse('service-categories-list'),
            {'name': 'Nova Cat'},
            format='json'
        )
        self.assertEqual(create_cat.status_code, http_status.HTTP_403_FORBIDDEN)
        
        # Tentar editar categoria
        edit_cat = self.client.patch(
            reverse('service-categories-detail', kwargs={'pk': category_id}),
            {'name': 'Editada'},
            format='json'
        )
        self.assertEqual(edit_cat.status_code, http_status.HTTP_403_FORBIDDEN)
        
        # Tentar deletar categoria
        delete_cat = self.client.delete(
            reverse('service-categories-detail', kwargs={'pk': category_id})
        )
        self.assertEqual(delete_cat.status_code, http_status.HTTP_403_FORBIDDEN)
        
        # Tentar criar serviço
        create_svc = self.client.post(
            reverse('services-list'),
            {'name': 'Novo Serviço', 'category': category_id},
            format='json'
        )
        self.assertEqual(create_svc.status_code, http_status.HTTP_403_FORBIDDEN)
        
        # Tentar editar serviço
        edit_svc = self.client.patch(
            reverse('services-detail', kwargs={'pk': service_id}),
            {'name': 'Editado'},
            format='json'
        )
        self.assertEqual(edit_svc.status_code, http_status.HTTP_403_FORBIDDEN)
        
        # Tentar deletar serviço
        delete_svc = self.client.delete(
            reverse('services-detail', kwargs={'pk': service_id})
        )
        self.assertEqual(delete_svc.status_code, http_status.HTTP_403_FORBIDDEN)
        
        # Mas pode ler
        list_cat = self.client.get(reverse('service-categories-list'))
        self.assertEqual(list_cat.status_code, http_status.HTTP_200_OK)
        
        list_svc = self.client.get(reverse('services-list'))
        self.assertEqual(list_svc.status_code, http_status.HTTP_200_OK)
