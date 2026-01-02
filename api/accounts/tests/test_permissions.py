"""
Testes unitários para as permissões customizadas do app accounts.
"""
from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
import uuid

from api.accounts.models import User
from api.accounts.enums import UserType
from api.accounts.permissions import (
    IsClient,
    IsProvider,
    IsAdmin,
    IsClientOrProvider,
    IsOwnerOrAdmin,
)


class MockRequest:
    """Mock de request para testes de permissões."""
    
    def __init__(self, user=None):
        self.user = user


class MockView:
    """Mock de view para testes de permissões."""
    pass


class IsClientPermissionTestCase(TestCase):
    """Testes para a permissão IsClient."""

    def setUp(self):
        """Cria dados de teste."""
        self.unique_id = str(uuid.uuid4())[:8]
        self.client_user = User.objects.create_user(
            email=f'client-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Client',
            last_name='User',
            user_type=UserType.CLIENT.value,
        )
        self.provider_user = User.objects.create_user(
            email=f'provider-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Provider',
            last_name='User',
            user_type=UserType.PROVIDER.value,
        )
        self.admin_user = User.objects.create_user(
            email=f'admin-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            user_type=UserType.ADMIN.value,
        )

    def test_client_user_has_permission(self):
        """Testa que cliente tem permissão."""
        permission = IsClient()
        request = MockRequest(user=self.client_user)
        
        self.assertTrue(permission.has_permission(request, MockView()))

    def test_provider_user_denied(self):
        """Testa que prestador é negado."""
        permission = IsClient()
        request = MockRequest(user=self.provider_user)
        
        self.assertFalse(permission.has_permission(request, MockView()))

    def test_admin_user_denied(self):
        """Testa que admin é negado."""
        permission = IsClient()
        request = MockRequest(user=self.admin_user)
        
        self.assertFalse(permission.has_permission(request, MockView()))

    def test_unauthenticated_user_denied(self):
        """Testa que usuário não autenticado é negado."""
        permission = IsClient()
        request = MockRequest(user=AnonymousUser())
        
        self.assertFalse(permission.has_permission(request, MockView()))

    def test_no_user_denied(self):
        """Testa que request sem usuário é negado."""
        permission = IsClient()
        request = MockRequest(user=None)
        
        self.assertFalse(permission.has_permission(request, MockView()))


class IsProviderPermissionTestCase(TestCase):
    """Testes para a permissão IsProvider."""

    def setUp(self):
        """Cria dados de teste."""
        self.unique_id = str(uuid.uuid4())[:8]
        self.client_user = User.objects.create_user(
            email=f'client-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Client',
            last_name='User',
            user_type=UserType.CLIENT.value,
        )
        self.provider_user = User.objects.create_user(
            email=f'provider-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Provider',
            last_name='User',
            user_type=UserType.PROVIDER.value,
        )
        self.admin_user = User.objects.create_user(
            email=f'admin-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            user_type=UserType.ADMIN.value,
        )

    def test_provider_user_has_permission(self):
        """Testa que prestador tem permissão."""
        permission = IsProvider()
        request = MockRequest(user=self.provider_user)
        
        self.assertTrue(permission.has_permission(request, MockView()))

    def test_client_user_denied(self):
        """Testa que cliente é negado."""
        permission = IsProvider()
        request = MockRequest(user=self.client_user)
        
        self.assertFalse(permission.has_permission(request, MockView()))

    def test_admin_user_denied(self):
        """Testa que admin é negado."""
        permission = IsProvider()
        request = MockRequest(user=self.admin_user)
        
        self.assertFalse(permission.has_permission(request, MockView()))

    def test_unauthenticated_user_denied(self):
        """Testa que usuário não autenticado é negado."""
        permission = IsProvider()
        request = MockRequest(user=AnonymousUser())
        
        self.assertFalse(permission.has_permission(request, MockView()))


class IsAdminPermissionTestCase(TestCase):
    """Testes para a permissão IsAdmin."""

    def setUp(self):
        """Cria dados de teste."""
        self.unique_id = str(uuid.uuid4())[:8]
        self.client_user = User.objects.create_user(
            email=f'client-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Client',
            last_name='User',
            user_type=UserType.CLIENT.value,
        )
        self.admin_user = User.objects.create_user(
            email=f'admin-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            user_type=UserType.ADMIN.value,
        )
        self.staff_user = User.objects.create_user(
            email=f'staff-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Staff',
            last_name='User',
            user_type=UserType.CLIENT.value,
            is_staff=True,
        )
        self.superuser = User.objects.create_superuser(
            email=f'super-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Super',
            last_name='User',
        )

    def test_admin_user_has_permission(self):
        """Testa que usuário com user_type ADMIN tem permissão."""
        permission = IsAdmin()
        request = MockRequest(user=self.admin_user)
        
        self.assertTrue(permission.has_permission(request, MockView()))

    def test_staff_user_has_permission(self):
        """Testa que usuário com is_staff tem permissão."""
        permission = IsAdmin()
        request = MockRequest(user=self.staff_user)
        
        self.assertTrue(permission.has_permission(request, MockView()))

    def test_superuser_has_permission(self):
        """Testa que superuser tem permissão."""
        permission = IsAdmin()
        request = MockRequest(user=self.superuser)
        
        self.assertTrue(permission.has_permission(request, MockView()))

    def test_client_user_denied(self):
        """Testa que cliente comum é negado."""
        permission = IsAdmin()
        request = MockRequest(user=self.client_user)
        
        self.assertFalse(permission.has_permission(request, MockView()))

    def test_unauthenticated_user_denied(self):
        """Testa que usuário não autenticado é negado."""
        permission = IsAdmin()
        request = MockRequest(user=AnonymousUser())
        
        self.assertFalse(permission.has_permission(request, MockView()))


class IsClientOrProviderPermissionTestCase(TestCase):
    """Testes para a permissão IsClientOrProvider."""

    def setUp(self):
        """Cria dados de teste."""
        self.unique_id = str(uuid.uuid4())[:8]
        self.client_user = User.objects.create_user(
            email=f'client-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Client',
            last_name='User',
            user_type=UserType.CLIENT.value,
        )
        self.provider_user = User.objects.create_user(
            email=f'provider-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Provider',
            last_name='User',
            user_type=UserType.PROVIDER.value,
        )
        self.admin_user = User.objects.create_user(
            email=f'admin-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            user_type=UserType.ADMIN.value,
        )

    def test_client_user_has_permission(self):
        """Testa que cliente tem permissão."""
        permission = IsClientOrProvider()
        request = MockRequest(user=self.client_user)
        
        self.assertTrue(permission.has_permission(request, MockView()))

    def test_provider_user_has_permission(self):
        """Testa que prestador tem permissão."""
        permission = IsClientOrProvider()
        request = MockRequest(user=self.provider_user)
        
        self.assertTrue(permission.has_permission(request, MockView()))

    def test_admin_user_denied(self):
        """Testa que admin é negado."""
        permission = IsClientOrProvider()
        request = MockRequest(user=self.admin_user)
        
        self.assertFalse(permission.has_permission(request, MockView()))


class IsOwnerOrAdminPermissionTestCase(TestCase):
    """Testes para a permissão IsOwnerOrAdmin."""

    def setUp(self):
        """Cria dados de teste."""
        self.unique_id = str(uuid.uuid4())[:8]
        self.owner_user = User.objects.create_user(
            email=f'owner-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Owner',
            last_name='User',
            user_type=UserType.CLIENT.value,
        )
        self.other_user = User.objects.create_user(
            email=f'other-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User',
            user_type=UserType.CLIENT.value,
        )
        self.admin_user = User.objects.create_user(
            email=f'admin-{self.unique_id}@example.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            user_type=UserType.ADMIN.value,
        )

    def test_owner_has_permission(self):
        """Testa que dono tem permissão."""
        permission = IsOwnerOrAdmin()
        request = MockRequest(user=self.owner_user)
        
        # Mock de objeto com atributo 'user'
        class MockObj:
            def __init__(self, user):
                self.user = user
        
        obj = MockObj(user=self.owner_user)
        
        self.assertTrue(permission.has_object_permission(request, MockView(), obj))

    def test_admin_has_permission_on_any_object(self):
        """Testa que admin tem permissão em qualquer objeto."""
        permission = IsOwnerOrAdmin()
        request = MockRequest(user=self.admin_user)
        
        class MockObj:
            def __init__(self, user):
                self.user = user
        
        obj = MockObj(user=self.owner_user)  # Objeto de outro usuário
        
        self.assertTrue(permission.has_object_permission(request, MockView(), obj))

    def test_non_owner_denied(self):
        """Testa que não-dono é negado."""
        permission = IsOwnerOrAdmin()
        request = MockRequest(user=self.other_user)
        
        class MockObj:
            def __init__(self, user):
                self.user = user
        
        obj = MockObj(user=self.owner_user)
        
        self.assertFalse(permission.has_object_permission(request, MockView(), obj))

    def test_owner_via_client_attribute(self):
        """Testa permissão via atributo 'client'."""
        permission = IsOwnerOrAdmin()
        request = MockRequest(user=self.owner_user)
        
        class MockObj:
            def __init__(self, client):
                self.client = client
        
        obj = MockObj(client=self.owner_user)
        
        self.assertTrue(permission.has_object_permission(request, MockView(), obj))

    def test_owner_via_provider_attribute(self):
        """Testa permissão via atributo 'provider'."""
        permission = IsOwnerOrAdmin()
        request = MockRequest(user=self.owner_user)
        
        class MockObj:
            def __init__(self, provider):
                self.provider = provider
        
        obj = MockObj(provider=self.owner_user)
        
        self.assertTrue(permission.has_object_permission(request, MockView(), obj))

    def test_owner_via_get_owner_method(self):
        """Testa permissão via método 'get_owner()'."""
        permission = IsOwnerOrAdmin()
        request = MockRequest(user=self.owner_user)
        
        class MockObj:
            def __init__(self, owner):
                self._owner = owner
            
            def get_owner(self):
                return self._owner
        
        obj = MockObj(owner=self.owner_user)
        
        self.assertTrue(permission.has_object_permission(request, MockView(), obj))
