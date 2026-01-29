"""
Agentes para Memo Completo Search Fund

Cada agente é responsável por gerar uma seção específica do memo completo.
"""

from .intro_agent import generate_intro_section
from .empresa_agent import generate_company_section
from .mercado_agent import generate_market_section
from .financials_agent import generate_financials_section
from .transacao_agent import generate_transaction_section
from .gestor_agent import generate_gestor_section
from .projecoes_agent import generate_projections_section
from .retornos_agent import generate_retornos_esperados_section
from .board_cap_table_agent import generate_board_cap_table_section
from .conclusao_agent import generate_conclusao_section
from .risks_agent import generate_risks_section

__all__ = [
    "generate_intro_section",
    "generate_company_section",
    "generate_market_section",
    "generate_financials_section",
    "generate_transaction_section",
    "generate_gestor_section",
    "generate_projections_section",
    "generate_retornos_esperados_section",
    "generate_board_cap_table_section",
    "generate_conclusao_section",
    "generate_risks_section",
]
