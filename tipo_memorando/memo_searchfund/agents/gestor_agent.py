"""
Agente de Gestor - Memo Completo Search Fund

Gera a seção "Gestor" do memo completo (5-7 parágrafos).
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os

from facts.builder import build_facts_section
from tipo_memorando._base.format_utils import get_currency_symbol, get_currency_label
from ..validator import fix_number_formatting


def generate_gestor_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Gestor COMPLETA para Memo Search Fund.
    
    EXTENSÃO: 5-7 parágrafos sobre análise dos searchers.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    # ===== FACTS =====
    identification_section = build_facts_section(
        facts, "identification",
        {
            "searcher_name": "Nome(s) do(s) searcher(s)",
            "investor_nationality": "Nacionalidade",
        }
    )
    
    # Buscar facts de gestor (pode estar em "gestor" ou "searcher")
    gestor_facts = facts.get("gestor", {}) or facts.get("searcher", {})
    gestor_section = ""
    if gestor_facts:
        gestor_section = build_facts_section(
            facts, "gestor",
            {
                "searcher_name": "Nome(s) do(s) searcher(s)",
                "searcher_background": "Formação e histórico profissional",
                "searcher_experience": "Experiência relevante",
                "searcher_assessment": "Assessment psicológico",
                "searcher_complementarity": "Complementaridade da dupla",
                "searcher_references": "Referências e validações",
                "searcher_track_record": "Histórico de deals anteriores",
            }
        )
    
    # Se não encontrou em gestor, tentar buscar de identification também
    if not gestor_section or len(gestor_section.strip()) < 50:
        idf_section = build_facts_section(
            facts, "identification",
            {
                "searcher_name": "Nome(s) do(s) searcher(s)",
                "investor_nationality": "Nacionalidade",
            }
        )
        if idf_section:
            gestor_section = (gestor_section + "\n" + idf_section) if gestor_section else idf_section

    prompt = f"""
Você é um analista sênior de PE/Search Funds, escrevendo a SEÇÃO GESTOR de um MEMO COMPLETO para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DO DEAL
═══════════════════════════════════════════════════════════════════════

IDENTIFICAÇÃO:
{identification_section}

GESTOR/SEARCHER:
{gestor_section}
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

§ PARÁGRAFO 1 - Apresentação dos Searchers:
  - Nome(s) do(s) searcher(s) e formação acadêmica
  - Histórico profissional resumido
  - Contexto de como conhecemos os searchers

§ PARÁGRAFO 2 - Experiência Relevante:
  - Detalhamento da experiência profissional
  - Empresas anteriores e cargos ocupados
  - Experiência específica relevante para o deal

§ PARÁGRAFO 3 - Assessment e Perfil:
  - Resultados de assessment psicológico (se disponível)
  - Perfil comportamental e características
  - Pontos fortes e áreas de desenvolvimento

§ PARÁGRAFO 4 - Complementaridade (se dupla):
  - Análise de como os searchers se complementam
  - Divisão de responsabilidades
  - Dinâmica de trabalho em equipe

§ PARÁGRAFO 5 - Referências e Validações:
  - Referências obtidas (ex-empregadores, mentores)
  - Validações de terceiros
  - Comparação com outros searchers conhecidos

§ PARÁGRAFO 6 - Track Record (se aplicável):
  - Histórico de deals anteriores
  - Experiências relevantes em M&A ou operações
  - Aprendizados e evolução

§ PARÁGRAFO 7 - Avaliação Final:
  - Nossa visão geral sobre os searchers
  - Pontos de atenção ou preocupações
  - Expectativa de performance

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE/Search Funds escrevendo MEMO COMPLETO para Spectra Capital."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())
