"""
Agente de Empresa - Memo Completo Search Fund

Gera a seção "Empresa" do memo completo (6-8 parágrafos).
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os

from facts.builder import build_facts_section
from tipo_memorando._base.format_utils import get_currency_symbol, get_currency_label
from ..validator import fix_number_formatting


def generate_company_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Empresa COMPLETA para Memo Search Fund.
    
    EXTENSÃO: 6-8 parágrafos com análise profunda do negócio.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    # ===== FACTS =====
    identification_section = build_facts_section(
        facts, "identification",
        {
            "company_name": "Nome da empresa",
            "company_location": "Localização",
            "company_founding_year": "Ano de fundação",
            "business_description": "Descrição do negócio",
            "employees_count": "Número de funcionários",
        }
    )
    
    trx = facts.get("transaction_structure", {})
    currency = trx.get("currency") or "BRL"
    currency_label = get_currency_label(currency)
    
    financials_section = build_facts_section(
        facts, "financials_history",
        {
            "revenue_current_mm": f"Receita atual ({currency_label})",
            "revenue_cagr_pct": "CAGR receita (%)",
            "revenue_by_segment": "Receita por segmento",
            "gross_margin_pct": "Margem bruta (%)",
            "ebitda_margin_current_pct": "Margem EBITDA (%)",
        }
    )
    
    qualitative_section = build_facts_section(
        facts, "qualitative",
        {
            "business_model": "Modelo de negócio",
            "revenue_model": "Modelo de receita",
            "customer_segments": "Segmentos de clientes",
            "main_products": "Principais produtos/serviços",
            "competitive_advantages": "Vantagens competitivas",
            "key_clients": "Principais clientes",
            "client_concentration": "Concentração de clientes",
        }
    )

    prompt = f"""
Você é um analista sênior de PE/Search Funds, escrevendo a SEÇÃO EMPRESA de um MEMO COMPLETO para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DO DEAL
═══════════════════════════════════════════════════════════════════════

IDENTIFICAÇÃO:
{identification_section}

FINANCIALS:
{financials_section}

QUALITATIVO:
{qualitative_section}
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

§ PARÁGRAFO 1 - Histórico e Fundação:
  - "Fundada em [ano] e sediada em [local], a [Empresa] é..."
  - História da empresa, fundadores, evolução

§ PARÁGRAFO 2 - Modelo de Negócio:
  - Core business, proposta de valor
  - Como a empresa gera receita

§ PARÁGRAFO 3 - Produtos e Serviços:
  - Principais linhas de negócio
  - Mix de receita por vertical: "(X% da receita)"
  - Detalhamento de cada vertical

§ PARÁGRAFO 4 - Base de Clientes:
  - Perfil de clientes (B2B, B2C, segmentos)
  - Concentração de clientes
  - Principais contratos e renovações

§ PARÁGRAFO 5 - Evolução Histórica:
  - "Entre [período], o faturamento apresentou CAGR de X%"
  - Marcos importantes, mudanças estratégicas
  - Drivers de crescimento

§ PARÁGRAFO 6 - Estrutura Operacional:
  - Número de funcionários, organograma
  - Processos-chave, capacidade operacional
  - Infraestrutura e ativos

§ PARÁGRAFO 7 - Margens e Rentabilidade:
  - Margem bruta e EBITDA
  - Dinâmica de custos e despesas
  - Conversão de caixa

§ PARÁGRAFO 8 - Riscos Operacionais:
  - Key person risk
  - Dependências operacionais
  - Pontos de atenção identificados

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE/Search Funds escrevendo MEMO COMPLETO para Spectra Capital."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())
