import streamlit as st
from funcoes import render_field_with_toggle


def render_tab_transaction(memo_type=None):
    """Tab 2: Estrutura da Transação"""
    st.markdown("### Estrutura da Transação")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Informações Básicas**")
        
        render_field_with_toggle(
            "Moeda",
            "currency",
            "transaction_structure",
            help_text="BRL, USD, MXN",
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "% Participação Adquirida",
            "stake_pct",
            "transaction_structure",
            input_type="number",
            help_text="Ex: 100%, 85%, 90%, 65%",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Enterprise Value (MM)",
            "ev_mm",
            "transaction_structure",
            input_type="number",
            help_text="Enterprise Value em milhões",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Equity Value (MM)",
            "equity_value_mm",
            "transaction_structure",
            input_type="number",
            help_text="Equity Value em milhões",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Múltiplo EV/EBITDA",
            "multiple_ev_ebitda",
            "transaction_structure",
            input_type="number",
            help_text="Ex: 6.5x, 3.5x, 4.4x",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Período de Referência do Múltiplo",
            "multiple_reference_period",
            "transaction_structure",
            help_text="Ex: mai/25 LTM, 2024, 25E",
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Dívida/Equity",
            "debt_equity_ratio",
            "transaction_structure",
            input_type="number",
            help_text="Proporção Dívida/Equity",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type
        )
    
    with col2:
        st.markdown("**Estrutura de Pagamento**")
        
        render_field_with_toggle(
            "Pagamento à Vista (MM)",
            "cash_payment_mm",
            "transaction_structure",
            input_type="number",
            help_text="Ex: R$ 67m, US$ 6m",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Seller Note (MM)",
            "seller_note_mm",
            "transaction_structure",
            input_type="number",
            help_text="Ex: R$ 50m, US$ 78m",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Termos da Seller Note",
            "seller_note_terms",
            "transaction_structure",
            help_text="Ex: 4 anos IPCA",
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Earnout (MM)",
            "earnout_mm",
            "transaction_structure",
            input_type="number",
            help_text="Ex: US$ 36m, R$ 30m",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Condições do Earnout",
            "earnout_conditions",
            "transaction_structure",
            input_type="text_area",
            help_text="Descrição das condições",
            height=80,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Múltiplo com Earnout Integral",
            "multiple_with_earnout",
            "transaction_structure",
            input_type="number",
            help_text="Ex: 4.6x, 7.2x",
            min_value=0.0,
            step=0.1,
            memo_type=memo_type
        )
    
    render_field_with_toggle(
        "Opinião do Analista",
        "investor_opinion",
        "transaction_structure",
        input_type="text_area",
        help_text="Opinião sobre o investidor/Search Fund",
        height=100,
        memo_type=memo_type
    )
