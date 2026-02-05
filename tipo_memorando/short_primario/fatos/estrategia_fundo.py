import streamlit as st
from funcoes import render_field_with_toggle


def render_tab_estrategia_fundo(memo_type=None):
    """Tab: Estratégia do Fundo (específica para Short Memo - Primário)"""
    st.markdown("### Estratégia do Fundo")

    st.markdown("**Tese e Portfólio**")

    col1, col2 = st.columns(2)

    with col1:
        render_field_with_toggle(
            "Tese de Investimento",
            "estrategia_tese",
            "estrategia",
            input_type="text_area",
            height=100,
            help_text="Tese principal do fundo",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Setores Foco",
            "estrategia_setores",
            "estrategia",
            input_type="text_area",
            height=80,
            help_text="Setores alvo (separar por vírgula)",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Geografia",
            "estrategia_geografia",
            "estrategia",
            help_text="Geografia de atuação (ex: Brasil, LATAM)",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Estágio",
            "estrategia_estagio",
            "estrategia",
            help_text="Ex: Early stage PE, Growth, Venture",
            memo_type=memo_type
        )

    with col2:
        render_field_with_toggle(
            "Número de Ativos Alvo",
            "estrategia_numero_ativos_alvo",
            "estrategia",
            input_type="number",
            help_text="Número planejado de investimentos",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Ticket Médio (R$ MM)",
            "estrategia_ticket_medio_mm",
            "estrategia",
            input_type="number",
            help_text="Ticket médio esperado",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Tipo de Participação",
            "estrategia_tipo_participacao",
            "estrategia",
            help_text="Ex: Minoritário, Controle, Misto",
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Estratégia de Alocação",
            "estrategia_alocacao",
            "estrategia",
            input_type="text_area",
            height=80,
            help_text="Ex: 2 anchor + 4-5 growth minoritário",
            memo_type=memo_type
        )
