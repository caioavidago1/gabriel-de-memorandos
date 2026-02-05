"""Fatos para Memorando - Co-investimento (Search Fund)."""

from tipo_memorando.memo_searchfund.fatos import extraction
from tipo_memorando.memo_searchfund.fatos.identificacao import render_tab_identification
from tipo_memorando.memo_searchfund.fatos.transacao import render_tab_transaction
from tipo_memorando.memo_searchfund.fatos.saida import render_tab_saida
from tipo_memorando.memo_searchfund.fatos.qualitativo import render_tab_qualitative

__all__ = [
    "extraction",
    "render_tab_identification",
    "render_tab_transaction",
    "render_tab_saida",
    "render_tab_qualitative",
]
