"""
Lógica completa de extração de fatos para Short Memo - Co-investimento (Search Fund).
"""

import logging
from pathlib import Path

from tipo_memorando._base.fatos.extraction_utils import get_base_system_message

from .config import MEMO_TYPE
from core.extraction_schemas import SaidaShortMemoFacts

logger = logging.getLogger(__name__)

_SEARCH_FUND_IDENTIFICATION = """

ATENÇÃO CRÍTICA PARA SEARCH FUND (seção identification):
Os campos NÃO costumam ter labels explícitos ("Nome do searcher:", "FIP:"). Extraia a partir de:
- fip_casca: Busque na CAPA, TÍTULO ou INÍCIO do documento. Ex: "Syonet Deal / ATLANTE CAPITAL SEARCH FUND" → fip_casca = "Atlante Capital Search Fund". Nomes em maiúsculas/negrito no início costumam ser a casca.
- searcher_name: Busque "liderado por [NOME]", "searcher [NOME]", ou nomes próprios em seções de apresentação/assinetas. Pode ser implícito (ex: "Daniel" em contexto de busca).
- search_start_date: "período de busca no 2S2024", "iniciou em", "busca iniciada em". Formatos: 1S2023, 2S2024, Janeiro 2024.
- investor_nationality: Inferir de "search fund brasileiro/mexicano/americano" ou contexto de mercado.

NÃO espere frases como "o nome do searcher é X". Extraia do contexto natural e da estrutura do documento."""

_SEARCH_FUND_TRANSACTION = """

ATENÇÃO PARA TRANSAÇÃO (seção transaction_structure):
- total_transaction_value_mm: Procure por "valor total da transação chega a X", "incluindo custos... X", "valor total de X"
- cash_pct_total: Procure por "X% à vista", "estruturados em X% à vista". Se tiver cash e total, calcule: (cash/total)*100
- multiple_total: Procure por "4,9x EBITDA 2024 ou 3,6x EBITDA 2025", "múltiplo total considerando custos"
- investor_opinion: Procure em conclusão, parecer, pontos de atenção, opinião sobre estrutura"""


def get_system_message(section: str, memo_type: str) -> str:
    """Retorna o system message completo para esta seção."""
    base = get_base_system_message(section)
    if section == "identification":
        return base + _SEARCH_FUND_IDENTIFICATION
    if section == "transaction_structure":
        return base + _SEARCH_FUND_TRANSACTION
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


def get_schema(section: str, memo_type: str):
    """Retorna schema específico para saida (Short Memo Search Fund); None para usar core."""
    if section == "saida" and memo_type == MEMO_TYPE:
        return SaidaShortMemoFacts
    return None
