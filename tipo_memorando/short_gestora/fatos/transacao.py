"""
Aba Transação — Short Memo Co-investimento (Gestora).
Moeda, Equity, Estrutura de Pagamento, Debt, Cheque Coinvestimento, Governança, Opinião.
"""
import streamlit as st
from funcoes import render_field_with_toggle

SECTION = "transaction_structure"


def render_tab_transaction(memo_type=None):
    """Tab: Transação (Short Memo - Co-investimento Gestora)."""
    st.markdown("### Transação")

    render_field_with_toggle(
        "Moeda da Transação:",
        "currency",
        SECTION,
        help_text="Ex.: BRL, USD, MXN.",
        memo_type=memo_type,
    )

    st.markdown("**Equity**")
    render_field_with_toggle(
        "Valuation Total da Empresa:",
        "valuation_total_empresa",
        SECTION,
        help_text="[Moeda] [Valor]. Ex.: BRL 150M.",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Participação Total Adquirida (%):",
        "participacao_total_adquirida",
        SECTION,
        input_type="number",
        help_text="Percentual total do equity adquirido.",
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Participação do Fundo da Gestora (%):",
        "participacao_fundo_gestora",
        SECTION,
        input_type="number",
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Participação do Coinvestimento (%):",
        "participacao_coinvestimento",
        SECTION,
        input_type="number",
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Múltiplo de Entrada:",
        "multiple_ev_ebitda",
        SECTION,
        input_type="number",
        help_text="[X]x EV/EBITDA.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Período de Referência do Múltiplo:",
        "multiple_reference_period",
        SECTION,
        help_text="Período do EBITDA de referência.",
        memo_type=memo_type,
    )

    st.markdown("**Estrutura de Pagamento**")
    render_field_with_toggle(
        "À Vista:",
        "cash_payment_mm",
        SECTION,
        input_type="number",
        help_text="[Moeda] [Valor] em milhões.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "À Vista (% do total):",
        "cash_pct_total",
        SECTION,
        input_type="number",
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Seller Note / Seller Finance:",
        "seller_note_mm",
        SECTION,
        input_type="number",
        help_text="[Moeda] [Valor] em milhões.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Seller Note (% do total):",
        "seller_note_pct_total",
        SECTION,
        input_type="number",
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Prazo (anos):",
        "seller_note_tenor_years",
        SECTION,
        input_type="number",
        min_value=0.0,
        step=0.5,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Indexador:",
        "seller_note_index",
        SECTION,
        help_text="CDI, IPCA, etc.",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Periodicidade:",
        "seller_note_frequency",
        SECTION,
        help_text="Mensal, trimestral, etc.",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Carência:",
        "seller_note_grace",
        SECTION,
        help_text="Se aplicável.",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Earn-out:",
        "earnout_mm",
        SECTION,
        input_type="number",
        help_text="[Moeda] [Valor] em milhões.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Condições do Earn-out:",
        "earnout_conditions",
        SECTION,
        input_type="text_area",
        help_text="Métrica de performance.",
        height=60,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Timeline do Earn-out:",
        "earnout_timeline",
        SECTION,
        help_text="Período/ano de pagamento.",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Compensação via Dividendos:",
        "compensacao_dividendos",
        SECTION,
        help_text="Se aplicável.",
        memo_type=memo_type,
    )

    st.markdown("**Debt (Financiamento de Aquisição)**")
    render_field_with_toggle(
        "Acquisition Debt:",
        "acquisition_debt_mm",
        SECTION,
        input_type="number",
        help_text="[Moeda] [Valor] em milhões.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Taxa:",
        "acquisition_debt_rate",
        SECTION,
        help_text="% em moeda ou índice + spread.",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Prazo (anos):",
        "acquisition_debt_tenor_years",
        SECTION,
        input_type="number",
        min_value=0.0,
        step=0.5,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Instituição:",
        "acquisition_debt_institution",
        SECTION,
        help_text="Banco/fundo.",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Leverage Resultante:",
        "leverage_resulting_x",
        SECTION,
        input_type="number",
        help_text="[X]x Net Debt/EBITDA.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type,
    )

    st.markdown("**Cheque do Coinvestimento**")
    render_field_with_toggle(
        "Valor Total Disponível para Coinvestimento:",
        "valor_total_coinvestimento",
        SECTION,
        help_text="[Valor].",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Alocação Pretendida pelo Fundo:",
        "alocacao_fundo",
        SECTION,
        help_text="[Valor].",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Disponível para Coinvestidores:",
        "disponivel_coinvestidores",
        SECTION,
        help_text="[Valor].",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Cheque Proposto Spectra:",
        "cheque_spectra",
        SECTION,
        help_text="[Valor].",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Cheque Spectra (% do coinvestimento):",
        "cheque_spectra_pct",
        SECTION,
        input_type="number",
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        memo_type=memo_type,
    )

    st.markdown("**Termos de Governança**")
    render_field_with_toggle(
        "Assentos no Conselho:",
        "assentos_conselho",
        SECTION,
        help_text="Distribuição.",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Vesting / Lock-up:",
        "vesting_lockup",
        SECTION,
        help_text="Termos.",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Matérias Protegidas:",
        "materias_protegidas",
        SECTION,
        input_type="text_area",
        help_text="Listar.",
        height=60,
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Tag Along:",
        "tag_along",
        SECTION,
        help_text="%.",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Drag Along:",
        "drag_along",
        SECTION,
        help_text="Condições.",
        memo_type=memo_type,
    )
    render_field_with_toggle(
        "Opções de Liquidez:",
        "opcoes_liquidez",
        SECTION,
        help_text="Detalhar.",
        memo_type=memo_type,
    )

    st.markdown("**Opinião do Analista sobre a Transação**")
    render_field_with_toggle(
        "Opinião do Analista sobre a Transação:",
        "investor_opinion",
        SECTION,
        input_type="text_area",
        height=100,
        memo_type=memo_type,
    )
