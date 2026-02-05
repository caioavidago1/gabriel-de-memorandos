import streamlit as st
from funcoes import render_field_with_toggle


def render_tab_fundo(memo_type=None):
    """Tab: Fundo (específica para Short Memo - Primário)"""
    st.markdown("### Informações do Fundo")

    st.markdown("**Identificação e Tamanho**")

    col1, col2 = st.columns(2)

    with col1:
        render_field_with_toggle(
            "Nome do Fundo",
            "fundo_nome",
            "fundo",
            help_text="Nome completo do fundo (ex: Shift Alpha II)",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Número do Fundo",
            "fundo_closing",
            "fundo",
            help_text="Ex: primeiro, segundo, terceiro",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Moeda",
            "fundo_moeda",
            "fundo",
            input_type="select",
            options=["BRL", "USD", "EUR"],
            help_text="Moeda do fundo",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Target (R$ MM)",
            "fundo_target_mm",
            "fundo",
            input_type="number",
            help_text="Tamanho alvo do fundo em milhões",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Hard Cap (R$ MM)",
            "fundo_hard_cap_mm",
            "fundo",
            input_type="number",
            help_text="Limite máximo do fundo",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Vintage Year",
            "fundo_vintage",
            "fundo",
            input_type="number",
            help_text="Ano vintage do fundo",
            memo_type=memo_type
        )

    with col2:
        render_field_with_toggle(
            "Status da Captação",
            "fundo_status_captacao",
            "fundo",
            help_text="Ex: Em captação, Primeiro closing concluído",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Data Primeiro Closing",
            "fundo_primeiro_closing_data",
            "fundo",
            help_text="Data prevista (ex: mar/26)",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Target Primeiro Closing (R$ MM)",
            "fundo_primeiro_closing_target_mm",
            "fundo",
            input_type="number",
            help_text="Meta do primeiro closing",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Capital Já Levantado (R$ MM)",
            "fundo_captado_mm",
            "fundo",
            input_type="number",
            help_text="Capital já comprometido",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "% Levantado",
            "fundo_percentual_levantado",
            "fundo",
            input_type="number",
            help_text="Percentual do target já levantado",
            memo_type=memo_type
        )
