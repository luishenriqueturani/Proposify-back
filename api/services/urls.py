"""
URL configuration para o app services.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.services.views import (
    ServiceCategoryViewSet,
    ServiceViewSet,
)

router = DefaultRouter()
router.register(r'categories', ServiceCategoryViewSet, basename='service-categories')
router.register(r'', ServiceViewSet, basename='services')

urlpatterns = [
    path('', include(router.urls)),
]
