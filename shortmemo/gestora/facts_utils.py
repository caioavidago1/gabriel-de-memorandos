"""
Utilitários específicos para Gestora - wrappers com defaults apropriados

DEPRECADO: Use facts.utils diretamente com context="gestora"
"""

from typing import Dict, Any, Optional
from facts.utils import (
    get_currency_safe as _get_currency_safe,
    get_name_safe as _get_name_safe,
    get_numeric_safe,
    get_text_safe,
)


def get_currency_safe(
    facts: Dict[str, Any], 
    section: str = "fundo", 
    field: str = "fundo_moeda"
) -> str:
    """
    Helper específico para obter moeda com fallback garantido.
    Defaults apropriados para Gestora.
    
    Args:
        facts: Dict de facts
        section: Seção (padrão: "fundo")
        field: Campo (padrão: "fundo_moeda")
    
    Returns:
        Código da moeda (sempre retorna, nunca None)
    """
    return _get_currency_safe(facts, section, field, default="BRL")


def get_name_safe(
    facts: Dict[str, Any], 
    section: str, 
    field: str, 
    default: Optional[str] = None
) -> Optional[str]:
    """
    Helper específico para obter nome/identificador com placeholder.
    Usa contexto "gestora" para personalizar placeholders.
    
    Args:
        facts: Dict de facts
        section: Seção
        field: Campo
        default: Placeholder customizado (opcional)
    
    Returns:
        Nome ou placeholder
    """
    return _get_name_safe(facts, section, field, default=default, context="gestora")


# Re-exportar funções que não precisam de wrapper
__all__ = ["get_currency_safe", "get_name_safe", "get_numeric_safe", "get_text_safe"]