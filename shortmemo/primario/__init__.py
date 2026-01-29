"""
Short Memo Primário (Gestora) - Módulo de Geração

Análise de oportunidades de investimento primário em fundos de PE/VC.

COMPONENTES:
- orchestrator: Coordenação de agentes (FIXED_STRUCTURE)
- Agentes: IntroAgent, GestoraAgent, PortfolioAgent, FundoAtualAgent
- templates: Templates estruturados com exemplos
- validator: Validação de consistência e formatação
- facts_builder: Formatação de facts estruturados
- utils: Multi-moeda e helpers

USO:
    from shortmemo.primario.orchestrator import generate_full_memo
    
    memo_sections = generate_full_memo(
        facts=facts_dict,
        rag_context="contexto do documento..."
    )
"""

from .orchestrator import (
    generate_full_memo,
    FIXED_STRUCTURE,
)

from .validator import (
    validate_memo_consistency,
    fix_number_formatting,
    check_section_length,
)

# Importar do módulo centralizado facts
from facts.builder import (
    build_facts_section,
    format_facts_for_prompt,
    clean_facts,
)
from facts.utils import get_fact_value

from .utils import (
    get_currency_symbol,
    get_currency_label,
    format_currency_value,
    format_multiple,
    format_percentage,
)

from typing import Dict, Any, Optional

from .intro_agent import IntroAgent
from .gestora_agent import GestoraAgent
from .portfolio_agent import PortfolioAgent
from .fundo_atual_agent import FundoAtualAgent


def generate_section(
    section_name: str,
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera uma seção do Short Memo Primário (compatibilidade com router unificado).
    
    Args:
        section_name: Nome da seção (mapeado para agentes da FIXED_STRUCTURE)
        facts: Facts estruturados
        rag_context: Contexto RAG opcional
        model: Modelo OpenAI
        temperature: Criatividade
    
    Returns:
        Texto da seção gerada
    
    Note:
        Esta função mantém compatibilidade com shortmemo/__init__.py router.
        Para geração completa, use generate_full_memo() do orchestrator.
    """
    # Mapear nomes de seção para classes de agentes
    section_map = {
        "intro": IntroAgent,
        "introduction": IntroAgent,
        "introducao": IntroAgent,
        "resumo": IntroAgent,
        "gestora": GestoraAgent,
        "portfolio": PortfolioAgent,
        "portfólio": PortfolioAgent,
        "fundo": FundoAtualAgent,
        "fundo_atual": FundoAtualAgent,
    }
    
    # Normalizar nome da seção
    section_key = section_name.lower().replace("1. ", "").replace("2. ", "").replace("3. ", "").replace("4. ", "").replace(" ", "_")
    
    # Tentar mapeamento direto primeiro
    agent_class = section_map.get(section_key)
    
    # Se não encontrou, tentar busca parcial
    if not agent_class:
        for key, mapped_class in section_map.items():
            if key in section_key or section_key in key:
                agent_class = mapped_class
                break
    
    if not agent_class:
        raise ValueError(
            f"Seção '{section_name}' não reconhecida. "
            f"Disponíveis: {list(section_map.keys())}"
        )
    
    # Instanciar agente com model e temperature
    agent = agent_class(model=model, temperature=temperature)
    return agent.generate(facts, rag_context)


__all__ = [
    # Generators principais
    "generate_full_memo",
    "FIXED_STRUCTURE",
    
    # Validação
    "validate_memo_consistency",
    "fix_number_formatting",
    "check_section_length",
    
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
    
    # Agentes
    "IntroAgent",
    "GestoraAgent",
    "PortfolioAgent",
    "FundoAtualAgent",
    
    # Compatibilidade router
    "generate_section",
]
