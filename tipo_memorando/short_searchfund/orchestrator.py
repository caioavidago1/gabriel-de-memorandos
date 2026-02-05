"""
Orchestrator para Short Memo Search Fund - Estrutura Fixa

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
5. Transação/Oportunidade → TransacaoAgent
6. Pontos a Aprofundar → PontosAprofundarAgent

Migrado para tipo_memorando/short_searchfund/
"""

from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.document_processor import DocumentProcessor

from .agents import (
    IntroAgent,
    MercadoAgent,
    EmpresaAgent,
    FinancialsAgent,
    TransacaoAgent,
    PontosAprofundarAgent,
)
from .langgraph_orchestrator import SearchFundLangGraphOrchestrator


# Estrutura FIXA (não pode ser alterada)
FIXED_STRUCTURE = {
    "Introdução": IntroAgent(),
    "Mercado": MercadoAgent(),
    "Empresa": EmpresaAgent(),
    "Financials": FinancialsAgent(),
    "Transação/Oportunidade": TransacaoAgent(),
    "Pontos a Aprofundar": PontosAprofundarAgent()
}

# Queries semânticas para busca RAG por seção no ChromaDB
SECTION_QUERIES = {
    "Introdução": (
        "search fund searcher liderado FIP casca empresa alvo aquisição está avaliando "
        "nome companhia codinome período de busca segundo semestre nacionalidade "
        "especializada em negócio transação EV múltiplo EBITDA participação"
    ),
    "Mercado": (
        "mercado setor tamanho crescimento tendências competição "
        "dinâmica posicionamento oportunidades ameaças ambiente "
        "contexto macroeconômico demanda"
    ),
    "Empresa": (
        "empresa histórico fundação posicionamento diferenciação modelo negócio "
        "competências expertise capacidades força equipe management "
        "estrutura operacional"
    ),
    "Financials": (
        "financials receita EBITDA lucro fluxo caixa margem múltiplo valuation "
        "projeção cenário financial performance histórico crescimento rentabilidade"
    ),
    "Transação/Oportunidade": (
        "transação estrutura valuation preço múltiplo ticket investimento "
        "saída potencial retorno expected timeline due diligence earn out"
    ),
    "Pontos a Aprofundar": (
        "riscos desafios aprofundar pendências questões validação due diligence "
        "investigação confirmação hipóteses considerações relevantes incertezas"
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
    Gera memo COMPLETO de Short Memo Search Fund (estrutura fixa).
    
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
    orchestrator = SearchFundLangGraphOrchestrator(
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
