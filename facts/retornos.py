import streamlit as st
from funcoes import render_field_with_toggle


def render_tab_returns(memo_type=None):
    """Tab 5: Retornos"""
    st.markdown("### Retornos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_field_with_toggle(
            "TIR Projetada (%)",
            "irr_pct",
            "returns",
            input_type="number",
            help_text="Ex: 36%, 38%, 39%, 42%",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "MOIC",
            "moic",
            "returns",
            input_type="number",
            help_text="Ex: 3.9x, 5.0x, 4.6x, 6.8x",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type
        )
    
    with col2:
        render_field_with_toggle(
            "Período de Holding (anos)",
            "holding_period_years",
            "returns",
            input_type="number",
            help_text="Período de holding em anos",
            min_value=0,
            step=1,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Múltiplo de Entrada",
            "entry_multiple",
            "returns",
            input_type="number",
            help_text="Múltiplo EV/EBITDA de entrada",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type
        )
