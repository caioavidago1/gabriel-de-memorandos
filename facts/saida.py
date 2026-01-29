import streamlit as st
from funcoes import render_field_with_toggle


def render_tab_saida(memo_type=None):
    """Tab 4: Projeções e Saída"""
    st.markdown("### Projeções e Saída")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Projeções de Saída**")
        
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
        
        render_field_with_toggle(
            "Tipo de Cenário",
            "scenario_type",
            "saida",
            help_text="base, conservador, otimista",
            memo_type=memo_type
        )
    
    with col2:
        st.markdown("**EBITDA e Múltiplos**")
        
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
