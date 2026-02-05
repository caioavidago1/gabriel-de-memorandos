"""
Agente de Retornos - Memo Completo Search Fund

Gera a seção "Retornos Esperados" do memo completo (5-7 parágrafos).
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
import json

from facts.builder import build_facts_section
from tipo_memorando._base.format_utils import get_currency_symbol, get_currency_label
from ..validator import fix_number_formatting


def generate_retornos_esperados_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Retornos Esperados COMPLETA para Memo Search Fund.
    
    EXTENSÃO: 5-7 parágrafos com análise detalhada de retornos por cenário.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    trx = facts.get("transaction_structure", {})
    currency = trx.get("currency") or "BRL"
    currency_label = get_currency_label(currency)
    
    # Facts de retornos padrão
    returns_section = build_facts_section(
        facts, "returns",
        {
            "irr_pct": "IRR base (%)",
            "moic": "MOIC base (x)",
            "holding_period_years": "Holding period (anos)",
        }
    )
    
    # Facts de tabelas de retornos (se disponível)
    returns_table = facts.get("returns_table", {})
    returns_table_section = ""
    if returns_table:
        returns_table_section = f"""
TABELAS DE RETORNOS:
{json.dumps(returns_table, indent=2, ensure_ascii=False)}
"""

    prompt = f"""
Você é um analista sênior de PE/Search Funds, escrevendo a SEÇÃO RETORNOS ESPERADOS de um MEMO COMPLETO para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DO DEAL
═══════════════════════════════════════════════════════════════════════

RETORNOS:
{returns_section}
{returns_table_section}
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

§ PARÁGRAFO 1 - Retornos no Cenário Base:
  - IRR e MOIC detalhados
  - "Considerando as projeções e saída em [ano] a [X]x EBITDA..."
  - Holding period e timing de saída
  - Waterfall de retorno (se disponível)

§ PARÁGRAFO 2 - Retornos no Cenário Otimista (Upside):
  - IRR e MOIC no upside
  - Comparação com cenário base
  - O que precisa acontecer para atingir
  - Potencial de retorno máximo

§ PARÁGRAFO 3 - Retornos no Cenário Pessimista (Downside):
  - IRR e MOIC no downside
  - Comparação com cenário base
  - Proteção de capital (floor return)
  - Análise de perda máxima

§ PARÁGRAFO 4 - Sensibilidade a Múltiplo de Saída:
  - Tabela de sensibilidade (se disponível)
  - Impacto de variações no múltiplo de saída
  - Análise de diferentes múltiplos (5.5x, 6.0x, 6.5x)

§ PARÁGRAFO 5 - Sensibilidade a Timing de Saída:
  - Impacto de saída em diferentes anos
  - Análise de saída antecipada vs estendida
  - Trade-off entre timing e múltiplo

§ PARÁGRAFO 6 - Comparação com Benchmarks:
  - Comparação com outros deals de Search Fund
  - Comparação com retornos alvo da Spectra
  - Posicionamento relativo do deal

§ PARÁGRAFO 7 - Proteções e Estrutura:
  - Mecanismos de proteção (multiple compression, etc)
  - Estrutura de earnout e seller note
  - Impacto na distribuição de retornos

Gere apenas texto corrido (SEM títulos, SEM markdown).
Se houver tabelas de retornos nos facts, incorpore os dados nas análises.
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE/Search Funds escrevendo MEMO COMPLETO para Spectra Capital."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())
