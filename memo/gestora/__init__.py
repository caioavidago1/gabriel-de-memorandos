"""
Memo Completo Gestora

Módulo para geração de memos completos (~20 páginas) de análise de gestora.
Versão expandida com 5-8 parágrafos por seção.
"""

from .generator import (
    generate_section,
    generate_intro_section,
    generate_track_record_section,
    generate_team_section,
    generate_strategy_section,
    generate_terms_section,
    generate_risks_section,
)

from .validator import (
    fix_number_formatting,
    validate_section_length,
    validate_memo_consistency,
    validate_track_record_coherence,
    validate_terms_coherence,
    validate_complete_memo,
    format_validation_report,
)

__all__ = [
    "generate_section",
    "generate_intro_section",
    "generate_track_record_section",
    "generate_team_section",
    "generate_strategy_section",
    "generate_terms_section",
    "generate_risks_section",
    "fix_number_formatting",
    "validate_section_length",
    "validate_memo_consistency",
    "validate_track_record_coherence",
    "validate_terms_coherence",
    "validate_complete_memo",
    "format_validation_report",
]
