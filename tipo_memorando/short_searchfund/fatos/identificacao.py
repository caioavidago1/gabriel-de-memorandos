import streamlit as st
from funcoes import render_field_with_toggle


def render_tab_identification(memo_type=None):
    """Tab 1: Identificação — exatamente: Searcher(s), Nacionalidade, FIP, Início Busca, Empresa Alvo, Localização, Descrição."""
    st.markdown("### Identificação")

    render_field_with_toggle(
        "Nome(s) do(s) Searcher(s):",
        "searcher_name",
        "identification",
        help_text="Ex.: Pedro Dorea; Fernando Ponce e Eduardo Haro; Guilherme Ferrari; Hunibert Tuch.",
        memo_type=memo_type
    )

    render_field_with_toggle(
        "Nacionalidade do Search:",
        "investor_nationality",
        "identification",
        help_text="Ex.: brasileiro; mexicano.",
        memo_type=memo_type
    )

    render_field_with_toggle(
        "FIP (casca):",
        "fip_casca",
        "identification",
        help_text="Ex.: Minerva Capital; Eunoia; Redfoot Capital; Entrevo Capital.",
        memo_type=memo_type
    )

    render_field_with_toggle(
        "Início do Período de Busca:",
        "search_start_date",
        "identification",
        help_text="Data em que o searcher iniciou o período de busca. Ex.: segundo semestre de 2024; 2S2023; 1S2024.",
        memo_type=memo_type
    )

    render_field_with_toggle(
        "Empresa Alvo:",
        "company_name",
        "identification",
        help_text="Ex.: TSE; Project Oca; Disktrans; Project Baja.",
        memo_type=memo_type
    )

    render_field_with_toggle(
        "Localização da Empresa Alvo:",
        "company_location",
        "identification",
        help_text="Cidade, região ou país da empresa alvo. Ex.: península da Baja California (México); São Paulo (BR); México.",
        memo_type=memo_type
    )

    render_field_with_toggle(
        "Descrição do Negócio:",
        "business_description",
        "identification",
        input_type="text_area",
        help_text="Uma linha descrevendo o negócio da empresa alvo. Ex.: automação industrial; software de programas de fidelidade para farmácias e laboratórios; aluguel de transpaleteiras para logística interna; logística integrada transfronteiriça EUA–México.",
        height=100,
        memo_type=memo_type
    )
