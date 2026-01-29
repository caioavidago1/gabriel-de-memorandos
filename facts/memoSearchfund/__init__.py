"""
Facts Module para Memo Completo Search Fund

DEPRECADO: Este módulo é um wrapper de compatibilidade.
Use facts.builder e shortmemo.format_utils diretamente.

Mantido para compatibilidade com agentes em memo/searchfund/agents/
"""

# Importar do módulo centralizado facts
from facts.builder import build_facts_section

# Importar funções de formatação de moeda do módulo apropriado
from shortmemo.format_utils import (
    get_currency_symbol,
    get_currency_label,
)

__all__ = [
    "build_facts_section",
    "get_currency_symbol",
    "get_currency_label",
]
