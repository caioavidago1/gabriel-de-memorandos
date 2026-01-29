"""
Templates estruturados para Short Memo - Primário (Gestora)

Este módulo fornece templates padronizados para cada seção do memo,
incluindo estrutura, tom, exemplos e guidelines de escrita extraídos
de Short Memos reais de investimento primário em fundos.
"""

from .template_loader import (
    TemplateLoader,
    SectionTemplate,
    get_template_loader,
    get_template,
    enrich_prompt,
    validate_facts,
    get_global_guidelines
)

__all__ = [
    'TemplateLoader',
    'SectionTemplate',
    'get_template_loader',
    'get_template',
    'enrich_prompt',
    'validate_facts',
    'get_global_guidelines'
]
