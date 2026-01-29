"""
Agente de Mercado - Memo Completo Search Fund

Gera a seção "Mercado" do memo completo (5-7 parágrafos).
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os

from facts.memoSearchfund import build_facts_section, get_currency_symbol, get_currency_label
from ..validator import fix_number_formatting


def generate_market_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Mercado COMPLETA para Memo Search Fund.
    
    EXTENSÃO: 5-7 parágrafos com análise profunda de mercado e competição.
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
            "business_description": "Descrição do negócio",
        }
    )
    
    qualitative_section = build_facts_section(
        facts, "qualitative",
        {
            "market_size_mm": "Tamanho mercado (MM)",
            "market_growth_rate_pct": "Crescimento mercado (%)",
            "market_share_pct": "Market share (%)",
            "market_dynamics": "Dinâmica do mercado",
            "main_competitors": "Principais competidores",
            "competitive_advantages": "Vantagens competitivas",
            "barriers_to_entry": "Barreiras à entrada",
            "regulatory_environment": "Ambiente regulatório",
            "industry_trends": "Tendências do setor",
        }
    )

    prompt = f"""
Você é um analista sênior de PE/Search Funds, escrevendo a SEÇÃO MERCADO de um MEMO COMPLETO para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DO DEAL
═══════════════════════════════════════════════════════════════════════

IDENTIFICAÇÃO:
{identification_section}

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
ESTRUTURA OBRIGATÓRIA (5-7 parágrafos - MEMO COMPLETO)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Definição do Mercado:
  - O que é o mercado/setor
  - Tamanho (TAM/SAM/SOM) se disponível
  - Características principais

§ PARÁGRAFO 2 - Dinâmica de Crescimento:
  - Taxa de crescimento histórica e projetada
  - Drivers de crescimento
  - Tendências estruturais

§ PARÁGRAFO 3 - Estrutura Competitiva:
  - Fragmentação vs concentração
  - Principais players e market share
  - Posicionamento da empresa

§ PARÁGRAFO 4 - Análise de Competidores:
  - Detalhamento dos principais competidores
  - Comparativo de ofertas e posicionamento
  - Validações do searcher

§ PARÁGRAFO 5 - Diferenciais Competitivos:
  - OBRIGATÓRIO: "De acordo com o searcher, os principais diferenciais são..."
  - Lista detalhada: "(i) [diferencial 1], (ii) [diferencial 2]..."
  - Análise crítica de cada diferencial

§ PARÁGRAFO 6 - Barreiras à Entrada:
  - Switching costs, network effects
  - Regulação, certificações
  - Escala e investimentos necessários

§ PARÁGRAFO 7 - Riscos de Mercado:
  - Ameaças competitivas
  - Mudanças regulatórias
  - Disrupção tecnológica

REGRA DE OURO:
- SEMPRE atribuir diferenciais ao searcher
- Análise crítica, não apenas descritiva

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE/Search Funds escrevendo MEMO COMPLETO para Spectra Capital."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())
