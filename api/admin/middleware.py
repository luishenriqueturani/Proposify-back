"""
Middleware de auditoria para ações administrativas.

Intercepta requisições nos endpoints /api/admin/ e registra ações
que modificam dados (POST, PUT, PATCH, DELETE) no modelo AdminAction.
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from api.accounts.enums import UserType

logger = logging.getLogger(__name__)


class AdminAuditMiddleware(MiddlewareMixin):
    """
    Middleware que registra ações administrativas automaticamente.
    
    Intercepta requisições que modificam dados nos endpoints /api/admin/
    e cria registros de auditoria no modelo AdminAction.
    
    Métodos registrados: POST, PUT, PATCH, DELETE
    
    Nota: Requisições GET não são registradas para evitar excesso de logs,
    exceto para ações específicas como visualização de dados sensíveis.
    """
    
    # Métodos HTTP que devem ser auditados
    AUDITABLE_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}
    
    # Prefixo das URLs do admin
    ADMIN_URL_PREFIX = '/api/admin/'
    
    def process_response(self, request, response):
        """
        Processa a resposta e registra a ação se necessário.
        
        Registra apenas ações bem-sucedidas (status 2xx) para evitar
        logging de tentativas falhas.
        """
        # Verifica se é uma URL do admin
        if not request.path.startswith(self.ADMIN_URL_PREFIX):
            return response
        
        # Verifica se é um método que deve ser auditado
        if request.method not in self.AUDITABLE_METHODS:
            return response
        
        # Verifica se a resposta foi bem-sucedida (2xx)
        if not (200 <= response.status_code < 300):
            return response
        
        # Verifica se o usuário está autenticado e é admin
        if not self._is_admin_user(request):
            return response
        
        # Registra a ação
        self._log_action(request, response)
        
        return response
    
    def _is_admin_user(self, request) -> bool:
        """Verifica se o usuário é um administrador autenticado."""
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        
        return (
            getattr(user, 'user_type', None) == UserType.ADMIN.value or
            getattr(user, 'is_staff', False) or
            getattr(user, 'is_superuser', False)
        )
    
    def _log_action(self, request, response):
        """Registra a ação administrativa no banco de dados."""
        try:
            # Import aqui para evitar imports circulares
            from api.admin.audit import (
                log_admin_action,
                get_client_ip,
                get_action_type_from_request,
                get_target_id_from_path,
                URL_MODEL_MAP,
            )
            
            user = request.user
            action_type = get_action_type_from_request(request)
            ip_address = get_client_ip(request)
            target_id = get_target_id_from_path(request.path)
            
            # Determina o modelo alvo
            target_model = None
            for url_part, model_name in URL_MODEL_MAP.items():
                if url_part in request.path:
                    target_model = model_name
                    break
            
            # Cria descrição da ação
            description = self._build_description(request, response, target_id)
            
            # Monta metadados
            metadata = {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'query_params': dict(request.GET) if request.GET else None,
            }
            
            # Adiciona body da requisição (exceto senhas e dados sensíveis)
            if hasattr(request, 'data') and request.data:
                safe_data = self._sanitize_data(dict(request.data))
                if safe_data:
                    metadata['request_data'] = safe_data
            
            log_admin_action(
                admin_user=user,
                action_type=action_type,
                description=description,
                target_model=target_model,
                target_id=target_id,
                metadata=metadata,
                ip_address=ip_address,
            )
            
        except Exception as e:
            # Log de erro mas não interrompe a requisição
            logger.error(
                f"Erro no middleware de auditoria: {e}",
                exc_info=True
            )
    
    def _build_description(self, request, response, target_id: int | None) -> str:
        """Constrói uma descrição legível da ação."""
        method = request.method
        path = request.path
        user_email = request.user.email
        
        # Descrições específicas para ações comuns
        if 'suspend' in path:
            return f"Admin {user_email} suspendeu objeto ID {target_id}"
        elif 'activate' in path:
            return f"Admin {user_email} ativou objeto ID {target_id}"
        elif 'cancel' in path:
            return f"Admin {user_email} cancelou objeto ID {target_id}"
        elif 'reactivate' in path:
            return f"Admin {user_email} reativou objeto ID {target_id}"
        
        # Descrições genéricas por método
        method_descriptions = {
            'POST': 'criou',
            'PUT': 'atualizou',
            'PATCH': 'atualizou',
            'DELETE': 'removeu',
        }
        action_verb = method_descriptions.get(method, 'acessou')
        
        if target_id:
            return f"Admin {user_email} {action_verb} objeto ID {target_id} em {path}"
        else:
            return f"Admin {user_email} {action_verb} recurso em {path}"
    
    def _sanitize_data(self, data: dict) -> dict:
        """Remove dados sensíveis do dicionário."""
        sensitive_keys = {
            'password', 'password1', 'password2', 'new_password',
            'old_password', 'confirm_password', 'token', 'secret',
            'api_key', 'access_token', 'refresh_token',
        }
        
        return {
            key: '***REDACTED***' if key.lower() in sensitive_keys else value
            for key, value in data.items()
        }
