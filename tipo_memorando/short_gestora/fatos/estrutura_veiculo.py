"""
Aba Estrutura do Veículo de Coinvestimento — Short Memo Co-investimento (Gestora).
Regulamento, política de distribuição, pontos de atenção.
"""
import streamlit as st
from funcoes import render_field_with_toggle

SECTION = "estrutura_veiculo"


def render_tab_estrutura_veiculo(memo_type=None):
    """Tab: Estrutura do Veículo de Coinvestimento."""
    st.markdown("### Estrutura do Veículo de Coinvestimento")

    st.markdown("**Regulamento**")
    render_field_with_toggle(
        "Duração do Fundo (anos):",
        "duracao_fundo_anos",
        SECTION,
        input_type="number",
        min_value=0,
        step=1,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Capital Autorizado:",
        "capital_autorizado",
        SECTION,
        help_text="[Valor].",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Taxa de Gestão (%):",
        "taxa_gestao_veiculo_pct",
        SECTION,
        input_type="number",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Taxa de Performance (%):",
        "taxa_performance_veiculo_pct",
        SECTION,
        input_type="number",
        help_text="% sobre hurdle rate.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Hurdle Rate:",
        "hurdle_rate",
        SECTION,
        help_text="Taxa sobre a qual incide performance.",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Catch-up:",
        "catch_up",
        SECTION,
        help_text="Sim/Não - detalhes.",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Evento Equipe Chave:",
        "evento_equipe_chave",
        SECTION,
        input_type="text_area",
        help_text="Condições.",
        height=80,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Quórum Destituição Gestor (%):",
        "quorum_destituicao_pct",
        SECTION,
        input_type="number",
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        memo_type=memo_type,
    )

    st.markdown("**Política de Distribuição**")
    render_field_with_toggle(
        "Chamadas de Capital:",
        "chamadas_capital",
        SECTION,
        input_type="text_area",
        help_text="Expectativa de timing e valores.",
        height=80,
        memo_type=memo_type,
    )

    st.markdown("**Pontos de Atenção Regulamento**")
    render_field_with_toggle(
        "Pontos de Atenção Regulamento:",
        "pontos_atencao_regulamento",
        SECTION,
        input_type="text_area",
        height=100,
        memo_type=memo_type,
    )
