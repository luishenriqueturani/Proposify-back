"""
ViewSets para o app admin (dashboard, gerenciamento administrativo).

Este módulo exporta todos os ViewSets do admin organizados em arquivos separados.
"""
from api.admin.views.dashboard import AdminDashboardViewSet
from api.admin.views.users import AdminUserViewSet
from api.admin.views.orders import AdminOrderViewSet, AdminProposalViewSet
from api.admin.views.payments import AdminPaymentViewSet
from api.admin.views.subscriptions import AdminSubscriptionViewSet
from api.admin.views.reviews import AdminReviewViewSet
from api.admin.views.audit import AdminAuditLogViewSet

__all__ = [
    'AdminDashboardViewSet',
    'AdminUserViewSet',
    'AdminOrderViewSet',
    'AdminProposalViewSet',
    'AdminPaymentViewSet',
    'AdminSubscriptionViewSet',
    'AdminReviewViewSet',
    'AdminAuditLogViewSet',
]
