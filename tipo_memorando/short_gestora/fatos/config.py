"""
Config de fatos para Short Memo - Co-investimento (Gestora).

Totalmente autocontido: apenas as seções e campos usados nas abas
Identificação, Gestora, Transação, Saída, Estrutura do Veículo, Opinião do Analista.
"""

from tipo_memorando._base.fatos.config_utils import (
    get_relevant_fields_from_visibility,
    get_field_count_from_relevant,
)

SECTIONS = [
    "identification",
    "gestora",
    "transaction_structure",
    "saida",
    "estrutura_veiculo",
    "opinioes",
]

MEMO_TYPE = "Short Memo - Co-investimento (Gestora)"

FIELD_VISIBILITY = {
    "identification": {
        "gestora_name": "ALL",
        "gestora_fundacao": "ALL",
        "aum_total": "ALL",
        "aum_fundo_especifico": "ALL",
        "veiculo_coinvestimento": "ALL",
        "data_oportunidade": "ALL",
        "company_name": "ALL",
        "company_location": "ALL",
        "setor": "ALL",
        "business_description": "ALL",
    },
    "gestora": {
        "track_record": "ALL",
        "principais_exits": "ALL",
        "equipe": "ALL",
        "estrategia_investimento": "ALL",
        "tese_gestora": "ALL",
        "performance_historica": "ALL",
        "relacionamento_anterior_spectra": "ALL",
    },
    "transaction_structure": {
        "currency": "ALL",
        "valuation_total_empresa": "ALL",
        "participacao_total_adquirida": "ALL",
        "participacao_fundo_gestora": "ALL",
        "participacao_coinvestimento": "ALL",
        "multiple_ev_ebitda": "ALL",
        "multiple_reference_period": "ALL",
        "cash_payment_mm": "ALL",
        "cash_pct_total": "ALL",
        "seller_note_mm": "ALL",
        "seller_note_pct_total": "ALL",
        "seller_note_tenor_years": "ALL",
        "seller_note_index": "ALL",
        "seller_note_frequency": "ALL",
        "seller_note_grace": "ALL",
        "earnout_mm": "ALL",
        "earnout_conditions": "ALL",
        "earnout_timeline": "ALL",
        "compensacao_dividendos": "ALL",
        "acquisition_debt_mm": "ALL",
        "acquisition_debt_rate": "ALL",
        "acquisition_debt_tenor_years": "ALL",
        "acquisition_debt_institution": "ALL",
        "leverage_resulting_x": "ALL",
        "valor_total_coinvestimento": "ALL",
        "alocacao_fundo": "ALL",
        "disponivel_coinvestidores": "ALL",
        "cheque_spectra": "ALL",
        "cheque_spectra_pct": "ALL",
        "assentos_conselho": "ALL",
        "vesting_lockup": "ALL",
        "materias_protegidas": "ALL",
        "tag_along": "ALL",
        "drag_along": "ALL",
        "opcoes_liquidez": "ALL",
        "investor_opinion": "ALL",
    },
    "saida": {
        "cenario_base_ano_saida": "ALL",
        "cenario_base_cagr_receita_pct": "ALL",
        "cenario_base_margem_ebitda_pct": "ALL",
        "cenario_base_multiplo_saida_x": "ALL",
        "cenario_base_multiplo_saida_ano": "ALL",
        "cenario_base_dividendos_periodo": "ALL",
        "cenario_base_tir_bruta_pct": "ALL",
        "cenario_base_moic_bruto": "ALL",
        "cenario_base_tir_liquida_pct": "ALL",
        "cenario_base_moic_liquido": "ALL",
        "cenario_alternativo_ano_saida": "ALL",
        "cenario_alternativo_cagr_receita_pct": "ALL",
        "cenario_alternativo_margem_ebitda_pct": "ALL",
        "cenario_alternativo_multiplo_saida_x": "ALL",
        "cenario_alternativo_multiplo_saida_ano": "ALL",
        "cenario_alternativo_dividendos_periodo": "ALL",
        "cenario_alternativo_tir_bruta_pct": "ALL",
        "cenario_alternativo_moic_bruto": "ALL",
        "cenario_alternativo_tir_liquida_pct": "ALL",
        "cenario_alternativo_moic_liquido": "ALL",
        "cenario_conservador_ano_saida": "ALL",
        "cenario_conservador_cagr_receita_pct": "ALL",
        "cenario_conservador_margem_ebitda_pct": "ALL",
        "cenario_conservador_multiplo_saida_x": "ALL",
        "cenario_conservador_multiplo_saida_ano": "ALL",
        "cenario_conservador_dividendos_periodo": "ALL",
        "cenario_conservador_tir_bruta_pct": "ALL",
        "cenario_conservador_moic_bruto": "ALL",
        "cenario_conservador_tir_liquida_pct": "ALL",
        "cenario_conservador_moic_liquido": "ALL",
        "taxa_gestao_pct": "ALL",
        "taxa_performance_pct": "ALL",
        "saida_observacoes": "ALL",
    },
    "estrutura_veiculo": {
        "duracao_fundo_anos": "ALL",
        "capital_autorizado": "ALL",
        "taxa_gestao_veiculo_pct": "ALL",
        "taxa_performance_veiculo_pct": "ALL",
        "hurdle_rate": "ALL",
        "catch_up": "ALL",
        "evento_equipe_chave": "ALL",
        "quorum_destituicao_pct": "ALL",
        "chamadas_capital": "ALL",
        "pontos_atencao_regulamento": "ALL",
    },
    "opinioes": {
        "key_strengths": "ALL",
        "key_concerns": "ALL",
        "spectra_recommendation": "ALL",
    },
}


def get_sections_for_memo_type(memo_type: str) -> list:
    if memo_type == MEMO_TYPE:
        return SECTIONS
    return []


def get_relevant_fields_for_memo_type(memo_type: str) -> dict:
    if memo_type != MEMO_TYPE:
        return {}
    return get_relevant_fields_from_visibility(FIELD_VISIBILITY, memo_type)


def get_field_count_for_memo_type(memo_type: str) -> dict:
    relevant = get_relevant_fields_for_memo_type(memo_type)
    return get_field_count_from_relevant(relevant)
