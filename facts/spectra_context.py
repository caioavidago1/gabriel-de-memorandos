import streamlit as st
from funcoes import render_field_with_toggle


def render_tab_spectra_context(memo_type=None):
    """Tab: Contexto Spectra (específica para Short Memo - Primário)"""
    st.markdown("### Contexto Spectra")
    
    st.markdown("**Relacionamento e Commitment**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_field_with_toggle(
            "Spectra já é LP?",
            "spectra_is_existing_lp",
            "spectra_context",
            input_type="checkbox",
            help_text="Spectra já investiu em fundos anteriores desta gestora?",
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Fundos Anteriores Investidos",
            "spectra_previous_funds",
            "spectra_context",
            input_type="text_area",
            height=60,
            help_text="Nomes dos fundos que Spectra já investiu",
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Veículo Spectra",
            "spectra_vehicle",
            "spectra_context",
            help_text="Ex: Fundo VII, Fundo VIII",
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Relação Histórica",
            "spectra_relacao_historica",
            "spectra_context",
            input_type="text_area",
            height=100,
            help_text="Descrição do histórico de relacionamento",
            memo_type=memo_type
        )
    
    with col2:
        render_field_with_toggle(
            "Commitment Target (R$ MM)",
            "spectra_commitment_target_mm",
            "spectra_context",
            input_type="number",
            help_text="Commitment alvo da Spectra no fundo",
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "% do Fundo",
            "spectra_commitment_pct",
            "spectra_context",
            input_type="number",
            help_text="Percentual que Spectra representa no fundo",
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Closing Alvo",
            "spectra_closing_alvo",
            "spectra_context",
            help_text="Ex: Primeiro closing, Final closing",
            memo_type=memo_type
        )
