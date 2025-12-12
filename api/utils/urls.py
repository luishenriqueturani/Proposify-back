"""
URLs para endpoints utilitários (health checks).
"""
from django.urls import path
from . import views

app_name = 'utils'

urlpatterns = [
    path('health/', views.health_check, name='health'),
    path('health/db/', views.health_db, name='health-db'),
    path('health/redis/', views.health_redis, name='health-redis'),
    path('health/celery/', views.health_celery, name='health-celery'),
]

