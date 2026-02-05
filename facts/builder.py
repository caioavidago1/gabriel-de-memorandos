"""
Builder centralizado para construção e formatação de facts

Formata facts estruturados em texto legível para uso em prompts e geração de texto.
Consolida funcionalidades duplicadas dos builders específicos de cada tipo de memo.
"""

from typing import Dict, Any, Optional, Union


def build_facts_section(
    facts: Dict[str, Any],
    section_name: str,
    field_labels: Union[Dict[str, str], list]
) -> str:
    """
    Constrói seção formatada de facts omitindo campos vazios.
    
    Args:
        facts: Dict completo de facts estruturados
        section_name: Nome da seção (ex: "identification", "transaction_structure", "gestora")
        field_labels: Dict de {field_key: label} OU lista de field_keys
                     Ex: {"company_name": "Nome da empresa"} ou ["field1", "field2"]
    
    Returns:
        String formatada com facts não vazios
        Retorna string vazia se a seção não existir ou estiver vazia
    
    Examples:
        >>> facts = {"identification": {"company_name": "TSE", "investor_name": "Minerva"}}
        >>> labels = {"company_name": "Empresa", "investor_name": "Investidor"}
        >>> build_facts_section(facts, "identification", labels)
        '- Empresa: TSE\\n- Investidor: Minerva'
        
        >>> build_facts_section(facts, "identification", ["company_name", "investor_name"])
        '- company_name: TSE\\n- investor_name: Minerva'
    """
    section_data = facts.get(section_name, {})
    
    if not section_data:
        return ""
    
    # Determinar se é lista ou dict
    if isinstance(field_labels, dict):
        # Dict de labels
        field_config = field_labels
    else:
        # Lista de keys - criar labels iguais às keys
        field_config = {key: key for key in field_labels}
    
    lines = []
    for field_key, label in field_config.items():
        value = section_data.get(field_key)
        
        # Omitir valores vazios/None
        if value is None or value == "" or value == [] or value == {}:
            continue
        
        # Formatar listas
        if isinstance(value, list):
            if len(value) == 0:
                continue
            value_str = ", ".join(str(v) for v in value)
        # Formatar dicts
        elif isinstance(value, dict):
            if len(value) == 0:
                continue
            value_str = "; ".join(f"{k}: {v}" for k, v in value.items())
        # Valores simples
        else:
            value_str = str(value)
        
        lines.append(f"- {label}: {value_str}")
    
    return "\n".join(lines) if lines else ""


def format_facts_for_prompt(
    facts: Dict[str, Any],
    section_configs: Dict[str, Dict[str, str]],
    section_titles: Optional[Dict[str, str]] = None
) -> str:
    """
    Formata múltiplas seções de facts para inclusão em prompt.
    
    Args:
        facts: Dict completo de facts
        section_configs: Dict de {section_name: {field_key: label}}
        section_titles: Dict opcional de {section_name: title} para personalizar títulos
                       Se não fornecido, usa títulos padrão ou o nome da seção em uppercase
    
    Returns:
        String formatada com todas as seções não vazias
    
    Examples:
        >>> facts = {
        ...     "identification": {"company_name": "TSE"},
        ...     "transaction_structure": {"ev_mm": 138}
        ... }
        >>> configs = {
        ...     "identification": {"company_name": "Empresa"},
        ...     "transaction_structure": {"ev_mm": "EV (R$ MM)"}
        ... }
        >>> format_facts_for_prompt(facts, configs)
        'IDENTIFICAÇÃO:\\n- Empresa: TSE\\n\\nTRANSAÇÃO:\\n- EV (R$ MM): 138'
    """
    # Títulos padrão para seções comuns
    default_titles = {
        "identification": "IDENTIFICAÇÃO",
        "transaction_structure": "TRANSAÇÃO",
        "financials_history": "FINANCIALS HISTÓRICO",
        "projections": "PROJEÇÕES (SAÍDA)",
        "saida": "SAÍDA",
        "returns": "RETORNOS",
        "qualitative": "ASPECTOS QUALITATIVOS",
        "opinioes": "OPINIÕES",
        "gestora": "GESTORA",
        "fundo": "FUNDO",
        "estrategia": "ESTRATÉGIA",
        "estrategia_fundo": "ESTRATÉGIA",
        "spectra_context": "CONTEXTO SPECTRA",
    }
    
    # Usar títulos fornecidos ou padrão
    if section_titles is None:
        section_titles = {}
    
    # Combinar títulos padrão com customizados
    titles = {**default_titles, **section_titles}
    
    sections = []
    for section_name, field_labels in section_configs.items():
        section_text = build_facts_section(facts, section_name, field_labels)
        
        if section_text:
            title = titles.get(section_name, section_name.upper())
            sections.append(f"{title}:\n{section_text}")
    
    return "\n\n".join(sections)


def clean_facts(facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove todos os campos None/vazios de um dict de facts recursivamente.
    
    Args:
        facts: Dict de facts (pode ter estrutura aninhada)
    
    Returns:
        Dict limpo sem campos vazios
    
    Examples:
        >>> clean_facts({"a": 1, "b": None, "c": {"d": 2, "e": None}})
        {'a': 1, 'c': {'d': 2}}
    """
    if not isinstance(facts, dict):
        return facts
    
    cleaned = {}
    for key, value in facts.items():
        # Pular valores vazios/None
        if value is None or value == "" or value == [] or value == {}:
            continue
        
        # Limpar recursivamente dicts aninhados
        if isinstance(value, dict):
            cleaned_nested = clean_facts(value)
            if cleaned_nested:  # Só incluir se não ficou vazio
                cleaned[key] = cleaned_nested
        else:
            cleaned[key] = value
    
    return cleaned
