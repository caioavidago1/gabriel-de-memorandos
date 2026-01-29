"""
Orchestrator para Short Memo Gestora - Estrutura Fixa

ARQUITETURA:
- Estrutura FIXA de 6 seções (não customizável)
- Cada seção usa agente especializado
- Integração com core/few_shot.py para exemplos
- Query de facts nos prompts para contextualização
- LangGraph para orquestração com retry automático e validação

SEÇÕES FIXAS:
1. Introdução → IntroAgent
2. Mercado → MercadoAgent
3. Empresa → EmpresaAgent
4. Financials → FinancialsAgent
5. Transação → TransacaoAgent
6. Pontos a Aprofundar → PontosAprofundarAgent

VERSÃO 3.0 - Reestruturação para co-investimentos
"""

from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.document_processor import DocumentProcessor

from .intro_agent import IntroAgent
from .mercado_agent import MercadoAgent
from .empresa_agent import EmpresaAgent
from .financials_agent import FinancialsAgent
from .transacao_agent import TransacaoAgent
from .pontos_aprofundar_agent import PontosAprofundarAgent
from .langgraph_orchestrator import GestaraLangGraphOrchestrator


# Estrutura FIXA (não pode ser alterada)
FIXED_STRUCTURE = {
    "Introdução": IntroAgent(),
    "Mercado": MercadoAgent(),
    "Empresa": EmpresaAgent(),
    "Financials": FinancialsAgent(),
    "Transação": TransacaoAgent(),
    "Pontos a Aprofundar": PontosAprofundarAgent()
}

# Queries semânticas para busca RAG por seção no ChromaDB
SECTION_QUERIES = {
    "Introdução": (
        "gestora apresentou oportunidade co-investir empresa contexto "
        "transação estrutura valuation múltiplo participação"
    ),
    "Mercado": (
        "mercado setor tamanho crescimento tendências competição "
        "dinâmica posicionamento oportunidades ameaças ambiente "
        "contexto macroeconômico demanda fragmentação market share"
    ),
    "Empresa": (
        "empresa histórico fundação posicionamento diferenciação modelo negócio "
        "competências expertise capacidades força equipe management "
        "estrutura operacional produtos serviços clientes"
    ),
    "Financials": (
        "financials receita EBITDA lucro fluxo caixa margem múltiplo valuation "
        "projeção cenário financial performance histórico crescimento rentabilidade "
        "dívida alavancagem conversão caixa"
    ),
    "Transação": (
        "transação estrutura valuation preço múltiplo ticket investimento "
        "saída potencial retorno expected timeline due diligence earn out "
        "seller note governança conselho veto tag drag vesting lock-up"
    ),
    "Pontos a Aprofundar": (
        "riscos desafios aprofundar pendências questões validação due diligence "
        "investigação confirmação hipóteses considerações relevantes incertezas "
        "premissas validação estrutura operacional mercado competição"
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
    Gera memo COMPLETO de Short Memo Gestora (estrutura fixa).
    
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
    orchestrator = GestaraLangGraphOrchestrator(
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
