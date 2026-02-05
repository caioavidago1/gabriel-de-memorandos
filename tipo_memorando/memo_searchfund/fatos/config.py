"""
Config de fatos para Memorando - Co-investimento (Search Fund).
"""

from tipo_memorando._base.fatos.config import (
    FIELD_VISIBILITY as _FIELD_VISIBILITY,
    get_sections_for_memo_type as _get_sections,
    get_relevant_fields_for_memo_type as _get_relevant,
    get_field_count_for_memo_type as _get_field_count,
)

SECTIONS = [
    "identification",
    "gestor",
    "transaction_structure",
    "financials_history",
    "projections_table",
    "returns_table",
    "board_cap_table",
    "qualitative",
    "opinioes",
]

MEMO_TYPE = "Memorando - Co-investimento (Search Fund)"
FIELD_VISIBILITY = _FIELD_VISIBILITY


def get_sections_for_memo_type(memo_type: str) -> list:
    if memo_type == MEMO_TYPE:
        return SECTIONS
    return _get_sections(memo_type)


def get_relevant_fields_for_memo_type(memo_type: str) -> dict:
    return _get_relevant(memo_type)


def get_field_count_for_memo_type(memo_type: str) -> dict:
    return _get_field_count(memo_type)
