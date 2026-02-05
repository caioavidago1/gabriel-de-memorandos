"""
Short Memo Gestora - Módulo de Geração

Arquitetura de agentes especializados para análise de Co-investimentos apresentados por Gestoras.

COMPONENTES:
- orchestrator: Coordenação de agentes (FIXED_STRUCTURE)
- Agentes: IntroAgent, MercadoAgent, EmpresaAgent, FinancialsAgent, TransacaoAgent, PontosAprofundarAgent
- validator: Validação de consistência e formatação

USO:
    from tipo_memorando.short_gestora.orchestrator import generate_full_memo
    
    memo_sections = generate_full_memo(
        facts=facts_dict,
        memo_id="memo_id",
        processor=processor
    )
"""

from .orchestrator import (
    generate_full_memo,
    FIXED_STRUCTURE,
)

from .validator import (
    validate_memo_consistency,
    fix_number_formatting,
    check_section_length,
    validate_gestora_intro,
)

# Exportar agentes
from .agents import (
    IntroAgent,
    MercadoAgent,
    EmpresaAgent,
    FinancialsAgent,
    TransacaoAgent,
    PontosAprofundarAgent,
)

__all__ = [
    # Generators
    "generate_full_memo",
    "FIXED_STRUCTURE",
    # Agents
    "IntroAgent",
    "MercadoAgent",
    "EmpresaAgent",
    "FinancialsAgent",
    "TransacaoAgent",
    "PontosAprofundarAgent",
    # Validators
    "validate_memo_consistency",
    "fix_number_formatting",
    "check_section_length",
    "validate_gestora_intro",
]
