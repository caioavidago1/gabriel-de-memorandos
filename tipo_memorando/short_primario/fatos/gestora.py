import streamlit as st
from funcoes import render_field_with_toggle


def render_tab_gestora(memo_type=None):
    """Tab: Gestora (específica para Short Memo - Primário)"""
    st.markdown("### Informações da Gestora")

    st.markdown("**Dados Gerais**")

    col1, col2 = st.columns(2)

    with col1:
        render_field_with_toggle(
            "Nome da Gestora",
            "gestora_nome",
            "gestora",
            help_text="Nome completo da gestora (ex: Shift Capital)",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Ano de Fundação",
            "gestora_ano_fundacao",
            "gestora",
            input_type="number",
            help_text="Ano de fundação da gestora",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Localização",
            "gestora_localizacao",
            "gestora",
            help_text="Cidade/Estado da sede",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Tipo de Investidor",
            "gestora_tipo",
            "gestora",
            help_text="Ex: Operator-led PE, Growth equity, Venture capital",
            memo_type=memo_type
        )

    with col2:
        render_field_with_toggle(
            "AUM Total (R$ MM)",
            "gestora_aum_mm",
            "gestora",
            input_type="number",
            help_text="Assets under management total",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Número de Fundos",
            "gestora_num_fundos",
            "gestora",
            input_type="number",
            help_text="Quantos fundos já levantou",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Sócios/GPs Principais",
            "gestora_socios_principais",
            "gestora",
            input_type="text_area",
            height=80,
            help_text="Nomes dos General Partners principais",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Filosofia de Investimento",
            "gestora_filosofia_investimento",
            "gestora",
            input_type="text_area",
            height=80,
            help_text="Descrição da filosofia e abordagem",
            memo_type=memo_type
        )
