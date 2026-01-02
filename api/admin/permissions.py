"""
Permissões customizadas para o app admin.

Este módulo re-exporta a permissão IsAdmin do app accounts para
manter compatibilidade com imports existentes.
"""
from api.accounts.permissions import IsAdmin  # noqa: F401

# Re-exporta para compatibilidade
__all__ = ['IsAdmin']
