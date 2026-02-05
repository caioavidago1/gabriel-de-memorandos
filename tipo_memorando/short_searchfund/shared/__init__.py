"""
Código compartilhado entre agentes do Search Fund

Contém utilitários, builders, validators e templates usados por todos os agentes.
"""

# Importar do módulo centralizado facts
from facts.builder import (
    build_facts_section,
    format_facts_for_prompt,
    clean_facts,
)
from facts.utils import (
    get_fact_value,
    get_currency_safe,
    get_name_safe,
    get_numeric_safe,
    get_text_safe,
)

from .utils import (
    get_currency_symbol,
    get_currency_label,
    format_currency_value,
    format_multiple,
    format_percentage,
)

from .validator import (
    validate_memo_consistency,
    fix_number_formatting,
    check_section_length,
    validate_search_fund_intro,
)

from .templates import (
    enrich_prompt,
    get_template,
)

__all__ = [
    # Facts builder
    "build_facts_section",
    "format_facts_for_prompt",
    "clean_facts",
    "get_fact_value",
    # Facts utils
    "get_currency_safe",
    "get_name_safe",
    "get_numeric_safe",
    "get_text_safe",
    # Format utils
    "get_currency_symbol",
    "get_currency_label",
    "format_currency_value",
    "format_multiple",
    "format_percentage",
    # Validator
    "validate_memo_consistency",
    "fix_number_formatting",
    "check_section_length",
    "validate_search_fund_intro",
    # Templates
    "enrich_prompt",
    "get_template",
]
