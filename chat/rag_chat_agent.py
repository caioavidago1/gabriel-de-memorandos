"""
Agente de Chat com RAG para responder perguntas sobre documentos parseados

Usa RAG (Retrieval Augmented Generation) para buscar informações relevantes
nos documentos PDF parseados e responder perguntas do usuário de forma
contextualizada usando os fatos extraídos.
"""

from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from core.logger import get_logger
from core.chromadb_store import get_or_create_collection, search_memo_chunks

# Imports condicionais para múltiplos providers
try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    ChatOpenAI = None

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    ChatAnthropic = None

logger = get_logger(__name__)


class RAGChatAgent:
    """
    Agente de chat que usa RAG para responder perguntas sobre documentos.
    
    Funcionalidades:
    - Busca semântica nos documentos parseados via ChromaDB
    - Usa fatos extraídos como contexto adicional
    - Responde perguntas de forma natural e contextualizada
    """
    
    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_context_chunks: int = 5
    ):
        # Detectar provider baseado no nome do modelo e inicializar LLM apropriado
        if "claude" in model.lower():
            if not ANTHROPIC_AVAILABLE:
                logger.warning(f"Modelo Claude solicitado mas langchain-anthropic não está instalado. Usando GPT-4o como fallback.")
                logger.info("Para usar Claude, instale: pip install langchain-anthropic anthropic")
                model = "gpt-4o"
                self.llm = ChatOpenAI(model=model, temperature=temperature)
                self.provider = "openai"
            else:
                self.llm = ChatAnthropic(model=model, temperature=temperature)
                self.provider = "anthropic"
                logger.info(f"Usando modelo Anthropic: {model}")
        else:
            if not OPENAI_AVAILABLE:
                raise ImportError("langchain-openai não está instalado. Execute: pip install langchain-openai")
            self.llm = ChatOpenAI(model=model, temperature=temperature)
            self.provider = "openai"
            logger.info(f"Usando modelo OpenAI: {model}")
        
        self.max_context_chunks = max_context_chunks
        self.model = model
        self.temperature = temperature
    
    def _build_system_prompt(self, facts: Dict[str, Any], memo_type: str) -> str:
        """
        Constrói o prompt do sistema otimizado para o agente de chat.
        
        Args:
            facts: Fatos extraídos do documento
            memo_type: Tipo de memorando
            
        Returns:
            Prompt do sistema
        """
        # Formatar fatos de forma legível
        facts_summary = self._format_facts_summary(facts)
        
        system_prompt = f"""Você é um assistente especializado em análise de documentos financeiros e de investimento.

CONTEXTO DO MEMORANDO:
- Tipo: {memo_type}
- Fatos Extraídos:
{facts_summary}

SUA FUNÇÃO:
Você ajuda o usuário a entender e trabalhar com informações extraídas de documentos PDF parseados.

QUANDO O USUÁRIO FAZ UMA PERGUNTA:
1. Use os fatos extraídos acima como contexto primário
2. Se a informação não estiver nos fatos, busque nos documentos parseados usando RAG
3. Cite sempre a fonte quando usar informações dos documentos
4. Seja preciso, conciso e objetivo
5. Use formatação markdown quando apropriado (negrito, listas, etc.)

EXEMPLOS DE PERGUNTAS QUE VOCÊ PODE RECEBER:
- "Cite os produtos da empresa"
- "Qual é a receita atual?"
- "Quais são os principais riscos mencionados?"
- "Descreva o modelo de negócio"
- "Quem são os fundadores?"

RESPOSTAS:
- Sempre baseie-se nos fatos e documentos disponíveis
- Se não encontrar informação, seja honesto: "Não encontrei essa informação nos documentos"
- Use formatação clara e estruturada
- Cite números e dados específicos quando disponíveis

IMPORTANTE:
- Você NÃO deve inventar informações
- Você NÃO deve fazer suposições não baseadas nos documentos
- Sempre priorize informações dos fatos extraídos, depois dos documentos parseados"""
        
        return system_prompt
    
    def _format_facts_summary(self, facts: Dict[str, Any]) -> str:
        """Formata os fatos de forma legível para o prompt"""
        if not facts:
            return "Nenhum fato extraído ainda."
        
        summary_parts = []
        for section, section_facts in facts.items():
            if not section_facts:
                continue
            
            # Filtrar apenas fatos com valor
            filled_facts = {
                k: v for k, v in section_facts.items()
                if v and str(v).lower() not in ("null", "", "none")
            }
            
            if filled_facts:
                summary_parts.append(f"\n**{section.upper()}:**")
                for key, value in filled_facts.items():
                    # Formatar chave de forma legível
                    readable_key = key.replace("_", " ").title()
                    summary_parts.append(f"  - {readable_key}: {value}")
        
        return "\n".join(summary_parts) if summary_parts else "Nenhum fato preenchido ainda."
    
    def _search_documents(
        self,
        query: str,
        memo_id: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Busca documentos relevantes usando RAG via ChromaDB.
        
        Args:
            query: Pergunta ou query do usuário
            memo_id: ID do memorando (opcional, para filtrar)
            n_results: Número de chunks a retornar
            
        Returns:
            Lista de chunks relevantes com metadados
        """
        try:
            collection = get_or_create_collection()
            
            # Buscar chunks relevantes
            results = search_memo_chunks(
                collection=collection,
                query=query,
                memo_id=memo_id,
                n_results=n_results
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Erro ao buscar documentos: {e}")
            return []
    
    def _format_rag_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Formata chunks de RAG para incluir no prompt.
        
        Args:
            chunks: Lista de chunks retornados pela busca
            
        Returns:
            String formatada com contexto dos documentos
        """
        if not chunks:
            return ""
        
        context_parts = ["\n**INFORMAÇÕES DOS DOCUMENTOS PARSEADOS:**"]
        
        for i, chunk in enumerate(chunks, 1):
            text = chunk.get("text", "")
            metadata = chunk.get("metadata", {})
            
            # Adicionar metadados úteis se disponíveis
            source_info = ""
            if metadata:
                filename = metadata.get("filename", "")
                section = metadata.get("section_title", "")
                if filename:
                    source_info = f" (Fonte: {filename}"
                    if section:
                        source_info += f" - {section}"
                    source_info += ")"
            
            context_parts.append(f"\n[{i}]{source_info}\n{text[:500]}...")  # Limitar tamanho
        
        return "\n".join(context_parts)
    
    def chat(
        self,
        user_message: str,
        facts: Dict[str, Any],
        memo_type: str,
        memo_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Responde uma pergunta do usuário usando RAG e fatos extraídos.
        
        Args:
            user_message: Mensagem/pergunta do usuário
            facts: Fatos extraídos do documento
            memo_type: Tipo de memorando
            memo_id: ID do memorando (para buscar documentos específicos)
            conversation_history: Histórico da conversa (opcional)
            
        Returns:
            Resposta do agente
        """
        # Construir prompt do sistema
        system_prompt = self._build_system_prompt(facts, memo_type)
        
        # Buscar documentos relevantes usando RAG
        rag_chunks = self._search_documents(
            query=user_message,
            memo_id=memo_id,
            n_results=self.max_context_chunks
        )
        
        # Formatar contexto RAG
        rag_context = self._format_rag_context(rag_chunks)
        
        # Construir mensagens
        messages = [SystemMessage(content=system_prompt)]
        
        # Adicionar histórico da conversa se disponível
        if conversation_history:
            for msg in conversation_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        # Adicionar contexto RAG se houver
        if rag_context:
            context_message = f"""Abaixo estão informações relevantes encontradas nos documentos parseados que podem ajudar a responder a pergunta:

{rag_context}

Use essas informações para complementar sua resposta, sempre citando a fonte quando apropriado."""
            messages.append(HumanMessage(content=context_message))
        
        # Adicionar mensagem do usuário
        messages.append(HumanMessage(content=user_message))
        
        # Chamar LLM
        try:
            response = self.llm.invoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return f"❌ Erro ao processar sua pergunta: {str(e)}"
    
    def regenerate_paragraph_with_query(
        self,
        current_paragraph: str,
        user_query: str,
        facts: Dict[str, Any],
        memo_type: str,
        memo_id: Optional[str] = None
    ) -> str:
        """
        Regenera um parágrafo baseado em uma query do usuário usando RAG.
        
        Args:
            current_paragraph: Parágrafo atual
            user_query: Query do usuário (ex: "cite os produtos da empresa")
            facts: Fatos extraídos
            memo_type: Tipo de memorando
            memo_id: ID do memorando
            
        Returns:
            Parágrafo regenerado
        """
        system_prompt = f"""Você é um assistente especializado em escrever parágrafos para memorandos de investimento.

CONTEXTO:
- Tipo de Memo: {memo_type}
- Parágrafo Atual:
{current_paragraph}

FATOS EXTRAÍDOS:
{self._format_facts_summary(facts)}

INSTRUÇÕES:
1. Use a query do usuário para modificar ou melhorar o parágrafo atual
2. Se a query pedir informações específicas (ex: "cite os produtos"), busque nos fatos e documentos
3. Mantenha o estilo e tom do parágrafo original
4. Seja preciso e cite fontes quando usar informações dos documentos
5. Use formatação markdown apropriada

IMPORTANTE:
- Não invente informações
- Baseie-se apenas nos fatos e documentos disponíveis
- Se não encontrar a informação solicitada, seja honesto no parágrafo"""
        
        # Buscar documentos relevantes
        rag_chunks = self._search_documents(
            query=user_query,
            memo_id=memo_id,
            n_results=self.max_context_chunks
        )
        
        rag_context = self._format_rag_context(rag_chunks)
        
        # Construir prompt
        user_prompt = f"""QUERY DO USUÁRIO: {user_query}

INFORMAÇÕES DOS DOCUMENTOS:
{rag_context if rag_context else "Nenhuma informação adicional encontrada nos documentos."}

TAREFA:
Modifique o parágrafo atual conforme a query do usuário. Se a query pedir informações específicas, 
inclua-as no parágrafo usando as informações dos documentos acima. Mantenha o estilo profissional 
e preciso de um memorando de investimento."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Erro ao regenerar parágrafo: {e}")
            return current_paragraph  # Retornar original em caso de erro
