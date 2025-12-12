"""
Testes de integração para endpoints de health check.
"""
from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch, MagicMock


class HealthCheckTestCase(TestCase):
    """Testes para o endpoint de health check básico."""

    def test_health_check_returns_200(self):
        """Testa se o endpoint /health/ retorna 200."""
        url = reverse('utils:health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'healthy')
        self.assertEqual(response.json()['service'], 'proposify-backend')

    def test_health_check_no_auth_required(self):
        """Testa se o endpoint não requer autenticação."""
        url = reverse('utils:health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)


class HealthDBCheckTestCase(TestCase):
    """Testes para o endpoint de health check do banco de dados."""

    def test_health_db_returns_200_when_connected(self):
        """Testa se o endpoint /health/db/ retorna 200 quando DB está conectado."""
        url = reverse('utils:health-db')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'healthy')
        self.assertEqual(response.json()['database'], 'connected')
        self.assertIn('engine', response.json())

    def test_health_db_returns_503_when_disconnected(self):
        """Testa se o endpoint retorna 503 quando DB está desconectado."""
        url = reverse('utils:health-db')
        
        with patch('django.db.connection.cursor') as mock_cursor:
            mock_cursor.side_effect = Exception("Database connection failed")
            
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json()['status'], 'unhealthy')
            self.assertEqual(response.json()['database'], 'disconnected')
            self.assertIn('error', response.json())


class HealthRedisCheckTestCase(TestCase):
    """Testes para o endpoint de health check do Redis."""

    @patch('api.utils.views.redis.from_url')
    def test_health_redis_returns_200_when_connected(self, mock_redis):
        """Testa se o endpoint /health/redis/ retorna 200 quando Redis está conectado."""
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis.return_value = mock_redis_instance
        
        url = reverse('utils:health-redis')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'healthy')
        self.assertEqual(response.json()['redis'], 'connected')

    @patch('api.utils.views.redis.from_url')
    def test_health_redis_returns_503_when_disconnected(self, mock_redis):
        """Testa se o endpoint retorna 503 quando Redis está desconectado."""
        mock_redis.side_effect = Exception("Redis connection failed")
        
        url = reverse('utils:health-redis')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['status'], 'unhealthy')
        self.assertEqual(response.json()['redis'], 'disconnected')
        self.assertIn('error', response.json())


class HealthCeleryCheckTestCase(TestCase):
    """Testes para o endpoint de health check do Celery."""

    @patch('api.utils.views.current_app.control.inspect')
    def test_health_celery_returns_200_when_workers_active(self, mock_inspect):
        """Testa se o endpoint /health/celery/ retorna 200 quando workers estão ativos."""
        mock_inspect_instance = MagicMock()
        mock_inspect_instance.active.return_value = {
            'worker1@hostname': [],
            'worker2@hostname': [],
        }
        mock_inspect.return_value = mock_inspect_instance
        
        url = reverse('utils:health-celery')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'healthy')
        self.assertEqual(response.json()['celery'], 'workers_active')
        self.assertEqual(response.json()['workers_count'], 2)

    @patch('api.utils.views.current_app.control.inspect')
    def test_health_celery_returns_503_when_no_workers(self, mock_inspect):
        """Testa se o endpoint retorna 503 quando não há workers ativos."""
        mock_inspect_instance = MagicMock()
        mock_inspect_instance.active.return_value = None
        mock_inspect.return_value = mock_inspect_instance
        
        url = reverse('utils:health-celery')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['status'], 'unhealthy')
        self.assertEqual(response.json()['celery'], 'no_workers')

    @patch('api.utils.views.current_app.control.inspect')
    def test_health_celery_returns_503_on_error(self, mock_inspect):
        """Testa se o endpoint retorna 503 quando há erro."""
        mock_inspect.side_effect = Exception("Celery error")
        
        url = reverse('utils:health-celery')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['status'], 'unhealthy')
        self.assertEqual(response.json()['celery'], 'error')
        self.assertIn('error', response.json())

