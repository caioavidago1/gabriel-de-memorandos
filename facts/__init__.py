"""
Facts Module - Módulo de fatos extraídos de análise de investimentos
Baseado no FACTS_SCHEMA

Este módulo centraliza:
- Schemas e estruturas de dados (facts/*.py)
- Renderizadores de UI (facts/*.py)
- Utilitários de acesso e manipulação (facts/utils.py)
- Builders para formatação (facts/builder.py)
- Filtragem de facts (facts/filtering.py)
"""

# UI Renderers
from facts.identificacao import render_tab_identification
from facts.transacao import render_tab_transaction
from facts.financials import render_tab_financials
from facts.saida import render_tab_saida
from facts.retornos import render_tab_returns
from facts.qualitativo import render_tab_qualitative
from facts.opinioes import render_tab_opinioes
from facts.gestora import render_tab_gestora
from facts.fundo import render_tab_fundo
from facts.estrategia_fundo import render_tab_estrategia_fundo
from facts.spectra_context import render_tab_spectra_context

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
    # UI Renderers
    'render_tab_identification',
    'render_tab_transaction',
    'render_tab_financials',
    'render_tab_saida',
    'render_tab_returns',
    'render_tab_qualitative',
    'render_tab_opinioes',
    'render_tab_gestora',
    'render_tab_fundo',
    'render_tab_estrategia_fundo',
    'render_tab_spectra_context',
    # Utilitários
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
