"""Fatos para Short Memo - Primário."""

from tipo_memorando.short_primario.fatos import extraction
from tipo_memorando.short_primario.fatos.gestora import render_tab_gestora
from tipo_memorando.short_primario.fatos.fundo import render_tab_fundo
from tipo_memorando.short_primario.fatos.estrategia_fundo import render_tab_estrategia_fundo
from tipo_memorando.short_primario.fatos.spectra_context import render_tab_spectra_context
from tipo_memorando.short_primario.fatos.opinioes import render_tab_opinioes

__all__ = [
    "extraction",
    "render_tab_gestora",
    "render_tab_fundo",
    "render_tab_estrategia_fundo",
    "render_tab_spectra_context",
    "render_tab_opinioes",
]
