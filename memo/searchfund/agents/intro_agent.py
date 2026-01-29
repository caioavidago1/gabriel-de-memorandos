"""
Agente de Introdução - Memo Completo Search Fund

Gera a seção "Overview/Introdução" do memo completo (5-7 parágrafos).
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os

from facts.memoSearchfund import build_facts_section, get_currency_symbol, get_currency_label
from ..validator import fix_number_formatting


def generate_intro_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção de Introdução COMPLETA para Memo Search Fund.
    
    EXTENSÃO: 5-7 parágrafos com contexto completo do deal.
    
    Args:
        facts: Dict com facts estruturados
        rag_context: Contexto extraído do documento (opcional)
        model: Modelo OpenAI a usar
        temperature: Criatividade (0.0-1.0)
    
    Returns:
        Texto da introdução (5-7 parágrafos)
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    # ===== CONSTRÓI SEÇÕES DE FACTS =====
    identification_section = build_facts_section(
        facts, "identification",
        {
            "investor_name": "Nome do investidor",
            "investor_nationality": "Nacionalidade",
            "searcher_name": "Responsável(is)",
            "search_start_date": "Início da busca",
            "company_name": "Empresa alvo",
            "company_location": "Localização",
            "company_founding_year": "Ano de fundação",
            "business_description": "Descrição do negócio",
            "deal_context": "Contexto do Deal",
            "deal_source": "Origem do deal",
        }
    )
    
    trx = facts.get("transaction_structure", {})
    currency = trx.get("currency") or "BRL"
    currency_symbol = get_currency_symbol(currency)
    currency_label = get_currency_label(currency)
    
    transaction_section = build_facts_section(
        facts, "transaction_structure",
        {
            "stake_pct": "Participação (%)",
            "ev_mm": f"EV ({currency_label})",
            "multiple_ev_ebitda": "Múltiplo EV/EBITDA",
            "multiple_reference_period": "Período do múltiplo",
            "cash_payment_mm": f"Pagamento à vista ({currency_label})",
            "seller_note_mm": f"Seller note ({currency_label})",
            "seller_note_terms": "Termos seller note",
            "earnout_mm": f"Earnout ({currency_label})",
            "earnout_conditions": "Condições earnout",
            "multiple_with_earnout": "Múltiplo c/ earnout",
        }
    )
    
    financials_section = build_facts_section(
        facts, "financials_history",
        {
            "revenue_current_mm": f"Receita atual ({currency_label})",
            "revenue_cagr_pct": "CAGR receita (%)",
            "revenue_cagr_period": "Período CAGR receita",
            "ebitda_current_mm": f"EBITDA atual ({currency_label})",
            "ebitda_margin_current_pct": "Margem EBITDA (%)",
            "net_debt_mm": f"Dívida líquida ({currency_label})",
            "cash_conversion_pct": "Conversão caixa (%)",
            "employees_count": "Número de funcionários",
        }
    )
    
    returns_section = build_facts_section(
        facts, "returns",
        {
            "irr_pct": "IRR alvo (%)",
            "moic": "MOIC alvo (x)",
            "holding_period_years": "Holding period (anos)",
            "irr_base_case": "IRR cenário base (%)",
            "irr_downside": "IRR downside (%)",
        }
    )
    
    qualitative_section = build_facts_section(
        facts, "qualitative",
        {
            "investment_thesis": "Tese de investimento",
            "key_risks": "Principais riscos",
            "key_opportunities": "Principais oportunidades",
        }
    )

    # ========== EXTRAI INFORMAÇÕES ==========
    idf = facts.get("identification", {})
    investor_name = idf.get("investor_name") or "o search fund"
    # Compatibilidade: aceita tanto searcher_name quanto investor_person_names
    searcher_names = idf.get("searcher_name") or idf.get("investor_person_names") or "o searcher"
    search_start_date = idf.get("search_start_date") or "[data]"
    company_name = idf.get("company_name") or "a empresa"

    # ========== MONTA PROMPT ==========
    prompt = f"""
Você é um analista sênior de private equity focado em Search Funds, escrevendo a SEÇÃO INTRODUÇÃO de um MEMO COMPLETO para comitê de investimento da Spectra Capital.

IMPORTANTE: Este é um MEMO COMPLETO (não short memo), portanto deve ser mais extenso e detalhado.

═══════════════════════════════════════════════════════════════════════
DADOS DO DEAL
═══════════════════════════════════════════════════════════════════════

IDENTIFICAÇÃO:
{identification_section}

TRANSAÇÃO:
{transaction_section}

FINANCIALS:
{financials_section}

RETORNOS:
{returns_section}

QUALITATIVO:
{qualitative_section}
"""

    if rag_context:
        prompt += f"""
═══════════════════════════════════════════════════════════════════════
CONTEXTO DO DOCUMENTO ORIGINAL
═══════════════════════════════════════════════════════════════════════

{rag_context}
"""

    prompt += f"""
═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA (5-7 parágrafos - MEMO COMPLETO)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Abertura e Contexto:
   - "A {investor_name} (search liderado por {searcher_names}, que iniciou seu período de busca em {search_start_date}) está avaliando a aquisição da {company_name}..."
   - Breve descrição do negócio e setor

§ PARÁGRAFO 2 - Estrutura da Transação:
   - Participação, EV, múltiplo de entrada
   - Detalhe completo: à vista, seller note, earnout
   - Análise da atratividade da estrutura

§ PARÁGRAFO 3 - Tese de Investimento:
   - Por que este deal faz sentido
   - Principais drivers de valor
   - Opcionalidades de crescimento

§ PARÁGRAFO 4 - Destaques Financeiros:
   - Receita, EBITDA, margens atuais
   - Histórico de crescimento (CAGR)
   - Conversão de caixa e alavancagem

§ PARÁGRAFO 5 - Retornos Esperados:
   - IRR e MOIC no cenário base
   - Premissas principais
   - Sensibilidade a variáveis-chave

§ PARÁGRAFO 6 - Pontos Positivos:
   - "Acreditamos que vale aprofundar no deal pelas seguintes razões..."
   - Lista de 3-5 razões com justificativa

§ PARÁGRAFO 7 - Pontos de Atenção:
   - "Os principais pontos que precisamos aprofundar são..."
   - Lista de 3-5 riscos/validações pendentes
   - Plano de mitigação preliminar

REGRAS:
- Tom profissional e analítico
- Parágrafos de 4-6 linhas cada
- Sem títulos ou bullets no texto (parágrafos corridos)
- Separar parágrafos com linha em branco
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE/Search Funds escrevendo um MEMO COMPLETO para IC da Spectra Capital."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())
