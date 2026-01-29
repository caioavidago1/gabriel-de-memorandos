"""
Memo Completo Secundário

Módulo para geração de memos completos (~20 páginas) de transações secundárias.
LP interests, GP-led secondaries, direct secondaries.
"""

from .generator import (
    generate_section,
    generate_intro_section,
    generate_seller_context_section,
    generate_portfolio_section,
    generate_valuation_section,
    generate_returns_section,
    generate_structure_section,
    generate_gp_analysis_section,
    generate_risks_section,
    generate_full_memo,
)

from .validator import (
    fix_number_formatting,
    validate_section_length,
    validate_secondary_metrics,
    validate_nav_consistency,
    validate_discount_coherence,
    validate_timeline_plausibility,
    validate_return_reasonability,
    validate_gp_analysis,
    validate_memo_consistency,
    validate_complete_memo,
    format_validation_report,
)

__all__ = [
    "generate_section",
    "generate_intro_section",
    "generate_seller_context_section",
    "generate_portfolio_section",
    "generate_valuation_section",
    "generate_returns_section",
    "generate_structure_section",
    "generate_gp_analysis_section",
    "generate_risks_section",
    "generate_full_memo",
    "fix_number_formatting",
    "validate_section_length",
    "validate_secondary_metrics",
    "validate_nav_consistency",
    "validate_discount_coherence",
    "validate_timeline_plausibility",
    "validate_return_reasonability",
    "validate_gp_analysis",
    "validate_memo_consistency",
    "validate_complete_memo",
    "format_validation_report",
]
