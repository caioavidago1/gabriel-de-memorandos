"""
Orchestrator para Short Memo Secundário - Estrutura Fixa

ARQUITETURA:
- Estrutura FIXA de 4 seções (não customizável)
- Cada seção usa função especializada ou agente
- Query de facts nos prompts para contextualização
- RAG inteligente por seção usando ChromaDB (busca semântica)
- LangGraph para orquestração com retry automático e validação

SEÇÕES FIXAS:
1. Introdução → generate_intro_section
2. Histórico Financeiro → generate_financials_section
3. Estrutura da Transação → generate_transaction_section
4. Portfólio → PortfolioAgent

VERSÃO 1.0 - LangGraph para orquestração complexa
"""

from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.document_processor import DocumentProcessor

from .generator import (
    generate_intro_section,
    generate_financials_section,
    generate_transaction_section,
)
from .portfolio_agent import PortfolioAgent
from .langgraph_orchestrator import SecondaryLangGraphOrchestrator


# Wrappers de agentes para funções existentes
class IntroAgentWrapper:
    """Wrapper para generate_intro_section seguindo interface de agente"""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        self.model = model
        self.temperature = temperature
        self.section_name = "Introdução"
        self.llm = None
    
    def set_llm(self, llm):
        """Injeta LLM compartilhado (compatibilidade com LangGraph)"""
        self.llm = llm
    
    def generate(self, facts: Dict[str, Any], rag_context: Optional[str] = None) -> str:
        """Gera seção de introdução"""
        return generate_intro_section(facts, rag_context, self.model, self.temperature)


class FinancialsAgentWrapper:
    """Wrapper para generate_financials_section seguindo interface de agente"""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        self.model = model
        self.temperature = temperature
        self.section_name = "Histórico Financeiro"
        self.llm = None
    
    def set_llm(self, llm):
        """Injeta LLM compartilhado (compatibilidade com LangGraph)"""
        self.llm = llm
    
    def generate(self, facts: Dict[str, Any], rag_context: Optional[str] = None) -> str:
        """Gera seção de histórico financeiro"""
        return generate_financials_section(facts, rag_context, self.model, self.temperature)


class TransactionAgentWrapper:
    """Wrapper para generate_transaction_section seguindo interface de agente"""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        self.model = model
        self.temperature = temperature
        self.section_name = "Estrutura da Transação"
        self.llm = None
    
    def set_llm(self, llm):
        """Injeta LLM compartilhado (compatibilidade com LangGraph)"""
        self.llm = llm
    
    def generate(self, facts: Dict[str, Any], rag_context: Optional[str] = None) -> str:
        """Gera seção de estrutura da transação"""
        return generate_transaction_section(facts, rag_context, self.model, self.temperature)


# Estrutura FIXA (não pode ser alterada)
FIXED_STRUCTURE = {
    "Introdução": IntroAgentWrapper,
    "Histórico Financeiro": FinancialsAgentWrapper,
    "Estrutura da Transação": TransactionAgentWrapper,
    "Portfólio": PortfolioAgent
}

# Queries semânticas para busca RAG por seção no ChromaDB
SECTION_QUERIES = {
    "Introdução": (
        "transação secundária oportunidade investimento NAV data base "
        "expectativa recebimento timing saída empresa madura cash yield "
        "FCF geração caixa estável"
    ),
    "Histórico Financeiro": (
        "financials receita EBITDA FCF histórico crescimento margem "
        "endividamento estabilidade previsibilidade conversão caixa "
        "CAGR ROIC ROE capital structure"
    ),
    "Estrutura da Transação": (
        "transação estrutura valuation múltiplo EV EBITDA FCF "
        "alavancagem dívida equity participação stake retornos "
        "IRR MOIC dividend recapitalization"
    ),
    "Portfólio": (
        "portfolio fundos ativos NAV data base expectativa recebimento "
        "MOIC NAV timing saída projeções gestor Spectra comparação "
        "processos judiciais arbitragem tabelas DRE"
    )
}


def generate_full_memo(
    facts: Dict[str, Any],
    rag_context: str = None,  # Deprecated - manter para compatibilidade
    memo_id: Optional[str] = None,
    processor: Optional["DocumentProcessor"] = None,
    model: str = "gpt-4o",
    temperature: float = 0.25
) -> Dict[str, list]:
    """
    Gera memo COMPLETO de Short Memo Secundário (estrutura fixa).
    
    Wrapper que mantém interface atual mas usa LangGraph internamente.
    
    Args:
        facts: Facts extraídos (todas as seções)
        rag_context: Contexto do documento (DEPRECATED - usar memo_id/processor)
        memo_id: ID do memo no ChromaDB para busca RAG por seção
        processor: Instância de DocumentProcessor para busca no ChromaDB
        model: Modelo OpenAI
        temperature: Criatividade
    
    Returns:
        Dict com estrutura: {section_title: [paragraph1, paragraph2, ...]}
    """
    # Instanciar agentes com model e temperature
    fixed_structure_instances = {
        title: agent_class(model=model, temperature=temperature)
        for title, agent_class in FIXED_STRUCTURE.items()
    }
    
    # Usar LangGraph orchestrator (baseado em classe com reuso de lógica)
    orchestrator = SecondaryLangGraphOrchestrator(
        fixed_structure=fixed_structure_instances,
        section_queries=SECTION_QUERIES,
        model=model,
        temperature=temperature,
        max_retries=2
    )
    
    return orchestrator.generate_full_memo(
        facts=facts,
        memo_id=memo_id,
        processor=processor,
        rag_context=rag_context
    )
