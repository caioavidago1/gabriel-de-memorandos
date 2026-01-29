"""
Agente de Financials - Memo Completo Search Fund

Gera a seção "Histórico Financeiro" do memo completo (6-8 parágrafos).
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os

from facts.memoSearchfund import build_facts_section, get_currency_symbol, get_currency_label
from ..validator import fix_number_formatting


def generate_financials_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Histórico Financeiro COMPLETA para Memo Search Fund.
    
    EXTENSÃO: 6-8 parágrafos com análise profunda de financials.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    trx = facts.get("transaction_structure", {})
    currency = trx.get("currency") or "BRL"
    currency_label = get_currency_label(currency)

    financials_section = build_facts_section(
        facts, "financials_history",
        {
            "revenue_history": "Histórico de receita",
            "revenue_current_mm": f"Receita atual ({currency_label})",
            "revenue_cagr_pct": "CAGR receita (%)",
            "revenue_cagr_period": "Período CAGR",
            "revenue_by_segment": "Receita por segmento",
            "gross_margin_history": "Histórico margem bruta",
            "gross_margin_pct": "Margem bruta atual (%)",
            "ebitda_history": "Histórico EBITDA",
            "ebitda_current_mm": f"EBITDA atual ({currency_label})",
            "ebitda_margin_current_pct": "Margem EBITDA (%)",
            "net_income_mm": f"Lucro líquido ({currency_label})",
            "capex_mm": f"Capex ({currency_label})",
            "working_capital_mm": f"Capital de giro ({currency_label})",
            "cash_conversion_pct": "Conversão de caixa (%)",
            "net_debt_mm": f"Dívida líquida ({currency_label})",
        }
    )

    prompt = f"""
Você é um analista sênior de PE/Search Funds, escrevendo a SEÇÃO HISTÓRICO FINANCEIRO de um MEMO COMPLETO para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DO DEAL
═══════════════════════════════════════════════════════════════════════

FINANCIALS:
{financials_section}
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
ESTRUTURA OBRIGATÓRIA (6-8 parágrafos - MEMO COMPLETO)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Evolução de Receita:
  - "Entre [período], o faturamento apresentou CAGR de X%..."
  - Evolução ano a ano
  - Drivers de crescimento

§ PARÁGRAFO 2 - Composição de Receita:
  - Mix por produto/serviço/cliente
  - Evolução do mix ao longo do tempo
  - Concentração de receita

§ PARÁGRAFO 3 - Margem Bruta:
  - Margem bruta atual e histórica
  - Dinâmica de custos
  - Comparação com peers

§ PARÁGRAFO 4 - EBITDA e Margem Operacional:
  - EBITDA atual e evolução
  - Análise da margem EBITDA
  - Despesas operacionais como % da receita

§ PARÁGRAFO 5 - Estrutura de Custos:
  - Breakdown de custos e despesas
  - Custos fixos vs variáveis
  - Alavancagem operacional

§ PARÁGRAFO 6 - Geração de Caixa:
  - Conversão de EBITDA em caixa
  - Capex (manutenção vs expansão)
  - Necessidade de capital de giro

§ PARÁGRAFO 7 - Posição de Balanço:
  - Dívida líquida e estrutura de capital
  - Ativos e passivos relevantes
  - Contingências e provisões

§ PARÁGRAFO 8 - Qualidade dos Números:
  - Ajustes necessários (normalização)
  - Consistência com QofE se disponível
  - Red flags identificados

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE/Search Funds escrevendo MEMO COMPLETO para Spectra Capital."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())
