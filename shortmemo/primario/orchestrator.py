"""
Orchestrator para Short Memo Primário (Gestora) - Estrutura Fixa

ARQUITETURA:
- Estrutura FIXA de 4 seções (não customizável)
- Cada seção usa agente especializado
- Integração com templates JSON para exemplos
- Query de facts nos prompts para contextualização
- RAG inteligente por seção usando ChromaDB (busca semântica)
- LangGraph para orquestração com retry automático e validação

SEÇÕES FIXAS:
1. Resumo da oportunidade → IntroAgent
2. Gestora, time e forma de atuação → GestoraAgent
3. Portfolio Atual → PortfolioAgent
4. Fundo que Estamos Investindo → FundoAtualAgent

VERSÃO 3.0 - LangGraph para orquestração complexa
"""

from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.document_processor import DocumentProcessor

from .intro_agent import IntroAgent
from .gestora_agent import GestoraAgent
from .portfolio_agent import PortfolioAgent
from .fundo_atual_agent import FundoAtualAgent
from .langgraph_orchestrator import PrimaryLangGraphOrchestrator


# Estrutura FIXA (não pode ser alterada)
FIXED_STRUCTURE = {
    "Resumo da oportunidade": IntroAgent(),
    "Gestora, time e forma de atuação": GestoraAgent(),
    "Portfolio Atual": PortfolioAgent(),
    "Fundo que Estamos Investindo": FundoAtualAgent()
}

# Queries semânticas para busca RAG por seção no ChromaDB
SECTION_QUERIES = {
    "Resumo da oportunidade": (
        "gestora fundo investimento primário commitment target captação "
        "relacionamento Spectra veículo closing timeline ativos"
    ),
    "Gestora, time e forma de atuação": (
        "gestora histórico fundação posicionamento mercado diferenciação "
        "time equipe sócios GPs filosofia investimento estilo atuação "
        "operator led growth equity track record AUM"
    ),
    "Portfolio Atual": (
        "portfolio fundos deals investimentos empresas performance retornos "
        "MOIC TIR marcação receita EBITDA múltiplo desinvestimento "
        "ativo status valuation"
    ),
    "Fundo que Estamos Investindo": (
        "fundo target tamanho ativos estratégia alocação tese investimento "
        "playbook ticket setores geografia número investimentos planejados"
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
    Gera memo COMPLETO de Short Memo Primário (estrutura fixa).
    
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
    # Usar LangGraph orchestrator (baseado em classe com reuso de lógica)
    orchestrator = PrimaryLangGraphOrchestrator(
        fixed_structure=FIXED_STRUCTURE,
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
