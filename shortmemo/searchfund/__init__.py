"""
Short Memo Search Fund - Módulo de Geração

Arquitetura de agentes especializados validados por 2+ anos de uso real.

COMPONENTES:
- orchestrator: Coordenação de agentes (FIXED_STRUCTURE)
- Agentes: IntroAgent, MercadoAgent, EmpresaAgent, TransacaoAgent, PontosAprofundarAgent
- examples: Casos reais (TSE/Minerva, Oca/Eunoia, Grano)
- validator: Validação de consistência e formatação
- facts_builder: Formatação de facts estruturados
- utils: Multi-moeda e helpers

USO:
    from shortmemo.searchfund.orchestrator import generate_full_memo
    
    memo_sections = generate_full_memo(
        facts=facts_dict,
        rag_context="contexto do documento..."
    )
"""

from .orchestrator import (
    generate_full_memo,
    FIXED_STRUCTURE,
)

from .shared import (
    validate_memo_consistency,
    fix_number_formatting,
    check_section_length,
    validate_search_fund_intro,
    build_facts_section,
    format_facts_for_prompt,
    clean_facts,
    get_fact_value,
    get_currency_symbol,
    get_currency_label,
    format_currency_value,
    format_multiple,
    format_percentage,
)


__all__ = [
    # Generators principais
    "generate_intro_section",
    "generate_company_section",
    "generate_market_section",
    "generate_section",
    
    # Validação
    "validate_memo_consistency",
    "fix_number_formatting",
    "check_section_length",
    "validate_search_fund_intro",
    
    # Facts
    "build_facts_section",
    "format_facts_for_prompt",
    "clean_facts",
    "get_fact_value",
    
    # Utils
    "get_currency_symbol",
    "get_currency_label",
    "format_currency_value",
    "format_multiple",
    "format_percentage",
]
