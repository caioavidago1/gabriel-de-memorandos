"""
Schema Pydantic para extração de valores DRE dos documentos.

Este schema define a estrutura de dados esperada para extração
de valores financeiros da tabela DRE por ano.
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class DREValuesByYear(BaseModel):
    """
    Valores DRE para um ano específico.
    
    Args:
        receita_bruta: Receita bruta em milhões
        receita_liquida: Receita líquida em milhões
        lucro_bruto: Lucro bruto em milhões
        ebitda: EBITDA em milhões
        ebit: EBIT em milhões
        lucro_liquido: Lucro líquido em milhões
        capex: Capex em milhões
        divida_liquida: Dívida líquida em milhões
        geracao_caixa_operacional: Geração de caixa operacional em milhões
        geracao_caixa: Geração de caixa em milhões
    """
    model_config = ConfigDict(strict=True)
    
    receita_bruta: Optional[float] = Field(
        None,
        ge=0.0,
        description="Receita bruta em milhões"
    )
    
    receita_liquida: Optional[float] = Field(
        None,
        ge=0.0,
        description="Receita líquida em milhões"
    )
    
    lucro_bruto: Optional[float] = Field(
        None,
        description="Lucro bruto em milhões (pode ser negativo)"
    )
    
    ebitda: Optional[float] = Field(
        None,
        description="EBITDA em milhões (pode ser negativo)"
    )
    
    ebit: Optional[float] = Field(
        None,
        description="EBIT em milhões (pode ser negativo)"
    )
    
    lucro_liquido: Optional[float] = Field(
        None,
        description="Lucro líquido em milhões (pode ser negativo)"
    )
    
    capex: Optional[float] = Field(
        None,
        ge=0.0,
        description="Capex em milhões"
    )
    
    divida_liquida: Optional[float] = Field(
        None,
        description="Dívida líquida em milhões (pode ser negativa se caixa líquido)"
    )
    
    geracao_caixa_operacional: Optional[float] = Field(
        None,
        description="Geração de caixa operacional em milhões"
    )
    
    geracao_caixa: Optional[float] = Field(
        None,
        description="Geração de caixa em milhões"
    )


class DRETableExtractionResult(BaseModel):
    """
    Resultado da extração de valores DRE para múltiplos anos.
    
    Args:
        values_by_year: Dicionário com valores por ano (ex: {"2024": DREValuesByYear(...)})
    """
    model_config = ConfigDict(strict=True)
    
    values_by_year: Dict[str, DREValuesByYear] = Field(
        default_factory=dict,
        description="Valores DRE por ano (chave como string do ano)"
    )
