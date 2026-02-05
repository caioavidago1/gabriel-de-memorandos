"""
Módulo para cálculos da DRE.

Este módulo realiza os cálculos das linhas calculadas da DRE
baseado nos valores extraídos dos documentos.
"""

from typing import Dict, Optional
from core.logger import get_logger

logger = get_logger(__name__)


def calcular_margem_bruta(
    lucro_bruto: Optional[float],
    receita_liquida: Optional[float]
) -> Optional[float]:
    """
    Calcula margem bruta: (lucro bruto / receita líquida) * 100.
    
    Args:
        lucro_bruto: Lucro bruto
        receita_liquida: Receita líquida
        
    Returns:
        Margem bruta em percentual ou None se não puder calcular
    """
    if lucro_bruto is None or receita_liquida is None:
        return None
    
    if receita_liquida == 0:
        return None
    
    try:
        margem = (lucro_bruto / receita_liquida) * 100
        return round(margem, 2)
    except (ZeroDivisionError, TypeError):
        return None


def calcular_margem_ebitda(
    ebitda: Optional[float],
    receita_liquida: Optional[float]
) -> Optional[float]:
    """
    Calcula margem EBITDA: (EBITDA / receita líquida) * 100.
    
    Args:
        ebitda: EBITDA
        receita_liquida: Receita líquida
        
    Returns:
        Margem EBITDA em percentual ou None se não puder calcular
    """
    if ebitda is None or receita_liquida is None:
        return None
    
    if receita_liquida == 0:
        return None
    
    try:
        margem = (ebitda / receita_liquida) * 100
        return round(margem, 2)
    except (ZeroDivisionError, TypeError):
        return None


def calcular_margem_ebit(
    ebit: Optional[float],
    receita_liquida: Optional[float]
) -> Optional[float]:
    """
    Calcula margem EBIT: (EBIT / receita líquida) * 100.
    
    Args:
        ebit: EBIT
        receita_liquida: Receita líquida
        
    Returns:
        Margem EBIT em percentual ou None se não puder calcular
    """
    if ebit is None or receita_liquida is None:
        return None
    
    if receita_liquida == 0:
        return None
    
    try:
        margem = (ebit / receita_liquida) * 100
        return round(margem, 2)
    except (ZeroDivisionError, TypeError):
        return None


def calcular_margem_liquida(
    lucro_liquido: Optional[float],
    receita_liquida: Optional[float]
) -> Optional[float]:
    """
    Calcula margem líquida: (lucro líquido / receita líquida) * 100.
    
    Args:
        lucro_liquido: Lucro líquido
        receita_liquida: Receita líquida
        
    Returns:
        Margem líquida em percentual ou None se não puder calcular
    """
    if lucro_liquido is None or receita_liquida is None:
        return None
    
    if receita_liquida == 0:
        return None
    
    try:
        margem = (lucro_liquido / receita_liquida) * 100
        return round(margem, 2)
    except (ZeroDivisionError, TypeError):
        return None


def calcular_capex_pct_receita(
    capex: Optional[float],
    receita_liquida: Optional[float]
) -> Optional[float]:
    """
    Calcula Capex % Receita Líquida: (Capex / receita líquida) * 100.
    
    Args:
        capex: Capex
        receita_liquida: Receita líquida
        
    Returns:
        Capex % Receita Líquida em percentual ou None se não puder calcular
    """
    if capex is None or receita_liquida is None:
        return None
    
    if receita_liquida == 0:
        return None
    
    try:
        pct = (capex / receita_liquida) * 100
        return round(pct, 2)
    except (ZeroDivisionError, TypeError):
        return None


def calcular_dv_ebitda(
    divida_liquida: Optional[float],
    ebitda: Optional[float]
) -> Optional[float]:
    """
    Calcula DV/EBITDA: dívida líquida / EBITDA.
    
    Args:
        divida_liquida: Dívida líquida
        ebitda: EBITDA
        
    Returns:
        DV/EBITDA (múltiplo) ou None se não puder calcular
    """
    if divida_liquida is None or ebitda is None:
        return None
    
    if ebitda == 0:
        return None
    
    try:
        ratio = divida_liquida / ebitda
        return round(ratio, 2)
    except (ZeroDivisionError, TypeError):
        return None


def calcular_geracao_caixa_pct_ebitda(
    geracao_caixa: Optional[float],
    ebitda: Optional[float]
) -> Optional[float]:
    """
    Calcula Geração de Caixa % EBITDA: (geração de caixa / EBITDA) * 100.
    
    Args:
        geracao_caixa: Geração de caixa
        ebitda: EBITDA
        
    Returns:
        Geração de Caixa % EBITDA em percentual ou None se não puder calcular
    """
    if geracao_caixa is None or ebitda is None:
        return None
    
    if ebitda == 0:
        return None
    
    try:
        pct = (geracao_caixa / ebitda) * 100
        return round(pct, 2)
    except (ZeroDivisionError, TypeError):
        return None


def calcular_todos_valores_calculados(
    table_data: Dict[str, Dict[int, Optional[float]]]
) -> Dict[str, Dict[int, Optional[float]]]:
    """
    Calcula todos os valores calculados da DRE.
    
    Args:
        table_data: Dados da tabela com valores extraídos
        
    Returns:
        Dicionário com valores calculados adicionados
    """
    result = table_data.copy()
    
    # Obter anos disponíveis
    years = list(next(iter(table_data.values())).keys()) if table_data else []
    
    for year in years:
        # Obter valores do ano
        receita_liquida = table_data.get("receita_liquida", {}).get(year)
        lucro_bruto = table_data.get("lucro_bruto", {}).get(year)
        ebitda = table_data.get("ebitda", {}).get(year)
        ebit = table_data.get("ebit", {}).get(year)
        lucro_liquido = table_data.get("lucro_liquido", {}).get(year)
        capex = table_data.get("capex", {}).get(year)
        divida_liquida = table_data.get("divida_liquida", {}).get(year)
        geracao_caixa_operacional = table_data.get("geracao_caixa_operacional", {}).get(year)
        geracao_caixa = table_data.get("geracao_caixa", {}).get(year)
        
        # Calcular margens e ratios
        if "margem_bruta" not in result:
            result["margem_bruta"] = {}
        result["margem_bruta"][year] = calcular_margem_bruta(lucro_bruto, receita_liquida)
        
        if "margem_ebitda" not in result:
            result["margem_ebitda"] = {}
        result["margem_ebitda"][year] = calcular_margem_ebitda(ebitda, receita_liquida)
        
        if "margem_ebit" not in result:
            result["margem_ebit"] = {}
        result["margem_ebit"][year] = calcular_margem_ebit(ebit, receita_liquida)
        
        if "margem_liquida" not in result:
            result["margem_liquida"] = {}
        result["margem_liquida"][year] = calcular_margem_liquida(lucro_liquido, receita_liquida)
        
        if "capex_pct_receita_liquida" not in result:
            result["capex_pct_receita_liquida"] = {}
        result["capex_pct_receita_liquida"][year] = calcular_capex_pct_receita(capex, receita_liquida)
        
        if "dv_ebitda" not in result:
            result["dv_ebitda"] = {}
        result["dv_ebitda"][year] = calcular_dv_ebitda(divida_liquida, ebitda)
        
        if "geracao_caixa_operacional_pct_ebitda" not in result:
            result["geracao_caixa_operacional_pct_ebitda"] = {}
        result["geracao_caixa_operacional_pct_ebitda"][year] = calcular_geracao_caixa_pct_ebitda(
            geracao_caixa_operacional, ebitda
        )
        
        if "geracao_caixa_pct_ebitda" not in result:
            result["geracao_caixa_pct_ebitda"] = {}
        result["geracao_caixa_pct_ebitda"][year] = calcular_geracao_caixa_pct_ebitda(
            geracao_caixa, ebitda
        )
    
    logger.info("Cálculos da DRE concluídos")
    
    return result
