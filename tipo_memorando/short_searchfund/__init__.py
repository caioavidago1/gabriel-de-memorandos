"""
Short Memo Search Fund - Módulo de Geração

Arquitetura de agentes especializados validados por 2+ anos de uso real.
Migrado para tipo_memorando/short_searchfund/

USO:
    from tipo_memorando.short_searchfund.orchestrator import generate_full_memo
    
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
    "generate_full_memo",
    "FIXED_STRUCTURE",
    "validate_memo_consistency",
    "fix_number_formatting",
    "check_section_length",
    "validate_search_fund_intro",
    "build_facts_section",
    "format_facts_for_prompt",
    "clean_facts",
    "get_fact_value",
    "get_currency_symbol",
    "get_currency_label",
    "format_currency_value",
    "format_multiple",
    "format_percentage",
]
