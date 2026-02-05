"""
Geração de seções para Memo Completo Search Fund

Router principal e re-exports das funções de geração dos agentes.
Versão expandida (~20 páginas) com 5-8 parágrafos por seção.

DIFERENÇA VS SHORT MEMO:
- Short Memo: 2-4 parágrafos (triagem rápida)
- Memo Completo: 5-8 parágrafos (análise profunda para IC)

FOCO: Due diligence completa, análise de riscos detalhada, plano pós-aquisição

ARQUITETURA:
- Funções de geração individuais estão em memo/searchfund/agents/
- Este arquivo funciona como router e re-exporta as funções
"""

from typing import Dict, Any, Optional

# Re-exportar todas as funções de geração dos agentes
from .agents import (
    generate_intro_section,
    generate_company_section,
    generate_market_section,
    generate_financials_section,
    generate_transaction_section,
    generate_gestor_section,
    generate_projections_section,
    generate_retornos_esperados_section,
    generate_board_cap_table_section,
    generate_conclusao_section,
    generate_risks_section,
)


# ============================================================================
# ROUTER PRINCIPAL
# ============================================================================

def generate_section(
    section_name: str,
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Router principal para gerar qualquer seção de Memo Completo Search Fund.
    
    Args:
        section_name: Nome da seção
        facts: Facts estruturados
        rag_context: Contexto RAG opcional
        model: Modelo OpenAI
        temperature: Criatividade
    
    Returns:
        Texto gerado (5-8 parágrafos)
    """
    section_map = {
        "intro": generate_intro_section,
        "introduction": generate_intro_section,
        "introducao": generate_intro_section,
        "overview": generate_intro_section,  # Alias para overview
        "company": generate_company_section,
        "empresa": generate_company_section,
        "market": generate_market_section,
        "mercado": generate_market_section,
        "financials": generate_financials_section,
        "financeiro": generate_financials_section,
        "historico_financeiro": generate_financials_section,
        "transaction": generate_transaction_section,
        "transacao": generate_transaction_section,
        "estrutura": generate_transaction_section,
        "projections": generate_projections_section,
        "projecoes": generate_projections_section,
        "projecoes_financeiras": generate_projections_section,
        "saida": generate_projections_section,
        "retornos_esperados": generate_retornos_esperados_section,
        "retornos": generate_retornos_esperados_section,
        "gestor": generate_gestor_section,
        "searcher": generate_gestor_section,  # Alias
        "board_cap_table": generate_board_cap_table_section,
        "board": generate_board_cap_table_section,
        "cap_table": generate_board_cap_table_section,
        "conclusao": generate_conclusao_section,
        "conclusão": generate_conclusao_section,
        "risks": generate_risks_section,
        "riscos": generate_risks_section,
    }
    
    section_key = section_name.lower().replace("1. ", "").replace("2. ", "").replace("3. ", "").replace(" ", "_")
    
    if section_key not in section_map:
        raise ValueError(f"Seção '{section_name}' não implementada. Disponíveis: {list(section_map.keys())}")
    
    generator_func = section_map[section_key]
    return generator_func(facts, rag_context, model, temperature)
