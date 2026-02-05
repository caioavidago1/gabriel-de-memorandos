"""
Aba Opinião do Analista — Short Memo Co-investimento (Gestora).
Apenas: Pontos Positivos, Pontos de Atenção, Recomendação.
"""
import streamlit as st
from funcoes import render_field_with_toggle

SECTION = "opinioes"


def render_tab_opinioes(memo_type=None):
    """Tab: Opinião do Analista (Short Memo - Co-investimento Gestora)."""
    st.markdown("### Opinião do Analista")

    render_field_with_toggle(
        "Pontos Positivos:",
        "key_strengths",
        SECTION,
        input_type="text_area",
        height=120,
        memo_type=memo_type,
    )

    render_field_with_toggle(
        "Pontos de Atenção:",
        "key_concerns",
        SECTION,
        input_type="text_area",
        height=120,
        memo_type=memo_type,
    )

    render_field_with_toggle(
        "Recomendação:",
        "spectra_recommendation",
        SECTION,
        input_type="text_area",
        height=100,
        memo_type=memo_type,
    )
