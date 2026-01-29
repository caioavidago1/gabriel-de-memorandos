"""
Geração de seções para Memo Completo Primário

Funções especializadas para análise COMPLETA de deals primários (equity novo).
Versão expandida (~20 páginas) com 5-8 parágrafos por seção.

FOCO: Growth equity, minority investments, capital de crescimento
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os

from shortmemo.searchfund.shared import build_facts_section, get_currency_symbol, get_currency_label
from .validator import fix_number_formatting


def generate_intro_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção de Introdução COMPLETA para Memo Primário.
    
    EXTENSÃO: 5-7 parágrafos com contexto completo do deal.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    identification_section = build_facts_section(
        facts, "identification",
        {
            "company_name": "Nome da empresa",
            "company_location": "Localização",
            "company_founding_year": "Ano de fundação",
            "business_description": "Descrição do negócio",
            "deal_type": "Tipo de deal",
            "deal_source": "Origem do deal",
            "founders": "Fundadores",
        }
    )
    
    trx = facts.get("transaction_structure", {})
    currency = trx.get("currency") or "BRL"
    currency_label = get_currency_label(currency)
    
    transaction_section = build_facts_section(
        facts, "transaction_structure",
        {
            "round_size_mm": f"Tamanho da rodada ({currency_label})",
            "pre_money_mm": f"Pre-money valuation ({currency_label})",
            "post_money_mm": f"Post-money valuation ({currency_label})",
            "stake_pct": "Participação (%)",
            "investment_mm": f"Investimento Spectra ({currency_label})",
            "co_investors": "Co-investidores",
            "use_of_proceeds": "Uso dos recursos",
            "round_type": "Tipo de rodada",
        }
    )
    
    financials_section = build_facts_section(
        facts, "financials_history",
        {
            "revenue_current_mm": f"Receita atual ({currency_label})",
            "revenue_cagr_pct": "CAGR receita (%)",
            "ebitda_current_mm": f"EBITDA atual ({currency_label})",
            "ebitda_margin_current_pct": "Margem EBITDA (%)",
            "arr_mm": f"ARR ({currency_label})",
            "mrr_mm": f"MRR ({currency_label})",
        }
    )
    
    returns_section = build_facts_section(
        facts, "returns",
        {
            "target_irr_pct": "IRR alvo (%)",
            "target_moic": "MOIC alvo (x)",
            "holding_period_years": "Holding period (anos)",
        }
    )

    prompt = f"""
Você é um analista sênior de private equity/venture capital, escrevendo a SEÇÃO INTRODUÇÃO de um MEMO COMPLETO para comitê de investimento da Spectra Capital.

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

§ PARÁGRAFO 1 - Abertura e Contexto:
   - Apresentação da oportunidade e empresa
   - Tipo de rodada e estágio
   - Breve descrição do negócio

§ PARÁGRAFO 2 - Estrutura da Transação:
   - Tamanho da rodada, pre/post-money
   - Participação da Spectra
   - Co-investidores e sindicato

§ PARÁGRAFO 3 - Tese de Investimento:
   - Por que este deal faz sentido
   - Principais drivers de valor
   - Timing e oportunidade

§ PARÁGRAFO 4 - Destaques Financeiros:
   - Receita, crescimento, margens
   - Unit economics se aplicável
   - Métricas SaaS (ARR, NRR, etc.) se aplicável

§ PARÁGRAFO 5 - Retornos Esperados:
   - IRR e MOIC no cenário base
   - Premissas principais
   - Rota de saída

§ PARÁGRAFO 6 - Pontos Positivos:
   - Lista de 3-5 razões para investir

§ PARÁGRAFO 7 - Pontos de Atenção:
   - Lista de 3-5 riscos/validações

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE/VC escrevendo MEMO COMPLETO para IC da Spectra Capital."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())


def generate_company_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Empresa COMPLETA para Memo Primário.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    identification_section = build_facts_section(
        facts, "identification",
        {
            "company_name": "Nome da empresa",
            "company_location": "Localização",
            "company_founding_year": "Ano de fundação",
            "business_description": "Descrição do negócio",
            "founders": "Fundadores",
            "employees_count": "Funcionários",
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
        }
    )
    
    qualitative_section = build_facts_section(
        facts, "qualitative",
        {
            "business_model": "Modelo de negócio",
            "revenue_model": "Modelo de receita",
            "customer_segments": "Segmentos de clientes",
            "main_products": "Principais produtos",
            "competitive_advantages": "Vantagens competitivas",
        }
    )

    prompt = f"""
Você é um analista sênior de PE/VC, escrevendo a SEÇÃO EMPRESA de um MEMO COMPLETO para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS
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
ESTRUTURA OBRIGATÓRIA (6-8 parágrafos)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Histórico e Fundação
§ PARÁGRAFO 2 - Modelo de Negócio
§ PARÁGRAFO 3 - Produtos e Serviços
§ PARÁGRAFO 4 - Base de Clientes
§ PARÁGRAFO 5 - Evolução Histórica
§ PARÁGRAFO 6 - Estrutura Operacional
§ PARÁGRAFO 7 - Margens e Unit Economics
§ PARÁGRAFO 8 - Riscos Operacionais

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Analista sênior de PE/VC escrevendo MEMO COMPLETO."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())


def generate_market_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Mercado COMPLETA para Memo Primário.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    qualitative_section = build_facts_section(
        facts, "qualitative",
        {
            "market_size_mm": "Tamanho mercado (MM)",
            "market_growth_rate_pct": "Crescimento mercado (%)",
            "market_share_pct": "Market share (%)",
            "tam_sam_som": "TAM/SAM/SOM",
            "main_competitors": "Principais competidores",
            "competitive_advantages": "Vantagens competitivas",
            "barriers_to_entry": "Barreiras à entrada",
            "industry_trends": "Tendências do setor",
        }
    )

    prompt = f"""
Você é um analista sênior de PE/VC, escrevendo a SEÇÃO MERCADO de um MEMO COMPLETO para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS
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
ESTRUTURA OBRIGATÓRIA (5-7 parágrafos)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Definição e Tamanho do Mercado
§ PARÁGRAFO 2 - Dinâmica de Crescimento
§ PARÁGRAFO 3 - Estrutura Competitiva
§ PARÁGRAFO 4 - Análise de Competidores
§ PARÁGRAFO 5 - Diferenciais Competitivos
§ PARÁGRAFO 6 - Barreiras à Entrada
§ PARÁGRAFO 7 - Riscos de Mercado

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Analista sênior de PE/VC escrevendo MEMO COMPLETO."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())


def generate_financials_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Histórico Financeiro COMPLETA para Memo Primário.
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
            "arr_mm": f"ARR ({currency_label})",
            "mrr_mm": f"MRR ({currency_label})",
            "gross_margin_pct": "Margem bruta (%)",
            "ebitda_current_mm": f"EBITDA atual ({currency_label})",
            "ebitda_margin_current_pct": "Margem EBITDA (%)",
            "net_revenue_retention_pct": "NRR (%)",
            "gross_revenue_retention_pct": "GRR (%)",
            "cac_mm": f"CAC ({currency_label})",
            "ltv_mm": f"LTV ({currency_label})",
            "ltv_cac_ratio": "LTV/CAC (x)",
            "payback_months": "Payback (meses)",
            "burn_rate_mm": f"Burn rate ({currency_label})",
            "runway_months": "Runway (meses)",
        }
    )

    prompt = f"""
Você é um analista sênior de PE/VC, escrevendo a SEÇÃO HISTÓRICO FINANCEIRO de um MEMO COMPLETO para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS
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
ESTRUTURA OBRIGATÓRIA (6-8 parágrafos)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Evolução de Receita
§ PARÁGRAFO 2 - Métricas de Receita Recorrente (ARR, MRR, NRR)
§ PARÁGRAFO 3 - Margem Bruta e Estrutura de Custos
§ PARÁGRAFO 4 - EBITDA e Margem Operacional
§ PARÁGRAFO 5 - Unit Economics (CAC, LTV, Payback)
§ PARÁGRAFO 6 - Posição de Caixa e Runway
§ PARÁGRAFO 7 - Evolução para Rentabilidade
§ PARÁGRAFO 8 - Qualidade dos Números

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Analista sênior de PE/VC escrevendo MEMO COMPLETO."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())


def generate_founders_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Fundadores e Time COMPLETA para Memo Primário.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    team_section = build_facts_section(
        facts, "team",
        {
            "founders": "Fundadores",
            "founder_backgrounds": "Background dos fundadores",
            "founder_equity_pct": "Equity dos fundadores (%)",
            "c_suite": "C-Level",
            "employees_count": "Número de funcionários",
            "key_hires_planned": "Contratações planejadas",
            "equity_pool_pct": "ESOP pool (%)",
        }
    )
    
    qualitative_section = build_facts_section(
        facts, "qualitative",
        {
            "founder_market_fit": "Founder-market fit",
            "team_strengths": "Pontos fortes do time",
            "team_gaps": "Gaps do time",
            "culture": "Cultura",
        }
    )

    prompt = f"""
Você é um analista sênior de PE/VC, escrevendo a SEÇÃO FUNDADORES E TIME de um MEMO COMPLETO para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS
═══════════════════════════════════════════════════════════════════════

TIME:
{team_section}

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
ESTRUTURA OBRIGATÓRIA (5-7 parágrafos)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Fundadores: Background e Experiência
§ PARÁGRAFO 2 - Founder-Market Fit
§ PARÁGRAFO 3 - Time de Liderança (C-Level)
§ PARÁGRAFO 4 - Estrutura de Equity e Alinhamento
§ PARÁGRAFO 5 - Capacidade de Execução
§ PARÁGRAFO 6 - Gaps e Contratações Necessárias
§ PARÁGRAFO 7 - Avaliação Geral do Time

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Analista sênior de PE/VC escrevendo MEMO COMPLETO."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())


def generate_transaction_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Estrutura da Transação COMPLETA para Memo Primário.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    trx = facts.get("transaction_structure", {})
    currency = trx.get("currency") or "BRL"
    currency_label = get_currency_label(currency)

    transaction_section = build_facts_section(
        facts, "transaction_structure",
        {
            "round_size_mm": f"Tamanho da rodada ({currency_label})",
            "pre_money_mm": f"Pre-money ({currency_label})",
            "post_money_mm": f"Post-money ({currency_label})",
            "stake_pct": "Participação (%)",
            "investment_mm": f"Investimento Spectra ({currency_label})",
            "co_investors": "Co-investidores",
            "lead_investor": "Lead investor",
            "round_type": "Tipo de rodada",
            "use_of_proceeds": "Uso dos recursos",
            "key_terms": "Termos-chave",
            "liquidation_preference": "Liquidation preference",
            "anti_dilution": "Anti-dilution",
            "board_seats": "Assentos no board",
            "pro_rata_rights": "Pro-rata rights",
        }
    )

    prompt = f"""
Você é um analista sênior de PE/VC, escrevendo a SEÇÃO ESTRUTURA DA TRANSAÇÃO de um MEMO COMPLETO para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS
═══════════════════════════════════════════════════════════════════════

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

    prompt += """
═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA (5-7 parágrafos)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Visão Geral da Rodada
§ PARÁGRAFO 2 - Valuation e Múltiplos
§ PARÁGRAFO 3 - Sindicato de Investidores
§ PARÁGRAFO 4 - Uso dos Recursos
§ PARÁGRAFO 5 - Termos Econômicos (Liquidation Pref, Anti-dilution)
§ PARÁGRAFO 6 - Governança e Direitos
§ PARÁGRAFO 7 - Comparação com Mercado

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Analista sênior de PE/VC escrevendo MEMO COMPLETO."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())


def generate_projections_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Projeções e Saída COMPLETA para Memo Primário.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    trx = facts.get("transaction_structure", {})
    currency = trx.get("currency") or "BRL"
    currency_label = get_currency_label(currency)

    projections_section = build_facts_section(
        facts, "projections",
        {
            "revenue_projected_mm": f"Receita projetada ({currency_label})",
            "revenue_cagr_projected_pct": "CAGR receita projetado (%)",
            "ebitda_projected_mm": f"EBITDA projetado ({currency_label})",
            "arr_projected_mm": f"ARR projetado ({currency_label})",
            "profitability_timeline": "Timeline para rentabilidade",
            "next_round_size_mm": f"Próxima rodada ({currency_label})",
            "next_round_timeline": "Timeline próxima rodada",
        }
    )
    
    returns_section = build_facts_section(
        facts, "returns",
        {
            "target_irr_pct": "IRR alvo (%)",
            "target_moic": "MOIC alvo (x)",
            "holding_period_years": "Holding period (anos)",
            "exit_routes": "Rotas de saída",
            "exit_multiples": "Múltiplos de saída",
        }
    )

    prompt = f"""
Você é um analista sênior de PE/VC, escrevendo a SEÇÃO PROJEÇÕES E SAÍDA de um MEMO COMPLETO para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS
═══════════════════════════════════════════════════════════════════════

PROJEÇÕES:
{projections_section}

RETORNOS:
{returns_section}
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
ESTRUTURA OBRIGATÓRIA (5-7 parágrafos)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Premissas do Cenário Base
§ PARÁGRAFO 2 - Projeções de Receita e ARR
§ PARÁGRAFO 3 - Evolução para Rentabilidade
§ PARÁGRAFO 4 - Tese de Saída
§ PARÁGRAFO 5 - Retornos no Cenário Base
§ PARÁGRAFO 6 - Cenários Upside e Downside
§ PARÁGRAFO 7 - Sensibilidade e Riscos

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Analista sênior de PE/VC escrevendo MEMO COMPLETO."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())


def generate_risks_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Riscos COMPLETA para Memo Primário.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    qualitative_section = build_facts_section(
        facts, "qualitative",
        {
            "key_risks": "Principais riscos",
            "execution_risks": "Riscos de execução",
            "market_risks": "Riscos de mercado",
            "technology_risks": "Riscos tecnológicos",
            "funding_risks": "Riscos de funding",
            "mitigations": "Mitigações",
        }
    )

    prompt = f"""
Você é um analista sênior de PE/VC, escrevendo a SEÇÃO RISCOS de um MEMO COMPLETO para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS
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
ESTRUTURA OBRIGATÓRIA (5-7 parágrafos)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Riscos de Execução
§ PARÁGRAFO 2 - Riscos de Mercado
§ PARÁGRAFO 3 - Riscos de Time
§ PARÁGRAFO 4 - Riscos de Funding
§ PARÁGRAFO 5 - Riscos Tecnológicos
§ PARÁGRAFO 6 - Riscos de Diluição
§ PARÁGRAFO 7 - Matriz de Riscos e Mitigações

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Analista sênior de PE/VC escrevendo MEMO COMPLETO."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())


# ============================================================================
# ROUTER PRINCIPAL
# ============================================================================

def generate_section(
    section_name: str,
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Router principal para gerar qualquer seção de Memo Completo Primário.
    """
    section_map = {
        "intro": generate_intro_section,
        "introduction": generate_intro_section,
        "introducao": generate_intro_section,
        "company": generate_company_section,
        "empresa": generate_company_section,
        "market": generate_market_section,
        "mercado": generate_market_section,
        "financials": generate_financials_section,
        "financeiro": generate_financials_section,
        "founders": generate_founders_section,
        "fundadores": generate_founders_section,
        "team": generate_founders_section,
        "time": generate_founders_section,
        "transaction": generate_transaction_section,
        "transacao": generate_transaction_section,
        "projections": generate_projections_section,
        "projecoes": generate_projections_section,
        "risks": generate_risks_section,
        "riscos": generate_risks_section,
    }
    
    section_key = section_name.lower().replace(" ", "_")
    
    if section_key not in section_map:
        raise ValueError(f"Seção '{section_name}' não implementada. Disponíveis: {list(section_map.keys())}")
    
    generator_func = section_map[section_key]
    return generator_func(facts, rag_context, model, temperature)
