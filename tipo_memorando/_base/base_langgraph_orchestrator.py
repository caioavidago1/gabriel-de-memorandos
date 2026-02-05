"""
Classe Base Comum para todos os Orchestrators LangGraph de Short Memo

Centraliza lógica compartilhada entre:
- short_searchfund, short_gestora, short_primario
"""

from typing import TypedDict, Dict, Any, Optional, List, Literal
from langgraph.graph import StateGraph, END
from model_config import get_llm_for_agents
from core.logger import get_logger

logger = get_logger(__name__)


class BaseShortMemoGenerationState(TypedDict, total=False):
    """Estado compartilhado entre nós do grafo LangGraph (base comum)"""
    # Input
    section_title: str
    agent: Any  # Agente especializado
    facts: Dict[str, Any]
    memo_id: Optional[str]
    processor: Optional[Any]  # DocumentProcessor
    
    # RAG Context
    section_rag_context: Optional[str]
    query: str
    
    # Generation
    generated_text: str
    paragraphs: List[str]
    
    # Validation
    validation_errors: List[str]
    retry_count: int
    max_retries: int
    
    # Final
    is_complete: bool
    final_output: Dict[str, List[str]]


class BaseLangGraphOrchestrator:
    """
    Classe base para todos os orchestrators de Short Memo.
    
    Implementa lógica comum:
    - Gerenciamento de LLM compartilhado
    - Construção do grafo LangGraph
    - Nós comuns (_prepare_section, _generate_with_agent, etc)
    - Fluxo padrão com retry
    
    Subclasses devem:
    1. Definir fixed_structure
    2. Passar section_queries no __init__ se precisarem de queries específicas
    3. Herdar tudo mais automaticamente
    """
    
    def __init__(
        self,
        fixed_structure: Dict[str, Any],
        section_queries: Optional[Dict[str, str]] = None,
        model: str = "gpt-4o",
        temperature: float = 0.25,
        max_retries: int = 2
    ):
        """
        Inicializa orchestrator base.
        
        Args:
            fixed_structure: Dict com estrutura fixa de seções
            section_queries: Dict opcional de queries RAG específicas por seção
            model: Modelo OpenAI
            temperature: Criatividade (0-1)
            max_retries: Tentativas de retry se falhar
        """
        self.fixed_structure = fixed_structure
        self.section_queries = section_queries or {}
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        
        # LLM centralizado em model_config (OpenAI/Anthropic conforme cadastro)
        self.llm = get_llm_for_agents(model, temperature)
        
        # Construir grafo
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Constrói o grafo LangGraph (implementação base comum)"""
        
        workflow = StateGraph(BaseShortMemoGenerationState)
        
        # === NÓS COMUNS ===
        workflow.add_node("prepare_section", self._prepare_section)
        workflow.add_node("generate_with_agent", self._generate_with_agent)
        workflow.add_node("validate_output", self._validate_output)
        workflow.add_node("retry_section", self._retry_section)
        workflow.add_node("finalize", self._finalize)
        
        # === FLUXO ===
        workflow.set_entry_point("prepare_section")
        workflow.add_edge("prepare_section", "generate_with_agent")
        workflow.add_edge("generate_with_agent", "validate_output")
        
        workflow.add_conditional_edges(
            "validate_output",
            self._should_retry,
            {"retry": "retry_section", "finalize": "finalize", "end": END}
        )
        
        workflow.add_edge("retry_section", "generate_with_agent")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _prepare_section(self, state: BaseShortMemoGenerationState) -> Dict[str, Any]:
        """Nó 1: Busca contexto RAG relevante no ChromaDB"""
        section_title = state["section_title"]
        memo_id = state.get("memo_id")
        processor = state.get("processor")
        
        logger.info(f"🔍 [LangGraph] Preparando seção '{section_title}'...")
        
        section_rag_context = None
        # Usar query específica se disponível, senão usar título genérico
        query = self.section_queries.get(section_title, section_title.lower().replace(" ", " "))
        
        if memo_id and processor:
            try:
                chunks = processor.search_chromadb_chunks(
                    memo_id=memo_id,
                    query=query,
                    top_k=10
                )
                
                if chunks:
                    section_rag_context = "\n\n".join([chunk["chunk"] for chunk in chunks])
                    logger.info(f"✅ [LangGraph] {len(chunks)} chunks para '{section_title}'")
                else:
                    logger.warning(f"⚠️ [LangGraph] Nenhum chunk para '{section_title}'")
                    
            except Exception as e:
                logger.error(f"❌ [LangGraph] Erro RAG: {e}")
                section_rag_context = None
        else:
            logger.info(f"ℹ️ [LangGraph] Sem memo_id/processor, pulando RAG")
        
        return {
            "section_rag_context": section_rag_context,
            "query": query
        }
    
    def _generate_with_agent(self, state: BaseShortMemoGenerationState) -> Dict[str, Any]:
        """Nó 2: Chama agente especializado para gerar texto"""
        section_title = state["section_title"]
        agent = state["agent"]
        facts = state["facts"]
        section_rag_context = state.get("section_rag_context")
        
        logger.info(f"🤖 [LangGraph] Gerando '{section_title}' com {agent.__class__.__name__}...")
        
        try:
            # Injetar LLM compartilhado no agente (se suportar)
            if hasattr(agent, 'set_llm'):
                agent.set_llm(self.llm)
            
            # Chamar método generate do agente
            generated_text = agent.generate(
                facts=facts,
                rag_context=section_rag_context
            )
            
            logger.info(f"✅ [LangGraph] Texto gerado ({len(generated_text)} chars)")
            
            return {"generated_text": generated_text}
            
        except Exception as e:
            logger.error(f"❌ [LangGraph] Erro ao gerar: {e}")
            return {
                "generated_text": f"(Erro ao gerar seção: {e})",
                "validation_errors": [f"Erro na geração: {str(e)}"]
            }
    
    def _validate_output(self, state: BaseShortMemoGenerationState) -> Dict[str, Any]:
        """Nó 3: Valida qualidade e formato do texto gerado"""
        section_title = state["section_title"]
        generated_text = state.get("generated_text", "")
        
        logger.info(f"🔍 [LangGraph] Validando output...")
        
        errors = []
        
        # Validação 1: Texto não vazio
        if not generated_text or not generated_text.strip():
            errors.append("Texto gerado está vazio")
        
        # Validação 2: Mínimo de caracteres
        if len(generated_text.strip()) < 100:
            errors.append(f"Texto muito curto ({len(generated_text)} chars, mín: 100)")
        
        # Validação 3: Verificar placeholder de erro
        if "(Erro" in generated_text or "Erro ao gerar" in generated_text:
            errors.append("Texto contém placeholder de erro")
        
        # Score de qualidade
        quality_score = 0.9 if not errors else max(0.5, 1.0 - len(errors) * 0.2)
        
        if errors:
            logger.warning(f"⚠️ [LangGraph] {len(errors)} erro(s): {errors}")
        else:
            logger.info(f"✅ [LangGraph] Validação OK (score: {quality_score})")
        
        return {
            "validation_errors": errors,
            "quality_score": quality_score
        }
    
    def _should_retry(self, state: BaseShortMemoGenerationState) -> Literal["retry", "finalize", "end"]:
        """Decisão se deve fazer retry"""
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", self.max_retries)
        errors = state.get("validation_errors", [])
        
        if errors and retry_count < max_retries:
            logger.info(f"🔄 [LangGraph] Retry {retry_count + 1}/{max_retries}")
            return "retry"
        
        return "finalize"
    
    def _retry_section(self, state: BaseShortMemoGenerationState) -> Dict[str, Any]:
        """Nó 4: Incrementa contador de retry"""
        new_count = state.get("retry_count", 0) + 1
        logger.info(f"🔄 [LangGraph] Tentativa {new_count}")
        return {"retry_count": new_count}
    
    def _finalize(self, state: BaseShortMemoGenerationState) -> Dict[str, Any]:
        """Nó 5: Finaliza e formata resultado"""
        generated_text = state.get("generated_text", "")
        
        # Quebrar em parágrafos
        paragraphs = [p.strip() for p in generated_text.split("\n\n") if p.strip()]
        
        logger.info(f"✅ [LangGraph] Finalizado: {len(paragraphs)} parágrafos")
        
        return {
            "is_complete": True,
            "paragraphs": paragraphs,
            "final_output": {"text": paragraphs}
        }
    
    def generate_full_memo(
        self,
        facts: Dict[str, Any],
        memo_id: Optional[str] = None,
        processor: Optional[Any] = None,
        rag_context: Optional[str] = None  # Deprecated
    ) -> Dict[str, List[str]]:
        """
        Gera memo completo orquestrando todos os agentes via LangGraph.
        
        Args:
            facts: Facts estruturados (todas as seções)
            memo_id: ID do memo no ChromaDB para RAG
            processor: DocumentProcessor para busca RAG
            rag_context: DEPRECATED - ignorado
            
        Returns:
            Dict com estrutura: {section_title: [paragraph1, paragraph2, ...]}
        """
        if rag_context:
            logger.warning("⚠️ rag_context deprecated, use memo_id+processor")
        
        result = {}
        
        for section_title, agent in self.fixed_structure.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"📝 Processando: {section_title}")
            logger.info(f"{'='*60}\n")
            
            # Estado inicial para esta seção
            initial_state = {
                "section_title": section_title,
                "agent": agent,
                "facts": facts,
                "memo_id": memo_id,
                "processor": processor,
                "retry_count": 0,
                "max_retries": self.max_retries
            }
            
            # Executar grafo (sincronamente)
            try:
                # O grafo é compilado, então executamos como função
                final_state = self.graph.invoke(initial_state)
                paragraphs = final_state.get("paragraphs", [])
                result[section_title] = paragraphs
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar '{section_title}': {e}")
                result[section_title] = [f"(Erro ao gerar seção: {e})"]
        
        logger.info(f"\n✅ Memo gerado com {len(result)} seções")
        return result
