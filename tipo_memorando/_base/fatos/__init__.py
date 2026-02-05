"""
Módulo fatos base - builder e utils compartilhados.

Importado pelos tipos de memorando para formatação e manipulação de facts.
"""

from tipo_memorando._base.fatos.builder import (
    build_facts_section,
    format_facts_for_prompt,
    clean_facts,
)
from tipo_memorando._base.fatos.utils import (
    get_fact_safe,
    get_currency_safe,
    get_name_safe,
    get_numeric_safe,
    get_text_safe,
    get_fact_value,
)

__all__ = [
    "build_facts_section",
    "format_facts_for_prompt",
    "clean_facts",
    "get_fact_safe",
    "get_currency_safe",
    "get_name_safe",
    "get_numeric_safe",
    "get_text_safe",
    "get_fact_value",
]
