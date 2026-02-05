"""
Config de fatos para Short Memo - Primário.
"""

from tipo_memorando._base.fatos.config import (
    FIELD_VISIBILITY as _FIELD_VISIBILITY,
    get_sections_for_memo_type as _get_sections,
    get_relevant_fields_for_memo_type as _get_relevant,
    get_field_count_for_memo_type as _get_field_count,
)

SECTIONS = [
    "gestora",
    "fundo",
    "estrategia",
    "spectra_context",
    "opinioes",
]

MEMO_TYPE = "Short Memo - Primário"
FIELD_VISIBILITY = _FIELD_VISIBILITY


def get_sections_for_memo_type(memo_type: str) -> list:
    if memo_type == MEMO_TYPE:
        return SECTIONS
    return _get_sections(memo_type)


def get_relevant_fields_for_memo_type(memo_type: str) -> dict:
    return _get_relevant(memo_type)


def get_field_count_for_memo_type(memo_type: str) -> dict:
    return _get_field_count(memo_type)
