"""
Agente de Conclusão - Memo Completo Search Fund

Gera a seção "Conclusão" do memo completo (3-5 parágrafos).
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os

from facts.builder import build_facts_section
from tipo_memorando._base.format_utils import get_currency_symbol, get_currency_label
from ..validator import fix_number_formatting


def generate_conclusao_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Conclusão COMPLETA para Memo Search Fund.
    
    EXTENSÃO: 3-5 parágrafos com resumo e recomendação final.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    trx = facts.get("transaction_structure", {})
    currency = trx.get("currency") or "BRL"
    currency_symbol = get_currency_symbol(currency)
    currency_label = get_currency_label(currency)

    # Facts de opiniões (pontos positivos e negativos)
    opinioes_section = build_facts_section(
        facts, "opinioes",
        {
            "key_strengths": "Principais pontos positivos",
            "key_concerns": "Principais preocupações",
            "investment_rationale": "Racional de investimento",
            "spectra_recommendation": "Recomendação da Spectra",
        }
    )
    
    # Facts de retornos para mencionar na conclusão
    returns_section = build_facts_section(
        facts, "returns",
        {
            "irr_pct": "IRR base (%)",
            "moic": "MOIC base (x)",
        }
    )
    
    # Facts de transação para mencionar alocação
    transaction_section = build_facts_section(
        facts, "transaction_structure",
        {
            "ev_mm": f"EV ({currency_label})",
            "stake_pct": "Participação (%)",
        }
    )

    prompt = f"""
Você é um analista sênior de PE/Search Funds, escrevendo a SEÇÃO CONCLUSÃO de um MEMO COMPLETO para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DO DEAL
═══════════════════════════════════════════════════════════════════════

OPINIÕES:
{opinioes_section}

RETORNOS:
{returns_section}

TRANSAÇÃO:
{transaction_section}
"""

    if rag_context:
        prompt += f"""
═══════════════════════════════════════════════════════════════════════
CONTEXTO DO DOCUMENTO
═══════════════════════════════════════════════════════════════════════

{rag_context}
"""

    prompt += f"""
═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA (3-5 parágrafos - MEMO COMPLETO)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Resumo dos Pontos Positivos:
  - Listar os 3-5 principais aspectos positivos do investimento
  - Formato: "Em nossa visão, os principais aspectos positivos do investimento são:"
  - Usar bullets implícitos (não usar markdown, apenas texto corrido)
  - Exemplo: "• Mercado endereçável grande e fragmentado, sem players capitalizados."
  - Cada ponto deve ser uma frase completa e específica

§ PARÁGRAFO 2 - Resumo dos Riscos Principais:
  - Listar os 3-5 principais riscos ou pontos de atenção
  - Formato: "Por outro lado, os principais riscos são:"
  - Usar bullets implícitos (não usar markdown, apenas texto corrido)
  - Exemplo: "• Business de capital intensivo e companhia alavancada considerando o seller note e earn-out (3x dívida líquida / EBITDA)."
  - Cada risco deve ser específico e quantificado quando possível

§ PARÁGRAFO 3 - Análise de Balanceamento:
  - Comparar pontos positivos vs negativos
  - Avaliar se os pontos positivos superam os negativos
  - Contexto do deal e posicionamento

§ PARÁGRAFO 4 - Recomendação Final:
  - Recomendação clara (aprovar, rejeitar, aprovar com condições)
  - Alocação sugerida (ex: "R$ 20m pelo Spectra VI" ou "{currency_symbol} Xm")
  - Justificativa da alocação
  - Limites ou condições (ex: "respeitando nosso limite máximo de 1/3 do captable em investimentos realizados por Search Funds")

§ PARÁGRAFO 5 - Próximos Passos (opcional):
  - Próximos passos recomendados
  - Validações pendentes
  - Timeline esperado

IMPORTANTE:
- Use primeira pessoa plural: "entendemos", "acreditamos", "recomendamos"
- Seja específico e quantificado
- A recomendação deve ser clara e direta
- Formato de bullets: use "•" no início de cada ponto, mas mantenha texto corrido

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE/Search Funds escrevendo MEMO COMPLETO para Spectra Capital."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())
