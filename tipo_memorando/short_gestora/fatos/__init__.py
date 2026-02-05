"""Fatos para Short Memo - Co-investimento (Gestora). Apenas as 6 abas: Identificação, Gestora, Transação, Saída, Estrutura do Veículo, Opinião do Analista."""

from tipo_memorando.short_gestora.fatos import extraction
from tipo_memorando.short_gestora.fatos.identificacao import render_tab_identification
from tipo_memorando.short_gestora.fatos.gestora import render_tab_gestora
from tipo_memorando.short_gestora.fatos.transacao import render_tab_transaction
from tipo_memorando.short_gestora.fatos.saida import render_tab_saida
from tipo_memorando.short_gestora.fatos.estrutura_veiculo import render_tab_estrutura_veiculo
from tipo_memorando.short_gestora.fatos.opinioes import render_tab_opinioes

__all__ = [
    "extraction",
    "render_tab_identification",
    "render_tab_gestora",
    "render_tab_transaction",
    "render_tab_saida",
    "render_tab_estrutura_veiculo",
    "render_tab_opinioes",
]
