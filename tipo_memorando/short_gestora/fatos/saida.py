"""
Aba Saída — Short Memo Co-investimento (Gestora).
Cenário Base, Alternativo/Upside e Conservador/Downside com Retornos Brutos (Gestora) e Líquidos (Coinvestidor).
"""
import streamlit as st
from funcoes import render_field_with_toggle

SECTION = "saida"


def _render_premissas(prefix: str, label: str, memo_type=None):
    st.markdown(f"**Premissas**")
    c1, c2, c3 = st.columns(3)
    with c1:
        render_field_with_toggle(
            "Ano da Saída",
            f"{prefix}_ano_saida",
            SECTION,
            input_type="number",
            min_value=2020,
            max_value=2050,
            step=1,
            memo_type=memo_type,
        )
        render_field_with_toggle(
            "CAGR Receita (%)",
            f"{prefix}_cagr_receita_pct",
            SECTION,
            input_type="number",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type,
        )
    with c2:
        render_field_with_toggle(
            "Margem EBITDA no Ano de Saída (%)",
            f"{prefix}_margem_ebitda_pct",
            SECTION,
            input_type="number",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type,
        )
        render_field_with_toggle(
            "Múltiplo de Saída (x EV/EBITDA)",
            f"{prefix}_multiplo_saida_x",
            SECTION,
            input_type="number",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type,
        )
        render_field_with_toggle(
            "Ano do Múltiplo",
            f"{prefix}_multiplo_saida_ano",
            SECTION,
            input_type="number",
            min_value=2020,
            max_value=2050,
            step=1,
            memo_type=memo_type,
        )
    with c3:
        render_field_with_toggle(
            "Dividendos ao Longo do Período",
            f"{prefix}_dividendos_periodo",
            SECTION,
            input_type="text_area",
            height=60,
            memo_type=memo_type,
        )


def _render_retornos(prefix: str, memo_type=None):
    st.markdown("**Retornos Brutos (Gestora)**")
    col1, col2 = st.columns(2)
    with col1:
        render_field_with_toggle(
            "TIR Bruta (%)",
            f"{prefix}_tir_bruta_pct",
            SECTION,
            input_type="number",
            min_value=-100.0,
            step=0.1,
            memo_type=memo_type,
        )
    with col2:
        render_field_with_toggle(
            "MOIC Bruto (x)",
            f"{prefix}_moic_bruto",
            SECTION,
            input_type="number",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type,
        )
    st.markdown("**Retornos Líquidos (Coinvestidor)**")
    col3, col4 = st.columns(2)
    with col3:
        render_field_with_toggle(
            "TIR Líquida (%)",
            f"{prefix}_tir_liquida_pct",
            SECTION,
            input_type="number",
            help_text="Após taxas de gestão e performance.",
            min_value=-100.0,
            step=0.1,
            memo_type=memo_type,
        )
    with col4:
        render_field_with_toggle(
            "MOIC Líquido (x)",
            f"{prefix}_moic_liquido",
            SECTION,
            input_type="number",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type,
        )


def render_tab_saida(memo_type=None):
    """Tab Saída: Cenário Base, Alternativo/Upside, Conservador/Downside, Taxas, Observações."""
    st.markdown("### Saída")

    render_field_with_toggle(
        "Taxa de Gestão (%):",
        "taxa_gestao_pct",
        SECTION,
        input_type="number",
        help_text="Para cálculo de retornos líquidos.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Taxa de Performance (%):",
        "taxa_performance_pct",
        SECTION,
        input_type="number",
        help_text="Sobre hurdle rate.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type,
    )

    st.markdown("#### Cenário Base")
    _render_premissas("cenario_base", "Base", memo_type)
    _render_retornos("cenario_base", memo_type)

    st.markdown("#### Cenário Alternativo / Upside")
    _render_premissas("cenario_alternativo", "Alternativo", memo_type)
    _render_retornos("cenario_alternativo", memo_type)

    st.markdown("#### Cenário Conservador / Downside")
    _render_premissas("cenario_conservador", "Conservador", memo_type)
    _render_retornos("cenario_conservador", memo_type)

    st.markdown("#### Observações")
    render_field_with_toggle(
        "Observações",
        "saida_observacoes",
        SECTION,
        input_type="text_area",
        memo_type=memo_type,
    )
