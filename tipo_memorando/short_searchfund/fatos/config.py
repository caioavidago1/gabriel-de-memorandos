"""
Config de fatos para Short Memo - Co-investimento (Search Fund).

FIELD_VISIBILITY e funções de seções/campos específicas deste tipo.
"""

# Seções extraídas para Short Memo Search Fund
SECTIONS = [
    "identification",
    "transaction_structure",
    "financials_history",
    "saida",
    "qualitative",
    "opinioes",
]

# Campos por seção - apenas os relevantes para Short Memo Search Fund
# (ALL ou lista contendo "Short Memo - Co-investimento (Search Fund)")
FIELD_VISIBILITY = {
    "identification": {
        "searcher_name": ["Short Memo - Co-investimento (Search Fund)"],
        "investor_nationality": ["Short Memo - Co-investimento (Search Fund)"],
        "fip_casca": ["Short Memo - Co-investimento (Search Fund)"],
        "search_start_date": ["Short Memo - Co-investimento (Search Fund)"],
        "company_name": "ALL",
        "company_location": "ALL",
        "business_description": "ALL",
        "deal_context": "ALL",
    },
    "transaction_structure": {
        "currency": "ALL",
        "stake_pct": "ALL",
        "equity_value_mm": "ALL",
        "ev_mm": "ALL",
        "multiple_ev_ebitda": "ALL",
        "multiple_reference_period": "ALL",
        "total_transaction_value_mm": "ALL",
        "multiple_total": "ALL",
        "cash_payment_mm": "ALL",
        "cash_pct_total": "ALL",
        "equity_cash_mm": "ALL",
        "seller_note_mm": "ALL",
        "seller_note_pct_total": "ALL",
        "seller_note_tenor_years": "ALL",
        "seller_note_index": "ALL",
        "seller_note_frequency": "ALL",
        "seller_note_grace": "ALL",
        "seller_note_terms": "ALL",
        "earnout_mm": "ALL",
        "earnout_conditions": "ALL",
        "earnout_timeline": "ALL",
        "step_up_mm": "ALL",
        "acquisition_debt_mm": "ALL",
        "acquisition_debt_rate": "ALL",
        "acquisition_debt_tenor_years": "ALL",
        "acquisition_debt_institution": "ALL",
        "leverage_resulting_x": "ALL",
        "multiple_with_earnout": "ALL",
        "debt_equity_ratio": "ALL",
        "investor_opinion": ["Short Memo - Co-investimento (Search Fund)"],
    },
    "financials_history": {
        "revenue_current_mm": "ALL",
        "revenue_cagr_pct": "ALL",
        "revenue_cagr_period": "ALL",
        "revenue_base_year": "ALL",
        "revenue_base_year_mm": "ALL",
        "ebitda_current_mm": "ALL",
        "ebitda_margin_current_pct": "ALL",
        "net_debt_mm": "ALL",
        "leverage_net_debt_ebitda": "ALL",
        "cash_conversion_pct": ["Short Memo - Co-investimento (Search Fund)"],
        "opex_pct_revenue": ["Short Memo - Co-investimento (Search Fund)"],
        "employees_count": ["Short Memo - Co-investimento (Search Fund)"],
        "financials_commentary": "ALL",
    },
    "saida": {
        "cenario_base_ano_saida": "ALL",
        "cenario_base_cagr_receita_pct": "ALL",
        "cenario_base_margem_ebitda_pct": "ALL",
        "cenario_base_multiplo_saida_x": "ALL",
        "cenario_base_multiplo_saida_ano": "ALL",
        "cenario_base_dividend_yield_pct": "ALL",
        "cenario_base_tir_pct": "ALL",
        "cenario_base_moic": "ALL",
        "cenario_alternativo_ano_saida": "ALL",
        "cenario_alternativo_cagr_receita_pct": "ALL",
        "cenario_alternativo_margem_ebitda_pct": "ALL",
        "cenario_alternativo_multiplo_saida_x": "ALL",
        "cenario_alternativo_multiplo_saida_ano": "ALL",
        "cenario_alternativo_dividend_yield_pct": "ALL",
        "cenario_alternativo_tir_pct": "ALL",
        "cenario_alternativo_moic": "ALL",
        "saida_observacoes": "ALL",
    },
    "qualitative": {
        "business_model": "ALL",
        "competitive_advantages": "ALL",
        "key_risks": "ALL",
        "next_steps": ["Short Memo - Co-investimento (Search Fund)"],
        "main_competitors": "ALL",
        "competitor_count": ["Short Memo - Co-investimento (Search Fund)"],
        "market_fragmentation": ["Short Memo - Co-investimento (Search Fund)"],
        "market_overview": "ALL",
        "management_team": "ALL",
        "growth_strategy": "ALL",
        "esg_considerations": "ALL",
        "qualitative_commentary": "ALL",
    },
    "opinioes": {
        "spectra_recommendation": "ALL",
        "key_strengths": "ALL",
        "key_concerns": "ALL",
        "investment_rationale": "ALL",
        "next_steps": ["Short Memo - Co-investimento (Search Fund)"],
    },
}

MEMO_TYPE = "Short Memo - Co-investimento (Search Fund)"


def get_sections_for_memo_type(memo_type: str) -> list:
    """Retorna lista de seções para Short Memo Search Fund."""
    if memo_type == MEMO_TYPE:
        return SECTIONS
    return []


def get_relevant_fields_for_memo_type(memo_type: str) -> dict:
    """Retorna campos relevantes para Short Memo Search Fund."""
    if memo_type != MEMO_TYPE:
        return {}

    relevant_fields = {}
    for section, fields in FIELD_VISIBILITY.items():
        relevant_fields[section] = []
        for field_key, visibility_config in fields.items():
            if visibility_config == "ALL":
                relevant_fields[section].append(field_key)
            elif isinstance(visibility_config, list) and memo_type in visibility_config:
                relevant_fields[section].append(field_key)
    return {k: v for k, v in relevant_fields.items() if v}


def get_field_count_for_memo_type(memo_type: str) -> dict:
    """Conta campos por seção para Short Memo Search Fund."""
    relevant = get_relevant_fields_for_memo_type(memo_type)
    by_section = {section: len(fields) for section, fields in relevant.items()}
    return {
        "total": sum(by_section.values()),
        "by_section": by_section,
    }
