"""
Testes para o app admin (dashboard, gerenciamento e auditoria).

Inclui testes unitários para serializers e testes de integração para ViewSets,
permissões e middleware de auditoria.
"""
import uuid
from decimal import Decimal
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import timedelta

from api.accounts.models import User, ProviderProfile, ClientProfile
from api.accounts.enums import UserType
from api.orders.models import Order, Proposal
from api.orders.enums import OrderStatus, ProposalStatus
from api.payments.models import Payment
from api.subscriptions.models import SubscriptionPlan, UserSubscription
from api.subscriptions.enums import SubscriptionStatus, PaymentStatus
from api.reviews.models import Review
from api.services.models import Service, ServiceCategory
from api.admin.models import AdminAction
from api.admin.permissions import IsAdmin
from api.admin.serializers import (
    UserStatsSerializer,
    OrderStatsSerializer,
    ProposalStatsSerializer,
    PaymentStatsSerializer,
    SubscriptionStatsSerializer,
    ReviewStatsSerializer,
    DashboardStatsSerializer,
)
from api.admin.audit import (
    get_client_ip,
    log_admin_action,
    get_action_type_from_request,
    get_target_id_from_path,
)


# ==================== FIXTURES ====================

class AdminTestMixin:
    """Mixin com métodos auxiliares para testes do admin."""
    
    @staticmethod
    def _get_unique_email(prefix='user'):
        """Gera um email único para cada chamada usando UUID."""
        return f'{prefix}_{uuid.uuid4().hex[:8]}@test.com'
    
    def create_admin_user(self, email=None, password='admin123'):
        """Cria e retorna um usuário administrador."""
        if email is None:
            email = self._get_unique_email('admin')
        return User.objects.create_user(
            email=email,
            password=password,
            first_name='Admin',
            last_name='User',
            user_type=UserType.ADMIN.value,
            is_staff=True,
        )
    
    def create_client_user(self, email=None, password='client123'):
        """Cria e retorna um usuário cliente."""
        if email is None:
            email = self._get_unique_email('client')
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name='Cliente',
            last_name='Teste',
            user_type=UserType.CLIENT.value,
        )
        ClientProfile.objects.create(user=user)
        return user
    
    def create_provider_user(self, email=None, password='provider123'):
        """Cria e retorna um usuário prestador."""
        if email is None:
            email = self._get_unique_email('provider')
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name='Prestador',
            last_name='Teste',
            user_type=UserType.PROVIDER.value,
        )
        ProviderProfile.objects.create(user=user, is_verified=True)
        return user
    
    def create_category(self, name=None):
        """Cria e retorna uma categoria de serviço."""
        if name is None:
            name = f'Categoria_{uuid.uuid4().hex[:8]}'
        return ServiceCategory.objects.create(name=name)
    
    def create_service(self, category=None, name=None):
        """Cria e retorna um serviço."""
        if not category:
            category = self.create_category()
        if name is None:
            name = f'Serviço_{uuid.uuid4().hex[:8]}'
        return Service.objects.create(
            name=name,
            category=category,
            description='Descrição do serviço de teste',
        )
    
    def create_order(self, client=None, service=None, order_status=OrderStatus.PENDING.value):
        """Cria e retorna um pedido."""
        if not client:
            client = self.create_client_user()
        if not service:
            service = self.create_service()
        return Order.objects.create(
            client=client.client_profile,
            service=service,
            title='Pedido de Teste',
            description='Descrição do pedido de teste',
            budget_min=Decimal('100.00'),
            budget_max=Decimal('500.00'),
            deadline=timezone.now() + timedelta(days=7),
            status=order_status,
        )
    
    def create_proposal(self, order=None, provider=None, proposal_status=ProposalStatus.PENDING.value):
        """Cria e retorna uma proposta."""
        if not order:
            order = self.create_order()
        if not provider:
            provider = self.create_provider_user()
        return Proposal.objects.create(
            order=order,
            provider=provider.provider_profile,
            message='Proposta de teste',
            price=Decimal('300.00'),
            estimated_days=5,
            status=proposal_status,
            expires_at=timezone.now() + timedelta(days=3),
        )
    
    def create_subscription_plan(self, name=None):
        """Cria e retorna um plano de assinatura."""
        if name is None:
            name = f'Plano_{uuid.uuid4().hex[:8]}'
        return SubscriptionPlan.objects.create(
            name=name,
            price_monthly=Decimal('29.90'),
            price_yearly=Decimal('299.00'),
            is_active=True,
        )
    
    def create_subscription(self, user=None, plan=None, sub_status=SubscriptionStatus.ACTIVE.value):
        """Cria e retorna uma assinatura."""
        if not user:
            user = self.create_client_user()
        if not plan:
            plan = self.create_subscription_plan()
        return UserSubscription.objects.create(
            user=user,
            plan=plan,
            status=sub_status,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
        )
    
    def create_review(self, order=None, reviewer=None, reviewed_user=None, rating=5):
        """Cria e retorna uma avaliação."""
        if not order:
            order = self.create_order(order_status=OrderStatus.COMPLETED.value)
        if not reviewer:
            reviewer = order.client.user
        if not reviewed_user:
            reviewed_user = self.create_provider_user()
        return Review.objects.create(
            order=order,
            reviewer=reviewer,
            reviewed_user=reviewed_user,
            rating=rating,
            comment='Excelente trabalho!',
        )


# ==================== TESTES UNITÁRIOS: SERIALIZERS ====================

class UserStatsSerializerTest(TestCase):
    """Testes unitários para UserStatsSerializer."""
    
    def test_serializer_with_valid_data(self):
        """Testa serialização com dados válidos."""
        data = {
            'total_users': 100,
            'total_clients': 80,
            'total_providers': 15,
            'total_admins': 5,
            'active_users': 95,
            'new_users_today': 3,
            'new_users_this_week': 10,
            'new_users_this_month': 25,
            'verified_providers': 10,
            'providers_with_profile': 15,
        }
        serializer = UserStatsSerializer(data)
        self.assertEqual(serializer.data['total_users'], 100)
        self.assertEqual(serializer.data['total_clients'], 80)
        self.assertEqual(serializer.data['verified_providers'], 10)


class OrderStatsSerializerTest(TestCase):
    """Testes unitários para OrderStatsSerializer."""
    
    def test_serializer_with_valid_data(self):
        """Testa serialização com dados válidos."""
        data = {
            'total_orders': 50,
            'pending_orders': 10,
            'accepted_orders': 15,
            'in_progress_orders': 10,
            'completed_orders': 12,
            'cancelled_orders': 3,
            'new_orders_today': 2,
            'new_orders_this_week': 8,
            'new_orders_this_month': 20,
            'avg_budget_min': Decimal('150.00'),
            'avg_budget_max': Decimal('350.00'),
        }
        serializer = OrderStatsSerializer(data)
        self.assertEqual(serializer.data['total_orders'], 50)
        self.assertEqual(str(serializer.data['avg_budget_min']), '150.00')


class DashboardStatsSerializerTest(TestCase):
    """Testes unitários para DashboardStatsSerializer."""
    
    def test_serializer_with_nested_data(self):
        """Testa serialização com dados aninhados."""
        data = {
            'users': {
                'total_users': 100,
                'total_clients': 80,
                'total_providers': 15,
                'total_admins': 5,
                'active_users': 95,
                'new_users_today': 3,
                'new_users_this_week': 10,
                'new_users_this_month': 25,
                'verified_providers': 10,
                'providers_with_profile': 15,
            },
            'orders': {
                'total_orders': 50,
                'pending_orders': 10,
                'accepted_orders': 15,
                'in_progress_orders': 10,
                'completed_orders': 12,
                'cancelled_orders': 3,
                'new_orders_today': 2,
                'new_orders_this_week': 8,
                'new_orders_this_month': 20,
                'avg_budget_min': None,
                'avg_budget_max': None,
            },
            'proposals': {
                'total_proposals': 30,
                'pending_proposals': 5,
                'accepted_proposals': 20,
                'declined_proposals': 3,
                'expired_proposals': 2,
                'new_proposals_today': 1,
                'new_proposals_this_week': 5,
                'new_proposals_this_month': 15,
                'avg_price': None,
                'avg_estimated_days': None,
            },
            'payments': {
                'total_payments': 25,
                'pending_payments': 2,
                'paid_payments': 20,
                'failed_payments': 2,
                'refunded_payments': 1,
                'total_revenue': Decimal('5000.00'),
                'revenue_today': Decimal('200.00'),
                'revenue_this_week': Decimal('1000.00'),
                'revenue_this_month': Decimal('3000.00'),
                'avg_payment_amount': Decimal('250.00'),
            },
            'subscriptions': {
                'total_subscriptions': 20,
                'active_subscriptions': 18,
                'cancelled_subscriptions': 1,
                'expired_subscriptions': 1,
                'suspended_subscriptions': 0,
                'total_subscription_revenue': Decimal('1000.00'),
                'subscription_revenue_this_month': Decimal('500.00'),
                'subscriptions_by_plan': {'Básico': 10, 'Premium': 8},
            },
            'reviews': {
                'total_reviews': 40,
                'avg_rating': Decimal('4.5'),
                'reviews_by_rating': {'5': 25, '4': 10, '3': 3, '2': 1, '1': 1},
                'new_reviews_today': 2,
                'new_reviews_this_week': 5,
                'new_reviews_this_month': 15,
            },
            'generated_at': timezone.now(),
        }
        serializer = DashboardStatsSerializer(data)
        self.assertEqual(serializer.data['users']['total_users'], 100)
        self.assertEqual(serializer.data['orders']['total_orders'], 50)


# ==================== TESTES DE INTEGRAÇÃO: PERMISSÕES ====================

class IsAdminPermissionTest(APITestCase, AdminTestMixin):
    """Testes para a permissão IsAdmin."""
    
    def setUp(self):
        self.admin_user = self.create_admin_user()
        self.client_user = self.create_client_user()
        self.provider_user = self.create_provider_user()
    
    def test_admin_user_has_permission(self):
        """Admin deve ter permissão."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/admin/dashboard/stats/')
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_client_user_denied(self):
        """Cliente não deve ter permissão."""
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get('/api/admin/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_provider_user_denied(self):
        """Prestador não deve ter permissão."""
        self.client.force_authenticate(user=self.provider_user)
        response = self.client.get('/api/admin/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthenticated_denied(self):
        """Usuário não autenticado não deve ter permissão."""
        response = self.client.get('/api/admin/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_staff_user_has_permission(self):
        """Usuário staff deve ter permissão."""
        staff_user = User.objects.create_user(
            email='staff@test.com',
            password='staff123',
            first_name='Staff',
            last_name='User',
            user_type=UserType.CLIENT.value,
            is_staff=True,
        )
        self.client.force_authenticate(user=staff_user)
        response = self.client.get('/api/admin/dashboard/stats/')
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ==================== TESTES DE INTEGRAÇÃO: DASHBOARD ====================

class AdminDashboardViewSetTest(APITestCase, AdminTestMixin):
    """Testes de integração para AdminDashboardViewSet."""
    
    def setUp(self):
        self.admin_user = self.create_admin_user()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_stats_endpoint_returns_200(self):
        """Endpoint stats deve retornar 200."""
        response = self.client.get('/api/admin/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_stats_contains_all_sections(self):
        """Stats deve conter todas as seções."""
        response = self.client.get('/api/admin/dashboard/stats/')
        data = response.json()
        
        self.assertIn('users', data)
        self.assertIn('orders', data)
        self.assertIn('proposals', data)
        self.assertIn('payments', data)
        self.assertIn('subscriptions', data)
        self.assertIn('reviews', data)
        self.assertIn('generated_at', data)
    
    def test_stats_user_counts_correct(self):
        """Contagem de usuários deve estar correta."""
        # Criar alguns usuários
        self.create_client_user(email='client2@test.com')
        self.create_provider_user(email='provider2@test.com')
        
        response = self.client.get('/api/admin/dashboard/stats/')
        data = response.json()
        
        # Admin + 2 clients + 2 providers = 5 (mas só 2 clientes e 2 providers foram criados)
        self.assertGreaterEqual(data['users']['total_users'], 3)


# ==================== TESTES DE INTEGRAÇÃO: USER VIEWSET ====================

class AdminUserViewSetTest(APITestCase, AdminTestMixin):
    """Testes de integração para AdminUserViewSet."""
    
    def setUp(self):
        self.admin_user = self.create_admin_user()
        self.target_user = self.create_client_user()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_list_users(self):
        """Deve listar todos os usuários."""
        response = self.client.get('/api/admin/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_retrieve_user(self):
        """Deve retornar detalhes de um usuário."""
        response = self.client.get(f'/api/admin/users/{self.target_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['email'], self.target_user.email)
    
    def test_update_user(self):
        """Deve atualizar um usuário."""
        response = self.client.patch(
            f'/api/admin/users/{self.target_user.id}/',
            {'first_name': 'Novo Nome'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.first_name, 'Novo Nome')
    
    def test_suspend_user(self):
        """Deve suspender um usuário."""
        response = self.client.post(f'/api/admin/users/{self.target_user.id}/suspend/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)
    
    def test_activate_user(self):
        """Deve ativar um usuário suspenso."""
        self.target_user.is_active = False
        self.target_user.save()
        
        response = self.client.post(f'/api/admin/users/{self.target_user.id}/activate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.is_active)
    
    def test_filter_by_user_type(self):
        """Deve filtrar usuários por tipo."""
        self.create_provider_user(email='provider2@test.com')
        
        response = self.client.get('/api/admin/users/', {'user_type': UserType.PROVIDER.value})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Todos os resultados devem ser do tipo PROVIDER
        for user in response.json().get('results', response.json()):
            self.assertEqual(user['user_type'], UserType.PROVIDER.value)


# ==================== TESTES DE INTEGRAÇÃO: ORDER VIEWSET ====================

class AdminOrderViewSetTest(APITestCase, AdminTestMixin):
    """Testes de integração para AdminOrderViewSet."""
    
    def setUp(self):
        self.admin_user = self.create_admin_user()
        self.client.force_authenticate(user=self.admin_user)
        self.order = self.create_order()
    
    def test_list_orders(self):
        """Deve listar todos os pedidos."""
        response = self.client.get('/api/admin/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_retrieve_order(self):
        """Deve retornar detalhes de um pedido."""
        response = self.client.get(f'/api/admin/orders/{self.order.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_by_status(self):
        """Deve filtrar pedidos por status."""
        self.create_order(order_status=OrderStatus.COMPLETED.value)
        
        response = self.client.get('/api/admin/orders/', {'status': OrderStatus.PENDING.value})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ==================== TESTES DE INTEGRAÇÃO: SUBSCRIPTION VIEWSET ====================

class AdminSubscriptionViewSetTest(APITestCase, AdminTestMixin):
    """Testes de integração para AdminSubscriptionViewSet."""
    
    def setUp(self):
        self.admin_user = self.create_admin_user()
        self.client.force_authenticate(user=self.admin_user)
        self.subscription = self.create_subscription()
    
    def test_list_subscriptions(self):
        """Deve listar todas as assinaturas."""
        response = self.client.get('/api/admin/subscriptions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_cancel_subscription(self):
        """Deve cancelar uma assinatura."""
        response = self.client.post(f'/api/admin/subscriptions/{self.subscription.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, SubscriptionStatus.CANCELLED.value)
    
    def test_reactivate_subscription(self):
        """Deve reativar uma assinatura cancelada."""
        self.subscription.status = SubscriptionStatus.CANCELLED.value
        self.subscription.save()
        
        response = self.client.post(f'/api/admin/subscriptions/{self.subscription.id}/reactivate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, SubscriptionStatus.ACTIVE.value)
    
    def test_suspend_subscription(self):
        """Deve suspender uma assinatura ativa."""
        response = self.client.post(f'/api/admin/subscriptions/{self.subscription.id}/suspend/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, SubscriptionStatus.SUSPENDED.value)


# ==================== TESTES DE INTEGRAÇÃO: REVIEW VIEWSET ====================

class AdminReviewViewSetTest(APITestCase, AdminTestMixin):
    """Testes de integração para AdminReviewViewSet."""
    
    def setUp(self):
        self.admin_user = self.create_admin_user()
        self.client.force_authenticate(user=self.admin_user)
        self.review = self.create_review()
    
    def test_list_reviews(self):
        """Deve listar todas as avaliações."""
        response = self.client.get('/api/admin/reviews/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_delete_review(self):
        """Deve remover uma avaliação (soft delete)."""
        review_id = self.review.id
        response = self.client.delete(f'/api/admin/reviews/{review_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Deve ter sido soft deleted
        self.review.refresh_from_db()
        self.assertIsNotNone(self.review.deleted_at)
    
    def test_filter_by_rating(self):
        """Deve filtrar avaliações por nota."""
        response = self.client.get('/api/admin/reviews/', {'rating': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ==================== TESTES DE INTEGRAÇÃO: AUDIT LOG VIEWSET ====================

class AdminAuditLogViewSetTest(APITestCase, AdminTestMixin):
    """Testes de integração para AdminAuditLogViewSet."""
    
    def setUp(self):
        self.admin_user = self.create_admin_user()
        self.client.force_authenticate(user=self.admin_user)
        # Criar um log de auditoria
        self.audit_log = AdminAction.objects.create(
            admin_user=self.admin_user,
            action_type='USER_VIEW',
            description='Admin visualizou usuário',
            target_model='User',
            target_id=1,
        )
    
    def test_list_audit_logs(self):
        """Deve listar todos os logs de auditoria."""
        response = self.client.get('/api/admin/audit-logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_retrieve_audit_log(self):
        """Deve retornar detalhes de um log."""
        response = self.client.get(f'/api/admin/audit-logs/{self.audit_log.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['action_type'], 'USER_VIEW')
    
    def test_filter_by_action_type(self):
        """Deve filtrar logs por tipo de ação."""
        response = self.client.get('/api/admin/audit-logs/', {'action_type': 'USER_VIEW'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_audit_logs_are_read_only(self):
        """Logs de auditoria não podem ser editados ou deletados."""
        # Tentar atualizar
        response = self.client.patch(
            f'/api/admin/audit-logs/{self.audit_log.id}/',
            {'description': 'Nova descrição'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Tentar deletar
        response = self.client.delete(f'/api/admin/audit-logs/{self.audit_log.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


# ==================== TESTES DE INTEGRAÇÃO: MIDDLEWARE DE AUDITORIA ====================

class AdminAuditMiddlewareTest(APITestCase, AdminTestMixin):
    """Testes de integração para AdminAuditMiddleware."""
    
    def setUp(self):
        self.admin_user = self.create_admin_user()
        self.target_user = self.create_client_user()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_post_action_creates_audit_log(self):
        """Ações POST devem criar log de auditoria."""
        initial_count = AdminAction.objects.count()
        
        # Suspender usuário (POST)
        self.client.post(f'/api/admin/users/{self.target_user.id}/suspend/')
        
        # Deve ter criado um log
        self.assertGreater(AdminAction.objects.count(), initial_count)
    
    def test_patch_action_creates_audit_log(self):
        """Ações PATCH devem criar log de auditoria."""
        initial_count = AdminAction.objects.count()
        
        # Atualizar usuário (PATCH)
        self.client.patch(
            f'/api/admin/users/{self.target_user.id}/',
            {'first_name': 'Novo'},
            format='json'
        )
        
        # Deve ter criado um log
        self.assertGreater(AdminAction.objects.count(), initial_count)
    
    def test_get_action_does_not_create_audit_log(self):
        """Ações GET não devem criar log de auditoria."""
        initial_count = AdminAction.objects.count()
        
        # Listar usuários (GET)
        self.client.get('/api/admin/users/')
        
        # Não deve ter criado log
        self.assertEqual(AdminAction.objects.count(), initial_count)
    
    def test_audit_log_contains_correct_info(self):
        """Log de auditoria deve conter informações corretas."""
        # Suspender usuário
        self.client.post(f'/api/admin/users/{self.target_user.id}/suspend/')
        
        # Buscar o log criado
        log = AdminAction.objects.filter(action_type__contains='SUSPEND').first()
        
        self.assertIsNotNone(log)
        self.assertEqual(log.admin_user, self.admin_user)
        self.assertEqual(log.target_model, 'User')
        self.assertEqual(log.target_id, self.target_user.id)
    
    def test_failed_requests_do_not_create_log(self):
        """Requisições com erro não devem criar log."""
        initial_count = AdminAction.objects.count()
        
        # Tentar acessar usuário inexistente
        self.client.post('/api/admin/users/999999/suspend/')
        
        # Não deve ter criado log
        self.assertEqual(AdminAction.objects.count(), initial_count)


# ==================== TESTES UNITÁRIOS: FUNÇÕES DE AUDITORIA ====================

class AuditFunctionsTest(TestCase, AdminTestMixin):
    """Testes unitários para funções de auditoria."""
    
    def test_get_target_id_from_path(self):
        """Deve extrair ID corretamente da URL."""
        self.assertEqual(get_target_id_from_path('/api/admin/users/123/'), 123)
        self.assertEqual(get_target_id_from_path('/api/admin/users/123/suspend/'), 123)
        self.assertIsNone(get_target_id_from_path('/api/admin/users/'))
    
    def test_get_action_type_from_request(self):
        """Deve determinar tipo de ação corretamente."""
        from django.test import RequestFactory
        factory = RequestFactory()
        
        # POST em suspend
        request = factory.post('/api/admin/users/123/suspend/')
        action_type = get_action_type_from_request(request)
        self.assertIn('SUSPEND', action_type)
        
        # DELETE em reviews
        request = factory.delete('/api/admin/reviews/456/')
        action_type = get_action_type_from_request(request)
        self.assertIn('DELETE', action_type)
    
    def test_log_admin_action_creates_record(self):
        """log_admin_action deve criar registro no banco."""
        admin_user = self.create_admin_user()
        
        action = log_admin_action(
            admin_user=admin_user,
            action_type='TEST_ACTION',
            description='Ação de teste',
            target_model='TestModel',
            target_id=1,
            metadata={'test': True},
            ip_address='127.0.0.1',
        )
        
        self.assertIsNotNone(action)
        self.assertEqual(action.action_type, 'TEST_ACTION')
        self.assertEqual(action.target_model, 'TestModel')
        self.assertEqual(action.ip_address, '127.0.0.1')


# ==================== TESTE E2E: FLUXO COMPLETO ====================

class AdminE2ETest(APITestCase, AdminTestMixin):
    """
    Teste E2E: Admin acessa dashboard → gerencia usuários → verifica logs de auditoria.
    """
    
    def test_admin_full_flow(self):
        """Testa fluxo completo de administração."""
        # 1. Criar admin e autenticar
        admin_user = self.create_admin_user()
        self.client.force_authenticate(user=admin_user)
        
        # 2. Acessar dashboard
        response = self.client.get('/api/admin/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. Criar usuário para gerenciar
        target_user = self.create_client_user()
        
        # 4. Listar usuários
        response = self.client.get('/api/admin/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 5. Visualizar usuário específico
        response = self.client.get(f'/api/admin/users/{target_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 6. Atualizar usuário
        response = self.client.patch(
            f'/api/admin/users/{target_user.id}/',
            {'first_name': 'Atualizado'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 7. Suspender usuário
        response = self.client.post(f'/api/admin/users/{target_user.id}/suspend/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 8. Verificar logs de auditoria
        response = self.client.get('/api/admin/audit-logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Deve haver logs das ações realizadas
        logs = response.json()
        if isinstance(logs, dict) and 'results' in logs:
            logs = logs['results']
        
        # Verificar que há logs de UPDATE e SUSPEND
        action_types = [log['action_type'] for log in logs]
        self.assertTrue(any('UPDATE' in at for at in action_types))
        self.assertTrue(any('SUSPEND' in at for at in action_types))
        
        # 9. Ativar usuário novamente
        response = self.client.post(f'/api/admin/users/{target_user.id}/activate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 10. Verificar que usuário está ativo
        target_user.refresh_from_db()
        self.assertTrue(target_user.is_active)
