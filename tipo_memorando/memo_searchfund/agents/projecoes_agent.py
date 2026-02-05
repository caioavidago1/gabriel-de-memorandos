"""
Agente de Projeções - Memo Completo Search Fund

Gera a seção "Projeções Financeiras" do memo completo (6-8 parágrafos).
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
import json

from facts.builder import build_facts_section
from tipo_memorando._base.format_utils import get_currency_symbol, get_currency_label
from ..validator import fix_number_formatting


def generate_projections_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Projeções Financeiras COMPLETA para Memo Search Fund.
    
    EXTENSÃO: 6-8 parágrafos com análise de 3 cenários (base/upside/downside).
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    trx = facts.get("transaction_structure", {})
    currency = trx.get("currency") or "BRL"
    currency_label = get_currency_label(currency)

    # Facts de projeções padrão
    projections_section = build_facts_section(
        facts, "saida",
        {
            "revenue_exit_mm": f"Receita na saída ({currency_label})",
            "revenue_cagr_projected_pct": "CAGR receita projetado (%)",
            "ebitda_exit_mm": f"EBITDA na saída ({currency_label})",
            "ebitda_margin_exit_pct": "Margem EBITDA na saída (%)",
            "exit_year": "Ano de saída",
            "exit_multiple_ev_ebitda": "Múltiplo de saída",
            "projection_period": "Período de projeção",
            "growth_drivers": "Drivers de crescimento",
        }
    )
    
    # Facts de tabelas de projeções (se disponível)
    projections_table = facts.get("projections_table", {})
    projections_table_section = ""
    if projections_table:
        projections_table_section = f"""
TABELAS DE PROJEÇÕES:
{json.dumps(projections_table, indent=2, ensure_ascii=False)}
"""

    prompt = f"""
Você é um analista sênior de PE/Search Funds, escrevendo a SEÇÃO PROJEÇÕES FINANCEIRAS de um MEMO COMPLETO para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DO DEAL
═══════════════════════════════════════════════════════════════════════

PROJEÇÕES:
{projections_section}
{projections_table_section}
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

§ PARÁGRAFO 1 - Premissas do Cenário Base:
  - CAGR de receita projetado vs histórico
  - Evolução de margem esperada
  - Principais drivers das projeções
  - Premissas detalhadas (crescimento de vendas, serviços, HaaS, NRR, etc)

§ PARÁGRAFO 2 - Projeções Cenário Base (Ano a Ano):
  - Evolução projetada ano a ano (receita, EBITDA, margem)
  - Receita e EBITDA no ano de saída
  - Justificativa das premissas
  - Se houver tabela, referenciar os dados da tabela

§ PARÁGRAFO 3 - Cenário Otimista (Upside):
  - Premissas mais agressivas (maior crescimento, melhor margem)
  - Comparação com cenário base
  - O que precisa acontecer para atingir este cenário
  - Receita e EBITDA projetados no upside

§ PARÁGRAFO 4 - Cenário Pessimista (Downside):
  - Premissas conservadoras/stress (menor crescimento, margem pressionada)
  - Comparação com cenário base
  - Principais riscos que levariam a este cenário
  - Receita e EBITDA projetados no downside

§ PARÁGRAFO 5 - Análise Comparativa dos Cenários:
  - Tabela comparativa dos 3 cenários (se disponível)
  - Principais diferenças entre cenários
  - Probabilidade de cada cenário (se mencionado)

§ PARÁGRAFO 6 - Drivers de Crescimento:
  - Principais alavancas de crescimento
  - Oportunidades de expansão
  - Investimentos necessários (Capex, contratações)

§ PARÁGRAFO 7 - Evolução de Margens:
  - Expectativa de melhoria de margem ao longo do tempo
  - Mix de receita e impacto nas margens
  - Alavancagem operacional

§ PARÁGRAFO 8 - Riscos das Projeções:
  - Principais riscos que podem impactar as projeções
  - Sensibilidade a variáveis-chave
  - Validações necessárias

Gere apenas texto corrido (SEM títulos, SEM markdown).
Se houver tabelas de projeções nos facts, incorpore os dados nas análises.
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE/Search Funds escrevendo MEMO COMPLETO para Spectra Capital."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())
