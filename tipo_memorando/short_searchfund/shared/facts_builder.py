"""
Construtor de seções de facts para Short Memo Search Fund

DEPRECADO: Este módulo é um wrapper de compatibilidade.
Use facts.builder e facts.utils diretamente.
"""

# Reexportar do módulo centralizado facts
from facts.builder import (
    build_facts_section,
    format_facts_for_prompt,
    clean_facts,
)
from facts.utils import get_fact_value

# Manter compatibilidade - estas funções agora apontam para o módulo centralizado
__all__ = [
    'build_facts_section',
    'format_facts_for_prompt',
    'clean_facts',
    'get_fact_value',
]
