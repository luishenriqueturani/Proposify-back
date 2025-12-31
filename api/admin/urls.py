"""
URL configuration para o app admin (dashboard e gerenciamento administrativo).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.admin.views import (
    AdminDashboardViewSet,
    AdminUserViewSet,
    AdminOrderViewSet,
    AdminProposalViewSet,
    AdminPaymentViewSet,
    AdminSubscriptionViewSet,
    AdminReviewViewSet,
    AdminAuditLogViewSet,
)

router = DefaultRouter()
router.register(r'dashboard', AdminDashboardViewSet, basename='admin-dashboard')
router.register(r'users', AdminUserViewSet, basename='admin-users')
router.register(r'orders', AdminOrderViewSet, basename='admin-orders')
router.register(r'proposals', AdminProposalViewSet, basename='admin-proposals')
router.register(r'payments', AdminPaymentViewSet, basename='admin-payments')
router.register(r'subscriptions', AdminSubscriptionViewSet, basename='admin-subscriptions')
router.register(r'reviews', AdminReviewViewSet, basename='admin-reviews')
router.register(r'audit-logs', AdminAuditLogViewSet, basename='admin-audit-logs')

urlpatterns = [
    path('', include(router.urls)),
]
