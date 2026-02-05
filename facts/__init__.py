"""
Facts Module - Utilitários para fatos extraídos de análise de investimentos.

Renderizadores de UI estão em tipo_memorando/<tipo>/fatos/.
Este módulo mantém: builder, utils, filtering.
"""

# Utilitários centralizados
from facts.utils import (
    get_fact_safe,
    get_currency_safe,
    get_name_safe,
    get_numeric_safe,
    get_text_safe,
    get_fact_value,
)

# Builders centralizados
from facts.builder import (
    build_facts_section,
    format_facts_for_prompt,
    clean_facts,
)

# Filtragem
from facts.filtering import filter_disabled_facts

__all__ = [
    'get_fact_safe',
    'get_currency_safe',
    'get_name_safe',
    'get_numeric_safe',
    'get_text_safe',
    'get_fact_value',
    # Builders
    'build_facts_section',
    'format_facts_for_prompt',
    'clean_facts',
    # Filtragem
    'filter_disabled_facts',
]
