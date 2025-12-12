# pyright: reportUndefinedVariable=false
# flake8: noqa: F403, F401
"""
Django settings for production environment.
"""
from .base import *  # noqa: F403, F401

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Security Settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Database - conexão otimizada para produção
DATABASES['default']['CONN_MAX_AGE'] = 600  # 10 minutos
DATABASES['default']['OPTIONS'] = {
    'connect_timeout': 10,
    'options': '-c statement_timeout=30000',  # 30 segundos
}

# Static files - usar storage otimizado em produção
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Email - usar backend real em produção
EMAIL_BACKEND = config('EMAIL_BACKEND', default='anymail.backends.mailgun.EmailBackend')

# CORS - restritivo em produção
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', cast=Csv())

# Logging - menos verboso em produção
LOGGING['root']['level'] = 'WARNING'  # type: ignore
LOGGING['loggers']['django']['level'] = 'WARNING'  # type: ignore
LOGGING['loggers']['api']['level'] = 'INFO'  # type: ignore

# DRF - apenas JSON em produção
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
)

# Celery - executar tarefas assincronamente em produção
CELERY_TASK_ALWAYS_EAGER = False

# Cache (usar Redis em produção)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'proposify',
        'TIMEOUT': 300,
    }
}

# Session - usar cache em produção
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

