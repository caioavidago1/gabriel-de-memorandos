import streamlit as st
from funcoes import render_field_with_toggle


def render_tab_opinioes(memo_type=None):
    """Tab: Opiniões (específica para Short Memo - Primário)"""
    st.markdown("### Opiniões da Spectra")

    st.markdown("**Avaliação dos Fundadores/Time**")

    col1, col2 = st.columns(2)

    with col1:
        render_field_with_toggle(
            "Gostamos dos fundadores/time?",
            "founders_opinion",
            "opinioes",
            input_type="text_area",
            help_text="Nossa opinião sobre os fundadores/time executivo",
            height=100,
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Os fundadores têm bom histórico de execução?",
            "founders_track_record",
            "opinioes",
            input_type="text_area",
            help_text="Histórico de performance e realizações dos fundadores",
            height=100,
            memo_type=memo_type
        )

        render_field_with_toggle(
            "Como eles se comparam com outros fundadores que já analisamos?",
            "founders_comparison",
            "opinioes",
            input_type="text_area",
            help_text="Comparação com outros deals/fundadores do portfólio",
            height=100,
            memo_type=memo_type
        )

    with col2:
        render_field_with_toggle(
            "Gostamos do posicionamento da empresa?",
            "company_positioning_opinion",
            "opinioes",
            input_type="text_area",
            help_text="Nossa visão sobre o posicionamento estratégico da empresa",
            height=100,
            memo_type=memo_type
        )

        render_field_with_toggle(
            "O mercado/investidores falam bem deles?",
            "market_reputation",
            "opinioes",
            input_type="text_area",
            help_text="Reputação no mercado, feedback de investidores, clientes, etc.",
            height=100,
            memo_type=memo_type
        )
