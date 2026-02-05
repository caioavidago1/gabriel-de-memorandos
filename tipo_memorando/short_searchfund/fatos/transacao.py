import streamlit as st
from funcoes import render_field_with_toggle


def render_tab_transaction(memo_type=None):
    """Tab 2: Estrutura da Transação — Moeda, Equity, Estrutura de Pagamento, Debt, Opinião."""
    st.markdown("### Estrutura da Transação")

    # Moeda da Transação
    render_field_with_toggle(
        "Moeda da Transação:",
        "currency",
        "transaction_structure",
        help_text="Moeda do deal. Ex.: BRL, USD, MXN.",
        memo_type=memo_type
    )

    # Equity
    st.markdown("**Equity**")
    render_field_with_toggle(
        "Participação Adquirida:",
        "stake_pct",
        "transaction_structure",
        input_type="number",
        help_text="Percentual do equity adquirido. Ex.: 100% (Project Baja, Oca); 90% da companhia.",
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Equity Value:",
        "equity_value_mm",
        "transaction_structure",
        input_type="number",
        help_text="Valor do equity da operação em milhões (EqV). Ex.: US$ 9m (Baja); R$ 284m (deal com dívida zero).",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Enterprise Value (EV):",
        "ev_mm",
        "transaction_structure",
        input_type="number",
        help_text="EV em milhões. Quando dívida líquida é zero, EV = EqV. Ex.: US$ 9m; R$ 256m.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Múltiplo de Entrada:",
        "multiple_ev_ebitda",
        "transaction_structure",
        input_type="number",
        help_text="Múltiplo EV/EBITDA de entrada. Ex.: 4,4x (EBITDA 2024); 6,5x (25E); 4,9x LTM jun/24.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Período de Referência do Múltiplo:",
        "multiple_reference_period",
        "transaction_structure",
        help_text="Período do EBITDA de referência. Ex.: 2024; 25E; LTM jun/24; mai/25 LTM.",
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Valor Total da Transação:",
        "total_transaction_value_mm",
        "transaction_structure",
        input_type="number",
        help_text="Valor total incluindo custos de transação, search capital e step-up. Ex.: US$ 10m (Baja); US$ 11m com step-up (Oca).",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Múltiplo Total:",
        "multiple_total",
        "transaction_structure",
        input_type="number",
        help_text="Múltiplo considerando valor total da transação. Ex.: 4,9x EBITDA 2024 ou 3,6x EBITDA 2025; 7,2x 25E.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type
    )

    # Estrutura de Pagamento
    st.markdown("**Estrutura de Pagamento**")
    render_field_with_toggle(
        "À Vista:",
        "cash_payment_mm",
        "transaction_structure",
        input_type="number",
        help_text="Pagamento à vista em milhões. Ex.: R$ 103m (equity à vista); US$ 6m; estruturados 60% ou 87% à vista.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type
    )
    render_field_with_toggle(
        "À Vista (% do total):",
        "cash_pct_total",
        "transaction_structure",
        input_type="number",
        help_text="Percentual do total pago à vista. Ex.: 60% (Baja); 87% (Oca).",
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Equity à vista:",
        "equity_cash_mm",
        "transaction_structure",
        input_type="number",
        help_text="Equity à vista em milhões quando detalhado. Ex.: R$ 103m em equity à vista.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type
    )

    render_field_with_toggle(
        "Seller Note / Seller Finance:",
        "seller_note_mm",
        "transaction_structure",
        input_type="number",
        help_text="Valor do seller's finance em milhões. Ex.: R$ 78m corrigido por CDI, pago trimestralmente até 2029; 13% do total (Oca).",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Seller Note (% do total):",
        "seller_note_pct_total",
        "transaction_structure",
        input_type="number",
        help_text="Percentual do total via seller note. Ex.: 13% (Oca); 40%.",
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Prazo (anos):",
        "seller_note_tenor_years",
        "transaction_structure",
        input_type="number",
        help_text="Prazo do seller note em anos. Ex.: 4 anos; pagamento até 2029.",
        min_value=0.0,
        step=0.5,
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Indexador:",
        "seller_note_index",
        "transaction_structure",
        help_text="Indexador e spread. Ex.: CDI; CDI+6%; IPCA.",
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Periodicidade:",
        "seller_note_frequency",
        "transaction_structure",
        help_text="Periodicidade de pagamento. Ex.: trimestral; mensal.",
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Carência:",
        "seller_note_grace",
        "transaction_structure",
        help_text="Carência se aplicável. Ex.: após 15 meses do closing.",
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Termos da Seller Note (texto livre):",
        "seller_note_terms",
        "transaction_structure",
        help_text="Resumo dos termos. Ex.: corrigido por CDI, pago trimestralmente após 15 meses do closing e até 2029; cujos termos ainda estão em negociação.",
        memo_type=memo_type
    )

    render_field_with_toggle(
        "Earn-out:",
        "earnout_mm",
        "transaction_structure",
        input_type="number",
        help_text="Valor do earn-out em milhões (ou equivalente). Ex.: aquisição ITX via earn-out; equivalente a 0,2x EBITDA 25E.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Condições do Earn-out:",
        "earnout_conditions",
        "transaction_structure",
        input_type="text_area",
        help_text="Métrica de performance e escopo. Ex.: participação 50,1% no ITX; crescimento de receita; aprofundar estrutura.",
        height=80,
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Timeline do Earn-out:",
        "earnout_timeline",
        "transaction_structure",
        help_text="Período ou ano de pagamento. Ex.: pagamento apenas em 2030.",
        memo_type=memo_type
    )

    render_field_with_toggle(
        "Step-up:",
        "step_up_mm",
        "transaction_structure",
        input_type="number",
        help_text="Step-up em milhões. Ex.: step-up que leva valor total a US$ 11m (Oca); incluindo step-up na transação.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type
    )

    # Debt (Financiamento de Aquisição)
    st.markdown("**Debt (Financiamento de Aquisição)**")
    render_field_with_toggle(
        "Acquisition Debt:",
        "acquisition_debt_mm",
        "transaction_structure",
        input_type="number",
        help_text="Dívida de aquisição em milhões. Ex.: 40% via acquisition debt (Baja); R$ 75m dívida na companhia.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Taxa (Acquisition Debt):",
        "acquisition_debt_rate",
        "transaction_structure",
        help_text="Taxa em % ou índice + spread. Ex.: CDI+6%; termos ainda em negociação.",
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Prazo (anos):",
        "acquisition_debt_tenor_years",
        "transaction_structure",
        input_type="number",
        help_text="Prazo do acquisition debt em anos.",
        min_value=0.0,
        step=0.5,
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Instituição:",
        "acquisition_debt_institution",
        "transaction_structure",
        help_text="Banco ou fundo financiador, se conhecido. Ex.: bancos de primeira linha; em negociação.",
        memo_type=memo_type
    )
    render_field_with_toggle(
        "Leverage Resultante:",
        "leverage_resulting_x",
        "transaction_structure",
        input_type="number",
        help_text="Alavancagem resultante (x Net Debt/EBITDA). Ex.: 2,2x Net Debt/EBITDA 2024E; 3,6x EBITDA 2025.",
        min_value=0.0,
        step=0.1,
        memo_type=memo_type
    )

    # Opinião do Analista
    render_field_with_toggle(
        "Opinião do Analista sobre a Transação:",
        "investor_opinion",
        "transaction_structure",
        input_type="text_area",
        help_text="Opinião sobre estrutura, atratividade, riscos e pendências (ex.: validar resultado 2024; aprofundar earn-out).",
        height=100,
        memo_type=memo_type
    )
