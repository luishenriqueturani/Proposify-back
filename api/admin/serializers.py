"""
Serializers para o app admin (dashboard, estatísticas e relatórios).
"""
from rest_framework import serializers


class UserStatsSerializer(serializers.Serializer):
    """
    Serializer para estatísticas de usuários.
    Retorna contagens de usuários por tipo e métricas relacionadas.
    """
    total_users = serializers.IntegerField(help_text='Total de usuários no sistema')
    total_clients = serializers.IntegerField(help_text='Total de clientes')
    total_providers = serializers.IntegerField(help_text='Total de prestadores')
    total_admins = serializers.IntegerField(help_text='Total de administradores')
    active_users = serializers.IntegerField(help_text='Usuários ativos (não deletados)')
    new_users_today = serializers.IntegerField(help_text='Novos usuários hoje')
    new_users_this_week = serializers.IntegerField(help_text='Novos usuários esta semana')
    new_users_this_month = serializers.IntegerField(help_text='Novos usuários este mês')
    verified_providers = serializers.IntegerField(help_text='Prestadores verificados')
    providers_with_profile = serializers.IntegerField(help_text='Prestadores com perfil completo')


class OrderStatsSerializer(serializers.Serializer):
    """
    Serializer para estatísticas de pedidos.
    Retorna contagens de pedidos por status e métricas relacionadas.
    """
    total_orders = serializers.IntegerField(help_text='Total de pedidos')
    pending_orders = serializers.IntegerField(help_text='Pedidos pendentes')
    accepted_orders = serializers.IntegerField(help_text='Pedidos aceitos')
    in_progress_orders = serializers.IntegerField(help_text='Pedidos em progresso')
    completed_orders = serializers.IntegerField(help_text='Pedidos completados')
    cancelled_orders = serializers.IntegerField(help_text='Pedidos cancelados')
    new_orders_today = serializers.IntegerField(help_text='Novos pedidos hoje')
    new_orders_this_week = serializers.IntegerField(help_text='Novos pedidos esta semana')
    new_orders_this_month = serializers.IntegerField(help_text='Novos pedidos este mês')
    avg_budget_min = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        allow_null=True,
        help_text='Orçamento mínimo médio'
    )
    avg_budget_max = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        allow_null=True,
        help_text='Orçamento máximo médio'
    )


class ProposalStatsSerializer(serializers.Serializer):
    """
    Serializer para estatísticas de propostas.
    Retorna contagens de propostas por status e métricas relacionadas.
    """
    total_proposals = serializers.IntegerField(help_text='Total de propostas')
    pending_proposals = serializers.IntegerField(help_text='Propostas pendentes')
    accepted_proposals = serializers.IntegerField(help_text='Propostas aceitas')
    declined_proposals = serializers.IntegerField(help_text='Propostas recusadas')
    expired_proposals = serializers.IntegerField(help_text='Propostas expiradas')
    new_proposals_today = serializers.IntegerField(help_text='Novas propostas hoje')
    new_proposals_this_week = serializers.IntegerField(help_text='Novas propostas esta semana')
    new_proposals_this_month = serializers.IntegerField(help_text='Novas propostas este mês')
    avg_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        allow_null=True,
        help_text='Preço médio das propostas'
    )
    avg_estimated_days = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        allow_null=True,
        help_text='Prazo médio estimado (dias)'
    )


class PaymentStatsSerializer(serializers.Serializer):
    """
    Serializer para estatísticas de pagamentos.
    Retorna contagens de pagamentos por status e métricas financeiras.
    """
    total_payments = serializers.IntegerField(help_text='Total de pagamentos')
    pending_payments = serializers.IntegerField(help_text='Pagamentos pendentes')
    paid_payments = serializers.IntegerField(help_text='Pagamentos confirmados')
    failed_payments = serializers.IntegerField(help_text='Pagamentos falhados')
    refunded_payments = serializers.IntegerField(help_text='Pagamentos reembolsados')
    total_revenue = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Receita total (apenas pagamentos confirmados)'
    )
    revenue_today = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Receita de hoje'
    )
    revenue_this_week = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Receita desta semana'
    )
    revenue_this_month = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Receita deste mês'
    )
    avg_payment_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        allow_null=True,
        help_text='Valor médio dos pagamentos'
    )


class SubscriptionStatsSerializer(serializers.Serializer):
    """
    Serializer para estatísticas de assinaturas.
    Retorna contagens de assinaturas por status e métricas relacionadas.
    """
    total_subscriptions = serializers.IntegerField(help_text='Total de assinaturas')
    active_subscriptions = serializers.IntegerField(help_text='Assinaturas ativas')
    cancelled_subscriptions = serializers.IntegerField(help_text='Assinaturas canceladas')
    expired_subscriptions = serializers.IntegerField(help_text='Assinaturas expiradas')
    suspended_subscriptions = serializers.IntegerField(help_text='Assinaturas suspensas')
    total_subscription_revenue = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Receita total de assinaturas'
    )
    subscription_revenue_this_month = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Receita de assinaturas deste mês'
    )
    subscriptions_by_plan = serializers.DictField(
        child=serializers.IntegerField(),
        help_text='Contagem de assinaturas por plano'
    )


class ReviewStatsSerializer(serializers.Serializer):
    """
    Serializer para estatísticas de avaliações.
    Retorna métricas de avaliações e ratings.
    """
    total_reviews = serializers.IntegerField(help_text='Total de avaliações')
    avg_rating = serializers.DecimalField(
        max_digits=3,
        decimal_places=2,
        allow_null=True,
        help_text='Avaliação média (1-5)'
    )
    reviews_by_rating = serializers.DictField(
        child=serializers.IntegerField(),
        help_text='Contagem de avaliações por nota (1, 2, 3, 4, 5)'
    )
    new_reviews_today = serializers.IntegerField(help_text='Novas avaliações hoje')
    new_reviews_this_week = serializers.IntegerField(help_text='Novas avaliações esta semana')
    new_reviews_this_month = serializers.IntegerField(help_text='Novas avaliações este mês')


class DashboardStatsSerializer(serializers.Serializer):
    """
    Serializer principal para o dashboard administrativo.
    Agrega todas as estatísticas principais do sistema em um único serializer.
    """
    users = UserStatsSerializer(help_text='Estatísticas de usuários')
    orders = OrderStatsSerializer(help_text='Estatísticas de pedidos')
    proposals = ProposalStatsSerializer(help_text='Estatísticas de propostas')
    payments = PaymentStatsSerializer(help_text='Estatísticas de pagamentos')
    subscriptions = SubscriptionStatsSerializer(help_text='Estatísticas de assinaturas')
    reviews = ReviewStatsSerializer(help_text='Estatísticas de avaliações')
    generated_at = serializers.DateTimeField(help_text='Data/hora de geração das estatísticas')


# ==================== RELATÓRIOS ====================


class FinancialReportSerializer(serializers.Serializer):
    """
    Serializer para relatório financeiro detalhado.
    Retorna informações financeiras agregadas por período.
    """
    period_start = serializers.DateTimeField(help_text='Início do período')
    period_end = serializers.DateTimeField(help_text='Fim do período')
    total_revenue = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Receita total no período'
    )
    total_payments = serializers.IntegerField(help_text='Total de pagamentos no período')
    paid_payments = serializers.IntegerField(help_text='Pagamentos confirmados no período')
    failed_payments = serializers.IntegerField(help_text='Pagamentos falhados no período')
    refunded_payments = serializers.IntegerField(help_text='Pagamentos reembolsados no período')
    revenue_by_status = serializers.DictField(
        child=serializers.DecimalField(max_digits=12, decimal_places=2),
        help_text='Receita por status de pagamento'
    )
    revenue_by_payment_method = serializers.DictField(
        child=serializers.DecimalField(max_digits=12, decimal_places=2),
        help_text='Receita por método de pagamento'
    )
    daily_revenue = serializers.ListField(
        child=serializers.DictField(),
        help_text='Receita diária no período (lista de {date, revenue})'
    )
    subscription_revenue = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Receita de assinaturas no período'
    )
    service_revenue = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Receita de serviços no período'
    )


class UserReportSerializer(serializers.Serializer):
    """
    Serializer para relatório de usuários.
    Retorna informações detalhadas sobre usuários e sua atividade.
    """
    period_start = serializers.DateTimeField(help_text='Início do período')
    period_end = serializers.DateTimeField(help_text='Fim do período')
    total_users = serializers.IntegerField(help_text='Total de usuários no período')
    new_users = serializers.IntegerField(help_text='Novos usuários no período')
    active_users = serializers.IntegerField(help_text='Usuários ativos no período')
    users_by_type = serializers.DictField(
        child=serializers.IntegerField(),
        help_text='Contagem de usuários por tipo'
    )
    users_by_status = serializers.DictField(
        child=serializers.IntegerField(),
        help_text='Contagem de usuários por status (ativo/inativo)'
    )
    top_active_clients = serializers.ListField(
        child=serializers.DictField(),
        help_text='Top clientes mais ativos (lista de {user_id, email, orders_count})'
    )
    top_active_providers = serializers.ListField(
        child=serializers.DictField(),
        help_text='Top prestadores mais ativos (lista de {user_id, email, proposals_count, rating_avg})'
    )
    daily_registrations = serializers.ListField(
        child=serializers.DictField(),
        help_text='Registros diários no período (lista de {date, count})'
    )


class ServiceReportSerializer(serializers.Serializer):
    """
    Serializer para relatório de serviços.
    Retorna informações sobre serviços, categorias e sua popularidade.
    """
    period_start = serializers.DateTimeField(help_text='Início do período')
    period_end = serializers.DateTimeField(help_text='Fim do período')
    total_services = serializers.IntegerField(help_text='Total de serviços cadastrados')
    total_categories = serializers.IntegerField(help_text='Total de categorias')
    active_services = serializers.IntegerField(help_text='Serviços ativos')
    active_categories = serializers.IntegerField(help_text='Categorias ativas')
    most_requested_services = serializers.ListField(
        child=serializers.DictField(),
        help_text='Serviços mais solicitados (lista de {service_id, name, orders_count})'
    )
    most_requested_categories = serializers.ListField(
        child=serializers.DictField(),
        help_text='Categorias mais solicitadas (lista de {category_id, name, orders_count})'
    )
    orders_by_service = serializers.DictField(
        child=serializers.IntegerField(),
        help_text='Contagem de pedidos por serviço'
    )
    orders_by_category = serializers.DictField(
        child=serializers.IntegerField(),
        help_text='Contagem de pedidos por categoria'
    )


class PerformanceReportSerializer(serializers.Serializer):
    """
    Serializer para relatório de performance.
    Retorna métricas de performance e conversão do sistema.
    """
    period_start = serializers.DateTimeField(help_text='Início do período')
    period_end = serializers.DateTimeField(help_text='Fim do período')
    total_orders = serializers.IntegerField(help_text='Total de pedidos no período')
    total_proposals = serializers.IntegerField(help_text='Total de propostas no período')
    conversion_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Taxa de conversão (propostas aceitas / total de propostas)'
    )
    avg_proposals_per_order = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        allow_null=True,
        help_text='Média de propostas por pedido'
    )
    avg_time_to_accept = serializers.DurationField(
        allow_null=True,
        help_text='Tempo médio até aceitar proposta (em dias)'
    )
    avg_time_to_complete = serializers.DurationField(
        allow_null=True,
        help_text='Tempo médio até completar pedido (em dias)'
    )
    completion_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Taxa de conclusão (pedidos completados / pedidos aceitos)'
    )
    cancellation_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Taxa de cancelamento (pedidos cancelados / total de pedidos)'
    )
    avg_rating = serializers.DecimalField(
        max_digits=3,
        decimal_places=2,
        allow_null=True,
        help_text='Avaliação média no período'
    )
