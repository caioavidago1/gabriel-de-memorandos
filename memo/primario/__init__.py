"""
Memo Completo Primário

Módulo para geração de memos completos (~20 páginas) de deals primários.
Growth equity, venture capital, rodadas de investimento.
"""

from .generator import (
    generate_section,
    generate_intro_section,
    generate_company_section,
    generate_market_section,
    generate_financials_section,
    generate_founders_section,
    generate_transaction_section,
    generate_projections_section,
    generate_risks_section,
)

from .validator import (
    fix_number_formatting,
    validate_section_length,
    validate_memo_consistency,
    validate_saas_metrics,
    validate_valuation_coherence,
    validate_complete_memo,
    format_validation_report,
)

__all__ = [
    "generate_section",
    "generate_intro_section",
    "generate_company_section",
    "generate_market_section",
    "generate_financials_section",
    "generate_founders_section",
    "generate_transaction_section",
    "generate_projections_section",
    "generate_risks_section",
    "fix_number_formatting",
    "validate_section_length",
    "validate_memo_consistency",
    "validate_saas_metrics",
    "validate_valuation_coherence",
    "validate_complete_memo",
    "format_validation_report",
]
