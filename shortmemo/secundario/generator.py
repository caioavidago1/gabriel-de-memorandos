"""
Geração de seções para Short Memo Secundário

Funções especializadas para análise de empresas maduras com foco em cash yield.
Seguindo padrão estabelecido em shortmemo/searchfund/generator.py

FOCO: FCF, geração de caixa estável, dividend recapitalization, ROIC
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os

from ..searchfund.shared import build_facts_section
from ..format_utils import get_currency_symbol, get_currency_label
from .validator import fix_number_formatting, validate_memo_consistency
from .portfolio_agent import PortfolioAgent


def generate_intro_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção de Introdução para Short Memo Secundário.
    
    PADRÃO OBRIGATÓRIO - Primeira frase:
    "Estamos avaliando a {company}, líder no segmento de {setor} com receita de
     {currency} {receita} e margem EBITDA de {margin}%."
    
    Args:
        facts: Dict com facts estruturados (todas as seções)
        rag_context: Contexto extraído do documento (opcional)
        model: Modelo OpenAI a usar
        temperature: Criatividade (0.0-1.0)
    
    Returns:
        Texto da introdução (3-4 parágrafos)
    
    Raises:
        ValueError: Se OPENAI_API_KEY não configurada
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    # ===== CONSTRÓI SEÇÕES DE FACTS (OMITE None) =====
    identification_section = build_facts_section(
        facts, "identification",
        {
            "company_name": "Nome da empresa",
            "business_description": "Descrição do negócio",
            "company_location": "Localização",
            "company_founding_year": "Ano de fundação",
        }
    )
    
    # Obtém moeda
    trx = facts.get("transaction_structure", {})
    currency = trx.get("currency") or "BRL"
    currency_symbol = get_currency_symbol(currency)
    currency_label = get_currency_label(currency)
    
    transaction_section = build_facts_section(
        facts, "transaction_structure",
        {
            "stake_pct": "Participação (%)",
            "ev_mm": f"EV ({currency_label})",
            "equity_value_mm": f"Equity Value ({currency_label})",
            "multiple_ev_ebitda": "Múltiplo EV/EBITDA",
            "multiple_ev_fcf": "Múltiplo EV/FCF",
            "leverage_net_debt_ebitda": "Dívida Líquida/EBITDA",
        }
    )
    
    financials_section = build_facts_section(
        facts, "financials_history",
        {
            "revenue_current_mm": f"Receita atual ({currency_label})",
            "revenue_cagr_pct": "CAGR receita (%)",
            "ebitda_current_mm": f"EBITDA atual ({currency_label})",
            "ebitda_margin_current_pct": "Margem EBITDA (%)",
            "fcf_current_mm": f"FCF atual ({currency_label})",
            "fcf_conversion_pct": "Conversão FCF (%)",
            "roic_pct": "ROIC (%)",
        }
    )
    
    returns_section = build_facts_section(
        facts, "returns",
        {
            "irr_pct": "IRR alvo (%)",
            "moic": "MOIC alvo (x)",
            "fcf_yield_pct": "FCF yield (%)",
            "holding_period_years": "Holding period (anos)",
            "dividend_recaps": "Dividend recaps planejados",
        }
    )

    # ========== EXTRAI INFORMAÇÕES PARA CONTEXTO ==========
    idf = facts.get("identification", {})
    fin = facts.get("financials_history", {})
    
    company_name = idf.get("company_name") or "a empresa"
    # Setor pode vir do business_description ou ser inferido
    sector = "[setor]"  # Campo não existe no schema, usar placeholder
    revenue = fin.get("revenue_current_mm") or "[receita]"
    ebitda_margin = fin.get("ebitda_margin_current_pct") or "[margem]"

    # ========== MONTA PROMPT ==========
    prompt = f"""
Você é um analista de private equity focado em secundário, escrevendo a SEÇÃO INTRODUÇÃO de um short memo para comitê de investimento da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DO DEAL ATUAL
═══════════════════════════════════════════════════════════════════════

DADOS ESTRUTURADOS (facts):

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
CONTEXTO DO DOCUMENTO ORIGINAL (use para enriquecer)
═══════════════════════════════════════════════════════════════════════

{rag_context}
"""

    prompt += f"""
═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA (3-4 parágrafos - SIGA EXATAMENTE)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 (obrigatório):
   - Abertura OBRIGATÓRIA seguindo o padrão Secundário:
   
   "Estamos avaliando a {company_name}, líder no segmento de {sector} com receita de {currency_symbol} {revenue}m e margem EBITDA de {ebitda_margin}%."
   
   - Mencione imediatamente: posição de mercado, estabilidade do negócio

§ PARÁGRAFO 2:
   - Tese de investimento: "A tese se baseia em geração de caixa previsível..."
   - FCF yield, conversão de caixa, potencial para dividend recaps
   - "O mercado é maduro com crescimento de ~X% ao ano"

§ PARÁGRAFO 3:
   - Estrutura da transação: valuation, múltiplos (EV/EBITDA, EV/FCF)
   - Alavancagem: Dívida/EBITDA
   - Retornos: IRR, MOIC (com componentes: FCF + growth + exit)

§ PARÁGRAFO 4:
   - Opinião Spectra: "Acreditamos que vale aprofundar pelas seguintes razões..."
   - Pontos de atenção: "Precisaremos validar: (i) [ponto 1], (ii) [ponto 2]..."
   - Foco em riscos de downside e estabilidade

REGRAS DE ESTILO (CRÍTICAS):
- Tom conservador, foco em proteção de downside
- Use números exatamente como fornecidos
- Não crie títulos, bullets ou numerações; produza apenas parágrafos separados por linha em branco
"""

    messages = [
        SystemMessage(
            content="Você é um analista de private equity com 15 anos de experiência em secundário, escrevendo a INTRODUÇÃO de um short memo para a Spectra Capital."
        ),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    generated_text = result.content.strip()
    
    # Aplicar correções de formatação
    corrected_text = fix_number_formatting(generated_text)
    
    return corrected_text


def generate_financials_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Histórico Financeiro para Short Memo Secundário.
    
    FOCO: Estabilidade histórica, FCF, conversão de caixa, margens.
    
    Args:
        facts: Dict com facts estruturados
        rag_context: Contexto do documento (opcional)
        model: Modelo OpenAI
        temperature: Criatividade
    
    Returns:
        Texto da seção Financials (3-5 parágrafos)
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    trx = facts.get("transaction_structure", {})
    currency = trx.get("currency") or "BRL"
    currency_label = get_currency_label(currency)

    # ===== FACTS =====
    financials_section = build_facts_section(
        facts, "financials_history",
        {
            "revenue_current_mm": f"Receita atual ({currency_label})",
            "revenue_cagr_pct": "CAGR receita (%)",
            "revenue_history": "Histórico receita (5 anos)",
            "ebitda_current_mm": f"EBITDA atual ({currency_label})",
            "ebitda_margin_current_pct": "Margem EBITDA (%)",
            "ebitda_margin_history": "Histórico margem EBITDA",
            "fcf_current_mm": f"FCF atual ({currency_label})",
            "fcf_conversion_pct": "Conversão FCF (% EBITDA)",
            "capex_mm": f"Capex ({currency_label})",
            "capex_pct_revenue": "Capex (% receita)",
            "working_capital_days": "Working capital (dias)",
        }
    )
    
    # Estrutura de capital vem de financials_history
    capital_structure_section = build_facts_section(
        facts, "financials_history",
        {
            "net_debt_mm": f"Dívida líquida ({currency_label})",
            "leverage_net_debt_ebitda": "Dívida/EBITDA",
            "roic_pct": "ROIC (%)",
        }
    )

    prompt = f"""
Você é um analista de private equity focado em secundário, escrevendo a SEÇÃO HISTÓRICO FINANCEIRO de um short memo para comitê de investimento da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DO DEAL
═══════════════════════════════════════════════════════════════════════

FINANCIALS:
{financials_section}

ESTRUTURA DE CAPITAL:
{capital_structure_section}
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
ESTRUTURA (3-5 parágrafos)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1: Receita e Crescimento Histórico
  - Receita atual e CAGR dos últimos 5 anos
  - Destaque estabilidade: "crescimento moderado de X% ao ano"
  - Sazonalidade mínima se aplicável

§ PARÁGRAFO 2: Margens e Eficiência
  - Margem EBITDA e estabilidade histórica
  - "margem estável entre X-Y% nos últimos 5 anos"
  - Mencionar riscos de erosão se aplicável

§ PARÁGRAFO 3: FCF e Conversão de Caixa
  - FCF atual e histórico
  - Conversão de FCF (% do EBITDA)
  - "alta conversão de X% do EBITDA demonstra..."

§ PARÁGRAFO 4: Capex e Capital de Giro
  - Capex sustentável (baixo para empresa madura)
  - Working capital needs
  - Modelo de baixa intensidade de capital

§ PARÁGRAFO 5: Estrutura de Capital
  - Dívida líquida/EBITDA
  - ROIC, ROE
  - Capacidade para dividend recaps

REGRA DE OURO:
- Foco em ESTABILIDADE e PREVISIBILIDADE
- Compare sempre com histórico (5 anos)
- Sinalize volatilidade como red flag

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Você é um analista de PE secundário escrevendo para a Spectra Capital."),
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
    Gera seção Estrutura da Transação para Short Memo Secundário.
    
    FOCO: Valuation, alavancagem, plano de distribuições.
    
    Args:
        facts: Dict com facts estruturados
        rag_context: Contexto do documento (opcional)
        model: Modelo OpenAI
        temperature: Criatividade
    
    Returns:
        Texto da seção Transaction (3-4 parágrafos)
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    trx = facts.get("transaction_structure", {})
    currency = trx.get("currency") or "BRL"
    currency_label = get_currency_label(currency)

    # ===== FACTS =====
    transaction_section = build_facts_section(
        facts, "transaction_structure",
        {
            "stake_pct": "Participação (%)",
            "ev_mm": f"EV ({currency_label})",
            "equity_value_mm": f"Equity Value ({currency_label})",
            "multiple_ev_ebitda": "Múltiplo EV/EBITDA",
            "multiple_ev_fcf": "Múltiplo EV/FCF",
            "target_leverage": "Alavancagem alvo (Dívida/EBITDA)",
            "acquisition_debt_mm": f"Dívida de aquisição ({currency_label})",
        }
    )
    
    returns_section = build_facts_section(
        facts, "returns",
        {
            "irr_pct": "IRR alvo (%)",
            "moic": "MOIC alvo (x)",
            "fcf_yield_pct": "FCF yield (%)",
            "dividend_recaps": "Dividend recaps planejados",
            "exit_multiple": "Múltiplo de saída",
            "holding_period_years": "Holding period (anos)",
        }
    )

    prompt = f"""
Você é um analista de private equity focado em secundário, escrevendo a SEÇÃO ESTRUTURA DA TRANSAÇÃO de um short memo para comitê de investimento da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DO DEAL
═══════════════════════════════════════════════════════════════════════

TRANSAÇÃO:
{transaction_section}

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
ESTRUTURA (3-4 parágrafos)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1: Valuation e Múltiplos
  - EV, Equity Value, participação adquirida
  - Múltiplo EV/EBITDA vs comparáveis maduros
  - "múltiplo de Xx vs média de peers de Yx"

§ PARÁGRAFO 2: Estrutura de Capital
  - Alavancagem alvo (Dívida/EBITDA)
  - Debt service coverage ratio
  - "alavancagem conservadora de X permite..."

§ PARÁGRAFO 3: Plano de Distribuições
  - FCF yield e potencial para dividendos
  - Dividend recapitalization structure
  - "FCF de Xm/ano permite distribuições anuais de..."

§ PARÁGRAFO 4: Retornos
  - IRR e MOIC com breakdown:
  - "IRR de X% composto por: Y% FCF yield + Z% crescimento + W% múltiplo"
  - Foco em cash-on-cash return

REGRA DE OURO:
- Alavancagem CONSERVADORA (2-3x Dívida/EBITDA)
- Retorno vem principalmente do FCF, não de crescimento
- Múltiplo de saída FLAT (sem prêmio de crescimento)

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Você é um analista de PE secundário escrevendo para a Spectra Capital."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())


def generate_portfolio_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção de Portfólio para Short Memo Secundário.
    
    FOCO: NAV data base, expectativa de recebimento, timing de saída,
    comparação entre projeções do gestor vs Spectra.
    
    Args:
        facts: Dict com facts estruturados
        rag_context: Contexto do documento (opcional, mas CRÍTICO para dados de portfolio)
        model: Modelo OpenAI
        temperature: Criatividade
    
    Returns:
        Texto da seção Portfólio (múltiplos parágrafos, organizados por fundo → ativo)
    """
    agent = PortfolioAgent(model=model, temperature=temperature)
    return agent.generate(facts, rag_context)


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
    Router principal para gerar qualquer seção de memo Secundário.
    
    Args:
        section_name: Nome da seção ("intro", "financials", "transaction", etc.)
        facts: Facts estruturados
        rag_context: Contexto RAG opcional
        model: Modelo OpenAI
        temperature: Criatividade
    
    Returns:
        Texto gerado
    
    Raises:
        ValueError: Se seção desconhecida
    """
    section_map = {
        "intro": generate_intro_section,
        "introduction": generate_intro_section,
        "introducao": generate_intro_section,
        "financials": generate_financials_section,
        "financeiro": generate_financials_section,
        "historico_financeiro": generate_financials_section,
        "transaction": generate_transaction_section,
        "transacao": generate_transaction_section,
        "estrutura": generate_transaction_section,
        "portfolio": generate_portfolio_section,
        "portfólio": generate_portfolio_section,
        "portfolio_secundario": generate_portfolio_section,
    }
    
    # Normalizar nome da seção
    section_key = section_name.lower().replace("1. ", "").replace("2. ", "").replace("3. ", "").replace(" ", "_")
    
    if section_key not in section_map:
        raise ValueError(f"Seção '{section_name}' não implementada. Disponíveis: {list(section_map.keys())}")
    
    generator_func = section_map[section_key]
    return generator_func(facts, rag_context, model, temperature)
