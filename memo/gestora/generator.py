"""
Geração de seções para Memo Completo Gestora

Funções especializadas para análise COMPLETA de gestoras de fundos.
Versão expandida (~20 páginas) com 5-8 parágrafos por seção.

FOCO: Track record, estratégia, time, termos do fundo
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
    Gera seção de Introdução COMPLETA para Memo Gestora.
    
    EXTENSÃO: 5-7 parágrafos com contexto completo da gestora e fundo.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    identification_section = build_facts_section(
        facts, "identification",
        {
            "fund_manager_name": "Nome da gestora",
            "fund_name": "Nome do fundo",
            "fund_vintage": "Vintage do fundo",
            "fund_size_mm": "Tamanho alvo (MM)",
            "fund_strategy": "Estratégia",
            "investment_focus": "Foco de investimento",
            "founding_year": "Ano de fundação",
            "headquarters": "Sede",
            "aum_mm": "AUM total (MM)",
        }
    )
    
    trx = facts.get("transaction_structure", {})
    currency = trx.get("currency") or "BRL"
    currency_label = get_currency_label(currency)
    
    transaction_section = build_facts_section(
        facts, "transaction_structure",
        {
            "commitment_mm": f"Compromisso solicitado ({currency_label})",
            "ownership_pct": "Participação no fundo (%)",
            "management_fee_pct": "Taxa de administração (%)",
            "carried_interest_pct": "Carried interest (%)",
            "hurdle_rate_pct": "Hurdle rate (%)",
            "fund_term_years": "Prazo do fundo (anos)",
            "investment_period_years": "Período de investimento (anos)",
        }
    )
    
    returns_section = build_facts_section(
        facts, "returns",
        {
            "target_irr_net_pct": "IRR líquido alvo (%)",
            "target_moic_net": "MOIC líquido alvo (x)",
            "historical_irr_gross_pct": "IRR bruto histórico (%)",
            "historical_moic_gross": "MOIC bruto histórico (x)",
        }
    )
    
    qualitative_section = build_facts_section(
        facts, "qualitative",
        {
            "investment_thesis": "Tese de investimento",
            "competitive_advantages": "Diferenciais da gestora",
            "key_persons": "Pessoas-chave",
        }
    )

    prompt = f"""
Você é um analista sênior de private equity escrevendo a SEÇÃO INTRODUÇÃO de um MEMO COMPLETO de análise de gestora para o comitê de investimento da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DA GESTORA/FUNDO
═══════════════════════════════════════════════════════════════════════

IDENTIFICAÇÃO:
{identification_section}

TRANSAÇÃO:
{transaction_section}

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

    prompt += """
═══════════════════════════════════════════════════════════════════════
ESTRUTURA OBRIGATÓRIA (5-7 parágrafos - MEMO COMPLETO)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Abertura e Contexto:
   - Apresentação da gestora e do fundo em avaliação
   - Histórico resumido da gestora (fundação, evolução)
   - Posicionamento no mercado

§ PARÁGRAFO 2 - Estratégia e Foco:
   - Estratégia de investimento
   - Setores e estágios foco
   - Tese de geração de valor

§ PARÁGRAFO 3 - Termos do Fundo:
   - Tamanho alvo, management fee, carry
   - Prazo e período de investimento
   - Estrutura de governança

§ PARÁGRAFO 4 - Track Record:
   - Performance de fundos anteriores
   - IRR e MOIC brutos e líquidos
   - Número de exits e realizations

§ PARÁGRAFO 5 - Compromisso Solicitado:
   - Valor do commitment proposto
   - Participação no fundo
   - Relacionamento existente com a gestora

§ PARÁGRAFO 6 - Pontos Positivos:
   - "Acreditamos que vale comprometer capital por..."
   - Lista de 3-5 razões com justificativa

§ PARÁGRAFO 7 - Pontos de Atenção:
   - "Os principais pontos de atenção são..."
   - Lista de 3-5 riscos/validações

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE escrevendo MEMO COMPLETO para IC da Spectra Capital."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())


def generate_track_record_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Track Record COMPLETA para Memo Gestora.
    
    EXTENSÃO: 6-8 parágrafos com análise detalhada de performance.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    trx = facts.get("transaction_structure", {})
    currency = trx.get("currency") or "BRL"
    currency_label = get_currency_label(currency)

    track_record_section = build_facts_section(
        facts, "track_record",
        {
            "funds_managed_count": "Número de fundos",
            "total_aum_mm": f"AUM total ({currency_label})",
            "total_investments": "Total de investimentos",
            "realized_investments": "Investimentos realizados",
            "realized_irr_gross_pct": "IRR bruto realizado (%)",
            "realized_moic_gross": "MOIC bruto realizado (x)",
            "unrealized_investments": "Investimentos não realizados",
            "unrealized_value_mm": f"Valor não realizado ({currency_label})",
            "loss_ratio_pct": "Taxa de perda (%)",
            "write_offs_count": "Write-offs",
        }
    )
    
    fund_details = build_facts_section(
        facts, "fund_details",
        {
            "fund_i_vintage": "Fund I vintage",
            "fund_i_size_mm": "Fund I tamanho (MM)",
            "fund_i_irr_gross_pct": "Fund I IRR bruto (%)",
            "fund_i_moic_gross": "Fund I MOIC bruto (x)",
            "fund_ii_vintage": "Fund II vintage",
            "fund_ii_size_mm": "Fund II tamanho (MM)",
            "fund_ii_irr_gross_pct": "Fund II IRR bruto (%)",
            "fund_ii_moic_gross": "Fund II MOIC bruto (x)",
            "fund_iii_vintage": "Fund III vintage",
            "fund_iii_size_mm": "Fund III tamanho (MM)",
            "fund_iii_irr_gross_pct": "Fund III IRR bruto (%)",
            "fund_iii_moic_gross": "Fund III MOIC bruto (x)",
        }
    )

    prompt = f"""
Você é um analista sênior de PE escrevendo a SEÇÃO TRACK RECORD de um MEMO COMPLETO de gestora para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DO TRACK RECORD
═══════════════════════════════════════════════════════════════════════

TRACK RECORD:
{track_record_section}

DETALHES POR FUNDO:
{fund_details}
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

§ PARÁGRAFO 1 - Visão Geral do Track Record:
  - Número de fundos e investimentos totais
  - Performance consolidada (IRR/MOIC brutos)
  - Comparação com benchmarks de mercado

§ PARÁGRAFO 2 - Performance por Fundo:
  - Detalhamento de cada fundo (vintage, tamanho, IRR, MOIC)
  - Evolução da performance ao longo dos fundos
  - Consistência de retornos

§ PARÁGRAFO 3 - Realizações (Exits):
  - Número de exits completos
  - IRR e MOIC das realizações
  - Principais exits de destaque

§ PARÁGRAFO 4 - Portfolio Não Realizado:
  - Composição do portfolio atual
  - Valorização implícita vs custo
  - Perspectivas de saída

§ PARÁGRAFO 5 - Análise de Perdas:
  - Taxa de perda histórica
  - Write-offs e impairments
  - Lições aprendidas

§ PARÁGRAFO 6 - Atribuição de Performance:
  - Principais drivers de retorno
  - Contribuição por investimento
  - Alpha vs beta de mercado

§ PARÁGRAFO 7 - Validações com LPs:
  - Feedback de outros investidores
  - Histórico de re-ups
  - Referências coletadas

§ PARÁGRAFO 8 - Comparação com Peers:
  - Posicionamento vs gestoras comparáveis
  - Quartil de performance
  - Diferenciação competitiva

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE escrevendo MEMO COMPLETO para Spectra Capital."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())


def generate_team_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Time COMPLETA para Memo Gestora.
    
    EXTENSÃO: 5-7 parágrafos com análise profunda do time.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    team_section = build_facts_section(
        facts, "team",
        {
            "partners_count": "Número de sócios",
            "investment_professionals_count": "Profissionais de investimento",
            "total_headcount": "Headcount total",
            "founding_partners": "Sócios fundadores",
            "partner_backgrounds": "Background dos sócios",
            "partner_tenure_years": "Tenure médio (anos)",
            "team_turnover": "Turnover do time",
            "carry_allocation": "Alocação de carry",
            "key_person_provisions": "Key person provisions",
        }
    )
    
    qualitative_section = build_facts_section(
        facts, "qualitative",
        {
            "team_strengths": "Pontos fortes do time",
            "team_weaknesses": "Pontos fracos do time",
            "succession_plan": "Plano de sucessão",
            "culture": "Cultura organizacional",
        }
    )

    prompt = f"""
Você é um analista sênior de PE escrevendo a SEÇÃO TIME de um MEMO COMPLETO de gestora para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DO TIME
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
ESTRUTURA OBRIGATÓRIA (5-7 parágrafos - MEMO COMPLETO)
═══════════════════════════════════════════════════════════════════════

§ PARÁGRAFO 1 - Composição do Time:
  - Número de sócios e profissionais
  - Estrutura organizacional
  - Histórico de estabilidade

§ PARÁGRAFO 2 - Sócios Fundadores:
  - Background de cada sócio-chave
  - Experiência relevante pré-gestora
  - Complementaridade de skills

§ PARÁGRAFO 3 - Time de Investimentos:
  - Profissionais de investimento
  - Experiência e formação
  - Capacidade de sourcing e execução

§ PARÁGRAFO 4 - Alinhamento e Incentivos:
  - Alocação de carry
  - Co-invest dos sócios
  - Mecanismos de retenção

§ PARÁGRAFO 5 - Key Person e Sucessão:
  - Key person provisions
  - Plano de sucessão
  - Riscos de concentração

§ PARÁGRAFO 6 - Cultura e Valores:
  - Cultura organizacional
  - Processo decisório
  - Governança interna

§ PARÁGRAFO 7 - Avaliação Geral:
  - Pontos fortes do time
  - Pontos de atenção
  - Comparação com peers

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE escrevendo MEMO COMPLETO para Spectra Capital."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())


def generate_strategy_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Estratégia COMPLETA para Memo Gestora.
    
    EXTENSÃO: 5-7 parágrafos com análise detalhada da estratégia.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    strategy_section = build_facts_section(
        facts, "strategy",
        {
            "investment_strategy": "Estratégia de investimento",
            "target_sectors": "Setores alvo",
            "target_stages": "Estágios alvo",
            "target_ticket_mm": "Ticket alvo (MM)",
            "target_ev_mm": "EV alvo (MM)",
            "target_ownership_pct": "Participação alvo (%)",
            "value_creation_approach": "Abordagem de criação de valor",
            "exit_strategy": "Estratégia de saída",
            "geography_focus": "Foco geográfico",
        }
    )
    
    qualitative_section = build_facts_section(
        facts, "qualitative",
        {
            "investment_thesis": "Tese de investimento",
            "competitive_advantages": "Vantagens competitivas",
            "sourcing_approach": "Abordagem de sourcing",
            "due_diligence_process": "Processo de due diligence",
            "portfolio_support": "Suporte a portfólio",
        }
    )

    prompt = f"""
Você é um analista sênior de PE escrevendo a SEÇÃO ESTRATÉGIA de um MEMO COMPLETO de gestora para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DA ESTRATÉGIA
═══════════════════════════════════════════════════════════════════════

ESTRATÉGIA:
{strategy_section}

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

§ PARÁGRAFO 1 - Estratégia Geral:
  - Posicionamento da gestora
  - Estratégia de investimento
  - Diferenciação no mercado

§ PARÁGRAFO 2 - Foco de Investimento:
  - Setores e estágios alvo
  - Tamanho de ticket e EV
  - Participação buscada

§ PARÁGRAFO 3 - Sourcing e Origination:
  - Abordagem de sourcing
  - Rede de relacionamentos
  - Pipeline e funnel

§ PARÁGRAFO 4 - Processo de Investimento:
  - Due diligence process
  - Comitê de investimento
  - Tempo médio de execução

§ PARÁGRAFO 5 - Criação de Valor:
  - Abordagem pós-investimento
  - Recursos de portfolio support
  - Value creation playbook

§ PARÁGRAFO 6 - Estratégia de Saída:
  - Rotas de saída preferidas
  - Histórico de exits
  - Tempo médio de holding

§ PARÁGRAFO 7 - Evolução da Estratégia:
  - Mudanças vs fundos anteriores
  - Adaptação ao mercado
  - Consistência vs flexibilidade

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE escrevendo MEMO COMPLETO para Spectra Capital."),
        HumanMessage(content=prompt),
    ]
    
    result = llm.invoke(messages)
    return fix_number_formatting(result.content.strip())


def generate_terms_section(
    facts: Dict[str, Any],
    rag_context: Optional[str] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> str:
    """
    Gera seção Termos do Fundo COMPLETA para Memo Gestora.
    
    EXTENSÃO: 5-7 parágrafos com análise detalhada dos termos.
    """
    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise ValueError("OPENAI_API_KEY não encontrada no ambiente")

    llm = ChatOpenAI(model=model, api_key=apikey, temperature=temperature)

    trx = facts.get("transaction_structure", {})
    currency = trx.get("currency") or "BRL"
    currency_label = get_currency_label(currency)

    terms_section = build_facts_section(
        facts, "transaction_structure",
        {
            "fund_size_mm": f"Tamanho do fundo ({currency_label})",
            "fund_size_hard_cap_mm": f"Hard cap ({currency_label})",
            "management_fee_pct": "Taxa de administração (%)",
            "management_fee_base": "Base da taxa de administração",
            "carried_interest_pct": "Carried interest (%)",
            "hurdle_rate_pct": "Hurdle rate (%)",
            "catch_up_pct": "Catch-up (%)",
            "fund_term_years": "Prazo do fundo (anos)",
            "investment_period_years": "Período de investimento (anos)",
            "extension_options": "Opções de extensão",
            "gp_commitment_pct": "GP commitment (%)",
            "key_person_events": "Key person events",
            "no_fault_divorce": "No fault divorce",
            "recycling_provisions": "Recycling provisions",
        }
    )

    prompt = f"""
Você é um analista sênior de PE escrevendo a SEÇÃO TERMOS DO FUNDO de um MEMO COMPLETO de gestora para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS DOS TERMOS
═══════════════════════════════════════════════════════════════════════

TERMOS:
{terms_section}
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

§ PARÁGRAFO 1 - Tamanho e Estrutura:
  - Tamanho alvo e hard cap
  - Base de LPs atual
  - Estrutura jurídica

§ PARÁGRAFO 2 - Taxas de Administração:
  - Management fee e base de cálculo
  - Evolução ao longo do fundo
  - Comparação com mercado

§ PARÁGRAFO 3 - Carried Interest:
  - Carry e hurdle rate
  - Catch-up provisions
  - Waterfall de distribuição

§ PARÁGRAFO 4 - GP Commitment e Alinhamento:
  - GP commitment em valor e %
  - Alinhamento de interesses
  - Co-invest rights

§ PARÁGRAFO 5 - Prazo e Extensões:
  - Fund term e investment period
  - Opções de extensão
  - Recycling provisions

§ PARÁGRAFO 6 - Governança e Proteções:
  - Key person provisions
  - No fault divorce
  - LPAC e direitos dos LPs

§ PARÁGRAFO 7 - Avaliação Geral:
  - Termos vs padrão de mercado
  - Pontos favoráveis aos LPs
  - Pontos de negociação

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE escrevendo MEMO COMPLETO para Spectra Capital."),
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
    Gera seção Riscos COMPLETA para Memo Gestora.
    
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
            "strategy_drift_risk": "Risco de strategy drift",
            "market_risks": "Riscos de mercado",
            "operational_risks": "Riscos operacionais",
            "mitigations": "Mitigações propostas",
        }
    )

    prompt = f"""
Você é um analista sênior de PE escrevendo a SEÇÃO RISCOS de um MEMO COMPLETO de gestora para IC da Spectra Capital.

═══════════════════════════════════════════════════════════════════════
DADOS QUALITATIVOS
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

§ PARÁGRAFO 1 - Riscos de Time:
  - Key person risk
  - Estabilidade do time
  - Plano de sucessão
  - Mitigações

§ PARÁGRAFO 2 - Riscos de Estratégia:
  - Strategy drift
  - Execução da tese
  - Mudanças de mercado
  - Mitigações

§ PARÁGRAFO 3 - Riscos de Performance:
  - Sustentabilidade do track record
  - J-curve prolongada
  - Portfolio risk
  - Mitigações

§ PARÁGRAFO 4 - Riscos de Mercado:
  - Ambiente competitivo
  - Valuations elevados
  - Exit environment
  - Mitigações

§ PARÁGRAFO 5 - Riscos Operacionais:
  - Capacidade operacional
  - Crescimento da gestora
  - Infraestrutura
  - Mitigações

§ PARÁGRAFO 6 - Riscos de Alinhamento:
  - Conflitos de interesse
  - Allocation policy
  - Termos desfavoráveis
  - Mitigações

§ PARÁGRAFO 7 - Matriz de Riscos:
  - Top 3 riscos críticos
  - Classificação probabilidade x impacto
  - Recomendações de due diligence adicional

Gere apenas texto corrido (SEM títulos, SEM markdown).
"""

    messages = [
        SystemMessage(content="Você é um analista sênior de PE escrevendo MEMO COMPLETO para Spectra Capital."),
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
    Router principal para gerar qualquer seção de Memo Completo Gestora.
    """
    section_map = {
        "intro": generate_intro_section,
        "introduction": generate_intro_section,
        "introducao": generate_intro_section,
        "track_record": generate_track_record_section,
        "trackrecord": generate_track_record_section,
        "performance": generate_track_record_section,
        "team": generate_team_section,
        "time": generate_team_section,
        "equipe": generate_team_section,
        "strategy": generate_strategy_section,
        "estrategia": generate_strategy_section,
        "terms": generate_terms_section,
        "termos": generate_terms_section,
        "risks": generate_risks_section,
        "riscos": generate_risks_section,
    }
    
    section_key = section_name.lower().replace(" ", "_")
    
    if section_key not in section_map:
        raise ValueError(f"Seção '{section_name}' não implementada. Disponíveis: {list(section_map.keys())}")
    
    generator_func = section_map[section_key]
    return generator_func(facts, rag_context, model, temperature)
