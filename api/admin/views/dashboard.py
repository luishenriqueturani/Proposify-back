"""
ViewSet para o dashboard administrativo.

Fornece estatísticas gerais do sistema para o painel administrativo.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from api.admin.serializers import (
    DashboardStatsSerializer,
    UserStatsSerializer,
    OrderStatsSerializer,
    ProposalStatsSerializer,
    PaymentStatsSerializer,
    SubscriptionStatsSerializer,
    ReviewStatsSerializer,
)
from api.admin.permissions import IsAdmin
from api.accounts.models import User, ProviderProfile
from api.accounts.enums import UserType
from api.orders.models import Order, Proposal
from api.orders.enums import OrderStatus, ProposalStatus
from api.payments.models import Payment
from api.subscriptions.models import UserSubscription
from api.subscriptions.enums import SubscriptionStatus, PaymentStatus
from api.reviews.models import Review


@extend_schema_view(
    stats=extend_schema(
        tags=['Admin - Dashboard'],
        summary='Estatísticas do Dashboard',
        description='''
Retorna estatísticas gerais do sistema para o painel administrativo.

**Requer permissão de administrador.**

Inclui métricas de:
- Usuários (total, por tipo, novos)
- Pedidos (total, por status)
- Propostas (total, por status)
- Pagamentos (total, receita)
- Assinaturas (total, por plano)
- Avaliações (total, média)
        ''',
        responses={
            200: DashboardStatsSerializer,
            401: OpenApiResponse(description='Não autenticado'),
            403: OpenApiResponse(description='Sem permissão de administrador'),
        },
    ),
)
class AdminDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet para o dashboard administrativo.
    
    Fornece estatísticas gerais do sistema para o painel administrativo.
    
    **Permissão necessária:** IsAdmin (user_type=ADMIN ou is_staff=True)
    """
    permission_classes = [IsAdmin]

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        Retorna estatísticas gerais do sistema.
        
        GET /admin/dashboard/stats/
        """
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = today_start.replace(day=1)

        # Estatísticas de usuários
        users_qs = User.objects.all()
        user_stats = UserStatsSerializer({
            'total_users': users_qs.count(),
            'total_clients': users_qs.filter(user_type=UserType.CLIENT.value).count(),
            'total_providers': users_qs.filter(user_type=UserType.PROVIDER.value).count(),
            'total_admins': users_qs.filter(user_type=UserType.ADMIN.value).count(),
            'active_users': users_qs.filter(deleted_at__isnull=True).count(),
            'new_users_today': users_qs.filter(created_at__gte=today_start).count(),
            'new_users_this_week': users_qs.filter(created_at__gte=week_start).count(),
            'new_users_this_month': users_qs.filter(created_at__gte=month_start).count(),
            'verified_providers': ProviderProfile.objects.filter(
                is_verified=True,
                deleted_at__isnull=True
            ).count(),
            'providers_with_profile': ProviderProfile.objects.filter(
                deleted_at__isnull=True
            ).count(),
        })

        # Estatísticas de pedidos
        orders_qs = Order.objects.all()
        orders_stats = orders_qs.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status=OrderStatus.PENDING.value)),
            accepted=Count('id', filter=Q(status=OrderStatus.ACCEPTED.value)),
            in_progress=Count('id', filter=Q(status=OrderStatus.IN_PROGRESS.value)),
            completed=Count('id', filter=Q(status=OrderStatus.COMPLETED.value)),
            cancelled=Count('id', filter=Q(status=OrderStatus.CANCELLED.value)),
            avg_budget_min=Avg('budget_min'),
            avg_budget_max=Avg('budget_max'),
        )
        order_stats = OrderStatsSerializer({
            'total_orders': orders_stats['total'],
            'pending_orders': orders_stats['pending'],
            'accepted_orders': orders_stats['accepted'],
            'in_progress_orders': orders_stats['in_progress'],
            'completed_orders': orders_stats['completed'],
            'cancelled_orders': orders_stats['cancelled'],
            'new_orders_today': orders_qs.filter(created_at__gte=today_start).count(),
            'new_orders_this_week': orders_qs.filter(created_at__gte=week_start).count(),
            'new_orders_this_month': orders_qs.filter(created_at__gte=month_start).count(),
            'avg_budget_min': orders_stats['avg_budget_min'],
            'avg_budget_max': orders_stats['avg_budget_max'],
        })

        # Estatísticas de propostas
        proposals_qs = Proposal.objects.all()
        proposals_stats = proposals_qs.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status=ProposalStatus.PENDING.value)),
            accepted=Count('id', filter=Q(status=ProposalStatus.ACCEPTED.value)),
            declined=Count('id', filter=Q(status=ProposalStatus.DECLINED.value)),
            expired=Count('id', filter=Q(status=ProposalStatus.EXPIRED.value)),
            avg_price=Avg('price'),
            avg_estimated_days=Avg('estimated_days'),
        )
        proposal_stats = ProposalStatsSerializer({
            'total_proposals': proposals_stats['total'],
            'pending_proposals': proposals_stats['pending'],
            'accepted_proposals': proposals_stats['accepted'],
            'declined_proposals': proposals_stats['declined'],
            'expired_proposals': proposals_stats['expired'],
            'new_proposals_today': proposals_qs.filter(created_at__gte=today_start).count(),
            'new_proposals_this_week': proposals_qs.filter(created_at__gte=week_start).count(),
            'new_proposals_this_month': proposals_qs.filter(created_at__gte=month_start).count(),
            'avg_price': proposals_stats['avg_price'],
            'avg_estimated_days': proposals_stats['avg_estimated_days'],
        })

        # Estatísticas de pagamentos
        payments_qs = Payment.objects.all()
        payments_stats = payments_qs.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(payment_status=PaymentStatus.PENDING.value)),
            paid=Count('id', filter=Q(payment_status=PaymentStatus.PAID.value)),
            failed=Count('id', filter=Q(payment_status=PaymentStatus.FAILED.value)),
            refunded=Count('id', filter=Q(payment_status=PaymentStatus.REFUNDED.value)),
            total_revenue=Sum('amount', filter=Q(payment_status=PaymentStatus.PAID.value)),
            revenue_today=Sum('amount', filter=Q(
                payment_status=PaymentStatus.PAID.value,
                payment_date__gte=today_start
            )),
            revenue_this_week=Sum('amount', filter=Q(
                payment_status=PaymentStatus.PAID.value,
                payment_date__gte=week_start
            )),
            revenue_this_month=Sum('amount', filter=Q(
                payment_status=PaymentStatus.PAID.value,
                payment_date__gte=month_start
            )),
            avg_amount=Avg('amount', filter=Q(payment_status=PaymentStatus.PAID.value)),
        )
        payment_stats = PaymentStatsSerializer({
            'total_payments': payments_stats['total'],
            'pending_payments': payments_stats['pending'],
            'paid_payments': payments_stats['paid'],
            'failed_payments': payments_stats['failed'],
            'refunded_payments': payments_stats['refunded'],
            'total_revenue': payments_stats['total_revenue'] or Decimal('0.00'),
            'revenue_today': payments_stats['revenue_today'] or Decimal('0.00'),
            'revenue_this_week': payments_stats['revenue_this_week'] or Decimal('0.00'),
            'revenue_this_month': payments_stats['revenue_this_month'] or Decimal('0.00'),
            'avg_payment_amount': payments_stats['avg_amount'],
        })

        # Estatísticas de assinaturas
        subscriptions_qs = UserSubscription.objects.all()
        subscriptions_stats = subscriptions_qs.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status=SubscriptionStatus.ACTIVE.value)),
            cancelled=Count('id', filter=Q(status=SubscriptionStatus.CANCELLED.value)),
            expired=Count('id', filter=Q(status=SubscriptionStatus.EXPIRED.value)),
            suspended=Count('id', filter=Q(status=SubscriptionStatus.SUSPENDED.value)),
        )
        subscription_payments = Payment.objects.filter(
            payment_status=PaymentStatus.PAID.value
        ).aggregate(
            total_revenue=Sum('amount'),
            revenue_this_month=Sum('amount', filter=Q(payment_date__gte=month_start)),
        )
        subscriptions_by_plan = {
            item['plan__name']: item['count']
            for item in subscriptions_qs.values('plan__name')
            .annotate(count=Count('id'))
        }
        subscription_stats = SubscriptionStatsSerializer({
            'total_subscriptions': subscriptions_stats['total'],
            'active_subscriptions': subscriptions_stats['active'],
            'cancelled_subscriptions': subscriptions_stats['cancelled'],
            'expired_subscriptions': subscriptions_stats['expired'],
            'suspended_subscriptions': subscriptions_stats['suspended'],
            'total_subscription_revenue': subscription_payments['total_revenue'] or Decimal('0.00'),
            'subscription_revenue_this_month': subscription_payments['revenue_this_month'] or Decimal('0.00'),
            'subscriptions_by_plan': subscriptions_by_plan,
        })

        # Estatísticas de avaliações
        reviews_qs = Review.objects.all()
        reviews_stats = reviews_qs.aggregate(
            total=Count('id'),
            avg_rating=Avg('rating'),
        )
        reviews_by_rating = {
            str(item['rating']): item['count']
            for item in reviews_qs.values('rating')
            .annotate(count=Count('id'))
        }
        review_stats = ReviewStatsSerializer({
            'total_reviews': reviews_stats['total'],
            'avg_rating': reviews_stats['avg_rating'],
            'reviews_by_rating': reviews_by_rating,
            'new_reviews_today': reviews_qs.filter(created_at__gte=today_start).count(),
            'new_reviews_this_week': reviews_qs.filter(created_at__gte=week_start).count(),
            'new_reviews_this_month': reviews_qs.filter(created_at__gte=month_start).count(),
        })

        # Serializer principal
        dashboard_data = DashboardStatsSerializer({
            'users': user_stats.data,
            'orders': order_stats.data,
            'proposals': proposal_stats.data,
            'payments': payment_stats.data,
            'subscriptions': subscription_stats.data,
            'reviews': review_stats.data,
            'generated_at': now,
        })

        return Response(dashboard_data.data, status=status.HTTP_200_OK)
