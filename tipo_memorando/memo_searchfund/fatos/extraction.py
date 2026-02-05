"""
Lógica completa de extração de fatos para Memorando - Co-investimento (Search Fund).
"""

import logging
from pathlib import Path

from tipo_memorando._base.fatos.extraction_utils import get_base_system_message

logger = logging.getLogger(__name__)

_SEARCH_FUND_IDENTIFICATION = """

ATENÇÃO CRÍTICA PARA SEARCH FUND (seção identification):
- searcher_name: É OBRIGATÓRIO extrair se mencionado. Procure por:
  * "search liderado por [NOME]"
  * "searcher [NOME]"
  * "empreendedor [NOME]"
  * Nomes próprios seguidos de "search" ou "busca"
  * Pode ser múltiplos nomes (ex: "Fernando Ponce e Eduardo Haro")
- search_start_date: É OBRIGATÓRIO extrair se mencionado. Procure por:
  * "iniciou o search em", "busca iniciada em", "período de busca"
  * Formatos: "1S2023", "Janeiro 2023", "2023", "1º semestre 2023"
- investor_nationality: É OBRIGATÓRIO extrair se mencionado. Procure por:
  * "brasileiro", "mexicano", "americano", "nacionalidade", "origem"

NÃO DEIXE DE EXTRAIR esses campos se estiverem no documento!"""

_GESTOR_SEARCHER = """

ATENÇÃO CRÍTICA PARA GESTOR/SEARCHER (seção gestor):
- searcher_name: Nome(s) completo(s) do(s) searcher(s) - pode ser múltiplos separados por vírgula
- searcher_background: Formação acadêmica completa e histórico profissional detalhado
- searcher_experience: Anos de experiência, empresas anteriores, cargos ocupados
- searcher_assessment: Resultados de assessment psicológico se mencionado (perfil, características)
- searcher_complementarity: Como os searchers se complementam (se dupla), divisão de papéis
- searcher_references: Referências obtidas (ex-empregadores, mentores, validadores)
- searcher_track_record: Histórico de deals anteriores, experiências em M&A (se aplicável)

PROCURE POR:
- Seções como "2. Gestor", "Gestor", "Searchers", "Equipe"
- Texto sobre formação, experiência, assessment
- Comparações com outros searchers conhecidos
- Validações e referências"""

_BOARD_CAP_TABLE = """

ATENÇÃO CRÍTICA PARA BOARD E CAP TABLE (seção board_cap_table):
- Procure por seções sobre composição do board e estrutura de investidores
- board_members: Lista de membros do board com nome, role, background, indication_source
- cap_table: Lista de investidores com nome, tipo, contribution, percentual, país
- governance_structure: Direitos de veto, tag-along, drag-along, composição do board
- board_commentary: Comentários sobre qualidade do board e cap table

FORMATO ESPERADO:
board_members: [
  {"name": "João Lima", "role": "Board Member", "background": "...", "indication_source": "Voke"},
  ...
]
cap_table: [
  {"investor_name": "Spectra", "investor_type": "Search Investor", "contribution_mm": 20.0, "contribution_pct": 22.0, "country": "Brazil"},
  ...
]

PROCURE POR:
- Seções como "Board e Cap Table", "Board", "Composição do Board"
- Tabelas de investidores
- Listas de membros do board com backgrounds"""

_PROJECTIONS_TABLE = """

ATENÇÃO CRÍTICA PARA PROJEÇÕES (seção projections_table):
- Procure por TABELAS de projeções financeiras no documento
- Extraia dados ano a ano para cada cenário (base, upside, downside)
- Cada linha da tabela deve ter: year, revenue_mm, ebitda_mm, ebitda_margin_pct
- Se houver múltiplas tabelas, identifique qual é qual cenário pelo contexto (título, texto próximo)
- projections_years: Lista de todos os anos projetados
- projections_assumptions: Premissas detalhadas mencionadas para cada cenário

FORMATO ESPERADO:
projections_base_case: [
  {"year": 2024, "revenue_mm": 100.0, "ebitda_mm": 35.0, "ebitda_margin_pct": 35.0},
  {"year": 2025, "revenue_mm": 120.0, "ebitda_mm": 45.0, "ebitda_margin_pct": 37.5},
  ...
]"""

_RETURNS_TABLE = """

ATENÇÃO CRÍTICA PARA RETORNOS (seção returns_table):
- Procure por TABELAS de retornos (IRR/MOIC) no documento
- Extraia retornos para cada cenário (base, upside, downside)
- Se houver tabela de sensibilidade, extraia múltiplos cenários variando múltiplo de saída ou ano
- returns_base_case: {irr_pct: float, moic: float, exit_year: int, exit_multiple: float}
- returns_sensitivity_table: Lista de cenários com diferentes combinações de múltiplo/ano

FORMATO ESPERADO:
returns_base_case: {"irr_pct": 39.8, "moic": 5.3, "exit_year": 2028, "exit_multiple": 6.0}
returns_sensitivity_table: [
  {"exit_year": 2028, "exit_multiple": 5.5, "irr_pct": 36.7, "moic": 4.8},
  {"exit_year": 2028, "exit_multiple": 6.0, "irr_pct": 39.8, "moic": 5.3},
  ...
]"""


def get_system_message(section: str, memo_type: str) -> str:
    """Retorna o system message completo para esta seção."""
    base = get_base_system_message(section)
    if section == "identification":
        return base + _SEARCH_FUND_IDENTIFICATION
    if section in ("gestor", "searcher"):
        return base + _GESTOR_SEARCHER
    if section == "board_cap_table":
        return base + _BOARD_CAP_TABLE
    if section == "projections_table":
        return base + _PROJECTIONS_TABLE
    if section == "returns_table":
        return base + _RETURNS_TABLE
    return base


def get_prompt(section: str, memo_type: str) -> str:
    """Retorna o texto completo do prompt (lê fatos/prompts/<section>.txt)."""
    prompt_dir = Path(__file__).resolve().parent / "prompts"
    prompt_path = prompt_dir / f"{section}.txt"
    try:
        return prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("Prompt não encontrado: %s", prompt_path)
        return f"Extraia informações relevantes para a seção {section}."


def get_schema(section: str):
    """Retorna None para usar os schemas do core."""
    return None
