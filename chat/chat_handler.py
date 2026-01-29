"""
Chat Handler - Processa interações de chat com IA
"""
import traceback
from typing import Dict, List, Optional
from .rag_chat_agent import RAGChatAgent


class ChatHandler:
    """Gerencia lógica de chat com IA para edição de parágrafos"""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.3):
        self.model = model
        self.temperature = temperature
        self.agent = RAGChatAgent(
            model=model,
            temperature=temperature,
            max_context_chunks=5
        )
    
    def is_modification_query(self, user_query: str) -> bool:
        """Verifica se a query é uma instrução de modificação ou uma pergunta"""
        modification_keywords = [
            # Verbos de modificação
            "modifique", "mude", "altere", "seja", "fique", "ajuste",
            # Verbos de adição
            "adicione", "cite", "inclua", "escreva", "insira",
            # Verbos de remoção/exclusão
            "remova", "retire", "exclua", "delete", "tire", "apague", "elimine",
            # Verbos de reescrita/melhoria
            "reescreva", "melhore", "corrija", "reformule", "simplifique", "resuma"
        ]
        return any(keyword in user_query.lower() for keyword in modification_keywords)
    
    def is_new_paragraph_query(self, user_query: str) -> bool:
        """Verifica se a query solicita criação de novo parágrafo"""
        new_paragraph_keywords = [
            "crie", "adicione um", "novo parágrafo", "gere", "faça um parágrafo",
            "escreva sobre", "adicione informação", "inclua um parágrafo"
        ]
        return any(keyword in user_query.lower() for keyword in new_paragraph_keywords)
    
    def build_section_context(
        self,
        section_name: str,
        all_paragraphs: List[str],
        current_idx: int,
        facts: Dict
    ) -> str:
        """
        Constrói contexto completo da seção para a IA
        
        Args:
            section_name: Nome da seção atual
            all_paragraphs: Todos os parágrafos da seção
            current_idx: Índice do parágrafo atual
            facts: Fatos extraídos
            
        Returns:
            String com contexto formatado
        """
        context_parts = [
            f"SEÇÃO ATUAL: {section_name}",
            f"Trabalhando no Parágrafo {current_idx + 1} de {len(all_paragraphs)}",
            "\n=== CONTEXTO COMPLETO DA SEÇÃO ===\n"
        ]
        
        # Adicionar todos os parágrafos da seção com numeração
        for idx, para in enumerate(all_paragraphs):
            if para.strip():  # Só incluir parágrafos não vazios
                marker = " <-- PARÁGRAFO ATUAL" if idx == current_idx else ""
                context_parts.append(f"Parágrafo {idx + 1}{marker}:")
                context_parts.append(para)
                context_parts.append("")
        
        # Adicionar fatos relevantes (opcional, para contexto adicional)
        if facts:
            context_parts.append("\n=== FATOS DISPONÍVEIS ===")
            facts_preview = str(facts)[:500]  # Limitar tamanho
            context_parts.append(facts_preview + "..." if len(str(facts)) > 500 else facts_preview)
        
        return "\n".join(context_parts)
    
    def process_chat_message(
        self,
        user_query: str,
        current_paragraph: str,
        section_name: str,
        all_section_paragraphs: List[str],
        current_paragraph_idx: int,
        facts: Dict,
        memo_type: str,
        memo_id: Optional[str],
        conversation_history: List[Dict]
    ) -> Dict:
        """
        Processa mensagem do chat e retorna resultado
        
        Args:
            user_query: Pergunta ou instrução do usuário
            current_paragraph: Conteúdo do parágrafo atual
            section_name: Nome da seção (ex: "Identificação", "Transação")
            all_section_paragraphs: Lista com todos os parágrafos da seção
            current_paragraph_idx: Índice do parágrafo atual
            facts: Fatos extraídos
            memo_type: Tipo de memorando
            memo_id: ID do memo para busca RAG
            conversation_history: Histórico da conversa
        
        Returns:
            Dict com keys:
                - type: "modification", "new_paragraph", "question" ou "error"
                - content: novo parágrafo, texto do novo parágrafo ou resposta
                - success: bool
                - error: str (se houver erro)
        """
        try:
            # Construir contexto completo da seção
            section_context = self.build_section_context(
                section_name=section_name,
                all_paragraphs=all_section_paragraphs,
                current_idx=current_paragraph_idx,
                facts=facts
            )
            
            # Verificar tipo de query
            if self.is_new_paragraph_query(user_query):
                # Criar novo parágrafo
                new_paragraph = self._create_new_paragraph(
                    user_query=user_query,
                    section_context=section_context,
                    section_name=section_name,
                    facts=facts,
                    memo_type=memo_type,
                    memo_id=memo_id
                )
                
                return {
                    "type": "new_paragraph",
                    "content": new_paragraph,
                    "success": True,
                    "message": "Novo parágrafo criado e adicionado ao final da seção"
                }
            
            elif self.is_modification_query(user_query):
                # Modificar parágrafo existente com contexto completo
                new_paragraph = self._modify_paragraph(
                    user_query=user_query,
                    current_paragraph=current_paragraph,
                    section_context=section_context,
                    section_name=section_name,
                    facts=facts,
                    memo_type=memo_type,
                    memo_id=memo_id
                )
                
                return {
                    "type": "modification",
                    "content": new_paragraph,
                    "success": True,
                    "message": "Parágrafo modificado conforme solicitado"
                }
            
            else:
                # Responder pergunta com contexto da seção
                response = self._answer_question(
                    user_query=user_query,
                    section_context=section_context,
                    section_name=section_name,
                    facts=facts,
                    memo_type=memo_type,
                    memo_id=memo_id,
                    conversation_history=conversation_history
                )
                
                return {
                    "type": "question",
                    "content": response,
                    "success": True
                }
        
        except Exception as e:
            return {
                "type": "error",
                "content": str(e),
                "success": False,
                "error": traceback.format_exc()
            }
    
    def _create_new_paragraph(
        self,
        user_query: str,
        section_context: str,
        section_name: str,
        facts: Dict,
        memo_type: str,
        memo_id: Optional[str]
    ) -> str:
        """Cria novo parágrafo baseado na instrução do usuário"""
        enhanced_query = f"""
CONTEXTO DA SEÇÃO:
{section_context}

INSTRUÇÃO DO USUÁRIO:
{user_query}

TAREFA:
Crie um novo parágrafo para a seção "{section_name}" seguindo a instrução do usuário.
O parágrafo deve:
- Ser coerente com os parágrafos existentes na seção
- Usar linguagem profissional e objetiva (estilo memorando de investimentos)
- Incluir informações relevantes dos documentos quando apropriado
- Ter entre 3-5 frases bem estruturadas
- NÃO repetir informações já presentes em outros parágrafos da seção

Retorne APENAS o texto do novo parágrafo, sem introduções ou explicações.
"""
        
        # Usar RAG agent para gerar com contexto dos documentos
        new_paragraph = self.agent.regenerate_paragraph_with_query(
            current_paragraph="",  # Vazio para novo parágrafo
            user_query=enhanced_query,
            facts=facts,
            memo_type=memo_type,
            memo_id=memo_id
        )
        
        return new_paragraph
    
    def _modify_paragraph(
        self,
        user_query: str,
        current_paragraph: str,
        section_context: str,
        section_name: str,
        facts: Dict,
        memo_type: str,
        memo_id: Optional[str]
    ) -> str:
        """Modifica parágrafo existente considerando contexto completo"""
        enhanced_query = f"""
CONTEXTO DA SEÇÃO:
{section_context}

PARÁGRAFO ATUAL:
{current_paragraph}

INSTRUÇÃO DO USUÁRIO:
{user_query}

TAREFA:
Modifique o parágrafo atual seguindo a instrução do usuário.
Considerações:
- Mantenha coerência com os demais parágrafos da seção "{section_name}"
- Use linguagem profissional e objetiva
- Preserve informações importantes a menos que a instrução peça explicitamente para remover
- NÃO adicione informações que já estejam em outros parágrafos da seção

Retorne APENAS o parágrafo modificado, sem introduções ou explicações.
"""
        
        new_paragraph = self.agent.regenerate_paragraph_with_query(
            current_paragraph=current_paragraph,
            user_query=enhanced_query,
            facts=facts,
            memo_type=memo_type,
            memo_id=memo_id
        )
        
        return new_paragraph
    
    def _answer_question(
        self,
        user_query: str,
        section_context: str,
        section_name: str,
        facts: Dict,
        memo_type: str,
        memo_id: Optional[str],
        conversation_history: List[Dict]
    ) -> str:
        """Responde pergunta considerando contexto da seção"""
        enhanced_query = f"""
CONTEXTO DA SEÇÃO "{section_name}":
{section_context}

PERGUNTA:
{user_query}

Responda a pergunta considerando:
1. O conteúdo dos documentos originais
2. Os parágrafos já escritos na seção
3. Os fatos extraídos disponíveis

Seja direto e objetivo na resposta.
"""
        
        response = self.agent.chat(
            user_message=enhanced_query,
            facts=facts,
            memo_type=memo_type,
            memo_id=memo_id,
            conversation_history=conversation_history
        )
        
        return response
    
    def regenerate_paragraph(
        self,
        current_paragraph: str,
        section_name: str,
        all_section_paragraphs: List[str],
        current_paragraph_idx: int,
        facts: Dict,
        memo_type: str,
        memo_id: Optional[str]
    ) -> Dict:
        """
        Regenera parágrafo com otimizações, considerando contexto completo
        
        Returns:
            Dict com keys:
                - content: novo parágrafo
                - success: bool
                - error: str (se houver erro)
        """
        try:
            # Construir contexto da seção
            section_context = self.build_section_context(
                section_name=section_name,
                all_paragraphs=all_section_paragraphs,
                current_idx=current_paragraph_idx,
                facts=facts
            )
            
            enhanced_query = f"""
CONTEXTO DA SEÇÃO:
{section_context}

TAREFA:
Melhore e otimize o parágrafo atual mantendo todas as informações importantes.
Considerações:
- Mantenha coerência com os demais parágrafos da seção "{section_name}"
- Use linguagem profissional e objetiva
- Torne o texto mais claro e impactante
- NÃO repita informações de outros parágrafos

Retorne APENAS o parágrafo melhorado, sem introduções ou explicações.
"""
            
            new_paragraph = self.agent.regenerate_paragraph_with_query(
                current_paragraph=current_paragraph,
                user_query=enhanced_query,
                facts=facts,
                memo_type=memo_type,
                memo_id=memo_id
            )
            
            return {
                "content": new_paragraph,
                "success": True
            }
        
        except Exception as e:
            return {
                "content": "",
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
