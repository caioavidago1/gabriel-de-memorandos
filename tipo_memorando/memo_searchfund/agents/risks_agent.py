"""
Agente de Riscos - Memo Completo Search Fund

Gera a seção "Riscos e Mitigações" do memo completo (5-7 parágrafos).
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os

from facts.builder import build_facts_section
from tipo_memorando._base.format_utils import get_currency_symbol, get_currency_label
from ..validator import fix_number_formatting


def generate_risks_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Riscos e Mitigações COMPLETA para Memo Search Fund.
    
    EXTENSÃO: 5-7 parágrafos com análise detalhada de riscos.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    qualitative_section = build_facts_section(
        facts, "qualitative",
        {
            "key_risks": "Principais riscos",
            "key_person_risk": "Key person risk",
            "client_concentration": "Concentração de clientes",
            "supplier_concentration": "Concentração de fornecedores",
            "regulatory_risks": "Riscos regulatórios",
            "competitive_risks": "Riscos competitivos",
            "operational_risks": "Riscos operacionais",
            "mitigations": "Mitigações propostas",
        }
    )

    prompt = f"""
Você é um analista sênior de PE/Search Funds, escrevendo a SEÇÃO RISCOS E MITIGAÇÕES de um MEMO COMPLETO para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DO DEAL
═══════════════════════════════════════════════════════════════════════

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

§ PARÁGRAFO 1 - Riscos de Mercado:
  - Dinâmica competitiva
  - Mudanças regulatórias
  - Disrupção tecnológica
  - Mitigações propostas

§ PARÁGRAFO 2 - Riscos Operacionais:
  - Key person risk (fundador, equipe-chave)
  - Complexidade operacional
  - Capacidade de execução do searcher
  - Mitigações propostas

§ PARÁGRAFO 3 - Riscos de Concentração:
  - Concentração de clientes
  - Concentração de fornecedores
  - Concentração geográfica
  - Mitigações propostas

§ PARÁGRAFO 4 - Riscos Financeiros:
  - Volatilidade de margens
  - Capital de giro
  - Contingências e passivos ocultos
  - Mitigações propostas

§ PARÁGRAFO 5 - Riscos de Execução:
  - Integração pós-aquisição
  - Transição de gestão
  - Implementação do plano de 100 dias
  - Mitigações propostas

§ PARÁGRAFO 6 - Riscos de Saída:
  - Liquidez do mercado
  - Múltiplo de saída
  - Timing do exit
  - Mitigações propostas

§ PARÁGRAFO 7 - Matriz de Riscos:
  - Classificação por probabilidade x impacto
  - Top 3 riscos críticos
  - Validações pendentes na due diligence

REGRA DE OURO:
- Para CADA risco, apresentar mitigação
- Ser específico, não genérico
- Ceticismo construtivo

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE/Search Funds escrevendo MEMO COMPLETO para Spectra Capital."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())
