"""
Schemas estruturados (Pydantic) para extração de facts com validação.

Cada seção tem um schema próprio com:
- Tipos validados (int, float, str, etc)
- Ranges permitidos (ge, le)
- Descrições detalhadas
- Validação automática

Uso: OpenAI Structured Output com response_format
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict
from datetime import date


class IdentificationFacts(BaseModel):
    """Schema para seção Identification - Dados da empresa/fundo"""
    model_config = ConfigDict(strict=True)
    
    company_name: Optional[str] = Field(
        None,
        description="Nome oficial da empresa ou fundo"
    )
    
    searcher_name: Optional[str] = Field(
        None,
        description="Nome do searcher (apenas para Search Fund)"
    )
    
    search_start_date: Optional[str] = Field(
        None,
        description="Data de início da busca (apenas para Search Fund), formato: 'Mês/Ano' ou 'Ano'"
    )
    
    business_description: Optional[str] = Field(
        None,
        description="Descrição do negócio da empresa-alvo ou tese do fundo"
    )
    
    investor_nationality: Optional[str] = Field(
        None,
        description="Nacionalidade do investidor/searcher"
    )
    
    company_location: Optional[str] = Field(
        None,
        description="Localização geográfica da empresa (cidade, estado, país)"
    )
    
    company_founding_year: Optional[int] = Field(
        None,
        ge=1800,
        le=2026,
        description="Ano de fundação da empresa"
    )
    
    deal_context: Optional[str] = Field(
        None,
        description="Contexto do deal: origem, processo competitivo, relacionamento com vendedor"
    )


class TransactionStructureFacts(BaseModel):
    """Schema para seção Transaction Structure - Estrutura da transação"""
    model_config = ConfigDict(strict=True)
    
    currency: Optional[str] = Field(
        None,
        description="Moeda da transação (BRL, USD, EUR, etc)"
    )
    
    investor_opinion: Optional[str] = Field(
        None,
        description="Opinião/visão do investidor sobre o deal"
    )
    
    stake_pct: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Percentual de participação adquirida (%)"
    )
    
    ev_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Enterprise Value em milhões"
    )
    
    equity_value_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Equity Value em milhões"
    )
    
    multiple_ev_ebitda: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Múltiplo EV/EBITDA de entrada"
    )
    
    multiple_reference_period: Optional[str] = Field(
        None,
        description="Período de referência do múltiplo (LTM, 2023, etc)"
    )
    
    cash_payment_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Pagamento em cash na entrada (milhões)"
    )
    
    seller_note_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Valor do seller note (milhões)"
    )
    
    seller_note_terms: Optional[str] = Field(
        None,
        description="Condições do seller note (prazo, juros, etc)"
    )
    
    earnout_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Valor potencial de earnout (milhões)"
    )
    
    earnout_conditions: Optional[str] = Field(
        None,
        description="Condições para pagamento do earnout"
    )
    
    multiple_with_earnout: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Múltiplo considerando earnout pago"
    )
    
    debt_equity_ratio: Optional[float] = Field(
        None,
        ge=0.0,
        description="Razão Dívida/Equity"
    )
    
    # Campos específicos para Short Memo - Secundário
    multiple_ev_fcf: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Múltiplo EV/FCF de entrada (específico para secundário)"
    )
    
    target_leverage: Optional[float] = Field(
        None,
        ge=0.0,
        description="Alavancagem alvo (Dívida/EBITDA) - específico para secundário"
    )
    
    acquisition_debt_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Dívida de aquisição (milhões) - específico para secundário"
    )


class FinancialsHistoryFacts(BaseModel):
    """Schema para seção Financials History - Histórico financeiro"""
    model_config = ConfigDict(strict=True)
    
    revenue_current_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Receita atual/mais recente (milhões)"
    )
    
    revenue_cagr_pct: Optional[float] = Field(
        None,
        ge=-100.0,
        le=1000.0,
        description="CAGR de receita (%)"
    )
    
    revenue_cagr_period: Optional[str] = Field(
        None,
        description="Período do CAGR de receita (ex: '2020-2023')"
    )
    
    revenue_base_year: Optional[str] = Field(
        None,
        description="Ano base para cálculo do CAGR"
    )
    
    revenue_base_year_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Receita no ano base (milhões)"
    )
    
    ebitda_current_mm: Optional[float] = Field(
        None,
        description="EBITDA atual/mais recente (milhões, pode ser negativo)"
    )
    
    ebitda_margin_current_pct: Optional[float] = Field(
        None,
        ge=-100.0,
        le=100.0,
        description="Margem EBITDA atual (%)"
    )
    
    ebitda_cagr_pct: Optional[float] = Field(
        None,
        ge=-100.0,
        le=2000.0,
        description="CAGR de EBITDA (%)"
    )
    
    ebitda_base_year_mm: Optional[float] = Field(
        None,
        description="EBITDA no ano base (milhões)"
    )
    
    net_debt_mm: Optional[float] = Field(
        None,
        description="Dívida líquida (milhões, pode ser negativa se caixa líquido)"
    )
    
    leverage_net_debt_ebitda: Optional[float] = Field(
        None,
        ge=0.0,
        description="Alavancagem Dívida Líquida/EBITDA"
    )
    
    cash_conversion_pct: Optional[float] = Field(
        None,
        ge=0.0,
        le=200.0,
        description="Conversão de caixa (% do EBITDA)"
    )
    
    gross_margin_pct: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Margem bruta (%)"
    )
    
    opex_pct_revenue: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Opex como % da receita"
    )
    
    employees_count: Optional[int] = Field(
        None,
        ge=0,
        description="Número de funcionários"
    )
    
    financials_commentary: Optional[str] = Field(
        None,
        description="Comentários sobre a performance financeira histórica"
    )
    
    # Campos específicos para Short Memo - Secundário
    fcf_current_mm: Optional[float] = Field(
        None,
        description="Free Cash Flow atual (milhões) - específico para secundário"
    )
    
    fcf_conversion_pct: Optional[float] = Field(
        None,
        ge=0.0,
        le=200.0,
        description="Conversão de FCF (% do EBITDA) - específico para secundário"
    )
    
    roic_pct: Optional[float] = Field(
        None,
        ge=-100.0,
        le=1000.0,
        description="ROIC (Return on Invested Capital) (%) - específico para secundário"
    )


class SaidaFacts(BaseModel):
    """Schema para seção Saída - Projeções e estratégia de exit"""
    model_config = ConfigDict(strict=True)
    
    revenue_exit_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Receita projetada no momento da saída (milhões)"
    )
    
    exit_year: Optional[int] = Field(
        None,
        ge=2024,
        le=2050,
        description="Ano projetado de saída"
    )
    
    revenue_cagr_projected_pct: Optional[float] = Field(
        None,
        ge=-50.0,
        le=500.0,
        description="CAGR de receita projetado até a saída (%)"
    )
    
    projection_period: Optional[str] = Field(
        None,
        description="Período de projeção (ex: '2024-2029', '5 anos')"
    )
    
    ebitda_exit_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="EBITDA projetado na saída (milhões)"
    )
    
    ebitda_margin_exit_pct: Optional[float] = Field(
        None,
        ge=-50.0,
        le=100.0,
        description="Margem EBITDA projetada na saída (%)"
    )
    
    ebitda_cagr_projected_pct: Optional[float] = Field(
        None,
        ge=-50.0,
        le=1000.0,
        description="CAGR de EBITDA projetado (%)"
    )
    
    exit_multiple_ev_ebitda: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Múltiplo EV/EBITDA esperado na saída"
    )
    
    exit_strategy: Optional[str] = Field(
        None,
        description="Estratégia de saída (trade sale, IPO, secundário, etc)"
    )
    
    growth_drivers: Optional[str] = Field(
        None,
        description="Principais drivers de crescimento até a saída"
    )
    
    value_creation_drivers: Optional[str] = Field(
        None,
        description="Principais drivers de criação de valor até a saída"
    )
    
    scenario_type: Optional[str] = Field(
        None,
        description="Tipo de cenário (base, otimista, pessimista, etc)"
    )
    
    projections_commentary: Optional[str] = Field(
        None,
        description="Comentários sobre as projeções e premissas"
    )
    
    exit_commentary: Optional[str] = Field(
        None,
        description="Comentários sobre a tese de saída e timing"
    )


class ReturnsFacts(BaseModel):
    """Schema para seção Returns - Retornos esperados"""
    model_config = ConfigDict(strict=True)
    
    irr_pct: Optional[float] = Field(
        None,
        ge=-100.0,
        le=1000.0,
        description="IRR (TIR) esperado (%)"
    )
    
    moic: Optional[float] = Field(
        None,
        ge=0.0,
        le=50.0,
        description="MOIC (múltiplo de dinheiro) esperado"
    )
    
    holding_period_years: Optional[float] = Field(
        None,
        ge=0.0,
        le=20.0,
        description="Período de holding esperado (anos)"
    )
    
    returns_commentary: Optional[str] = Field(
        None,
        description="Comentários sobre os retornos esperados e sensibilidades"
    )
    
    # Campos específicos para Short Memo - Secundário
    fcf_yield_pct: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="FCF yield (%) - específico para secundário"
    )
    
    dividend_recaps: Optional[str] = Field(
        None,
        description="Dividend recaps planejados - específico para secundário"
    )


class QualitativeFacts(BaseModel):
    """Schema para seção Qualitative - Análise qualitativa"""
    model_config = ConfigDict(strict=True)
    
    business_model: Optional[str] = Field(
        None,
        description="Descrição do modelo de negócio"
    )
    
    competitive_advantages: Optional[str] = Field(
        None,
        description="Vantagens competitivas e diferenciais da empresa"
    )
    
    market_overview: Optional[str] = Field(
        None,
        description="Visão geral do mercado e dinâmica competitiva"
    )
    
    key_risks: Optional[str] = Field(
        None,
        description="Principais riscos do investimento"
    )
    
    management_team: Optional[str] = Field(
        None,
        description="Avaliação do time de gestão"
    )
    
    growth_strategy: Optional[str] = Field(
        None,
        description="Estratégia de crescimento planejada"
    )
    
    esg_considerations: Optional[str] = Field(
        None,
        description="Considerações ESG relevantes"
    )
    
    qualitative_commentary: Optional[str] = Field(
        None,
        description="Outros comentários qualitativos relevantes"
    )
    
    main_competitors: Optional[str] = Field(
        None,
        description="Principais concorrentes da empresa"
    )
    
    competitor_count: Optional[int] = Field(
        None,
        ge=0,
        description="Número de concorrentes principais"
    )
    
    market_share_pct: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Participação de mercado da empresa (%)"
    )
    
    market_fragmentation: Optional[str] = Field(
        None,
        description="Nível de fragmentação do mercado (fragmentado, concentrado, etc)"
    )


class OpinioesFacts(BaseModel):
    """Schema para seção Opiniões - Opinião da Spectra"""
    model_config = ConfigDict(strict=True)
    
    spectra_recommendation: Optional[str] = Field(
        None,
        description="Recomendação final da Spectra (aprovar, rejeitar, aprovar com condições, etc)"
    )
    
    key_strengths: Optional[str] = Field(
        None,
        description="Principais pontos positivos identificados pela Spectra"
    )
    
    key_concerns: Optional[str] = Field(
        None,
        description="Principais preocupações identificadas pela Spectra"
    )
    
    investment_rationale: Optional[str] = Field(
        None,
        description="Racional de investimento da Spectra"
    )
    
    next_steps: Optional[str] = Field(
        None,
        description="Próximos passos recomendados"
    )
    
    founders_opinion: Optional[str] = Field(
        None,
        description="Opinião sobre os fundadores/empreendedores"
    )
    
    founders_track_record: Optional[str] = Field(
        None,
        description="Histórico e track record dos fundadores"
    )
    
    founders_comparison: Optional[str] = Field(
        None,
        description="Comparação dos fundadores com outros empreendedores do portfólio"
    )
    
    company_positioning_opinion: Optional[str] = Field(
        None,
        description="Opinião sobre o posicionamento da empresa no mercado"
    )
    
    market_reputation: Optional[str] = Field(
        None,
        description="Reputação da empresa no mercado"
    )


# ========== SCHEMAS PARA SHORT MEMO - PRIMÁRIO (FUNDOS) ==========

class GestoraFacts(BaseModel):
    """Schema para seção Gestora - Informações da gestora de fundos"""
    model_config = ConfigDict(strict=True)
    
    gestora_nome: Optional[str] = Field(
        None,
        description="Nome oficial da gestora"
    )
    
    gestora_ano_fundacao: Optional[int] = Field(
        None,
        ge=1900,
        le=2026,
        description="Ano de fundação da gestora"
    )
    
    gestora_localizacao: Optional[str] = Field(
        None,
        description="Localização/sede da gestora"
    )
    
    gestora_tipo: Optional[str] = Field(
        None,
        description="Tipo de investidor/gestora (ex: Operator-led PE, Growth equity, Venture capital)"
    )
    
    gestora_aum_mm: Optional[float] = Field(
        None,
        ge=0.0,
        le=100000.0,
        description="Assets Under Management total da gestora (milhões)"
    )
    
    gestora_num_fundos: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Número de fundos geridos pela gestora"
    )
    
    gestora_socios_principais: Optional[str] = Field(
        None,
        description="Sócios/GPs principais da gestora"
    )
    
    gestora_filosofia_investimento: Optional[str] = Field(
        None,
        description="Filosofia de investimento da gestora"
    )


class FundoFacts(BaseModel):
    """Schema para seção Fundo - Características do fundo"""
    model_config = ConfigDict(strict=True)
    
    fundo_nome: Optional[str] = Field(
        None,
        description="Nome oficial do fundo"
    )
    
    fundo_vintage: Optional[int] = Field(
        None,
        ge=2000,
        le=2030,
        description="Vintage year do fundo (ano de primeiro closing)"
    )
    
    fundo_closing: Optional[str] = Field(
        None,
        description="Status/número do closing (primeiro, segundo, final, etc)"
    )
    
    fundo_moeda: Optional[str] = Field(
        None,
        description="Moeda do fundo (BRL, USD, EUR, etc)"
    )
    
    fundo_target_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Target de captação (milhões)"
    )
    
    fundo_hard_cap_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Hard cap de captação (milhões)"
    )
    
    fundo_commitment_spectra_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Commitment da Spectra (milhões)"
    )
    
    fundo_commitment_spectra_pct: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Commitment da Spectra como % do target"
    )
    
    fundo_captado_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Valor já captado até o momento (milhões)"
    )
    
    fundo_periodo_investimento_anos: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Período de investimento (anos)"
    )
    
    fundo_vida_total_anos: Optional[float] = Field(
        None,
        ge=0.0,
        le=20.0,
        description="Vida total do fundo (anos)"
    )


class EstrategiaFundoFacts(BaseModel):
    """Schema para seção Estratégia - Estratégia de investimento do fundo"""
    model_config = ConfigDict(strict=True)
    
    estrategia_tese: Optional[str] = Field(
        None,
        description="Tese de investimento do fundo"
    )
    
    estrategia_setores: Optional[str] = Field(
        None,
        description="Setores-alvo do fundo"
    )
    
    estrategia_geografia: Optional[str] = Field(
        None,
        description="Geografia/regiões de atuação"
    )
    
    estrategia_estagio: Optional[str] = Field(
        None,
        description="Estágio de investimento (early stage, growth, buyout, etc)"
    )
    
    estrategia_ticket_min_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Ticket mínimo de investimento (milhões)"
    )
    
    estrategia_ticket_max_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Ticket máximo de investimento (milhões)"
    )
    
    estrategia_ticket_medio_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Ticket médio de investimento (milhões)"
    )
    
    estrategia_numero_ativos_alvo: Optional[int] = Field(
        None,
        ge=0,
        description="Número esperado de investimentos do fundo"
    )
    
    estrategia_num_investments_target: Optional[int] = Field(
        None,
        ge=0,
        description="Número esperado de investimentos do fundo (alias para estrategia_numero_ativos_alvo)"
    )
    
    estrategia_tipo_participacao: Optional[str] = Field(
        None,
        description="Tipo de participação (maioria, minoria, controle, etc)"
    )
    
    estrategia_alocacao: Optional[str] = Field(
        None,
        description="Estratégia de alocação do fundo"
    )
    
    estrategia_diferenciacao: Optional[str] = Field(
        None,
        description="Diferenciação da estratégia vs peers"
    )


class SpectraContextFacts(BaseModel):
    """Schema para seção Spectra Context - Contexto e racional da Spectra"""
    model_config = ConfigDict(strict=True)
    
    spectra_relacionamento: Optional[str] = Field(
        None,
        description="Histórico de relacionamento da Spectra com a gestora"
    )
    
    spectra_relacao_historica: Optional[str] = Field(
        None,
        description="Histórico de relacionamento da Spectra com a gestora (alias para spectra_relacionamento)"
    )
    
    spectra_coinvestidores: Optional[str] = Field(
        None,
        description="Outros LPs relevantes no fundo"
    )
    
    spectra_allocation_strategy: Optional[str] = Field(
        None,
        description="Como esse investimento se encaixa na estratégia de alocação da Spectra"
    )
    
    spectra_due_diligence: Optional[str] = Field(
        None,
        description="Resumo do processo de due diligence"
    )
    
    spectra_termos_negociados: Optional[str] = Field(
        None,
        description="Termos específicos negociados pela Spectra"
    )
    
    spectra_fees_terms: Optional[str] = Field(
        None,
        description="Management fee, carry, hurdle rate e outros termos econômicos"
    )
    
    spectra_governance: Optional[str] = Field(
        None,
        description="Direitos de governance (LPAC, approval rights, etc)"
    )
    
    spectra_is_existing_lp: Optional[str] = Field(
        None,
        description="Se a Spectra já é LP existente em outros fundos da gestora"
    )
    
    spectra_previous_funds: Optional[str] = Field(
        None,
        description="Fundos anteriores da gestora em que a Spectra investiu"
    )
    
    spectra_vehicle: Optional[str] = Field(
        None,
        description="Veículo de investimento da Spectra"
    )
    
    spectra_commitment_target_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Commitment target da Spectra (milhões)"
    )
    
    spectra_commitment_pct: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Commitment da Spectra como % do target"
    )
    
    spectra_closing_alvo: Optional[str] = Field(
        None,
        description="Closing alvo da Spectra"
    )


# ========== SCHEMAS PARA MEMO COMPLETO SEARCH FUND ==========

class SearcherFacts(BaseModel):
    """Schema para seção Gestor - Análise dos searchers (Search Fund)"""
    model_config = ConfigDict(strict=True)
    
    searcher_name: Optional[str] = Field(
        None,
        description="Nome(s) do(s) searcher(s) - pode ser múltiplos nomes separados por vírgula"
    )
    
    searcher_background: Optional[str] = Field(
        None,
        description="Formação acadêmica e histórico profissional dos searchers"
    )
    
    searcher_experience: Optional[str] = Field(
        None,
        description="Experiência relevante (anos, empresas anteriores, cargos)"
    )
    
    searcher_assessment: Optional[str] = Field(
        None,
        description="Resultados de assessment psicológico ou avaliação de perfil (se disponível)"
    )
    
    searcher_complementarity: Optional[str] = Field(
        None,
        description="Análise de complementaridade da dupla de searchers (se aplicável)"
    )
    
    searcher_references: Optional[str] = Field(
        None,
        description="Referências e validações dos searchers (ex-empregadores, mentores, etc)"
    )
    
    searcher_track_record: Optional[str] = Field(
        None,
        description="Histórico de deals anteriores ou experiências relevantes (se aplicável)"
    )


class ProjectionYearData(BaseModel):
    """Dados de um ano específico nas projeções"""
    model_config = ConfigDict(strict=True)
    
    year: Optional[int] = Field(None, ge=2020, le=2050, description="Ano da projeção")
    revenue_mm: Optional[float] = Field(None, ge=0.0, description="Receita projetada (milhões)")
    ebitda_mm: Optional[float] = Field(None, description="EBITDA projetado (milhões)")
    ebitda_margin_pct: Optional[float] = Field(None, ge=-100.0, le=100.0, description="Margem EBITDA (%)")
    capex_mm: Optional[float] = Field(None, description="Capex projetado (milhões)")
    net_debt_mm: Optional[float] = Field(None, description="Dívida líquida projetada (milhões)")


class ProjectionsTableFacts(BaseModel):
    """Schema para tabelas de projeções financeiras com múltiplos cenários"""
    model_config = ConfigDict(strict=True)
    
    projections_years: Optional[List[int]] = Field(
        None,
        description="Lista de anos projetados (ex: [2023, 2024, 2025, 2026, 2027, 2028])"
    )
    
    projections_base_case: Optional[List[Dict]] = Field(
        None,
        description="Lista de dados ano a ano para cenário base. Cada item deve ter: year, revenue_mm, ebitda_mm, ebitda_margin_pct"
    )
    
    projections_upside_case: Optional[List[Dict]] = Field(
        None,
        description="Lista de dados ano a ano para cenário otimista (upside). Cada item deve ter: year, revenue_mm, ebitda_mm, ebitda_margin_pct"
    )
    
    projections_downside_case: Optional[List[Dict]] = Field(
        None,
        description="Lista de dados ano a ano para cenário pessimista (downside). Cada item deve ter: year, revenue_mm, ebitda_mm, ebitda_margin_pct"
    )
    
    projections_assumptions_base: Optional[str] = Field(
        None,
        description="Premissas detalhadas do cenário base (crescimento, margens, drivers)"
    )
    
    projections_assumptions_upside: Optional[str] = Field(
        None,
        description="Premissas detalhadas do cenário otimista"
    )
    
    projections_assumptions_downside: Optional[str] = Field(
        None,
        description="Premissas detalhadas do cenário pessimista"
    )


class ReturnsScenarioData(BaseModel):
    """Dados de retorno para um cenário específico"""
    model_config = ConfigDict(strict=True)
    
    irr_pct: Optional[float] = Field(None, ge=-100.0, le=1000.0, description="IRR do cenário (%)")
    moic: Optional[float] = Field(None, ge=0.0, le=50.0, description="MOIC do cenário (x)")
    exit_year: Optional[int] = Field(None, ge=2024, le=2050, description="Ano de saída")
    exit_multiple: Optional[float] = Field(None, ge=0.0, le=100.0, description="Múltiplo de saída")


class ReturnsTableFacts(BaseModel):
    """Schema para tabelas de retornos esperados com múltiplos cenários"""
    model_config = ConfigDict(strict=True)
    
    returns_base_case: Optional[Dict] = Field(
        None,
        description="Retornos do cenário base: {irr_pct: float, moic: float, exit_year: int, exit_multiple: float}"
    )
    
    returns_upside_case: Optional[Dict] = Field(
        None,
        description="Retornos do cenário otimista: {irr_pct: float, moic: float, exit_year: int, exit_multiple: float}"
    )
    
    returns_downside_case: Optional[Dict] = Field(
        None,
        description="Retornos do cenário pessimista: {irr_pct: float, moic: float, exit_year: int, exit_multiple: float}"
    )
    
    returns_sensitivity_table: Optional[List[Dict]] = Field(
        None,
        description="Tabela de sensibilidade: lista de cenários variando múltiplo de saída e/ou ano. Cada item: {exit_year: int, exit_multiple: float, irr_pct: float, moic: float}"
    )
    
    returns_exit_scenarios: Optional[List[Dict]] = Field(
        None,
        description="Cenários de saída com diferentes múltiplos: lista de {exit_year: int, exit_multiple: float, irr_pct: float, moic: float}"
    )


class BoardMemberData(BaseModel):
    """Dados de um membro do board"""
    model_config = ConfigDict(strict=True)
    
    name: Optional[str] = Field(None, description="Nome do membro do board")
    role: Optional[str] = Field(None, description="Cargo/função no board (ex: 'Board Member', 'Observer', 'Chairman')")
    background: Optional[str] = Field(None, description="Histórico profissional e experiência")
    indication_source: Optional[str] = Field(None, description="Quem indicou (ex: 'KVIV', 'Spectra', 'TTCER')")


class CapTableInvestorData(BaseModel):
    """Dados de um investidor no cap table"""
    model_config = ConfigDict(strict=True)
    
    investor_name: Optional[str] = Field(None, description="Nome do investidor")
    investor_type: Optional[str] = Field(None, description="Tipo de investidor (ex: 'Search Investor', 'Gap Investor', 'Family Office')")
    contribution_mm: Optional[float] = Field(None, ge=0.0, description="Contribuição em milhões")
    contribution_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="Percentual do cap table (%)")
    country: Optional[str] = Field(None, description="País de origem do investidor")


class BoardCapTableFacts(BaseModel):
    """Schema para seção Board e Cap Table - Composição do board e investidores"""
    model_config = ConfigDict(strict=True)
    
    board_members: Optional[List[Dict]] = Field(
        None,
        description="Lista de membros do board. Cada item: {name: str, role: str, background: str, indication_source: str}"
    )
    
    cap_table: Optional[List[Dict]] = Field(
        None,
        description="Lista de investidores no cap table. Cada item: {investor_name: str, investor_type: str, contribution_mm: float, contribution_pct: float, country: str}"
    )
    
    governance_structure: Optional[str] = Field(
        None,
        description="Estrutura de governança e direitos (veto, tag-along, drag-along, etc)"
    )
    
    board_commentary: Optional[str] = Field(
        None,
        description="Comentários sobre a qualidade do board e cap table"
    )


# ========== SCHEMAS PARA SHORT MEMO - SECUNDÁRIO ==========

class PortfolioSecundarioFacts(BaseModel):
    """Schema para seção Portfolio Secundário - Dados de portfolio/ativos para transações secundárias"""
    model_config = ConfigDict(strict=True)
    
    nav_data_base: Optional[str] = Field(
        None,
        description="Data base do NAV (ex: '30/06/2024', 'Dez/23')"
    )
    
    nav_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="NAV (Net Asset Value) na data base (milhões)"
    )
    
    desconto_nav_pct: Optional[float] = Field(
        None,
        ge=-50.0,
        le=50.0,
        description="Desconto sobre NAV (%)"
    )
    
    expectativa_recebimento_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Expectativa de recebimento total (milhões)"
    )
    
    numero_fundos: Optional[int] = Field(
        None,
        ge=0,
        description="Número de fundos envolvidos na transação"
    )
    
    numero_ativos: Optional[int] = Field(
        None,
        ge=0,
        description="Número de ativos/empresas no portfolio"
    )
    
    portfolio_commentary: Optional[str] = Field(
        None,
        description="Comentários gerais sobre o portfolio e distribuição de ativos"
    )


# Mapa de schemas por seção
SECTION_SCHEMAS = {
    "identification": IdentificationFacts,
    "transaction_structure": TransactionStructureFacts,
    "financials_history": FinancialsHistoryFacts,
    "saida": SaidaFacts,
    "returns": ReturnsFacts,
    "qualitative": QualitativeFacts,
    "opinioes": OpinioesFacts,
    # Schemas para fundos
    "gestora": GestoraFacts,
    "fundo": FundoFacts,
    "estrategia": EstrategiaFundoFacts,
    "spectra_context": SpectraContextFacts,
    # Schemas para secundário
    "portfolio_secundario": PortfolioSecundarioFacts,
    # Schemas para Memo Completo Search Fund
    "searcher": SearcherFacts,
    "gestor": SearcherFacts,  # Alias para searcher
    "projections_table": ProjectionsTableFacts,
    "returns_table": ReturnsTableFacts,
    "board_cap_table": BoardCapTableFacts,
}


def get_schema_for_section(section_name: str) -> type[BaseModel]:
    """Retorna o schema Pydantic para uma seção"""
    schema = SECTION_SCHEMAS.get(section_name)
    if not schema:
        raise ValueError(f"Schema não encontrado para seção: {section_name}")
    return schema
