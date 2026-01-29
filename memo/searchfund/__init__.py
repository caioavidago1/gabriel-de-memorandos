"""
Memo Completo Search Fund

Módulo para geração de memos completos (~20 páginas) de aquisição via Search Fund.
Versão expandida com 5-8 parágrafos por seção para análise aprofundada.

DIFERENÇA VS SHORTMEMO:
- shortmemo: 2-4 páginas, triagem rápida
- memo (este módulo): ~20 páginas, análise completa para IC
"""

from .generator import (
    generate_section,
    generate_intro_section,
    generate_company_section,
    generate_market_section,
    generate_financials_section,
    generate_transaction_section,
    generate_projections_section,
    generate_retornos_esperados_section,
    generate_gestor_section,
    generate_board_cap_table_section,
    generate_conclusao_section,
    generate_risks_section,
)

from .validator import (
    fix_number_formatting,
    validate_section_length,
    validate_memo_consistency,
    validate_financial_coherence,
    validate_returns_coherence,
    validate_complete_memo,
    validate_no_redundancy,
    format_validation_report,
)

__all__ = [
    # Generators
    "generate_section",
    "generate_intro_section",
    "generate_company_section",
    "generate_market_section",
    "generate_financials_section",
    "generate_transaction_section",
    "generate_projections_section",
    "generate_retornos_esperados_section",
    "generate_gestor_section",
    "generate_board_cap_table_section",
    "generate_conclusao_section",
    "generate_risks_section",
    # Validators
    "fix_number_formatting",
    "validate_section_length",
    "validate_memo_consistency",
    "validate_financial_coherence",
    "validate_returns_coherence",
    "validate_complete_memo",
    "validate_no_redundancy",
    "format_validation_report",
]

# Estrutura fixa para Memo Completo Search Fund (9 seções)
FIXED_STRUCTURE = {
    "1. Overview": "overview",
    "2. Gestor": "gestor",
    "3. Mercado": "mercado",
    "4. Empresa": "empresa",
    "5. Transação": "transacao",
    "6. Projeções Financeiras": "projecoes_financeiras",
    "7. Retornos Esperados": "retornos_esperados",
    "8. Board e Cap Table": "board_cap_table",
    "9. Conclusão": "conclusao"
}
