"""
Agente de Transação - Memo Completo Search Fund

Gera a seção "Estrutura da Transação" do memo completo (5-7 parágrafos).
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os

from facts.builder import build_facts_section
from tipo_memorando._base.format_utils import get_currency_symbol, get_currency_label
from ..validator import fix_number_formatting


def generate_transaction_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Estrutura da Transação COMPLETA para Memo Search Fund.
    
    EXTENSÃO: 5-7 parágrafos com análise detalhada da estrutura.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    trx = facts.get("transaction_structure", {})
    currency = trx.get("currency") or "BRL"
    currency_label = get_currency_label(currency)

    transaction_section = build_facts_section(
        facts, "transaction_structure",
        {
            "stake_pct": "Participação (%)",
            "ev_mm": f"EV ({currency_label})",
            "equity_value_mm": f"Equity Value ({currency_label})",
            "multiple_ev_ebitda": "Múltiplo EV/EBITDA",
            "multiple_reference_period": "Período de referência",
            "cash_payment_mm": f"Pagamento à vista ({currency_label})",
            "seller_note_mm": f"Seller note ({currency_label})",
            "seller_note_terms": "Termos seller note",
            "seller_note_interest": "Juros seller note",
            "earnout_mm": f"Earnout ({currency_label})",
            "earnout_conditions": "Condições earnout",
            "earnout_period": "Período earnout",
            "multiple_with_earnout": "Múltiplo c/ earnout",
            "acquisition_debt_mm": f"Dívida de aquisição ({currency_label})",
            "escrow_mm": f"Escrow ({currency_label})",
        }
    )
    
    returns_section = build_facts_section(
        facts, "returns",
        {
            "irr_pct": "IRR alvo (%)",
            "moic": "MOIC alvo (x)",
            "holding_period_years": "Holding period (anos)",
        }
    )

    prompt = f"""
Você é um analista sênior de PE/Search Funds, escrevendo a SEÇÃO ESTRUTURA DA TRANSAÇÃO de um MEMO COMPLETO para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DO DEAL
═══════════════════════════════════════════════════════════════════════

TRANSAÇÃO:
{transaction_section}

RETORNOS:
{returns_section}
"""

    if rag_context:
        prompt += f"""
═══════════════════════════════════════════════════════════════════════
CONTEXTO DO DOCUMENTO
═══════════════════════════════════════════════════════════════════════

{rag_context}
"""

    prompt += """
═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA (5-7 parágrafos - MEMO COMPLETO)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Visão Geral da Transação:
  - Participação adquirida, EV, Equity Value
  - Múltiplo de entrada e período de referência
  - Comparação com transações similares

§ PARÁGRAFO 2 - Estrutura de Pagamento:
  - Pagamento à vista: valor e múltiplo implícito
  - Seller note: valor, prazo, juros, garantias
  - Earnout: valor máximo, condições, período

§ PARÁGRAFO 3 - Análise da Atratividade:
  - Por que a estrutura é favorável (ou não)
  - Alinhamento de incentivos com vendedor
  - Proteções e garantias

§ PARÁGRAFO 4 - Estrutura de Financiamento:
  - Equity vs dívida de aquisição
  - Termos da dívida (se aplicável)
  - Capacidade de debt service

§ PARÁGRAFO 5 - Governança e Direitos:
  - Direitos de veto, tag-along, drag-along
  - Composição do board
  - Papel do vendedor pós-transação

§ PARÁGRAFO 6 - Comparação com Benchmarks:
  - Múltiplo vs deals de Search Fund comparáveis
  - % de seller finance vs médias de mercado
  - Análise de prêmio/desconto

§ PARÁGRAFO 7 - Riscos da Estrutura:
  - Riscos de execução
  - Contingências e cláusulas de ajuste
  - Pontos de negociação pendentes

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE/Search Funds escrevendo MEMO COMPLETO para Spectra Capital."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())
