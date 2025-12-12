"""
Views utilitárias para health checks e status do sistema.
"""
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import redis  # type: ignore
from celery import current_app  # type: ignore


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check básico da aplicação.
    
    Retorna status 200 se a aplicação está funcionando.
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'proposify-backend',
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def health_db(request):
    """
    Health check do banco de dados.
    
    Verifica se a conexão com o banco de dados está funcionando.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'engine': settings.DATABASES['default']['ENGINE'].split('.')[-1],
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
        }, status=503)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_redis(request):
    """
    Health check do Redis.
    
    Verifica se a conexão com o Redis está funcionando.
    """
    try:
        redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        r.ping()
        
        return JsonResponse({
            'status': 'healthy',
            'redis': 'connected',
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'redis': 'disconnected',
            'error': str(e),
        }, status=503)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_celery(request):
    """
    Health check do Celery.
    
    Verifica se os workers do Celery estão ativos.
    """
    try:
        inspect = current_app.control.inspect()  # type: ignore
        active_workers = inspect.active()
        
        if active_workers:
            return JsonResponse({
                'status': 'healthy',
                'celery': 'workers_active',
                'workers_count': len(active_workers),
                'workers': list(active_workers.keys()),
            })
        else:
            return JsonResponse({
                'status': 'unhealthy',
                'celery': 'no_workers',
                'message': 'No active Celery workers found',
            }, status=503)
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'celery': 'error',
            'error': str(e),
        }, status=503)
