"""
Utilitários para filtragem de facts

Remove facts desabilitados e valida valores antes de usar em agentes de geração.
"""

from typing import Dict, Any, Set


def filter_disabled_facts(facts: Dict[str, Any], disabled_facts: Set[str]) -> Dict[str, Any]:
    """
    Remove facts desabilitados antes de passar para agentes.
    Isso evita que a IA tente inferir valores ausentes.
    
    Args:
        facts: Dict com facts estruturados {section: {field_key: value}}
        disabled_facts: Set de field_ids desabilitados (formato: "section.field_key")
    
    Returns:
        Dict com facts filtrados (sem campos desabilitados)
    
    Examples:
        >>> facts = {"identification": {"company_name": "TSE", "investor_name": "Minerva"}}
        >>> disabled = {"identification.investor_name"}
        >>> filter_disabled_facts(facts, disabled)
        {'identification': {'company_name': 'TSE'}}
    """
    filtered = {}
    
    for section, section_facts in facts.items():
        filtered[section] = {}
        
        for field_key, field_value in section_facts.items():
            field_id = f"{section}.{field_key}"
            
            # Só incluir se:
            # 1. NÃO estiver desabilitado
            # 2. Tiver valor válido (não None, não string vazia, não "null")
            if field_id not in disabled_facts:
                # Validar que o valor não é vazio/nulo
                if field_value not in (None, "", "null", "N/A", "n/a", "None"):
                    # Se for string, verificar se não é só espaços em branco
                    if isinstance(field_value, str):
                        if field_value.strip():
                            filtered[section][field_key] = field_value
                    else:
                        # Números e outros tipos sempre incluir
                        filtered[section][field_key] = field_value
    
    return filtered
