"""
Módulo para geração de tabelas DRE (Demonstração do Resultado do Exercício).

Este módulo permite criar tabelas DRE simples com histórico e projeções,
baseadas em inputs do usuário (ano referência, 1º ano histórico, último ano de projeção).
"""

from tipo_memorando.tabela.dre_table import DRETableGenerator, DRELineItem
from tipo_memorando.tabela.ui import render_dre_table_inputs, fill_dre_table_from_documents
from tipo_memorando.tabela.extractor import extract_dre_values
from tipo_memorando.tabela.calculos import calcular_todos_valores_calculados
from tipo_memorando.tabela.extraction_agent import DRETableExtractionAgent
from tipo_memorando.tabela.dre_extraction_schema import DREValuesByYear, DRETableExtractionResult

__all__ = [
    "DRETableGenerator",
    "DRELineItem",
    "render_dre_table_inputs",
    "fill_dre_table_from_documents",
    "extract_dre_values",
    "calcular_todos_valores_calculados",
    "DRETableExtractionAgent",
    "DREValuesByYear",
    "DRETableExtractionResult",
]
