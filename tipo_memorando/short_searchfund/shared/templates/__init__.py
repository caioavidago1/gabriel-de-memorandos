"""
Templates estruturados para Short Memo - Co-investimento (Search Fund)

Este módulo fornece templates padronizados para cada seção do memo,
incluindo estrutura, tom, exemplos e guidelines de escrita extraídos
de Short Memos reais de Search Fund.
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
