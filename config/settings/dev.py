# pyright: reportUndefinedVariable=false
# flake8: noqa: F403, F401
"""
Django settings for development environment.
"""
from .base import *  # noqa: F403, F401

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Database - pode usar SQLite para desenvolvimento rápido (opcional)
# Descomente se quiser usar SQLite em dev
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# Use SQLite para testes (mais rápido e não requer PostgreSQL)
import sys
if 'test' in sys.argv or 'pytest' in sys.modules:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

# Email backend para desenvolvimento (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Django Debug Toolbar (se instalado)
if DEBUG:
    try:
        import debug_toolbar  # type: ignore  # noqa: F401
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
        INTERNAL_IPS = ['127.0.0.1', 'localhost']
    except ImportError:
        pass

# CORS - mais permissivo em desenvolvimento
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=True, cast=bool)

# Logging - mais verboso em desenvolvimento
LOGGING['root']['level'] = 'DEBUG'  # type: ignore
LOGGING['loggers']['django']['level'] = 'DEBUG'  # type: ignore
LOGGING['loggers']['api']['level'] = 'DEBUG'  # type: ignore

# DRF - mostrar browsable API em dev
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)

# Celery - sempre eager em desenvolvimento (executa tarefas sincronamente)
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=True, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = True

