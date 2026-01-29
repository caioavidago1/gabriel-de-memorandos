import streamlit as st
from funcoes import render_field_with_toggle


def render_tab_qualitative(memo_type=None):
    """Tab 6: Aspectos Qualitativos"""
    st.markdown("### Aspectos Qualitativos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Modelo e Vantagens**")
        
        render_field_with_toggle(
            "Modelo de Negócio",
            "business_model",
            "qualitative",
            input_type="text_area",
            help_text="Resumo do modelo de negócio",
            height=100,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Vantagens Competitivas",
            "competitive_advantages",
            "qualitative",
            input_type="text_area",
            help_text="Principais vantagens competitivas",
            height=100,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Principais Competidores",
            "main_competitors",
            "qualitative",
            help_text="Ex: IHM Stefanini, GreyLogix, TSA",
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Número de Competidores",
            "competitor_count",
            "qualitative",
            help_text="Ex: aproximadamente 30 players",
            memo_type=memo_type
        )
    
    with col2:
        st.markdown("**Mercado e Riscos**")
        
        render_field_with_toggle(
            "Market Share (%)",
            "market_share_pct",
            "qualitative",
            input_type="number",
            help_text="Ex: 40%, 80%",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Fragmentação de Mercado",
            "market_fragmentation",
            "qualitative",
            help_text="fragmentado, consolidado, intermediário",
            memo_type=memo_type
        )
        
        render_field_with_toggle(
            "Principais Riscos",
            "key_risks",
            "qualitative",
            input_type="text_area",
            help_text="Principais riscos do investimento",
            height=120,
            memo_type=memo_type
        )
    
    render_field_with_toggle(
        "Due Diligence e Próximas Etapas",
        "next_steps",
        "qualitative",
        input_type="text_area",
        help_text="Próximos passos de due diligence",
        height=100,
        memo_type=memo_type
    )
