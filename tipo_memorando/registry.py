"""
Registry de tipos de memorando.

Mapeia memo_type (string da UI) para pasta tipo_memorando e fornece
funções para carregar config, prompts e verificar uso de DRE.
"""

from pathlib import Path
from typing import Optional
import importlib.util

# Mapeamento memo_type (UI) -> nome da pasta em tipo_memorando
MEMO_TYPE_TO_TIPO = {
    "Short Memo - Co-investimento (Search Fund)": "short_searchfund",
    "Short Memo - Co-investimento (Gestora)": "short_gestora",
    "Short Memo - Primário": "short_primario",
    "Memorando - Co-investimento (Search Fund)": "memo_searchfund",
}

# Tipos que usam a feature Histórico e Projeções (DRE)
_DRE_MEMO_TYPES = frozenset({
    "Short Memo - Co-investimento (Search Fund)",
    "Short Memo - Co-investimento (Gestora)",
    "Memorando - Co-investimento (Search Fund)",
})


def get_tipo(memo_type: str) -> Optional[str]:
    """Retorna o nome da pasta tipo_memorando para o memo_type, ou None se não mapeado."""
    return MEMO_TYPE_TO_TIPO.get(memo_type)


def uses_dre_table(memo_type: str) -> bool:
    """
    Retorna True se o tipo de memorando usa a feature Histórico e Projeções (DRE).

    DRE é usado apenas para: Short Memo Search Fund, Short Memo Gestora, Memorando Search Fund.
    """
    return memo_type in _DRE_MEMO_TYPES


def get_fatos_config(memo_type: str):
    """
    Carrega e retorna o módulo config do tipo correspondente ao memo_type.

    Importa tipo_memorando.<tipo>.fatos.config.
    """
    tipo = get_tipo(memo_type)
    if not tipo:
        raise ValueError(f"memo_type não mapeado: {memo_type!r}")
    return importlib.import_module(f"tipo_memorando.{tipo}.fatos.config")


def get_prompts_path(memo_type: str, section: str) -> Path:
    """
    Retorna o path para o arquivo de prompt da seção no tipo correspondente.

    Path: tipo_memorando/<tipo>/fatos/prompts/<section>.txt
    """
    tipo = get_tipo(memo_type)
    if not tipo:
        raise ValueError(f"memo_type não mapeado: {memo_type!r}")
    base = Path(__file__).resolve().parent
    return base / tipo / "fatos" / "prompts" / f"{section}.txt"


def get_fatos_module(memo_type: str):
    """
    Retorna o módulo fatos do tipo correspondente ao memo_type.

    Usado por app.py para obter render_tab_* e outras funções de UI.
    """
    tipo = get_tipo(memo_type)
    if not tipo:
        raise ValueError(f"memo_type não mapeado: {memo_type!r}")
    return importlib.import_module(f"tipo_memorando.{tipo}.fatos")
