"""
Módulo para extração de dados financeiros dos documentos parseados.

Este módulo usa agente de IA para extrair valores financeiros necessários
para preencher a tabela DRE dos documentos parseados.
"""

import os
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from core.logger import get_logger
from facts.tabela.extraction_agent import DRETableExtractionAgent

logger = get_logger(__name__)


def extract_dre_values(
    parsed_documents: List[Dict],
    years: List[int],
    ano_referencia: int
) -> Dict[str, Dict[int, Optional[float]]]:
    """
    Extrai valores financeiros dos documentos para todos os anos usando IA.
    
    Args:
        parsed_documents: Lista de documentos parseados (com campo "text")
        years: Lista de anos para buscar
        ano_referencia: Ano de referência
        
    Returns:
        Dicionário com estrutura {field_key: {year: value}}
    """
    if not parsed_documents:
        logger.warning("Nenhum documento fornecido para extração DRE")
        return _empty_result(years)
    
    try:
        # Inicializar LLM
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY não encontrada no ambiente")
            return _empty_result(years)
        
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            api_key=api_key
        )
        
        # Criar agente de extração
        agent = DRETableExtractionAgent(llm)
        
        # Extrair valores usando IA
        logger.info(f"Iniciando extração DRE com IA para {len(years)} anos")
        result = agent.extract_dre_values_sync(
            parsed_documents,
            years,
            ano_referencia
        )
        
        logger.info(
            f"Extração DRE concluída: {len(result)} campos, "
            f"{sum(len(v) for v in result.values())} valores extraídos"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao extrair valores DRE com IA: {e}", exc_info=True)
        return _empty_result(years)


def _empty_result(years: List[int]) -> Dict[str, Dict[int, Optional[float]]]:
    """
    Retorna estrutura vazia para todos os campos e anos.
    
    Args:
        years: Lista de anos
        
    Returns:
        Dicionário com todos os valores None
    """
    return {
        "receita_bruta": {year: None for year in years},
        "receita_liquida": {year: None for year in years},
        "lucro_bruto": {year: None for year in years},
        "ebitda": {year: None for year in years},
        "ebit": {year: None for year in years},
        "lucro_liquido": {year: None for year in years},
        "capex": {year: None for year in years},
        "divida_liquida": {year: None for year in years},
        "geracao_caixa_operacional": {year: None for year in years},
        "geracao_caixa": {year: None for year in years},
    }
