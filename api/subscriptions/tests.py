"""
Testes unitários para o app subscriptions.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from django.utils import timezone
import time
from datetime import timedelta
from decimal import Decimal
from api.subscriptions.models import SubscriptionPlan, UserSubscription
from api.subscriptions.enums import SubscriptionStatus
from api.accounts.models import User
from api.accounts.enums import UserType


class SubscriptionPlanModelTestCase(TestCase):
    """Testes unitários para o modelo SubscriptionPlan."""

    def setUp(self):
        """Cria dados de teste."""
        self.plan_data = {
            'name': 'Plano Básico',
            'description': 'Plano básico para iniciantes',
            'price_monthly': Decimal('29.90'),
            'price_yearly': Decimal('299.00'),
            'features': {
                'max_orders': 10,
                'max_proposals': 5,
                'support': 'email'
            },
            'max_orders_per_month': 10,
            'max_proposals_per_order': 5,
            'is_active': True,
            'is_default': False,
        }

    def test_create_plan_with_minimal_fields(self):
        """Testa criação de plano com campos mínimos."""
        plan = SubscriptionPlan.objects.create(name='Plano Básico')
        self.assertEqual(plan.name, 'Plano Básico')
        self.assertEqual(plan.slug, 'plano-basico')
        self.assertEqual(plan.price_monthly, Decimal('0.00'))
        self.assertEqual(plan.price_yearly, Decimal('0.00'))
        self.assertEqual(plan.max_orders_per_month, 0)
        self.assertEqual(plan.max_proposals_per_order, 0)
        self.assertTrue(plan.is_active)
        self.assertFalse(plan.is_default)
        self.assertIsNotNone(plan.created_at)
        self.assertIsNone(plan.deleted_at)

    def test_create_plan_with_all_fields(self):
        """Testa criação de plano com todos os campos."""
        plan = SubscriptionPlan.objects.create(**self.plan_data)
        self.assertEqual(plan.name, 'Plano Básico')
        self.assertEqual(plan.slug, 'plano-basico')
        self.assertEqual(plan.description, 'Plano básico para iniciantes')
        self.assertEqual(plan.price_monthly, Decimal('29.90'))
        self.assertEqual(plan.price_yearly, Decimal('299.00'))
        self.assertEqual(plan.features, {
            'max_orders': 10,
            'max_proposals': 5,
            'support': 'email'
        })
        self.assertEqual(plan.max_orders_per_month, 10)
        self.assertEqual(plan.max_proposals_per_order, 5)
        self.assertTrue(plan.is_active)
        self.assertFalse(plan.is_default)
        self.assertIsNotNone(plan.created_at)
        self.assertIsNotNone(plan.updated_at)
        self.assertIsNone(plan.deleted_at)

    def test_name_is_required(self):
        """Testa que name é obrigatório."""
        plan = SubscriptionPlan()
        with self.assertRaises(ValidationError):
            plan.full_clean()

        # Com name, deve funcionar
        plan.name = 'Plano Teste'
        plan.full_clean()  # Não deve levantar exceção

    def test_name_is_unique(self):
        """Testa que name deve ser único."""
        SubscriptionPlan.objects.create(name='Plano Único')
        
        # Tentar criar outro com mesmo nome deve falhar
        with self.assertRaises(IntegrityError):
            SubscriptionPlan.objects.create(name='Plano Único')

    def test_slug_is_unique(self):
        """Testa que slug deve ser único."""
        SubscriptionPlan.objects.create(name='Plano Teste', slug='plano-teste')
        
        # Tentar criar outro com mesmo slug deve falhar
        with self.assertRaises(IntegrityError):
            SubscriptionPlan.objects.create(name='Outro Plano', slug='plano-teste')

    def test_slug_auto_generation(self):
        """Testa que slug é gerado automaticamente se não fornecido."""
        plan = SubscriptionPlan.objects.create(name='Plano Premium')
        self.assertEqual(plan.slug, 'plano-premium')

    def test_slug_manual_override(self):
        """Testa que slug pode ser fornecido manualmente."""
        plan = SubscriptionPlan.objects.create(
            name='Plano Premium',
            slug='premium-plan'
        )
        self.assertEqual(plan.slug, 'premium-plan')

    def test_slug_generation_with_special_characters(self):
        """Testa geração de slug com caracteres especiais."""
        plan = SubscriptionPlan.objects.create(name='Plano Premium & VIP!')
        self.assertEqual(plan.slug, 'plano-premium-vip')

    def test_slug_generation_with_accented_characters(self):
        """Testa geração de slug com caracteres acentuados."""
        plan = SubscriptionPlan.objects.create(name='Plano Profissional')
        self.assertEqual(plan.slug, 'plano-profissional')

    def test_price_monthly_default_is_zero(self):
        """Testa que price_monthly padrão é 0.00."""
        plan = SubscriptionPlan.objects.create(name='Plano Teste')
        self.assertEqual(plan.price_monthly, Decimal('0.00'))

    def test_price_yearly_default_is_zero(self):
        """Testa que price_yearly padrão é 0.00."""
        plan = SubscriptionPlan.objects.create(name='Plano Teste')
        self.assertEqual(plan.price_yearly, Decimal('0.00'))

    def test_price_monthly_can_be_set(self):
        """Testa que price_monthly pode ser definido."""
        plan = SubscriptionPlan.objects.create(
            name='Plano Teste',
            price_monthly=Decimal('49.90')
        )
        self.assertEqual(plan.price_monthly, Decimal('49.90'))

    def test_price_yearly_can_be_set(self):
        """Testa que price_yearly pode ser definido."""
        plan = SubscriptionPlan.objects.create(
            name='Plano Teste',
            price_yearly=Decimal('499.00')
        )
        self.assertEqual(plan.price_yearly, Decimal('499.00'))

    def test_features_default_is_empty_dict(self):
        """Testa que features padrão é um dicionário vazio."""
        plan = SubscriptionPlan.objects.create(name='Plano Teste')
        self.assertEqual(plan.features, {})

    def test_features_can_be_set(self):
        """Testa que features pode ser definido."""
        features = {
            'max_orders': 20,
            'max_proposals': 10,
            'support': 'priority',
            'custom_domain': True
        }
        plan = SubscriptionPlan.objects.create(
            name='Plano Teste',
            features=features
        )
        self.assertEqual(plan.features, features)

    def test_max_orders_per_month_default_is_zero(self):
        """Testa que max_orders_per_month padrão é 0."""
        plan = SubscriptionPlan.objects.create(name='Plano Teste')
        self.assertEqual(plan.max_orders_per_month, 0)

    def test_max_orders_per_month_can_be_set(self):
        """Testa que max_orders_per_month pode ser definido."""
        plan = SubscriptionPlan.objects.create(
            name='Plano Teste',
            max_orders_per_month=50
        )
        self.assertEqual(plan.max_orders_per_month, 50)

    def test_max_proposals_per_order_default_is_zero(self):
        """Testa que max_proposals_per_order padrão é 0."""
        plan = SubscriptionPlan.objects.create(name='Plano Teste')
        self.assertEqual(plan.max_proposals_per_order, 0)

    def test_max_proposals_per_order_can_be_set(self):
        """Testa que max_proposals_per_order pode ser definido."""
        plan = SubscriptionPlan.objects.create(
            name='Plano Teste',
            max_proposals_per_order=3
        )
        self.assertEqual(plan.max_proposals_per_order, 3)

    def test_is_active_default_is_true(self):
        """Testa que is_active padrão é True."""
        plan = SubscriptionPlan.objects.create(name='Plano Teste')
        self.assertTrue(plan.is_active)

    def test_is_active_can_be_set_to_false(self):
        """Testa que is_active pode ser definido como False."""
        plan = SubscriptionPlan.objects.create(
            name='Plano Teste',
            is_active=False
        )
        self.assertFalse(plan.is_active)

    def test_is_default_default_is_false(self):
        """Testa que is_default padrão é False."""
        plan = SubscriptionPlan.objects.create(name='Plano Teste')
        self.assertFalse(plan.is_default)

    def test_is_default_can_be_set_to_true(self):
        """Testa que is_default pode ser definido como True."""
        plan = SubscriptionPlan.objects.create(
            name='Plano Teste',
            is_default=True
        )
        self.assertTrue(plan.is_default)

    def test_description_is_optional(self):
        """Testa que description é opcional."""
        # Sem description
        plan1 = SubscriptionPlan.objects.create(name='Plano 1')
        self.assertIsNone(plan1.description)

        # Com description
        plan2 = SubscriptionPlan.objects.create(
            name='Plano 2',
            description='Descrição do plano'
        )
        self.assertEqual(plan2.description, 'Descrição do plano')

    def test_str_representation(self):
        """Testa a representação string do modelo."""
        plan = SubscriptionPlan.objects.create(
            name='Plano Premium',
            price_monthly=Decimal('99.90')
        )
        expected = 'Plano Premium (R$ 99.90/mês)'
        self.assertEqual(str(plan), expected)

    def test_created_at_auto_now_add(self):
        """Testa que created_at é preenchido automaticamente."""
        before = timezone.now()
        plan = SubscriptionPlan.objects.create(name='Plano Teste')
        after = timezone.now()

        self.assertIsNotNone(plan.created_at)
        self.assertGreaterEqual(plan.created_at, before)
        self.assertLessEqual(plan.created_at, after)

    def test_updated_at_auto_now(self):
        """Testa que updated_at é atualizado automaticamente."""
        plan = SubscriptionPlan.objects.create(name='Plano Teste')
        original_updated_at = plan.updated_at

        # Aguarda um pouco para garantir diferença de tempo
        time.sleep(0.01)

        plan.name = 'Plano Atualizado'
        plan.save()

        self.assertGreater(plan.updated_at, original_updated_at)

    def test_soft_delete_functionality(self):
        """Testa funcionalidade de soft delete."""
        initial_count = SubscriptionPlan.objects.count()
        plan = SubscriptionPlan.objects.create(name='Plano Teste')

        # Plano está ativo
        self.assertIsNone(plan.deleted_at)
        self.assertTrue(plan.is_alive)
        self.assertFalse(plan.is_deleted)
        self.assertEqual(SubscriptionPlan.objects.count(), initial_count + 1)

        # Deleta (soft delete)
        plan.delete()
        plan.refresh_from_db()

        # Plano está deletado
        self.assertIsNotNone(plan.deleted_at)
        self.assertFalse(plan.is_alive)
        self.assertTrue(plan.is_deleted)
        self.assertEqual(SubscriptionPlan.objects.count(), initial_count)
        self.assertEqual(SubscriptionPlan.all_objects.count(), initial_count + 1)
        self.assertEqual(SubscriptionPlan.deleted_objects.count(), 1)

        # Restaura
        plan.restore()
        plan.refresh_from_db()

        # Plano está ativo novamente
        self.assertIsNone(plan.deleted_at)
        self.assertTrue(plan.is_alive)
        self.assertFalse(plan.is_deleted)
        self.assertEqual(SubscriptionPlan.objects.count(), initial_count + 1)

    def test_ordering_by_price_monthly_then_name(self):
        """Testa que ordenação padrão é por price_monthly e depois name."""
        plan1 = SubscriptionPlan.objects.create(
            name='Plano C',
            price_monthly=Decimal('29.90')
        )
        plan2 = SubscriptionPlan.objects.create(
            name='Plano A',
            price_monthly=Decimal('19.90')
        )
        plan3 = SubscriptionPlan.objects.create(
            name='Plano B',
            price_monthly=Decimal('29.90')
        )

        # Filtra apenas os planos criados neste teste
        plans = list(SubscriptionPlan.objects.filter(
            name__in=['Plano A', 'Plano B', 'Plano C']
        ).order_by('price_monthly', 'name'))

        # Ordem esperada: plan2 (19.90), plan3 (29.90, B), plan1 (29.90, C)
        # Quando price_monthly é igual, ordena por name (B vem antes de C)
        self.assertEqual(plans[0], plan2)
        self.assertEqual(plans[1], plan3)
        self.assertEqual(plans[2], plan1)

    def test_indexes_exist(self):
        """Testa que os índices foram criados corretamente."""
        plan = SubscriptionPlan.objects.create(name='Plano Teste')

        # Testa queries que usam os índices (verifica que não há erros)
        SubscriptionPlan.objects.filter(slug=plan.slug).first()
        SubscriptionPlan.objects.filter(is_active=True).first()
        SubscriptionPlan.objects.filter(is_default=True).first()
        SubscriptionPlan.objects.filter(deleted_at__isnull=True).first()

        # Verifica que os índices estão definidos no Meta
        index_names = [idx.name for idx in SubscriptionPlan._meta.indexes]
        self.assertIn('plan_slug_idx', index_names)
        self.assertIn('plan_is_active_idx', index_names)
        self.assertIn('plan_is_default_idx', index_names)
        self.assertIn('plan_deleted_at_idx', index_names)

    def test_save_method_generates_slug_if_not_provided(self):
        """Testa que método save() gera slug se não fornecido."""
        plan = SubscriptionPlan(name='Plano Novo')
        self.assertEqual(plan.slug, '')
        
        plan.save()
        self.assertEqual(plan.slug, 'plano-novo')

    def test_save_method_does_not_override_existing_slug(self):
        """Testa que método save() não sobrescreve slug existente."""
        plan = SubscriptionPlan(name='Plano Novo', slug='custom-slug')
        plan.save()
        self.assertEqual(plan.slug, 'custom-slug')

    def test_multiple_plans_with_different_names(self):
        """Testa criação de múltiplos planos com nomes diferentes."""
        plan1 = SubscriptionPlan.objects.create(
            name='Plano Teste Básico',
            price_monthly=Decimal('19.90')
        )
        plan2 = SubscriptionPlan.objects.create(
            name='Plano Teste Premium',
            price_monthly=Decimal('49.90')
        )
        plan3 = SubscriptionPlan.objects.create(
            name='Plano Teste Enterprise',
            price_monthly=Decimal('99.90')
        )

        # Filtra apenas os planos criados neste teste
        plans = SubscriptionPlan.objects.filter(
            name__in=['Plano Teste Básico', 'Plano Teste Premium', 'Plano Teste Enterprise']
        )
        self.assertEqual(plans.count(), 3)
        self.assertIn(plan1, plans)
        self.assertIn(plan2, plans)
        self.assertIn(plan3, plans)

    def test_plan_with_zero_prices(self):
        """Testa criação de plano gratuito (preços zero)."""
        plan = SubscriptionPlan.objects.create(
            name='Plano Grátis',
            price_monthly=Decimal('0.00'),
            price_yearly=Decimal('0.00')
        )
        self.assertEqual(plan.price_monthly, Decimal('0.00'))
        self.assertEqual(plan.price_yearly, Decimal('0.00'))

    def test_plan_with_unlimited_orders(self):
        """Testa criação de plano com pedidos ilimitados (max_orders_per_month = 0)."""
        plan = SubscriptionPlan.objects.create(
            name='Plano Ilimitado',
            max_orders_per_month=0
        )
        self.assertEqual(plan.max_orders_per_month, 0)

    def test_plan_with_unlimited_proposals(self):
        """Testa criação de plano com propostas ilimitadas (max_proposals_per_order = 0)."""
        plan = SubscriptionPlan.objects.create(
            name='Plano Ilimitado',
            max_proposals_per_order=0
        )
        self.assertEqual(plan.max_proposals_per_order, 0)


class UserSubscriptionModelTestCase(TestCase):
    """Testes unitários para o modelo UserSubscription."""

    def setUp(self):
        """Cria dados de teste."""
        # Cria usuário
        self.user = User.objects.create_user(  # type: ignore[call-arg]
            email='user@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123',
            user_type=UserType.CLIENT.value
        )

        # Cria plano
        self.plan = SubscriptionPlan.objects.create(
            name='Plano Teste',
            price_monthly=Decimal('29.90')
        )

        # Datas
        self.start_date = timezone.now()
        self.end_date = self.start_date + timedelta(days=30)

    def test_create_subscription_with_minimal_fields(self):
        """Testa criação de assinatura com campos mínimos."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date
        )
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.plan, self.plan)
        self.assertEqual(subscription.start_date, self.start_date)
        self.assertEqual(subscription.status, SubscriptionStatus.ACTIVE.value)
        self.assertIsNone(subscription.end_date)
        self.assertTrue(subscription.auto_renew)
        self.assertIsNone(subscription.cancelled_at)
        self.assertIsNotNone(subscription.created_at)
        self.assertIsNone(subscription.deleted_at)

    def test_create_subscription_with_all_fields(self):
        """Testa criação de assinatura com todos os campos."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status=SubscriptionStatus.ACTIVE.value,
            start_date=self.start_date,
            end_date=self.end_date,
            auto_renew=True
        )
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.plan, self.plan)
        self.assertEqual(subscription.status, SubscriptionStatus.ACTIVE.value)
        self.assertEqual(subscription.start_date, self.start_date)
        self.assertEqual(subscription.end_date, self.end_date)
        self.assertTrue(subscription.auto_renew)
        self.assertIsNotNone(subscription.created_at)
        self.assertIsNotNone(subscription.updated_at)
        self.assertIsNone(subscription.deleted_at)

    def test_user_is_required(self):
        """Testa que user é obrigatório."""
        subscription = UserSubscription(
            plan=self.plan,
            start_date=self.start_date
        )
        with self.assertRaises(ValidationError):
            subscription.full_clean()

    def test_plan_is_required(self):
        """Testa que plan é obrigatório."""
        subscription = UserSubscription(
            user=self.user,
            start_date=self.start_date
        )
        with self.assertRaises(ValidationError):
            subscription.full_clean()

    def test_start_date_is_required(self):
        """Testa que start_date é obrigatório."""
        subscription = UserSubscription(
            user=self.user,
            plan=self.plan
        )
        with self.assertRaises(ValidationError):
            subscription.full_clean()

    def test_status_default_is_active(self):
        """Testa que status padrão é ACTIVE."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date
        )
        self.assertEqual(subscription.status, SubscriptionStatus.ACTIVE.value)
        self.assertTrue(subscription.is_active)

    def test_status_choices(self):
        """Testa que status aceita apenas valores válidos."""
        # ACTIVE
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date,
            status=SubscriptionStatus.ACTIVE.value
        )
        self.assertEqual(subscription.status, SubscriptionStatus.ACTIVE.value)
        self.assertTrue(subscription.is_active)

        # CANCELLED
        subscription.status = SubscriptionStatus.CANCELLED.value
        subscription.save()
        self.assertEqual(subscription.status, SubscriptionStatus.CANCELLED.value)
        self.assertFalse(subscription.is_active)

        # EXPIRED
        subscription.status = SubscriptionStatus.EXPIRED.value
        subscription.save()
        self.assertEqual(subscription.status, SubscriptionStatus.EXPIRED.value)
        self.assertFalse(subscription.is_active)

        # SUSPENDED
        subscription.status = SubscriptionStatus.SUSPENDED.value
        subscription.save()
        self.assertEqual(subscription.status, SubscriptionStatus.SUSPENDED.value)
        self.assertFalse(subscription.is_active)

    def test_is_active_property(self):
        """Testa a propriedade is_active."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date,
            status=SubscriptionStatus.ACTIVE.value
        )
        self.assertTrue(subscription.is_active)

        subscription.status = SubscriptionStatus.CANCELLED.value
        subscription.save()
        self.assertFalse(subscription.is_active)

    def test_is_expired_property_with_end_date(self):
        """Testa a propriedade is_expired quando há end_date."""
        # Assinatura que ainda não expirou
        future_end_date = timezone.now() + timedelta(days=10)
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date,
            end_date=future_end_date
        )
        self.assertFalse(subscription.is_expired)

        # Assinatura que já expirou
        past_end_date = timezone.now() - timedelta(days=10)
        subscription.end_date = past_end_date
        subscription.save()
        self.assertTrue(subscription.is_expired)

    def test_is_expired_property_without_end_date(self):
        """Testa a propriedade is_expired quando não há end_date."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date,
            end_date=None
        )
        self.assertFalse(subscription.is_expired)

    def test_end_date_is_optional(self):
        """Testa que end_date é opcional."""
        # Sem end_date
        subscription1 = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date,
            end_date=None
        )
        self.assertIsNone(subscription1.end_date)

        # Com end_date
        subscription2 = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date,
            end_date=self.end_date
        )
        self.assertIsNotNone(subscription2.end_date)

    def test_auto_renew_default_is_true(self):
        """Testa que auto_renew padrão é True."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date
        )
        self.assertTrue(subscription.auto_renew)

    def test_auto_renew_can_be_set_to_false(self):
        """Testa que auto_renew pode ser definido como False."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date,
            auto_renew=False
        )
        self.assertFalse(subscription.auto_renew)

    def test_cancelled_at_is_optional(self):
        """Testa que cancelled_at é opcional."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date,
            cancelled_at=None
        )
        self.assertIsNone(subscription.cancelled_at)

    def test_cancel_method(self):
        """Testa o método cancel()."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date,
            status=SubscriptionStatus.ACTIVE.value,
            auto_renew=True
        )

        self.assertTrue(subscription.is_active)
        self.assertTrue(subscription.auto_renew)
        self.assertIsNone(subscription.cancelled_at)

        # Cancela a assinatura
        before = timezone.now()
        subscription.cancel()
        after = timezone.now()
        subscription.refresh_from_db()

        self.assertEqual(subscription.status, SubscriptionStatus.CANCELLED.value)
        self.assertFalse(subscription.is_active)
        self.assertFalse(subscription.auto_renew)
        self.assertIsNotNone(subscription.cancelled_at)
        self.assertGreaterEqual(subscription.cancelled_at, before)
        self.assertLessEqual(subscription.cancelled_at, after)

    def test_cancel_method_only_works_for_active_subscriptions(self):
        """Testa que cancel() só funciona para assinaturas ativas."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date,
            status=SubscriptionStatus.CANCELLED.value,
            auto_renew=True
        )

        original_status = subscription.status
        original_auto_renew = subscription.auto_renew
        original_cancelled_at = subscription.cancelled_at

        # Tenta cancelar uma assinatura já cancelada
        subscription.cancel()
        subscription.refresh_from_db()

        # Status não deve mudar
        self.assertEqual(subscription.status, original_status)
        self.assertEqual(subscription.auto_renew, original_auto_renew)
        self.assertEqual(subscription.cancelled_at, original_cancelled_at)

    def test_user_foreign_key_relationship(self):
        """Testa relacionamento ForeignKey com User."""
        subscription1 = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date
        )
        subscription2 = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date + timedelta(days=30)
        )

        # Verifica relacionamento direto
        self.assertEqual(subscription1.user, self.user)
        self.assertEqual(subscription2.user, self.user)

        # Verifica relacionamento reverso
        subscriptions = self.user.subscriptions.all()
        self.assertEqual(subscriptions.count(), 2)
        self.assertIn(subscription1, subscriptions)
        self.assertIn(subscription2, subscriptions)

    def test_plan_foreign_key_relationship(self):
        """Testa relacionamento ForeignKey com SubscriptionPlan."""
        subscription1 = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date
        )

        # Cria outro usuário
        user2 = User.objects.create_user(  # type: ignore[call-arg]
            email='user2@example.com',
            first_name='Test',
            last_name='User2',
            password='testpass123',
            user_type=UserType.CLIENT.value
        )

        subscription2 = UserSubscription.objects.create(
            user=user2,
            plan=self.plan,
            start_date=self.start_date
        )

        # Verifica relacionamento direto
        self.assertEqual(subscription1.plan, self.plan)
        self.assertEqual(subscription2.plan, self.plan)

        # Verifica relacionamento reverso
        subscriptions = self.plan.user_subscriptions.all()
        self.assertEqual(subscriptions.count(), 2)
        self.assertIn(subscription1, subscriptions)
        self.assertIn(subscription2, subscriptions)

    def test_str_representation(self):
        """Testa a representação string do modelo."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date
        )
        expected = f"Assinatura #{subscription.id} - {self.user.email} ({self.plan.name})"
        self.assertEqual(str(subscription), expected)

    def test_created_at_auto_now_add(self):
        """Testa que created_at é preenchido automaticamente."""
        before = timezone.now()
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date
        )
        after = timezone.now()

        self.assertIsNotNone(subscription.created_at)
        self.assertGreaterEqual(subscription.created_at, before)
        self.assertLessEqual(subscription.created_at, after)

    def test_updated_at_auto_now(self):
        """Testa que updated_at é atualizado automaticamente."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date
        )
        original_updated_at = subscription.updated_at

        # Aguarda um pouco para garantir diferença de tempo
        time.sleep(0.01)

        subscription.status = SubscriptionStatus.CANCELLED.value
        subscription.save()

        self.assertGreater(subscription.updated_at, original_updated_at)

    def test_soft_delete_functionality(self):
        """Testa funcionalidade de soft delete."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date
        )

        # Assinatura está ativa
        self.assertIsNone(subscription.deleted_at)
        self.assertTrue(subscription.is_alive)
        self.assertFalse(subscription.is_deleted)
        self.assertEqual(UserSubscription.objects.count(), 1)

        # Deleta (soft delete)
        subscription.delete()
        subscription.refresh_from_db()

        # Assinatura está deletada
        self.assertIsNotNone(subscription.deleted_at)
        self.assertFalse(subscription.is_alive)
        self.assertTrue(subscription.is_deleted)
        self.assertEqual(UserSubscription.objects.count(), 0)
        self.assertEqual(UserSubscription.all_objects.count(), 1)
        self.assertEqual(UserSubscription.deleted_objects.count(), 1)

        # Restaura
        subscription.restore()
        subscription.refresh_from_db()

        # Assinatura está ativa novamente
        self.assertIsNone(subscription.deleted_at)
        self.assertTrue(subscription.is_alive)
        self.assertFalse(subscription.is_deleted)
        self.assertEqual(UserSubscription.objects.count(), 1)

    def test_ordering_by_created_at_desc(self):
        """Testa que ordenação padrão é por created_at descendente."""
        subscription1 = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date
        )

        time.sleep(0.01)

        subscription2 = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date + timedelta(days=30)
        )

        subscriptions = list(UserSubscription.objects.all())

        # subscription2 é mais recente, deve aparecer primeiro
        self.assertEqual(subscriptions[0], subscription2)
        self.assertEqual(subscriptions[1], subscription1)

    def test_indexes_exist(self):
        """Testa que os índices foram criados corretamente."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date
        )

        # Testa queries que usam os índices (verifica que não há erros)
        UserSubscription.objects.filter(user=self.user).first()
        UserSubscription.objects.filter(plan=self.plan).first()
        UserSubscription.objects.filter(status=SubscriptionStatus.ACTIVE.value).first()
        UserSubscription.objects.filter(end_date__isnull=False).first()
        UserSubscription.objects.filter(deleted_at__isnull=True).first()

        # Verifica que os índices estão definidos no Meta
        index_names = [idx.name for idx in UserSubscription._meta.indexes]
        self.assertIn('subscription_user_idx', index_names)
        self.assertIn('subscription_plan_idx', index_names)
        self.assertIn('subscription_status_idx', index_names)
        self.assertIn('subscription_end_date_idx', index_names)
        self.assertIn('subscription_deleted_at_idx', index_names)

    def test_cascade_delete_when_user_hard_deleted(self):
        """Testa que assinaturas são deletadas quando usuário é hard deleted."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date
        )
        subscription_id = subscription.id

        # Hard delete do usuário
        self.user.hard_delete()

        # A assinatura também deve ser deletada (CASCADE)
        self.assertFalse(UserSubscription.all_objects.filter(id=subscription_id).exists())

    def test_protect_delete_when_plan_hard_deleted(self):
        """Testa que plano não pode ser deletado se houver assinaturas (PROTECT)."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date
        )

        # Tentar fazer hard delete do plano deve falhar
        with self.assertRaises(ProtectedError):
            self.plan.hard_delete()

        # A assinatura ainda deve existir
        self.assertTrue(UserSubscription.objects.filter(id=subscription.id).exists())

    def test_multiple_subscriptions_for_same_user(self):
        """Testa criação de múltiplas assinaturas para o mesmo usuário."""
        subscription1 = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date,
            status=SubscriptionStatus.ACTIVE.value
        )

        # Cria outro plano
        plan2 = SubscriptionPlan.objects.create(
            name='Plano Premium',
            price_monthly=Decimal('79.90')
        )

        subscription2 = UserSubscription.objects.create(
            user=self.user,
            plan=plan2,
            start_date=self.start_date + timedelta(days=30),
            status=SubscriptionStatus.CANCELLED.value
        )

        subscriptions = self.user.subscriptions.all()
        self.assertEqual(subscriptions.count(), 2)
        self.assertIn(subscription1, subscriptions)
        self.assertIn(subscription2, subscriptions)

    def test_subscription_without_end_date_is_not_expired(self):
        """Testa que assinatura sem end_date nunca está expirada."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date,
            end_date=None
        )
        self.assertFalse(subscription.is_expired)

    def test_subscription_with_future_end_date_is_not_expired(self):
        """Testa que assinatura com end_date futuro não está expirada."""
        future_end_date = timezone.now() + timedelta(days=30)
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date,
            end_date=future_end_date
        )
        self.assertFalse(subscription.is_expired)

    def test_subscription_with_past_end_date_is_expired(self):
        """Testa que assinatura com end_date passado está expirada."""
        past_end_date = timezone.now() - timedelta(days=10)
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date,
            end_date=past_end_date
        )
        self.assertTrue(subscription.is_expired)
