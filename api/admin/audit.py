"""
Serviço de auditoria para registrar ações administrativas.

Fornece funções helper para criar logs de auditoria no modelo AdminAction.
"""
import logging
from typing import Any
from api.admin.models import AdminAction

logger = logging.getLogger(__name__)


def get_client_ip(request) -> str | None:
    """
    Extrai o endereço IP do cliente da requisição.
    
    Args:
        request: Objeto de requisição Django/DRF
        
    Returns:
        str | None: Endereço IP do cliente ou None se não disponível
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Pega o primeiro IP da lista (IP real do cliente)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_admin_action(
    admin_user,
    action_type: str,
    description: str,
    target_model: str | None = None,
    target_id: int | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AdminAction | None:
    """
    Registra uma ação administrativa no banco de dados.
    
    Args:
        admin_user: Usuário administrador que realizou a ação
        action_type: Tipo da ação (ex: USER_SUSPEND, ORDER_VIEW, REVIEW_DELETE)
        description: Descrição detalhada da ação
        target_model: Nome do modelo afetado (ex: User, Order)
        target_id: ID do objeto afetado
        metadata: Informações adicionais em formato dict
        ip_address: Endereço IP de onde a ação foi realizada
        
    Returns:
        AdminAction | None: Objeto criado ou None em caso de erro
        
    Exemplo:
        >>> log_admin_action(
        ...     admin_user=request.user,
        ...     action_type='USER_SUSPEND',
        ...     description='Usuário john@example.com foi suspenso',
        ...     target_model='User',
        ...     target_id=123,
        ...     metadata={'reason': 'Violação de termos'},
        ...     ip_address='192.168.1.1'
        ... )
    """
    try:
        action = AdminAction.objects.create(
            admin_user=admin_user,
            action_type=action_type,
            description=description,
            target_model=target_model,
            target_id=target_id,
            metadata=metadata or {},
            ip_address=ip_address,
        )
        logger.info(
            f"Ação administrativa registrada: {action_type} por {admin_user.email}",
            extra={
                'action_id': action.id,
                'action_type': action_type,
                'admin_user_id': admin_user.id,
                'target_model': target_model,
                'target_id': target_id,
            }
        )
        return action
    except Exception as e:
        logger.error(
            f"Erro ao registrar ação administrativa: {e}",
            extra={
                'action_type': action_type,
                'admin_user_id': getattr(admin_user, 'id', None),
                'error': str(e),
            },
            exc_info=True
        )
        return None


# Mapeamento de métodos HTTP para tipos de ação
HTTP_METHOD_ACTION_MAP = {
    'POST': 'CREATE',
    'PUT': 'UPDATE',
    'PATCH': 'UPDATE',
    'DELETE': 'DELETE',
}

# Mapeamento de URLs para modelos
URL_MODEL_MAP = {
    'users': 'User',
    'orders': 'Order',
    'proposals': 'Proposal',
    'payments': 'Payment',
    'subscriptions': 'UserSubscription',
    'reviews': 'Review',
    'audit-logs': 'AdminAction',
    'dashboard': 'Dashboard',
}


def get_action_type_from_request(request, view_name: str | None = None) -> str:
    """
    Determina o tipo de ação baseado na requisição.
    
    Args:
        request: Objeto de requisição Django/DRF
        view_name: Nome da view sendo acessada
        
    Returns:
        str: Tipo de ação (ex: USER_UPDATE, ORDER_VIEW)
    """
    method = request.method
    path = request.path
    
    # Extrai o modelo da URL
    model = 'UNKNOWN'
    for url_part, model_name in URL_MODEL_MAP.items():
        if url_part in path:
            model = model_name.upper()
            break
    
    # Determina a ação baseada no método HTTP
    if method == 'GET':
        action = 'VIEW'
    else:
        action = HTTP_METHOD_ACTION_MAP.get(method, 'ACTION')
    
    # Verifica ações especiais na URL
    if 'suspend' in path:
        action = 'SUSPEND'
    elif 'activate' in path:
        action = 'ACTIVATE'
    elif 'cancel' in path:
        action = 'CANCEL'
    elif 'reactivate' in path:
        action = 'REACTIVATE'
    elif 'stats' in path:
        action = 'VIEW_STATS'
    
    return f"{model}_{action}"


def get_target_id_from_path(path: str) -> int | None:
    """
    Extrai o ID do objeto alvo da URL.
    
    Args:
        path: Caminho da URL
        
    Returns:
        int | None: ID do objeto ou None se não encontrado
    """
    import re
    # Procura por /número/ na URL
    match = re.search(r'/(\d+)/', path)
    if match:
        return int(match.group(1))
    return None
