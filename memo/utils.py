"""
Utilitários compartilhados para módulos de memo completo.

NOTA: Few-shot learning agora é centralizado em core/few_shot.py
Este módulo contém apenas utilitários auxiliares.
"""

from typing import Dict, List, Optional, Any


def format_facts_for_prompt(facts: Dict[str, Any]) -> str:
    """
    Formata facts de forma estruturada para uso em prompts.
    
    Args:
        facts: Dicionário com facts estruturados
    
    Returns:
        String formatada
    """
    # Tentar usar build_facts_section se disponível
    try:
        from shortmemo.searchfund.shared import build_facts_section
        return build_facts_section(facts)
    except ImportError:
        pass
    
    # Fallback: formatação simples
    lines = []
    
    def format_dict(d: Dict, indent: int = 0) -> None:
        prefix = "  " * indent
        for key, value in d.items():
            if value is None:
                continue
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                format_dict(value, indent + 1)
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        format_dict(item, indent + 1)
                        lines.append("")
                    else:
                        lines.append(f"{prefix}  - {item}")
            else:
                lines.append(f"{prefix}{key}: {value}")
    
    format_dict(facts)
    return "\n".join(lines)


def get_section_requirements(memo_type: str, section: str) -> Dict[str, Any]:
    """
    Retorna requisitos específicos por tipo de memo e seção.
    
    Args:
        memo_type: Tipo do memo
        section: Nome da seção
    
    Returns:
        Dict com requisitos (min_paragraphs, max_paragraphs, key_elements)
    """
    # Requisitos base para memo completo
    base = {
        "min_paragraphs": 5,
        "max_paragraphs": 8,
        "target_pages": 2,
    }
    
    # Ajustes por seção
    section_adjustments = {
        "intro": {"min_paragraphs": 5, "max_paragraphs": 7, "key_elements": ["sumário executivo", "tese", "recomendação"]},
        "company": {"min_paragraphs": 6, "max_paragraphs": 8, "key_elements": ["histórico", "modelo de negócio", "operações"]},
        "market": {"min_paragraphs": 5, "max_paragraphs": 8, "key_elements": ["TAM/SAM/SOM", "competição", "tendências"]},
        "financials": {"min_paragraphs": 6, "max_paragraphs": 8, "key_elements": ["receita", "EBITDA", "crescimento", "margens"]},
        "transaction": {"min_paragraphs": 5, "max_paragraphs": 7, "key_elements": ["estrutura", "valuation", "termos"]},
        "projections": {"min_paragraphs": 5, "max_paragraphs": 8, "key_elements": ["cenários", "TIR", "múltiplos"]},
        "risks": {"min_paragraphs": 6, "max_paragraphs": 8, "key_elements": ["riscos identificados", "mitigantes"]},
    }
    
    requirements = {**base}
    if section.lower() in section_adjustments:
        requirements.update(section_adjustments[section.lower()])
    
    return requirements


def get_currency_helpers(currency: str = "BRL") -> Dict[str, str]:
    """
    Retorna símbolos e labels para a moeda especificada.
    
    Args:
        currency: Código da moeda (BRL, USD, EUR)
    
    Returns:
        Dict com symbol e label
    """
    currency_map = {
        "BRL": {"symbol": "R$", "label": "R$ milhoes"},
        "USD": {"symbol": "US$", "label": "US$ million"},
        "EUR": {"symbol": "E", "label": "E million"},
    }
    return currency_map.get(currency.upper(), currency_map["BRL"])
