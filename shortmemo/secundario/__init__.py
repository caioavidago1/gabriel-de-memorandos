"""
Short Memo Secundário - Módulo de Geração

Funções especializadas para análise de empresas maduras com foco em cash yield.
Seguindo padrão estabelecido em shortmemo/searchfund/

COMPONENTES:
- generator: Funções de geração por seção (intro, financials, transaction)
- validator: Validação de consistência e formatação

USO:
    from shortmemo.secundario import generate_section
    
    text = generate_section(
        section_name="intro",
        facts=facts_dict,
        rag_context="contexto do documento..."
    )
"""

from .generator import (
    generate_intro_section,
    generate_financials_section,
    generate_transaction_section,
    generate_portfolio_section,
    generate_section,
)
from .portfolio_agent import PortfolioAgent

from .validator import (
    validate_memo_consistency,
    fix_number_formatting,
    check_section_length,
    validate_secundario_intro,
    validate_fcf_metrics,
)

__all__ = [
    # Generators
    "generate_intro_section",
    "generate_financials_section",
    "generate_transaction_section",
    "generate_portfolio_section",
    "generate_section",
    # Agents
    "PortfolioAgent",
    # Validators
    "validate_memo_consistency",
    "fix_number_formatting",
    "check_section_length",
    "validate_secundario_intro",
    "validate_fcf_metrics",
]
