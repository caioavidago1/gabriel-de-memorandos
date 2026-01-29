"""
Agente de Board e Cap Table - Memo Completo Search Fund

Gera a seção "Board e Cap Table" do memo completo (4-6 parágrafos).
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
import json

from facts.memoSearchfund import build_facts_section, get_currency_symbol, get_currency_label
from ..validator import fix_number_formatting


def generate_board_cap_table_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Board e Cap Table COMPLETA para Memo Search Fund.
    
    EXTENSÃO: 4-6 parágrafos sobre composição do board e investidores.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    # Facts de board e cap table
    board_cap_table_facts = facts.get("board_cap_table", {})
    
    # Construir seção de facts
    board_cap_table_section = build_facts_section(
        facts, "board_cap_table",
        {
            "board_members": "Membros do board",
            "cap_table": "Cap table de investidores",
            "governance_structure": "Estrutura de governança",
            "board_commentary": "Comentários sobre board e cap table",
        }
    )
    
    # Se os dados estão em formato estruturado, adicionar formatação melhor
    if board_cap_table_facts:
        # Adicionar dados estruturados se disponíveis
        structured_data = {}
        if board_cap_table_facts.get("board_members"):
            structured_data["board_members"] = board_cap_table_facts["board_members"]
        if board_cap_table_facts.get("cap_table"):
            structured_data["cap_table"] = board_cap_table_facts["cap_table"]
        
        if structured_data:
            board_cap_table_section += f"\n\nDADOS ESTRUTURADOS:\n{json.dumps(structured_data, indent=2, ensure_ascii=False)}"

    prompt = f"""
Você é um analista sênior de PE/Search Funds, escrevendo a SEÇÃO BOARD E CAP TABLE de um MEMO COMPLETO para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DO DEAL
═══════════════════════════════════════════════════════════════════════

BOARD E CAP TABLE:
{board_cap_table_section}
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
ESTRUTURA OBRIGATÓRIA (4-6 parágrafos - MEMO COMPLETO)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Composição do Board:
  - Membros do board com seus backgrounds
  - Quem indicou cada membro
  - Experiência relevante de cada membro
  - Papel esperado de cada membro

§ PARÁGRAFO 2 - Análise da Qualidade do Board:
  - Avaliação da qualidade e experiência do board
  - Complementaridade dos membros
  - Comparação com outros boards de Search Funds
  - Pontos fortes e potenciais gaps

§ PARÁGRAFO 3 - Estrutura de Investidores (Cap Table):
  - Principais investidores e suas participações
  - Tipos de investidores (Search Investor, Gap Investor, etc)
  - Distribuição geográfica dos investidores
  - Qualidade e reputação dos investidores

§ PARÁGRAFO 4 - Governança e Direitos:
  - Estrutura de governança
  - Direitos de veto, tag-along, drag-along
  - Composição e funcionamento do board
  - Papel da Spectra (se board observer ou membro)

§ PARÁGRAFO 5 - Análise da Qualidade do Cap Table:
  - Avaliação da qualidade dos investidores
  - Experiência em Search Funds
  - Potencial de value-add
  - Comparação com outros deals

§ PARÁGRAFO 6 - Considerações Finais:
  - Resumo da qualidade geral do board e cap table
  - Pontos de atenção
  - Expectativa de contribuição

Gere apenas texto corrido (SEM títulos, SEM markdown).
Se houver dados estruturados de board_members ou cap_table, incorpore nas análises.
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE/Search Funds escrevendo MEMO COMPLETO para Spectra Capital."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())
