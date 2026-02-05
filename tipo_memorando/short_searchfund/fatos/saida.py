"""
Aba Saída: premissas e retornos por cenário (Base e Alternativo).
Substitui a antiga aba Retornos.
"""
import streamlit as st
from funcoes import render_field_with_toggle

SECTION = "saida"


def render_tab_saida(memo_type=None):
    """Tab Saída: Cenário Base, Cenário Alternativo e Observações."""
    st.markdown("### Saída")

    # --- Cenário Base ---
    st.markdown("#### Cenário Base")
    st.markdown("**Premissas**")
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        render_field_with_toggle(
            "Ano da Saída",
            "cenario_base_ano_saida",
            SECTION,
            input_type="number",
            help_text="Ano previsto da saída",
            min_value=2020,
            max_value=2050,
            step=1,
            memo_type=memo_type,
        )
        render_field_with_toggle(
            "CAGR Receita (%)",
            "cenario_base_cagr_receita_pct",
            SECTION,
            input_type="number",
            help_text="CAGR da receita no período (%)",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type,
        )
    with col_b2:
        render_field_with_toggle(
            "Margem EBITDA (%)",
            "cenario_base_margem_ebitda_pct",
            SECTION,
            input_type="number",
            help_text="Margem EBITDA na saída (%)",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type,
        )
        st.caption("**Múltiplo de Saída:** [ ]x EV/EBITDA em [ ]")
        col_mult_b_x, col_mult_b_ano = st.columns(2)
        with col_mult_b_x:
            render_field_with_toggle(
                "X (múltiplo)",
                "cenario_base_multiplo_saida_x",
                SECTION,
                input_type="number",
                help_text="Ex: 6 → 6x EV/EBITDA em [ano]",
                min_value=0.0,
                step=0.1,
                memo_type=memo_type,
            )
        with col_mult_b_ano:
            render_field_with_toggle(
                "Ano",
                "cenario_base_multiplo_saida_ano",
                SECTION,
                input_type="number",
                help_text="Ex: 2030 → 6x EV/EBITDA em 2030",
                min_value=2020,
                max_value=2050,
                step=1,
                memo_type=memo_type,
            )
    with col_b3:
        render_field_with_toggle(
            "Dividend Yield (%)",
            "cenario_base_dividend_yield_pct",
            SECTION,
            input_type="number",
            help_text="Dividend yield no período",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type,
        )

    st.markdown("**Retornos**")
    col_br1, col_br2 = st.columns(2)
    with col_br1:
        render_field_with_toggle(
            "TIR (%)",
            "cenario_base_tir_pct",
            SECTION,
            input_type="number",
            help_text="Taxa interna de retorno (%)",
            min_value=-100.0,
            step=0.1,
            memo_type=memo_type,
        )
    with col_br2:
        render_field_with_toggle(
            "MOIC (x)",
            "cenario_base_moic",
            SECTION,
            input_type="number",
            help_text="Múltiplo do capital investido (ex: 2.5x)",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type,
        )

    # --- Cenário Alternativo ---
    st.markdown("#### Cenário Alternativo")
    st.markdown("**Premissas**")
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        render_field_with_toggle(
            "Ano da Saída",
            "cenario_alternativo_ano_saida",
            SECTION,
            input_type="number",
            help_text="Ano previsto da saída",
            min_value=2020,
            max_value=2050,
            step=1,
            memo_type=memo_type,
        )
        render_field_with_toggle(
            "CAGR Receita (%)",
            "cenario_alternativo_cagr_receita_pct",
            SECTION,
            input_type="number",
            help_text="CAGR da receita no período (%)",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type,
        )
    with col_a2:
        render_field_with_toggle(
            "Margem EBITDA (%)",
            "cenario_alternativo_margem_ebitda_pct",
            SECTION,
            input_type="number",
            help_text="Margem EBITDA na saída (%)",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type,
        )
        st.caption("**Múltiplo de Saída:** [ ]x EV/EBITDA em [ ]")
        col_mult_a_x, col_mult_a_ano = st.columns(2)
        with col_mult_a_x:
            render_field_with_toggle(
                "X (múltiplo)",
                "cenario_alternativo_multiplo_saida_x",
                SECTION,
                input_type="number",
                help_text="Ex: 6 → 6x EV/EBITDA em [ano]",
                min_value=0.0,
                step=0.1,
                memo_type=memo_type,
            )
        with col_mult_a_ano:
            render_field_with_toggle(
                "Ano",
                "cenario_alternativo_multiplo_saida_ano",
                SECTION,
                input_type="number",
                help_text="Ex: 2030 → 6x EV/EBITDA em 2030",
                min_value=2020,
                max_value=2050,
                step=1,
                memo_type=memo_type,
            )
    with col_a3:
        render_field_with_toggle(
            "Dividend Yield (%)",
            "cenario_alternativo_dividend_yield_pct",
            SECTION,
            input_type="number",
            help_text="Dividend yield no período",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type,
        )

    st.markdown("**Retornos**")
    col_ar1, col_ar2 = st.columns(2)
    with col_ar1:
        render_field_with_toggle(
            "TIR (%)",
            "cenario_alternativo_tir_pct",
            SECTION,
            input_type="number",
            help_text="Taxa interna de retorno (%)",
            min_value=-100.0,
            step=0.1,
            memo_type=memo_type,
        )
    with col_ar2:
        render_field_with_toggle(
            "MOIC (x)",
            "cenario_alternativo_moic",
            SECTION,
            input_type="number",
            help_text="Múltiplo do capital investido (ex: 2.5x)",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type,
        )

    # --- Observações ---
    st.markdown("#### Observações")
    render_field_with_toggle(
        "Observações",
        "saida_observacoes",
        SECTION,
        input_type="text_area",
        help_text="Comentários adicionais sobre premissas e retornos",
        memo_type=memo_type,
    )
