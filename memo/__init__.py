"""
Memos Completos - Módulos especializados por tipo

DIFERENÇA VS SHORT MEMO:
- Short Memo: 2-4 parágrafos por seção (resumido, para triagem)
- Memo Completo: 5-8 parágrafos por seção (análise profunda, ~20 páginas)

TIPOS DISPONÍVEIS:
- searchfund: Memo Completo para aquisições via Search Fund
- gestora: Memo Completo para análise de Gestoras de PE/VC
- primario: Memo Completo para growth equity (SaaS, tech)
- secundario: Memo Completo para transações secundárias (LP/GP-led)

USO:
    from memo import generate_section
    
    # Gerar seção específica
    result = generate_section(
        memo_type="searchfund",  # ou "gestora", "primario", "secundario"
        section_name="intro",
        facts=facts_dict
    )
    
    # Gerar memo completo
    from memo import generate_full_memo
    memo = generate_full_memo(memo_type="searchfund", facts=facts_dict)
"""

# Imports dos submódulos
from . import searchfund
from . import gestora
from . import primario
from . import secundario


def generate_section(memo_type: str, section_name: str, facts: dict, model=None) -> str:
    """
    Gera uma seção específica do memo completo.
    
    Args:
        memo_type: Tipo do memo ("searchfund", "gestora", "primario", "secundario")
        section_name: Nome da seção a gerar
        facts: Dicionário com facts estruturados
        model: Modelo LLM (opcional)
    
    Returns:
        Texto da seção gerada
    
    Seções por tipo:
        - searchfund: intro, company, market, financials, transaction, projections, risks
        - gestora: intro, track_record, team, strategy, terms, risks
        - primario: intro, company, market, financials, founders, transaction, projections, risks
        - secundario: intro, seller_context, portfolio, valuation, returns, structure, gp_analysis, risks
    """
    generators = {
        "searchfund": searchfund.generate_section,
        "gestora": gestora.generate_section,
        "primario": primario.generate_section,
        "secundario": secundario.generate_section,
    }
    
    if memo_type not in generators:
        available = ", ".join(generators.keys())
        raise ValueError(f"Tipo '{memo_type}' não encontrado. Disponíveis: {available}")
    
    return generators[memo_type](section_name, facts, model)


def generate_full_memo(memo_type: str, facts: dict, model=None) -> dict:
    """
    Gera memo completo com todas as seções.
    
    Args:
        memo_type: Tipo do memo
        facts: Dicionário com facts estruturados
        model: Modelo LLM (opcional)
    
    Returns:
        Dict com todas as seções geradas
    """
    sections_by_type = {
        "searchfund": ["intro", "company", "market", "financials", "transaction", "projections", "risks"],
        "gestora": ["intro", "track_record", "team", "strategy", "terms", "risks"],
        "primario": ["intro", "company", "market", "financials", "founders", "transaction", "projections", "risks"],
        "secundario": ["intro", "seller_context", "portfolio", "valuation", "returns", "structure", "gp_analysis", "risks"],
    }
    
    if memo_type not in sections_by_type:
        available = ", ".join(sections_by_type.keys())
        raise ValueError(f"Tipo '{memo_type}' não encontrado. Disponíveis: {available}")
    
    memo = {}
    for section in sections_by_type[memo_type]:
        memo[section] = generate_section(memo_type, section, facts, model)
    
    return memo


def get_available_types() -> list:
    """Retorna lista de tipos de memo disponíveis."""
    return ["searchfund", "gestora", "primario", "secundario"]


def get_sections_for_type(memo_type: str) -> list:
    """Retorna lista de seções disponíveis para um tipo de memo."""
    sections_by_type = {
        "searchfund": ["intro", "company", "market", "financials", "transaction", "projections", "risks"],
        "gestora": ["intro", "track_record", "team", "strategy", "terms", "risks"],
        "primario": ["intro", "company", "market", "financials", "founders", "transaction", "projections", "risks"],
        "secundario": ["intro", "seller_context", "portfolio", "valuation", "returns", "structure", "gp_analysis", "risks"],
    }
    
    return sections_by_type.get(memo_type, [])


__all__ = [
    "searchfund",
    "gestora",
    "primario",
    "secundario",
    "generate_section",
    "generate_full_memo",
    "get_available_types",
    "get_sections_for_type",
]
