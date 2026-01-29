"""
Schema de Facts para Short Memo Primário (Investimento em Fundos)

Define estrutura de dados específica para investimentos como LP em fundos de PE/VC.
NÃO reutiliza schema de investimento direto em empresas.
"""

from typing import Dict, Any, List, Optional


# ═══════════════════════════════════════════════════════════════════════
# SCHEMA DEDICADO PARA INVESTIMENTO PRIMÁRIO EM FUNDOS
# ═══════════════════════════════════════════════════════════════════════

FUND_INVESTMENT_SCHEMA = {
    "gestora": {
        "nome": str,  # Nome da gestora
        "ano_fundacao": int,  # Ano de fundação
        "localizacao": str,  # Cidade/Estado
        "tipo": str,  # "Operator-led PE", "Growth equity", "Venture capital", etc
        "aum_total_mm": float,  # Assets under management total
        "num_fundos_total": int,  # Quantos fundos já levantou
        "socios_principais": List[str],  # GPs principais
        "filosofia_investimento": str,  # Descrição da filosofia
    },
    "fundo": {
        "nome": str,  # Nome do fundo (ex: "Shift Alpha II")
        "numero_ordinal": str,  # "primeiro", "segundo", "terceiro", etc
        "numero_romano": str,  # "I", "II", "III", etc (opcional)
        "target_mm": float,  # Target size em milhões
        "hard_cap_mm": float,  # Hard cap em milhões
        "moeda": str,  # "BRL", "USD", etc
        "vintage_year": int,  # Ano vintage do fundo
        "status_captacao": str,  # "Em captação", "Primeiro closing concluído", etc
        "primeiro_closing_data": str,  # Data esperada (ex: "mar/26")
        "primeiro_closing_target_mm": float,  # Target do primeiro closing
        "capital_levantado_mm": float,  # Capital já comprometido
        "percentual_levantado": float,  # % do target já levantado
    },
    "estrategia": {
        "tese_investimento": str,  # Tese principal do fundo
        "setores_foco": List[str],  # Setores alvo
        "geografia": str,  # Geografia de atuação
        "estagio": str,  # "Early stage PE", "Growth", "Venture", etc
        "numero_ativos_alvo": int,  # Número de empresas planejadas no portfólio
        "numero_ativos_min": int,  # Mínimo de ativos
        "numero_ativos_max": int,  # Máximo de ativos
        "ticket_medio_mm": float,  # Ticket médio esperado
        "ticket_min_mm": float,  # Ticket mínimo
        "ticket_max_mm": float,  # Ticket máximo
        "tipo_participacao": str,  # "Minoritário", "Controle", "Misto"
        "estrategia_alocacao": str,  # Ex: "2 anchor + 4-5 growth minoritário"
    },
    "track_record": {
        "fundo_anterior_nome": str,  # Nome do fundo anterior
        "fundo_anterior_numero": str,  # Número do fundo anterior
        "fundo_anterior_tamanho_mm": float,  # Tamanho do fundo anterior
        "fundo_anterior_vintage": int,  # Vintage year do fundo anterior
        "fundo_anterior_num_ativos": int,  # Número de investimentos realizados
        "fundo_anterior_irr_gross_pct": float,  # IRR bruto
        "fundo_anterior_irr_net_pct": float,  # IRR líquido
        "fundo_anterior_moic_gross": float,  # MOIC bruto
        "fundo_anterior_moic_net": float,  # MOIC líquido
        "fundo_anterior_status": str,  # "Fully invested", "In harvest", etc
        "total_deals_gestora": int,  # Total de deals já feitos pela gestora
        "total_exits_gestora": int,  # Total de saídas realizadas
        "exits_destaque": List[str],  # Principais exits (nomes)
    },
    "termos": {
        "management_fee_investimento_pct": float,  # Fee durante período de investimento
        "management_fee_harvest_pct": float,  # Fee durante período de desinvestimento
        "periodo_investimento_anos": int,  # Período de investimento (ex: 5 anos)
        "duracao_total_anos": int,  # Duração total do fundo (ex: 10 anos)
        "extensoes_possiveis_anos": int,  # Extensões possíveis (ex: +2 anos)
        "carried_interest_pct": float,  # Carried interest (ex: 20%)
        "hurdle_rate_pct": float,  # Hurdle rate (ex: 8%)
        "catch_up_pct": float,  # Catch-up (ex: 100%)
        "estrutura_fees": str,  # Descrição da estrutura
        "clawback": bool,  # Se tem clawback
        "key_person": List[str],  # Key persons
        "commitment_minimo_mm": float,  # Commitment mínimo de LP
    },
    "retornos_alvo": {
        "irr_alvo_gross_pct": float,  # IRR alvo bruto
        "irr_alvo_net_pct": float,  # IRR alvo líquido
        "moic_alvo_gross": float,  # MOIC alvo bruto
        "moic_alvo_net": float,  # MOIC alvo líquido
        "holding_period_medio_anos": float,  # Holding period médio esperado
    },
    "spectra_context": {
        "is_existing_lp": bool,  # Spectra já é LP de fundos anteriores?
        "previous_funds_invested": List[str],  # Fundos anteriores que Spectra investiu
        "spectra_vehicle": str,  # Veículo da Spectra (ex: "Fundo VII")
        "commitment_target_mm": float,  # Commitment alvo da Spectra
        "commitment_pct_of_fund": float,  # % do fundo que Spectra representa
        "closing_alvo": str,  # "Primeiro closing", "Final closing", etc
        "relacao_historica": str,  # Descrição do histórico com a gestora
    },
    "opinioes_spectra": {
        "opiniao_gps": str,  # Opinião sobre os GPs
        "track_record_gps": str,  # Avaliação do track record dos GPs
        "opiniao_posicionamento_gestora": str,  # Opinião sobre posicionamento
        "reputacao_mercado": str,  # Reputação da gestora no mercado
        "comparacao_outras_gestoras": str,  # Comparação com peers
        "pontos_fortes": List[str],  # Principais pontos fortes
        "pontos_atencao": List[str],  # Pontos de atenção
    }
}


# ═══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def build_fund_facts_section(
    facts: Dict[str, Any],
    section_name: str,
    field_labels: Dict[str, str]
) -> str:
    """
    Constrói seção formatada de facts para FUNDOS, omitindo campos vazios.
    
    Similar ao build_facts_section mas específico para schema de fundos.
    
    Args:
        facts: Dict completo de facts estruturados
        section_name: Nome da seção (ex: "gestora", "fundo", "estrategia")
        field_labels: Mapeamento de field_key -> label amigável
    
    Returns:
        String formatada com facts não vazios
    """
    section_data = facts.get(section_name, {})
    
    if not section_data:
        return ""
    
    lines = []
    for field_key, label in field_labels.items():
        value = section_data.get(field_key)
        
        # Omitir valores vazios/None
        if value is None or value == "" or value == [] or value == {}:
            continue
        
        # Formatar listas
        if isinstance(value, list):
            if len(value) == 0:
                continue
            value_str = ", ".join(str(v) for v in value)
            lines.append(f"- {label}: {value_str}")
        # Formatar booleanos
        elif isinstance(value, bool):
            lines.append(f"- {label}: {'Sim' if value else 'Não'}")
        # Outros valores
        else:
            lines.append(f"- {label}: {value}")
    
    return "\n".join(lines)


def validate_fund_facts(facts: Dict[str, Any]) -> List[str]:
    """
    Valida facts de investimento em fundo.
    
    Args:
        facts: Dict de facts estruturados
    
    Returns:
        Lista de erros encontrados (vazia se tudo OK)
    """
    errors = []
    
    # Validações de FUNDO
    fundo = facts.get("fundo", {})
    if fundo:
        target = fundo.get("target_mm")
        hard_cap = fundo.get("hard_cap_mm")
        if target and hard_cap and hard_cap < target:
            errors.append("❌ Hard cap deve ser >= target do fundo")
        
        capital_levantado = fundo.get("capital_levantado_mm")
        if capital_levantado and target and capital_levantado > target:
            errors.append("❌ Capital levantado não pode exceder target")
    
    # Validações de GESTORA
    gestora = facts.get("gestora", {})
    if not gestora.get("nome"):
        errors.append("❌ Nome da gestora é obrigatório")
    
    # Validações de TERMOS
    termos = facts.get("termos", {})
    if termos:
        periodo_inv = termos.get("periodo_investimento_anos")
        duracao = termos.get("duracao_total_anos")
        if periodo_inv and duracao and periodo_inv > duracao:
            errors.append("❌ Período investimento não pode ser maior que duração total")
    
    # Validações de RETORNOS
    retornos = facts.get("retornos_alvo", {})
    if retornos:
        irr_gross = retornos.get("irr_alvo_gross_pct")
        irr_net = retornos.get("irr_alvo_net_pct")
        if irr_gross and irr_net and irr_net > irr_gross:
            errors.append("❌ IRR líquido não pode ser maior que IRR bruto")
    
    return errors


def get_default_fund_facts() -> Dict[str, Any]:
    """Retorna template vazio de facts para fundos."""
    return {
        "gestora": {},
        "fundo": {},
        "estrategia": {},
        "track_record": {},
        "termos": {},
        "retornos_alvo": {},
        "spectra_context": {},
        "opinioes_spectra": {}
    }
