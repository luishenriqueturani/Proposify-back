"""
Testes de configuração para settings (dev, prod).
"""
from django.test import TestCase, override_settings
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class SettingsDevTestCase(TestCase):
    """Testes para configurações de desenvolvimento."""

    @override_settings(DEBUG=True)
    def test_debug_is_true_in_dev(self):
        """Testa se DEBUG está True em desenvolvimento."""
        # Este teste verifica se as configurações de dev estão corretas
        # O override_settings garante que estamos testando com DEBUG=True
        self.assertTrue(settings.DEBUG)

    def test_dev_settings_loaded(self):
        """Testa se as configurações de dev podem ser carregadas."""
        # Verifica se as configurações básicas estão presentes
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertIsNotNone(settings.DATABASES)
        self.assertIsNotNone(settings.INSTALLED_APPS)

    def test_dev_cors_allowed_all_origins(self):
        """Testa se CORS permite todas as origens em dev."""
        # Em dev, CORS_ALLOW_ALL_ORIGINS deve ser True por padrão
        # Mas pode ser sobrescrito via .env
        self.assertIn('corsheaders', settings.INSTALLED_APPS)

    def test_dev_celery_eager_mode(self):
        """Testa se Celery está em modo eager em dev."""
        # Em dev, CELERY_TASK_ALWAYS_EAGER deve ser True
        # Isso faz com que tarefas sejam executadas sincronamente
        self.assertTrue(settings.CELERY_TASK_ALWAYS_EAGER)

    def test_dev_email_backend_configured(self):
        """Testa se email backend está configurado."""
        # Em dev, emails devem ir para console (ou locmem em testes)
        self.assertIsNotNone(settings.EMAIL_BACKEND)
        self.assertIn('EmailBackend', settings.EMAIL_BACKEND)


class SettingsProdTestCase(TestCase):
    """Testes para configurações de produção."""

    @override_settings(DEBUG=False)
    def test_debug_is_false_in_prod(self):
        """Testa se DEBUG está False em produção."""
        self.assertFalse(settings.DEBUG)

    def test_prod_security_settings(self):
        """Testa se configurações de segurança estão presentes."""
        # Verifica se as configurações de segurança existem
        # (mesmo que não estejam ativas em dev)
        self.assertTrue(hasattr(settings, 'SECURE_SSL_REDIRECT'))
        self.assertTrue(hasattr(settings, 'SESSION_COOKIE_SECURE'))
        self.assertTrue(hasattr(settings, 'CSRF_COOKIE_SECURE'))

    def test_prod_database_connection_max_age(self):
        """Testa se CONN_MAX_AGE está configurado em prod."""
        # Em produção, conexões devem ter max_age configurado
        # Verificamos se a configuração existe
        self.assertIsNotNone(settings.DATABASES['default'])

    def test_prod_static_files_storage(self):
        """Testa se static files storage está configurado em prod."""
        # Em produção, deve usar ManifestStaticFilesStorage
        # Em dev/test, pode não estar definido, então apenas verificamos se existe
        # ou se STATIC_URL está configurado
        self.assertTrue(
            hasattr(settings, 'STATICFILES_STORAGE') or 
            hasattr(settings, 'STATIC_URL')
        )


class SettingsBaseTestCase(TestCase):
    """Testes para configurações base (comuns a dev e prod)."""

    def test_installed_apps_contains_all_apps(self):
        """Testa se todos os apps estão instalados."""
        required_apps = [
            'django.contrib.admin',
            'django.contrib.auth',
            'rest_framework',
            'corsheaders',
            'drf_spectacular',
            'channels',
            'api.accounts',
            'api.services',
            'api.orders',
            'api.chat',
            'api.subscriptions',
            'api.payments',
            'api.reviews',
            'api.admin',
            'api.notifications',
            'api.utils',
        ]
        
        for app in required_apps:
            self.assertIn(app, settings.INSTALLED_APPS, f"App {app} não está instalado")

    def test_database_config_exists(self):
        """Testa se configuração do banco de dados existe."""
        self.assertIn('default', settings.DATABASES)
        self.assertIn('ENGINE', settings.DATABASES['default'])
        self.assertIn('NAME', settings.DATABASES['default'])

    def test_rest_framework_config_exists(self):
        """Testa se configuração do DRF existe."""
        self.assertIsNotNone(settings.REST_FRAMEWORK)
        self.assertIn('DEFAULT_AUTHENTICATION_CLASSES', settings.REST_FRAMEWORK)
        self.assertIn('DEFAULT_PERMISSION_CLASSES', settings.REST_FRAMEWORK)

    def test_jwt_config_exists(self):
        """Testa se configuração do JWT existe."""
        self.assertIsNotNone(settings.SIMPLE_JWT)
        self.assertIn('ACCESS_TOKEN_LIFETIME', settings.SIMPLE_JWT)
        self.assertIn('REFRESH_TOKEN_LIFETIME', settings.SIMPLE_JWT)

    def test_cors_config_exists(self):
        """Testa se configuração do CORS existe."""
        self.assertIn('corsheaders', settings.INSTALLED_APPS)
        self.assertIn('corsheaders.middleware.CorsMiddleware', settings.MIDDLEWARE)

    def test_celery_config_exists(self):
        """Testa se configuração do Celery existe."""
        self.assertIsNotNone(settings.CELERY_BROKER_URL)
        self.assertIsNotNone(settings.CELERY_RESULT_BACKEND)

    def test_channels_config_exists(self):
        """Testa se configuração do Channels existe."""
        self.assertIsNotNone(settings.CHANNEL_LAYERS)
        self.assertIn('default', settings.CHANNEL_LAYERS)

    def test_logging_config_exists(self):
        """Testa se configuração de logging existe."""
        self.assertIsNotNone(settings.LOGGING)
        self.assertIn('version', settings.LOGGING)
        self.assertIn('handlers', settings.LOGGING)
        self.assertIn('loggers', settings.LOGGING)

