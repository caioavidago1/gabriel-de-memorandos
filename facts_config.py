FIELD_VISIBILITY = {
    "identification": {
        "company_name": "ALL",
        "searcher_name": ["Short Memo - Co-investimento (Search Fund)"],
        "search_start_date": ["Short Memo - Co-investimento (Search Fund)"],
        "business_description": "ALL",
        "investor_nationality": ["Short Memo - Co-investimento (Search Fund)"],
        "company_location": "ALL",
        "company_founding_year": ["Memo - Primário", "Memo - Secundário"],
        "deal_context": "ALL",
    },
    "transaction_structure": {
        "currency": "ALL",
        "investor_opinion": ["Short Memo - Co-investimento (Search Fund)", "Short Memo - Co-investimento (Gestora)"],
        "stake_pct": "ALL",
        "ev_mm": "ALL",
        "equity_value_mm": "ALL",
        "multiple_ev_ebitda": "ALL",
        "multiple_reference_period": "ALL",
        "cash_payment_mm": "ALL",
        "seller_note_mm": ["Short Memo - Co-investimento (Search Fund)", "Short Memo - Primário", "Short Memo - Co-investimento (Gestora)", "Memo - Primário"],
        "seller_note_terms": ["Short Memo - Co-investimento (Search Fund)", "Short Memo - Primário", "Short Memo - Co-investimento (Gestora)", "Memo - Primário"],
        "earnout_mm": ["Short Memo - Co-investimento (Search Fund)", "Short Memo - Primário", "Memo - Primário", "Memo - Secundário"],
        "earnout_conditions": ["Short Memo - Co-investimento (Search Fund)", "Short Memo - Primário", "Memo - Primário", "Memo - Secundário"],
        "multiple_with_earnout": ["Short Memo - Co-investimento (Search Fund)", "Short Memo - Primário", "Memo - Primário"],
        "debt_equity_ratio": "ALL",
        # Campos específicos para Short Memo - Secundário
        "multiple_ev_fcf": ["Short Memo - Secundário"],
        "target_leverage": ["Short Memo - Secundário"],
        "acquisition_debt_mm": ["Short Memo - Secundário"],
    },
    "financials_history": {
        "revenue_current_mm": "ALL",
        "revenue_cagr_pct": "ALL",
        "revenue_cagr_period": "ALL",
        "revenue_base_year": "ALL",
        "revenue_base_year_mm": "ALL",
        "ebitda_current_mm": "ALL",
        "ebitda_margin_current_pct": "ALL",
        "ebitda_cagr_pct": ["Memo - Primário", "Memo - Secundário"],
        "ebitda_base_year_mm": ["Memo - Primário", "Memo - Secundário"],
        "net_debt_mm": "ALL",
        "leverage_net_debt_ebitda": "ALL",
        "cash_conversion_pct": ["Short Memo - Co-investimento (Search Fund)", "Short Memo - Co-investimento (Gestora)", "Memo - Primário"],
        "gross_margin_pct": ["Short Memo - Co-investimento (Gestora)", "Memo - Primário", "Memo - Secundário"],
        "opex_pct_revenue": ["Short Memo - Co-investimento (Search Fund)", "Memo - Primário"],
        "employees_count": ["Short Memo - Co-investimento (Search Fund)", "Memo - Primário"],
        "financials_commentary": "ALL",
        # Campos específicos para Short Memo - Secundário
        "fcf_current_mm": ["Short Memo - Secundário"],
        "fcf_conversion_pct": ["Short Memo - Secundário"],
        "roic_pct": ["Short Memo - Secundário"],
    },
    "saida": {
        "revenue_exit_mm": "ALL",
        "exit_year": "ALL",
        "revenue_cagr_projected_pct": "ALL",
        "projection_period": "ALL",
        "ebitda_exit_mm": "ALL",
        "ebitda_margin_exit_pct": "ALL",
        "exit_multiple_ev_ebitda": "ALL",
        "growth_drivers": "ALL",
        "scenario_type": "ALL",
        "projections_commentary": "ALL",
        "exit_strategy": "ALL",
        "value_creation_drivers": "ALL",
        "exit_commentary": "ALL",
    },
    "returns": {
        "irr_pct": "ALL",
        "moic": "ALL",
        "holding_period_years": "ALL",
        "entry_multiple": "ALL",
        "returns_commentary": "ALL",
        # Campos específicos para Short Memo - Secundário
        "fcf_yield_pct": ["Short Memo - Secundário"],
        "dividend_recaps": ["Short Memo - Secundário"],
    },
    "qualitative": {
        "business_model": "ALL",
        "competitive_advantages": "ALL",
        "key_risks": "ALL",
        "next_steps": ["Short Memo - Co-investimento (Search Fund)", "Short Memo - Co-investimento (Gestora)", "Short Memo - Primário"],
        "main_competitors": "ALL",
        "competitor_count": ["Short Memo - Co-investimento (Search Fund)", "Short Memo - Co-investimento (Gestora)", "Memo - Primário"],
        "market_share_pct": ["Short Memo - Co-investimento (Gestora)", "Memo - Primário", "Memo - Secundário"],
        "market_fragmentation": ["Short Memo - Co-investimento (Search Fund)", "Short Memo - Co-investimento (Gestora)", "Memo - Primário"],
        "market_overview": "ALL",
        "management_team": "ALL",
        "growth_strategy": "ALL",
        "esg_considerations": "ALL",
        "qualitative_commentary": "ALL",
    },
    "opinioes": {
        "founders_opinion": ["Short Memo - Primário"],
        "founders_track_record": ["Short Memo - Primário"],
        "founders_comparison": ["Short Memo - Primário"],
        "company_positioning_opinion": ["Short Memo - Primário"],
        "market_reputation": ["Short Memo - Primário"],
        "spectra_recommendation": "ALL",
        "key_strengths": "ALL",
        "key_concerns": "ALL",
        "investment_rationale": "ALL",
        "next_steps": ["Short Memo - Co-investimento (Search Fund)", "Short Memo - Co-investimento (Gestora)", "Short Memo - Primário"],
    },
    "gestora": {
        "gestora_nome": ["Short Memo - Primário"],
        "gestora_ano_fundacao": ["Short Memo - Primário"],
        "gestora_localizacao": ["Short Memo - Primário"],
        "gestora_tipo": ["Short Memo - Primário"],
        "gestora_aum_mm": ["Short Memo - Primário"],
        "gestora_num_fundos": ["Short Memo - Primário"],
        "gestora_socios_principais": ["Short Memo - Primário"],
        "gestora_filosofia_investimento": ["Short Memo - Primário"],
    },
    "fundo": {
        "fundo_nome": ["Short Memo - Primário"],
        "fundo_vintage": ["Short Memo - Primário"],  # CORRIGIDO: era fundo_vintage_year
        "fundo_closing": ["Short Memo - Primário"],  # CORRIGIDO: era fundo_numero_ordinal
        "fundo_moeda": ["Short Memo - Primário"],
        "fundo_target_mm": ["Short Memo - Primário"],
        "fundo_hard_cap_mm": ["Short Memo - Primário"],
        "fundo_status_captacao": ["Short Memo - Primário"],
        "fundo_primeiro_closing_data": ["Short Memo - Primário"],
        "fundo_primeiro_closing_target_mm": ["Short Memo - Primário"],
        "fundo_captado_mm": ["Short Memo - Primário"],  # CORRIGIDO: era fundo_capital_levantado_mm
        "fundo_percentual_levantado": ["Short Memo - Primário"],
        "fundo_commitment_spectra_mm": ["Short Memo - Primário"],  # ADICIONADO
        "fundo_commitment_spectra_pct": ["Short Memo - Primário"],  # ADICIONADO
        "fundo_periodo_investimento_anos": ["Short Memo - Primário"],  # ADICIONADO
        "fundo_vida_total_anos": ["Short Memo - Primário"],  # ADICIONADO
    },
    "estrategia": {
        "estrategia_tese": ["Short Memo - Primário"],  # CORRIGIDO: era estrategia_tese_investimento
        "estrategia_setores": ["Short Memo - Primário"],  # CORRIGIDO: era estrategia_setores_foco
        "estrategia_geografia": ["Short Memo - Primário"],
        "estrategia_estagio": ["Short Memo - Primário"],
        "estrategia_numero_ativos_alvo": ["Short Memo - Primário"],
        "estrategia_ticket_medio_mm": ["Short Memo - Primário"],
        "estrategia_ticket_min_mm": ["Short Memo - Primário"],  # ADICIONADO
        "estrategia_ticket_max_mm": ["Short Memo - Primário"],  # ADICIONADO
        "estrategia_tipo_participacao": ["Short Memo - Primário"],
        "estrategia_alocacao": ["Short Memo - Primário"],
        "estrategia_diferenciacao": ["Short Memo - Primário"],  # ADICIONADO
    },
    "spectra_context": {
        "spectra_is_existing_lp": ["Short Memo - Primário"],
        "spectra_previous_funds": ["Short Memo - Primário"],
        "spectra_vehicle": ["Short Memo - Primário"],
        "spectra_relacao_historica": ["Short Memo - Primário"],
        "spectra_relacionamento": ["Short Memo - Primário"],  # ADICIONADO (alias)
        "spectra_commitment_target_mm": ["Short Memo - Primário"],
        "spectra_commitment_pct": ["Short Memo - Primário"],
        "spectra_closing_alvo": ["Short Memo - Primário"],
        "spectra_coinvestidores": ["Short Memo - Primário"],  # ADICIONADO
        "spectra_allocation_strategy": ["Short Memo - Primário"],  # ADICIONADO
        "spectra_due_diligence": ["Short Memo - Primário"],  # ADICIONADO
        "spectra_termos_negociados": ["Short Memo - Primário"],  # ADICIONADO
        "spectra_fees_terms": ["Short Memo - Primário"],  # ADICIONADO
        "spectra_governance": ["Short Memo - Primário"],  # ADICIONADO
    },
    "portfolio_secundario": {
        "nav_data_base": ["Short Memo - Secundário"],
        "nav_mm": ["Short Memo - Secundário"],
        "desconto_nav_pct": ["Short Memo - Secundário"],
        "expectativa_recebimento_mm": ["Short Memo - Secundário"],
        "numero_fundos": ["Short Memo - Secundário"],
        "numero_ativos": ["Short Memo - Secundário"],
        "portfolio_commentary": ["Short Memo - Secundário"],
    },
    # Seções para Memo Completo Search Fund
    "searcher": {
        "searcher_name": ["Memo - Co-investimento (Search Fund)"],
        "searcher_background": ["Memo - Co-investimento (Search Fund)"],
        "searcher_experience": ["Memo - Co-investimento (Search Fund)"],
        "searcher_assessment": ["Memo - Co-investimento (Search Fund)"],
        "searcher_complementarity": ["Memo - Co-investimento (Search Fund)"],
        "searcher_references": ["Memo - Co-investimento (Search Fund)"],
        "searcher_track_record": ["Memo - Co-investimento (Search Fund)"],
    },
    "gestor": {
        "searcher_name": ["Memo - Co-investimento (Search Fund)"],
        "searcher_background": ["Memo - Co-investimento (Search Fund)"],
        "searcher_experience": ["Memo - Co-investimento (Search Fund)"],
        "searcher_assessment": ["Memo - Co-investimento (Search Fund)"],
        "searcher_complementarity": ["Memo - Co-investimento (Search Fund)"],
        "searcher_references": ["Memo - Co-investimento (Search Fund)"],
        "searcher_track_record": ["Memo - Co-investimento (Search Fund)"],
    },
    "projections_table": {
        "projections_years": ["Memo - Co-investimento (Search Fund)"],
        "projections_base_case": ["Memo - Co-investimento (Search Fund)"],
        "projections_upside_case": ["Memo - Co-investimento (Search Fund)"],
        "projections_downside_case": ["Memo - Co-investimento (Search Fund)"],
        "projections_assumptions_base": ["Memo - Co-investimento (Search Fund)"],
        "projections_assumptions_upside": ["Memo - Co-investimento (Search Fund)"],
        "projections_assumptions_downside": ["Memo - Co-investimento (Search Fund)"],
    },
    "returns_table": {
        "returns_base_case": ["Memorando - Co-investimento (Search Fund)"],
        "returns_upside_case": ["Memorando - Co-investimento (Search Fund)"],
        "returns_downside_case": ["Memorando - Co-investimento (Search Fund)"],
        "returns_sensitivity_table": ["Memorando - Co-investimento (Search Fund)"],
        "returns_exit_scenarios": ["Memorando - Co-investimento (Search Fund)"],
    },
    "board_cap_table": {
        "board_members": ["Memorando - Co-investimento (Search Fund)"],
        "cap_table": ["Memorando - Co-investimento (Search Fund)"],
        "governance_structure": ["Memorando - Co-investimento (Search Fund)"],
        "board_commentary": ["Memorando - Co-investimento (Search Fund)"],
    }
}


def should_show_field(section: str, field_key: str, memo_type: str) -> bool:
    """
    Verifica se um campo deve ser mostrado para um determinado tipo de memorando
    
    Args:
        section: Seção do campo (ex: "identification", "transaction_structure")
        field_key: Chave do campo (ex: "company_name", "investor_name")
        memo_type: Tipo de memorando selecionado
        
    Returns:
        True se o campo deve ser mostrado, False caso contrário
    """
    if section not in FIELD_VISIBILITY:
        return True  # Se a seção não está mapeada, mostra por padrão
    
    section_config = FIELD_VISIBILITY[section]
    
    if field_key not in section_config:
        return True  # Se o campo não está mapeado, mostra por padrão
    
    field_config = section_config[field_key]
    
    if field_config == "ALL":
        return True
    
    if isinstance(field_config, list):
        return memo_type in field_config
    
    return True  # Default: mostrar


def get_relevant_fields_for_memo_type(memo_type: str) -> dict:
    """
    Retorna apenas os campos relevantes para um tipo de memorando específico.
    
    Esta função filtra FIELD_VISIBILITY para retornar apenas os campos que devem
    ser extraídos/mostrados para o tipo de memo selecionado.
    
    Args:
        memo_type: Tipo de memorando (ex: "Short Memo - Primário")
    
    Returns:
        Dict com estrutura {section: [field_key1, field_key2, ...]}
        Contém apenas campos relevantes para o tipo selecionado
    
    Example:
        >>> get_relevant_fields_for_memo_type("Short Memo - Primário")
        {
            "gestora": ["gestora_nome", "gestora_ano_fundacao", ...],
            "fundo": ["fundo_nome", "fundo_target_mm", ...],
            ...
        }
    """
    relevant_fields = {}
    
    for section, fields in FIELD_VISIBILITY.items():
        relevant_fields[section] = []
        
        for field_key, visibility_config in fields.items():
            # Campo é relevante se:
            # 1. visibility_config == "ALL", ou
            # 2. visibility_config é lista contendo o memo_type
            if visibility_config == "ALL":
                relevant_fields[section].append(field_key)
            elif isinstance(visibility_config, list) and memo_type in visibility_config:
                relevant_fields[section].append(field_key)
    
    # Remover seções vazias
    relevant_fields = {k: v for k, v in relevant_fields.items() if v}
    
    return relevant_fields


def get_sections_for_memo_type(memo_type: str) -> list:
    """
    Retorna lista de seções que devem ser extraídas para um tipo de memo.
    
    Short Memo - Primário: gestora, fundo, estrategia, spectra_context, opinioes
    Short Memo - Secundário: identification, transaction_structure, financials_history, returns, qualitative, opinioes, portfolio_secundario
    Memo - Co-investimento (Search Fund): identification, gestor, transaction_structure, financials_history, projections_table, returns_table, board_cap_table, qualitative, opinioes
    Outros: identification, transaction_structure, financials_history, saida, returns, qualitative, opinioes
    
    Args:
        memo_type: Tipo de memorando
    
    Returns:
        Lista de nomes de seções a serem extraídas
    """
    if memo_type == "Short Memo - Primário":
        # Fundos: apenas seções específicas de fundos
        return ["gestora", "fundo", "estrategia", "spectra_context", "opinioes"]
    elif memo_type == "Short Memo - Secundário":
        # Secundário: seções padrão + portfolio_secundario (sem saida)
        return [
            "identification",
            "transaction_structure",
            "financials_history",
            "returns",
            "qualitative",
            "opinioes",
            "portfolio_secundario"
        ]
    elif memo_type == "Memorando - Co-investimento (Search Fund)":
        # Memo Completo Search Fund: seções padrão + gestor + tabelas específicas
        return [
            "identification",
            "gestor",  # NOVO - análise dos searchers
            "transaction_structure",
            "financials_history",
            "projections_table",  # NOVO - tabelas de projeções
            "returns_table",  # NOVO - tabelas de retornos
            "board_cap_table",  # NOVO - board e cap table
            "qualitative",
            "opinioes"
        ]
    else:
        # Investimentos em empresas: seções padrão
        return [
            "identification",
            "transaction_structure",
            "financials_history",
            "saida",
            "returns",
            "qualitative",
            "opinioes"
        ]


def get_field_count_for_memo_type(memo_type: str) -> dict:
    """
    Conta quantos campos serão extraídos para cada tipo de memo.
    
    Útil para debug e informar ao usuário quantos campos serão processados.
    
    Args:
        memo_type: Tipo de memorando
    
    Returns:
        Dict com {
            "total": int,
            "by_section": {"section_name": count, ...}
        }
    """
    relevant = get_relevant_fields_for_memo_type(memo_type)
    
    by_section = {section: len(fields) for section, fields in relevant.items()}
    total = sum(by_section.values())
    
    return {
        "total": total,
        "by_section": by_section
    }

