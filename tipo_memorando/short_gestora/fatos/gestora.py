"""
Aba Gestora — Short Memo Co-investimento (Gestora).
Track record, exits, equipe, estratégia, tese, performance, relacionamento Spectra.
"""
import streamlit as st
from funcoes import render_field_with_toggle

SECTION = "gestora"


def render_tab_gestora(memo_type=None):
    """Tab: Gestora (Short Memo - Co-investimento Gestora)."""
    st.markdown("### Gestora")

    st.markdown("**Track Record**")
    render_field_with_toggle(
        "Track Record:",
        "track_record",
        SECTION,
        input_type="text_area",
        help_text="Fundo [Nome]: [Ano], AUM [Valor], TVPI [X]x, DPI [X]x, IRR [%]. Um por linha ou texto corrido.",
        height=120,
        memo_type=memo_type,
    )

    render_field_with_toggle(
        "Principais Exits:",
        "principais_exits",
        SECTION,
        input_type="text_area",
        help_text="Listar empresas e múltiplos de saída.",
        height=100,
        memo_type=memo_type,
    )

    st.markdown("**Equipe**")
    render_field_with_toggle(
        "Equipe:",
        "equipe",
        SECTION,
        input_type="text_area",
        help_text="[Nome]: [Cargo] - [Anos de experiência] - [Background relevante]. Um por linha.",
        height=120,
        memo_type=memo_type,
    )

    st.markdown("**Estratégia e Tese**")
    render_field_with_toggle(
        "Estratégia de Investimento:",
        "estrategia_investimento",
        SECTION,
        input_type="text_area",
        help_text="Como a gestora investe (estágio, setores, ticket).",
        height=100,
        memo_type=memo_type,
    )

    render_field_with_toggle(
        "Tese da Gestora:",
        "tese_gestora",
        SECTION,
        input_type="text_area",
        help_text="Tese de investimento da gestora para este tipo de ativo.",
        height=100,
        memo_type=memo_type,
    )

    render_field_with_toggle(
        "Performance Histórica:",
        "performance_historica",
        SECTION,
        input_type="text_area",
        help_text="Resumo de performance histórica (fundos anteriores, IRR, MOIC).",
        height=100,
        memo_type=memo_type,
    )

    render_field_with_toggle(
        "Relacionamento Anterior com a Spectra:",
        "relacionamento_anterior_spectra",
        SECTION,
        input_type="text_area",
        help_text="Histórico de relacionamento e operações anteriores com a Spectra.",
        height=80,
        memo_type=memo_type,
    )
