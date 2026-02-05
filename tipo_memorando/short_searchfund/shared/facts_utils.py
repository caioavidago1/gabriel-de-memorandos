"""
Utilitários compartilhados para acesso seguro a facts

DEPRECADO: Este módulo é um wrapper de compatibilidade.
Use facts.utils diretamente.
"""

# Reexportar do módulo centralizado facts
from facts.utils import (
    get_fact_safe,
    get_currency_safe,
    get_name_safe,
    get_numeric_safe,
    get_text_safe,
)

__all__ = [
    'get_fact_safe',
    'get_currency_safe',
    'get_name_safe',
    'get_numeric_safe',
    'get_text_safe',
]
