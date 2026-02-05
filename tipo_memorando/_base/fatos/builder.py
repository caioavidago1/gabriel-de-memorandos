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
    """
    section_data = facts.get(section_name, {})

    if not section_data:
        return ""

    if isinstance(field_labels, dict):
        field_config = field_labels
    else:
        field_config = {key: key for key in field_labels}

    lines = []
    for field_key, label in field_config.items():
        value = section_data.get(field_key)

        if value is None or value == "" or value == [] or value == {}:
            continue

        if isinstance(value, list):
            if len(value) == 0:
                continue
            value_str = ", ".join(str(v) for v in value)
        elif isinstance(value, dict):
            if len(value) == 0:
                continue
            value_str = "; ".join(f"{k}: {v}" for k, v in value.items())
        else:
            value_str = str(value)

        lines.append(f"- {label}: {value_str}")

    return "\n".join(lines) if lines else ""


def format_facts_for_prompt(
    facts: Dict[str, Any],
    section_configs: Dict[str, Dict[str, str]],
    section_titles: Optional[Dict[str, str]] = None
) -> str:
    """Formata múltiplas seções de facts para inclusão em prompt."""
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

    if section_titles is None:
        section_titles = {}
    titles = {**default_titles, **section_titles}

    sections = []
    for section_name, field_labels in section_configs.items():
        section_text = build_facts_section(facts, section_name, field_labels)
        if section_text:
            title = titles.get(section_name, section_name.upper())
            sections.append(f"{title}:\n{section_text}")

    return "\n\n".join(sections)


def clean_facts(facts: Dict[str, Any]) -> Dict[str, Any]:
    """Remove todos os campos None/vazios de um dict de facts recursivamente."""
    if not isinstance(facts, dict):
        return facts

    cleaned = {}
    for key, value in facts.items():
        if value is None or value == "" or value == [] or value == {}:
            continue
        if isinstance(value, dict):
            cleaned_nested = clean_facts(value)
            if cleaned_nested:
                cleaned[key] = cleaned_nested
        else:
            cleaned[key] = value

    return cleaned
