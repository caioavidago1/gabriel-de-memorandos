"""
Lógica completa de extração de fatos para Short Memo - Co-investimento (Gestora).
"""

import logging
from pathlib import Path

from tipo_memorando._base.fatos.extraction_utils import get_base_system_message

from .config import MEMO_TYPE
from core.extraction_schemas import SaidaShortMemoFacts

logger = logging.getLogger(__name__)


def get_system_message(section: str, memo_type: str) -> str:
    """Retorna o system message completo para esta seção."""
    return get_base_system_message(section)


def get_prompt(section: str, memo_type: str) -> str:
    """Retorna o texto completo do prompt (lê fatos/prompts/<section>.txt)."""
    prompt_dir = Path(__file__).resolve().parent / "prompts"
    prompt_path = prompt_dir / f"{section}.txt"
    try:
        return prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("Prompt não encontrado: %s", prompt_path)
        return f"Extraia informações relevantes para a seção {section}."


def get_schema(section: str, memo_type: str):
    """Retorna SaidaShortMemoFacts para saida (cenários base/alternativo/conservador); None para o resto."""
    if section == "saida" and memo_type == MEMO_TYPE:
        return SaidaShortMemoFacts
    return None
