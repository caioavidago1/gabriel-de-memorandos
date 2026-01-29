import streamlit as st
from funcoes import render_field_with_toggle


def render_tab_identification(memo_type=None):
    """Tab 1: Identificação"""
    st.markdown("### Identificação")
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_field_with_toggle(
            "Nome da Empresa",
            "company_name",
            "identification",
            help_text="Nome da empresa alvo",
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Nome(s) do(s) Searcher(s)",
            "searcher_name",
            "identification",
            help_text="Ex: Fernando Ponce e Eduardo Haro, Pedro Dorea",
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Início do Período de Busca",
            "search_start_date",
            "identification",
            help_text="Ex: 1S2023, Janeiro 2023",
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Nacionalidade do Investidor",
            "investor_nationality",
            "identification",
            help_text="Ex: brasileiro, mexicano",
            memo_type=memo_type
        )
    
    with col2:
        render_field_with_toggle(
            "Localização da Empresa",
            "company_location",
            "identification",
            help_text="Ex: Goiânia (GO), Serafina Corrêa (RS)",
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Ano de Fundação",
            "company_founding_year",
            "identification",
            input_type="number",
            help_text="Ex: 1990, 2015",
            min_value=1800,
            max_value=2030,
            step=1,
            memo_type=memo_type
        )

    render_field_with_toggle(
        "Descrição do Negócio:",
        "business_description",
        "identification",
        input_type="text_area",
        help_text="Ex: automação industrial, programas de fidelidade para farmácias",
        height=100,
        memo_type=memo_type
    )

    render_field_with_toggle(
        "Contexto do Deal:",
        "deal_context",
        "identification",
        input_type="text_area",
        help_text="Como surgiu, relacionamento com vendedor, motivações, etc.",
        height=120,
        memo_type=memo_type
    )
