"""
Short Memos - Módulos especializados por tipo

TIPOS DISPONÍVEIS:
- searchfund: Short Memo para aquisições via Search Fund
- gestora: Short Memo para análise de Gestoras de PE/VC
- primario: Short Memo para growth equity (SaaS, tech)
- secundario: Short Memo para empresas maduras (cash yield)

USO:
    # Search Fund
    from shortmemo.searchfund import generate_section as generate_searchfund
    text = generate_searchfund("intro", facts, rag_context)
    
    # Gestora
    from shortmemo.gestora import generate_section as generate_gestora
    text = generate_gestora("intro", facts, rag_context)
    
    # Primário
    from shortmemo.primario import generate_section as generate_primario
    text = generate_primario("intro", facts, rag_context)
    
    # Secundário
    from shortmemo.secundario import generate_section as generate_secundario
    text = generate_secundario("intro", facts, rag_context)

ROUTER UNIFICADO:
    from shortmemo import generate_shortmemo_section
    
    text = generate_shortmemo_section(
        memo_type="Search Fund",  # ou "Gestora", "Primário", "Secundário"
        section_name="intro",
        facts=facts_dict,
        rag_context="contexto..."
    )
"""

from typing import Dict, Any, Optional


def generate_shortmemo_section(
    memo_type: str,
    section_name: str,
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Router unificado para geração de seções de Short Memo.
    
    Args:
        memo_type: Tipo do memo ("Search Fund", "Gestora", "Primário", "Secundário")
        section_name: Nome da seção ("intro", "company", "market", etc.)
        facts: Facts estruturados
        rag_context: Contexto RAG opcional
        model: Modelo OpenAI
        temperature: Criatividade
    
    Returns:
        Texto gerado
    
    Raises:
        ValueError: Se tipo de memo não reconhecido
    """
    memo_type_lower = memo_type.lower()
    
    if "search" in memo_type_lower:
        from .searchfund import generate_section
    elif "gestora" in memo_type_lower:
        from .gestora import generate_section
    elif "primario" in memo_type_lower or "primário" in memo_type_lower:
        from .primario import generate_section
    elif "secundario" in memo_type_lower or "secundário" in memo_type_lower:
        from .secundario import generate_section
    else:
        raise ValueError(
            f"Tipo de memo '{memo_type}' não reconhecido. "
            "Use: 'Search Fund', 'Gestora', 'Primário', 'Secundário'"
        )
    
    return generate_section(
        section_name=section_name,
        facts=facts,
        rag_context=rag_context,
        model=model,
        temperature=temperature
    )


__all__ = [
    "generate_shortmemo_section",
]
