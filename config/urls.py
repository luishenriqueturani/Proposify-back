"""
URL configuration for Proposify Backend.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Health Checks
    path('', include('api.utils.urls')),
    
    # API Routes (serão adicionadas conforme os apps forem implementados)
    # path('api/auth/', include('api.accounts.urls')),
    # path('api/services/', include('api.services.urls')),
    # path('api/orders/', include('api.orders.urls')),
    # path('api/proposals/', include('api.orders.urls')),  # propostas ficam em orders
    # path('api/chat/', include('api.chat.urls')),
    # path('api/subscriptions/', include('api.subscriptions.urls')),
    # path('api/payments/', include('api.payments.urls')),
    # path('api/reviews/', include('api.reviews.urls')),
    path('api/admin/', include('api.admin.urls')),
]

