"""
ViewSets para o app admin (dashboard, gerenciamento administrativo).
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

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
from api.accounts.models import User, ProviderProfile, ClientProfile
from api.accounts.enums import UserType
from api.orders.models import Order, Proposal
from api.orders.enums import OrderStatus, ProposalStatus
from api.payments.models import Payment
from api.subscriptions.models import UserSubscription, SubscriptionPlan
from api.subscriptions.enums import SubscriptionStatus, PaymentStatus
from api.reviews.models import Review


class AdminDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet para o dashboard administrativo.
    
    Fornece estatísticas gerais do sistema para o painel administrativo.
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
        # Receita de assinaturas (soma dos pagamentos de assinatura)
        subscription_payments = Payment.objects.filter(
            payment_status=PaymentStatus.PAID.value
        ).aggregate(
            total_revenue=Sum('amount'),
            revenue_this_month=Sum('amount', filter=Q(payment_date__gte=month_start)),
        )
        # Contagem por plano
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
        # Contagem por rating
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


class AdminUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de usuários pelo administrador.
    
    Permite listar, visualizar, atualizar, suspender e ativar usuários.
    """
    queryset = User.objects.all()
    permission_classes = [IsAdmin]
    serializer_class = None  # Será definido quando criarmos o serializer
    lookup_field = 'pk'

    def get_serializer_class(self):
        """Retorna o serializer apropriado baseado na ação."""
        # Por enquanto, usa um serializer básico do DRF
        # TODO: Criar UserSerializer quando necessário
        from rest_framework.serializers import ModelSerializer
        from api.accounts.models import User
        
        class UserSerializer(ModelSerializer):
            class Meta:
                model = User
                fields = [
                    'id', 'email', 'first_name', 'last_name', 'phone',
                    'user_type', 'is_active', 'is_staff', 'is_superuser',
                    'date_joined', 'last_login', 'created_at', 'updated_at'
                ]
                read_only_fields = ['id', 'date_joined', 'last_login', 'created_at', 'updated_at']
        
        return UserSerializer

    def list(self, request, *args, **kwargs):
        """
        Lista todos os usuários.
        
        GET /admin/users/
        """
        queryset = self.get_queryset()
        # Aplicar filtros se necessário
        user_type = request.query_params.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Paginação será aplicada automaticamente pelo DRF
        page = self.paginate_queryset(queryset)
        if page is not None:
            # TODO: Usar serializer apropriado
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Retorna detalhes de um usuário específico.
        
        GET /admin/users/{id}/
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        Atualiza um usuário.
        
        PATCH /admin/users/{id}/
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='suspend')
    def suspend(self, request, pk=None):
        """
        Suspende um usuário (desativa).
        
        POST /admin/users/{id}/suspend/
        """
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response({
            'message': f'Usuário {user.email} foi suspenso com sucesso.',
            'user_id': user.id,
            'is_active': user.is_active,
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        """
        Ativa um usuário.
        
        POST /admin/users/{id}/activate/
        """
        user = self.get_object()
        user.is_active = True
        user.save(update_fields=['is_active'])
        return Response({
            'message': f'Usuário {user.email} foi ativado com sucesso.',
            'user_id': user.id,
            'is_active': user.is_active,
        }, status=status.HTTP_200_OK)


class AdminOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualização de pedidos pelo administrador.
    
    Permite listar e visualizar pedidos (somente leitura).
    """
    queryset = Order.objects.select_related('client', 'client__user', 'service', 'service__category')
    permission_classes = [IsAdmin]
    serializer_class = None  # Será definido quando criarmos o serializer

    def get_serializer_class(self):
        """Retorna o serializer apropriado."""
        from rest_framework.serializers import ModelSerializer
        from api.orders.models import Order
        
        class OrderSerializer(ModelSerializer):
            class Meta:
                model = Order
                fields = [
                    'id', 'client', 'service', 'title', 'description',
                    'budget_min', 'budget_max', 'deadline', 'status',
                    'created_at', 'updated_at'
                ]
                read_only_fields = ['id', 'created_at', 'updated_at']
        
        return OrderSerializer

    def list(self, request, *args, **kwargs):
        """
        Lista todos os pedidos.
        
        GET /admin/orders/
        """
        queryset = self.get_queryset()
        
        # Filtros
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Retorna detalhes de um pedido específico.
        
        GET /admin/orders/{id}/
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class AdminProposalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualização de propostas pelo administrador.
    
    Permite listar e visualizar propostas (somente leitura).
    """
    queryset = Proposal.objects.select_related('order', 'provider', 'provider__user')
    permission_classes = [IsAdmin]
    serializer_class = None  # Será definido quando criarmos o serializer

    def get_serializer_class(self):
        """Retorna o serializer apropriado."""
        from rest_framework.serializers import ModelSerializer
        from api.orders.models import Proposal
        
        class ProposalSerializer(ModelSerializer):
            class Meta:
                model = Proposal
                fields = [
                    'id', 'order', 'provider', 'message', 'price',
                    'estimated_days', 'status', 'created_at', 'updated_at',
                    'expires_at'
                ]
                read_only_fields = ['id', 'created_at', 'updated_at']
        
        return ProposalSerializer

    def list(self, request, *args, **kwargs):
        """
        Lista todas as propostas.
        
        GET /admin/proposals/
        """
        queryset = self.get_queryset()
        
        # Filtros
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Retorna detalhes de uma proposta específica.
        
        GET /admin/proposals/{id}/
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class AdminPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualização de pagamentos pelo administrador.
    
    Permite listar e visualizar pagamentos (somente leitura).
    """
    queryset = Payment.objects.select_related('order', 'proposal')
    permission_classes = [IsAdmin]
    serializer_class = None  # Será definido quando criarmos o serializer

    def get_serializer_class(self):
        """Retorna o serializer apropriado."""
        from rest_framework.serializers import ModelSerializer
        from api.payments.models import Payment
        
        class PaymentSerializer(ModelSerializer):
            class Meta:
                model = Payment
                fields = [
                    'id', 'order', 'proposal', 'amount', 'payment_method',
                    'payment_status', 'transaction_id', 'payment_date',
                    'metadata', 'created_at', 'updated_at'
                ]
                read_only_fields = ['id', 'created_at', 'updated_at']
        
        return PaymentSerializer

    def list(self, request, *args, **kwargs):
        """
        Lista todos os pagamentos.
        
        GET /admin/payments/
        """
        queryset = self.get_queryset()
        
        # Filtros
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(payment_status=status_filter)
        
        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Retorna detalhes de um pagamento específico.
        
        GET /admin/payments/{id}/
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
