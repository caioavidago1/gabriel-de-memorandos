import streamlit as st
from funcoes import render_field_with_toggle


def render_tab_financials(memo_type=None):
    """
    Tab unificada: Financials e Projeções
    
    Combina histórico financeiro e projeções em uma única aba,
    incluindo todos os campos extraíveis da DRE.
    """
    st.markdown("### Financials e Projeções")
    st.caption("Histórico financeiro, projeções e métricas da DRE")
    
    # ===== SEÇÃO 1: RECEITA (HISTÓRICO) =====
    with st.expander("📊 Receita - Histórico", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            render_field_with_toggle(
                "Receita Atual (MM)",
                "revenue_current_mm",
                "financials_history",
                input_type="number",
                help_text="Receita atual em MM",
                min_value=0.0,
                step=0.1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "Receita Bruta (MM)",
                "revenue_gross_mm",
                "financials_history",
                input_type="number",
                help_text="Receita bruta (antes de deduções)",
                min_value=0.0,
                step=0.1,
                memo_type=memo_type
            )
        
        with col2:
            render_field_with_toggle(
                "CAGR Receita (%)",
                "revenue_cagr_pct",
                "financials_history",
                input_type="number",
                help_text="Ex: 43%, 14%, 24%",
                min_value=0.0,
                step=0.1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "Período do CAGR",
                "revenue_cagr_period",
                "financials_history",
                help_text="Ex: 2019-2024",
                memo_type=memo_type
            )
        
        with col3:
            render_field_with_toggle(
                "Ano Base",
                "revenue_base_year",
                "financials_history",
                input_type="number",
                help_text="Ex: 2020",
                min_value=2000,
                max_value=2030,
                step=1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "Receita Ano Base (MM)",
                "revenue_base_year_mm",
                "financials_history",
                input_type="number",
                help_text="Ex: 74m",
                min_value=0.0,
                step=0.1,
                memo_type=memo_type
            )
    
    # ===== SEÇÃO 2: LUCRO BRUTO E MARGENS =====
    with st.expander("💰 Lucro Bruto e Margens"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            render_field_with_toggle(
                "Lucro Bruto (MM)",
                "gross_profit_mm",
                "financials_history",
                input_type="number",
                help_text="Lucro bruto (Receita - CMV)",
                step=0.1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "Margem Bruta (%)",
                "gross_margin_pct",
                "financials_history",
                input_type="number",
                help_text="Ex: 36%, 32%, 30%",
                min_value=0.0,
                max_value=100.0,
                step=0.1,
                memo_type=memo_type
            )
        
        with col2:
            render_field_with_toggle(
                "Opex (% Receita)",
                "opex_pct_revenue",
                "financials_history",
                input_type="number",
                help_text="Despesas operacionais % receita",
                min_value=0.0,
                max_value=100.0,
                step=0.1,
                memo_type=memo_type
            )
        
        with col3:
            render_field_with_toggle(
                "Número de Funcionários",
                "employees_count",
                "financials_history",
                input_type="number",
                help_text="Ex: 600, 340",
                min_value=0,
                step=1,
                memo_type=memo_type
            )
    
    # ===== SEÇÃO 3: EBITDA (HISTÓRICO) =====
    with st.expander("📈 EBITDA - Histórico", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            render_field_with_toggle(
                "EBITDA Atual (MM)",
                "ebitda_current_mm",
                "financials_history",
                input_type="number",
                help_text="EBITDA atual em MM",
                step=0.1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "EBITDA Ano Base (MM)",
                "ebitda_base_year_mm",
                "financials_history",
                input_type="number",
                help_text="EBITDA no ano inicial",
                step=0.1,
                memo_type=memo_type
            )
        
        with col2:
            render_field_with_toggle(
                "Margem EBITDA Atual (%)",
                "ebitda_margin_current_pct",
                "financials_history",
                input_type="number",
                help_text="Ex: 36%, 22%, 16%",
                min_value=0.0,
                max_value=100.0,
                step=0.1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "CAGR EBITDA (%)",
                "ebitda_cagr_pct",
                "financials_history",
                input_type="number",
                help_text="CAGR de EBITDA",
                min_value=0.0,
                step=0.1,
                memo_type=memo_type
            )
        
        with col3:
            render_field_with_toggle(
                "EBIT Atual (MM)",
                "ebit_current_mm",
                "financials_history",
                input_type="number",
                help_text="EBIT (EBITDA - Depreciação/Amortização)",
                step=0.1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "Margem EBIT (%)",
                "ebit_margin_pct",
                "financials_history",
                input_type="number",
                help_text="Margem EBIT sobre receita",
                min_value=0.0,
                max_value=100.0,
                step=0.1,
                memo_type=memo_type
            )
    
    # ===== SEÇÃO 4: LUCRO LÍQUIDO =====
    with st.expander("💵 Lucro Líquido"):
        col1, col2 = st.columns(2)
        
        with col1:
            render_field_with_toggle(
                "Lucro Líquido (MM)",
                "net_income_mm",
                "financials_history",
                input_type="number",
                help_text="Lucro líquido após impostos",
                step=0.1,
                memo_type=memo_type
            )
        
        with col2:
            render_field_with_toggle(
                "Margem Líquida (%)",
                "net_margin_pct",
                "financials_history",
                input_type="number",
                help_text="Margem líquida sobre receita",
                min_value=0.0,
                max_value=100.0,
                step=0.1,
                memo_type=memo_type
            )
    
    # ===== SEÇÃO 5: CAPEX E INVESTIMENTOS =====
    with st.expander("🏗️ Capex e Investimentos"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            render_field_with_toggle(
                "Capex (MM)",
                "capex_mm",
                "financials_history",
                input_type="number",
                help_text="Investimentos em capital (CAPEX)",
                step=0.1,
                memo_type=memo_type
            )
        
        with col2:
            render_field_with_toggle(
                "Capex (% Receita)",
                "capex_pct_revenue",
                "financials_history",
                input_type="number",
                help_text="Capex como % da receita",
                min_value=0.0,
                max_value=100.0,
                step=0.1,
                memo_type=memo_type
            )
        
        with col3:
            render_field_with_toggle(
                "Capex Manutenção (MM)",
                "capex_maintenance_mm",
                "financials_history",
                input_type="number",
                help_text="Capex de manutenção vs expansão",
                step=0.1,
                memo_type=memo_type
            )
    
    # ===== SEÇÃO 6: GERAÇÃO DE CAIXA =====
    with st.expander("💸 Geração de Caixa"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            render_field_with_toggle(
                "Geração de Caixa Operacional (MM)",
                "operating_cash_flow_mm",
                "financials_history",
                input_type="number",
                help_text="Fluxo de caixa operacional",
                step=0.1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "Geração de Caixa Operacional (% EBITDA)",
                "operating_cash_flow_pct_ebitda",
                "financials_history",
                input_type="number",
                help_text="% do EBITDA convertido em caixa operacional",
                min_value=0.0,
                max_value=200.0,
                step=0.1,
                memo_type=memo_type
            )
        
        with col2:
            render_field_with_toggle(
                "Geração de Caixa Livre (MM)",
                "free_cash_flow_mm",
                "financials_history",
                input_type="number",
                help_text="Free Cash Flow (FCF)",
                step=0.1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "Geração de Caixa (% EBITDA)",
                "cash_conversion_pct",
                "financials_history",
                input_type="number",
                help_text="% do EBITDA → Caixa (ex: ~70%)",
                min_value=0.0,
                max_value=200.0,
                step=0.1,
                memo_type=memo_type
            )
        
        with col3:
            render_field_with_toggle(
                "Working Capital (MM)",
                "working_capital_mm",
                "financials_history",
                input_type="number",
                help_text="Capital de giro",
                step=0.1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "Working Capital (Dias)",
                "working_capital_days",
                "financials_history",
                input_type="number",
                help_text="Capital de giro em dias",
                step=0.1,
                memo_type=memo_type
            )
    
    # ===== SEÇÃO 7: DÍVIDA E ESTRUTURA DE CAPITAL =====
    with st.expander("🏦 Dívida e Estrutura de Capital"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            render_field_with_toggle(
                "Dívida Líquida (MM)",
                "net_debt_mm",
                "financials_history",
                input_type="number",
                help_text="Dívida líquida em MM",
                step=0.1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "Dívida Bruta (MM)",
                "gross_debt_mm",
                "financials_history",
                input_type="number",
                help_text="Dívida bruta (antes de caixa)",
                step=0.1,
                memo_type=memo_type
            )
        
        with col2:
            render_field_with_toggle(
                "Alavancagem (Dívida/EBITDA)",
                "leverage_net_debt_ebitda",
                "financials_history",
                input_type="number",
                help_text="Ex: 2.0x, 0.2x, 1.5x",
                min_value=0.0,
                step=0.1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "Caixa e Equivalentes (MM)",
                "cash_and_equivalents_mm",
                "financials_history",
                input_type="number",
                help_text="Caixa e equivalentes de caixa",
                step=0.1,
                memo_type=memo_type
            )
        
        with col3:
            render_field_with_toggle(
                "ROIC (%)",
                "roic_pct",
                "financials_history",
                input_type="number",
                help_text="Return on Invested Capital",
                min_value=-100.0,
                max_value=1000.0,
                step=0.1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "ROE (%)",
                "roe_pct",
                "financials_history",
                input_type="number",
                help_text="Return on Equity",
                min_value=-100.0,
                max_value=1000.0,
                step=0.1,
                memo_type=memo_type
            )
    
    # ===== SEÇÃO 8: PROJEÇÕES DE SAÍDA =====
    with st.expander("🚀 Projeções de Saída", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Receita na Saída**")
            render_field_with_toggle(
                "Receita na Saída (MM)",
                "revenue_exit_mm",
                "saida",
                input_type="number",
                help_text="Receita projetada na saída",
                min_value=0.0,
                step=0.1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "CAGR Receita Projetado (%)",
                "revenue_cagr_projected_pct",
                "saida",
                input_type="number",
                help_text="Ex: 25%, 16%, 17%, 18%",
                min_value=0.0,
                step=0.1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "Período de Projeção",
                "projection_period",
                "saida",
                help_text="Ex: 2025-2030",
                memo_type=memo_type
            )
        
        with col2:
            st.markdown("**EBITDA na Saída**")
            render_field_with_toggle(
                "EBITDA na Saída (MM)",
                "ebitda_exit_mm",
                "saida",
                input_type="number",
                help_text="EBITDA projetado na saída",
                min_value=0.0,
                step=0.1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "Margem EBITDA na Saída (%)",
                "ebitda_margin_exit_pct",
                "saida",
                input_type="number",
                help_text="Ex: 44%, 21%, 52%, 13%",
                min_value=0.0,
                max_value=100.0,
                step=0.1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "CAGR EBITDA Projetado (%)",
                "ebitda_cagr_projected_pct",
                "saida",
                input_type="number",
                help_text="CAGR de EBITDA projetado",
                min_value=0.0,
                step=0.1,
                memo_type=memo_type
            )
        
        with col3:
            st.markdown("**Múltiplos e Saída**")
            render_field_with_toggle(
                "Ano de Saída",
                "exit_year",
                "saida",
                input_type="number",
                help_text="Ex: 2030",
                min_value=2024,
                max_value=2050,
                step=1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "Múltiplo de Saída (EV/EBITDA)",
                "exit_multiple_ev_ebitda",
                "saida",
                input_type="number",
                help_text="Ex: 7x, 5x, 4.9x",
                min_value=0.0,
                step=0.1,
                memo_type=memo_type
            )
            
            render_field_with_toggle(
                "Tipo de Cenário",
                "scenario_type",
                "saida",
                help_text="base, conservador, otimista",
                memo_type=memo_type
            )
    
    # ===== SEÇÃO 9: COMENTÁRIOS E ANÁLISES =====
    with st.expander("📝 Comentários e Análises"):
        render_field_with_toggle(
            "Comentários sobre Histórico Financeiro",
            "financials_commentary",
            "financials_history",
            input_type="text_area",
            help_text="Análise das variações de receita, EBITDA, dívida, etc.",
            height=120,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Drivers de Crescimento",
            "growth_drivers",
            "saida",
            input_type="text_area",
            help_text="Principais drivers de crescimento",
            height=100,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Comentários sobre as Projeções",
            "projections_commentary",
            "saida",
            input_type="text_area",
            help_text="Análise das premissas, drivers e riscos",
            height=120,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Estratégia de Saída",
            "exit_strategy",
            "saida",
            input_type="text_area",
            help_text="Estratégia de saída do investimento",
            height=100,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Drivers de Criação de Valor",
            "value_creation_drivers",
            "saida",
            input_type="text_area",
            help_text="Principais drivers de criação de valor",
            height=100,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Comentários Adicionais sobre Saída",
            "exit_commentary",
            "saida",
            input_type="text_area",
            help_text="Comentários adicionais sobre a estratégia de saída",
            height=100,
            memo_type=memo_type
        )
