"""
Aba Identificação — Short Memo Co-investimento (Gestora).
Gestora, fundação, AUM, veículo, data da oportunidade, empresa alvo, setor, descrição.
"""
import streamlit as st
from funcoes import render_field_with_toggle


def render_tab_identification(memo_type=None):
    """Tab: Identificação (Short Memo - Co-investimento Gestora)."""
    st.markdown("### Identificação")

    render_field_with_toggle(
        "Gestora:",
        "gestora_name",
        "identification",
        help_text="Nome da gestora. Ex.: Minerva Capital; Eunoia; Redfoot Capital.",
        memo_type=memo_type,
    )

    render_field_with_toggle(
        "Fundação da Gestora:",
        "gestora_fundacao",
        "identification",
        help_text="Ano ou data de fundação da gestora.",
        memo_type=memo_type,
    )

    render_field_with_toggle(
        "AUM Total:",
        "aum_total",
        "identification",
        help_text="AUM total da gestora. Ex.: USD 500M; BRL 2 bi.",
        memo_type=memo_type,
    )

    render_field_with_toggle(
        "AUM do Fundo Específico:",
        "aum_fundo_especifico",
        "identification",
        help_text="AUM do fundo relacionado a esta oportunidade.",
        memo_type=memo_type,
    )

    render_field_with_toggle(
        "Veículo de Coinvestimento:",
        "veiculo_coinvestimento",
        "identification",
        help_text="FIP, SPE ou outro veículo de coinvestimento.",
        memo_type=memo_type,
    )

    render_field_with_toggle(
        "Data da Oportunidade:",
        "data_oportunidade",
        "identification",
        help_text="Data de referência da oportunidade. Ex.: 4T2025; dez/2025.",
        memo_type=memo_type,
    )

    render_field_with_toggle(
        "Empresa Alvo:",
        "company_name",
        "identification",
        help_text="Ex.: TSE; Project Oca; Disktrans; Project Baja.",
        memo_type=memo_type,
    )

    render_field_with_toggle(
        "Localização da Empresa Alvo:",
        "company_location",
        "identification",
        help_text="Cidade, região ou país da empresa alvo.",
        memo_type=memo_type,
    )

    render_field_with_toggle(
        "Setor:",
        "setor",
        "identification",
        help_text="Setor de atuação da empresa alvo.",
        memo_type=memo_type,
    )

    render_field_with_toggle(
        "Descrição do Negócio:",
        "business_description",
        "identification",
        input_type="text_area",
        help_text="Uma linha ou breve descrição do negócio da empresa alvo.",
        height=100,
        memo_type=memo_type,
    )
