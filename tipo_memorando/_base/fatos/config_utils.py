"""
Utilitários puros para config de fatos.

Permite que cada tipo de memorando (short_gestora, short_searchfund, etc.)
tenha seu próprio FIELD_VISIBILITY e SECTIONS sem depender de um config
central. Use estes helpers para implementar get_relevant_fields_for_memo_type
e get_field_count_for_memo_type no config de cada tipo.
"""

from typing import Dict, List, Any


def get_relevant_fields_from_visibility(
    field_visibility: Dict[str, Dict[str, Any]],
    memo_type: str,
) -> Dict[str, List[str]]:
    """
    Dado um FIELD_VISIBILITY e memo_type, retorna {section: [field_keys]}.
    Inclui campo se visibility for "ALL" ou se memo_type estiver na lista.
    """
    relevant_fields = {}
    for section, fields in field_visibility.items():
        relevant_fields[section] = []
        for field_key, visibility_config in fields.items():
            if visibility_config == "ALL":
                relevant_fields[section].append(field_key)
            elif isinstance(visibility_config, list) and memo_type in visibility_config:
                relevant_fields[section].append(field_key)
    return {k: v for k, v in relevant_fields.items() if v}


def get_field_count_from_relevant(relevant_fields: Dict[str, List[str]]) -> Dict[str, Any]:
    """Dado o retorno de get_relevant_fields_*, retorna total e by_section."""
    by_section = {section: len(fields) for section, fields in relevant_fields.items()}
    return {
        "total": sum(by_section.values()),
        "by_section": by_section,
    }
