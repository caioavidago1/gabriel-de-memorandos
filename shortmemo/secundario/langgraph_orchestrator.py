"""
Orchestrator baseado em LangGraph para Short Memo Secundário

Usa classe base comum para evitar duplicação.
Herda de BaseLangGraphOrchestrator toda lógica de orquestração.
"""

from typing import Dict, Any
from ..base_langgraph_orchestrator import BaseLangGraphOrchestrator


class SecondaryLangGraphOrchestrator(BaseLangGraphOrchestrator):
    """
    Orchestrator baseado em LangGraph para geração de Short Memo Secundário.
    
    Herda toda a funcionalidade de geração de BaseLangGraphOrchestrator.
    Customização específica: section_queries para busca RAG Secundário.
    """
    
    def __init__(
        self,
        fixed_structure: Dict[str, Any],
        section_queries: Dict[str, str],
        model: str = "gpt-4o",
        temperature: float = 0.25,
        max_retries: int = 2
    ):
        """
        Inicializa o orchestrator do Secundário.
        
        Args:
            fixed_structure: Dict de {section_title: specialized_agent} (instâncias)
            section_queries: Dict de queries RAG específicas por seção
            model: Modelo LLM (default: gpt-4o)
            temperature: Temperatura do LLM (default: 0.25)
            max_retries: Máximo de tentativas de retry (default: 2)
        """
        # Inicializar a classe base (constrói o grafo + LLM)
        # Passa section_queries para a classe base usar em _prepare_section
        super().__init__(fixed_structure, section_queries, model, temperature, max_retries)
