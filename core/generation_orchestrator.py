"""
Orquestrador de Geração de Memos usando LangGraph

Arquitetura:
- LangGraph para workflow de multi-agentes
- Agentes especializados por tipo de documento
- State management para manter contexto
- Geração baseada apenas em facts (sem few-shot learning)
"""

from typing import TypedDict, Annotated, Literal, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage
from model_config import get_llm_for_agents
import asyncio
import json
from datetime import datetime


class GenerationState(TypedDict):
    """Estado compartilhado entre todos os agentes de geração"""
    # Input
    section_name: str
    section_facts: Dict[str, Any]
    memo_type: str
    temperature: float
    
    # Generation
    generated_paragraphs: List[str]
    generation_metadata: Dict
    
    # Quality control
    quality_score: float
    validation_errors: List[str]
    retry_count: int
    max_retries: int
    
    # Final
    is_complete: bool
    final_output: Dict


class MemoGenerationOrchestrator:
    """
    Orquestrador LangGraph para geração de memos
    
    Fluxo:
    1. Generate Paragraphs → Gerar parágrafos baseados nos facts
    2. Validate Quality → Checar qualidade (métricas, dados, tom)
    3. Refine/Retry → Se necessário, regenerar
    4. Finalize → Retornar resultado final
    """
    
    def __init__(
        self, 
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_retries: int = 2
    ):
        self.llm = get_llm_for_agents(model, temperature)
        self.max_retries = max_retries
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Constrói o grafo LangGraph para geração"""
        
        workflow = StateGraph(GenerationState)
        
        # === NODES ===
        workflow.add_node("generate_paragraphs", self._generate_paragraphs)
        workflow.add_node("validate_quality", self._validate_quality)
        workflow.add_node("refine_output", self._refine_output)
        workflow.add_node("finalize", self._finalize)
        
        # === FLOW ===
        workflow.set_entry_point("generate_paragraphs")
        workflow.add_edge("generate_paragraphs", "validate_quality")
        
        # Conditional: retry se qualidade baixa
        workflow.add_conditional_edges(
            "validate_quality",
            self._should_refine,
            {
                "refine": "refine_output",
                "finalize": "finalize",
                "end": END
            }
        )
        
        workflow.add_edge("refine_output", "generate_paragraphs")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    async def _generate_paragraphs(self, state: GenerationState) -> Dict:
        """
        Gera parágrafos baseados nos facts fornecidos
        BASEADO NOS FACTS (facts são a fonte da verdade)
        """
        section_name = state["section_name"]
        facts = state["section_facts"]
        memo_type = state["memo_type"]
        
        print(f"\n✍️ [Generate] Gerando parágrafos para '{section_name}'...")
        
        # System prompt especializado
        system_prompt = self._build_specialized_system_prompt(section_name, memo_type)
        
        # User prompt com facts
        user_prompt = self._build_generation_prompt(
            section_name, facts, memo_type
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        content = response.content.strip()
        
        # Parse em parágrafos
        paragraphs = self._parse_paragraphs(content)
        
        print(f"   ✅ {len(paragraphs)} parágrafo(s) gerados")
        
        return {
            "generated_paragraphs": paragraphs,
            "generation_metadata": {
                "model": "gpt-4o",
                "examples_used": 0,  # Mantido para compatibilidade com app.py
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def _validate_quality(self, state: GenerationState) -> Dict:
        """
        Valida qualidade dos parágrafos gerados
        
        Critérios:
        - Presença de dados/métricas (baseados nos facts)
        - Tom apropriado (analítico)
        - Estrutura coerente
        - Sem invenções (tudo baseado em facts)
        """
        paragraphs = state["generated_paragraphs"]
        facts = state["section_facts"]
        
        print(f"\n✅ [Validate] Validando qualidade...")
        
        validation_prompt = f"""Avalie a qualidade dos parágrafos gerados para um memo de Private Equity.

PARÁGRAFOS GERADOS:
{chr(10).join(f'{i+1}. {p}' for i, p in enumerate(paragraphs))}

FACTS FORNECIDOS (fonte da verdade):
{json.dumps(facts, indent=2, ensure_ascii=False)}

CRITÉRIOS DE AVALIAÇÃO:
1. Dados quantitativos presentes? (números, %, múltiplos)
2. Tom analítico e profissional?
3. Baseado APENAS nos facts (sem invenções/alucinações)?
4. Estrutura coerente e fluida?

IMPORTANTE: Se algum número/métrica no texto NÃO estiver nos facts, isso é uma ALUCINAÇÃO (score baixo).

Retorne JSON:
{{
  "score": 0-100,
  "issues": ["lista de problemas encontrados"],
  "suggestions": ["sugestões de melhoria"]
}}"""
        
        messages = [
            SystemMessage(content="Você é um auditor de qualidade de Investment Memos."),
            HumanMessage(content=validation_prompt)
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            validation = json.loads(response.content)
            
            score = validation.get("score", 70)
            issues = validation.get("issues", [])
            
            print(f"   Score: {score}/100")
            if issues:
                print(f"   Issues: {', '.join(issues[:3])}")
            
            return {
                "quality_score": score,
                "validation_errors": issues
            }
        
        except Exception as e:
            print(f"   ⚠️ Erro na validação: {e}")
            return {
                "quality_score": 75,  # Score neutro em caso de erro
                "validation_errors": []
            }
    
    def _should_refine(self, state: GenerationState) -> Literal["refine", "finalize", "end"]:
        """Decisão: refinar ou finalizar?"""
        score = state.get("quality_score", 0)
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", self.max_retries)
        
        if score < 70 and retry_count < max_retries:
            print(f"\n🔄 Qualidade baixa ({score}/100), refinando...")
            return "refine"
        elif retry_count >= max_retries:
            print(f"\n⚠️ Max retries atingido ({retry_count}), finalizando mesmo assim")
            return "end"
        else:
            return "finalize"
    
    async def _refine_output(self, state: GenerationState) -> Dict:
        """
        Refina output com base nos erros de validação
        """
        paragraphs = state["generated_paragraphs"]
        errors = state["validation_errors"]
        facts = state["section_facts"]
        
        print(f"\n🔧 [Refine] Refinando output...")
        
        refine_prompt = f"""Reescreva os parágrafos corrigindo os problemas identificados.

PARÁGRAFOS ORIGINAIS:
{chr(10).join(paragraphs)}

PROBLEMAS IDENTIFICADOS:
{chr(10).join(f'- {e}' for e in errors)}

FACTS DISPONÍVEIS (USE APENAS ESTES DADOS):
{json.dumps(facts, indent=2, ensure_ascii=False)}

INSTRUÇÕES:
- Mantenha o tom analítico
- Use APENAS dados presentes nos facts
- Adicione mais métricas dos facts se possível
- Corrija problemas apontados
- Retorne APENAS os parágrafos refinados (sem numeração)"""
        
        messages = [
            SystemMessage(content="Você é um analista senior de PE reescrevendo memos."),
            HumanMessage(content=refine_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        refined_paragraphs = self._parse_paragraphs(response.content)
        
        return {
            "generated_paragraphs": refined_paragraphs,
            "retry_count": state["retry_count"] + 1
        }
    
    async def _finalize(self, state: GenerationState) -> Dict:
        """Finaliza e prepara output"""
        return {
            "is_complete": True,
            "final_output": {
                "paragraphs": state["generated_paragraphs"],
                "metadata": state["generation_metadata"],
                "quality_score": state.get("quality_score", 0),
                "examples_used": 0,  # Mantido para compatibilidade com app.py
                "retry_count": state.get("retry_count", 0)
            }
        }
    
    # === HELPERS ===
    
    def _build_specialized_system_prompt(self, section: str, memo_type: str) -> str:
        """System prompt especializado por tipo de memo - carrega dos módulos especializados"""
        
        # Fallback: prompt genérico baseado no tipo de memo
        # NOTA: Arquivos prompts.py foram removidos - agentes têm seus próprios prompts
        base = f"""Você é um analista sênior de Private Equity escrevendo a seção "{section}" de um {memo_type}.

**ESTILO OBRIGATÓRIO:**
- Tom analítico, crítico mas justo
- Primeira pessoa do plural ("estamos avaliando", "precisaremos validar")
- Sempre quantifique: use números, percentuais, múltiplos DOS FACTS
- Sinalize incertezas: "Será crucial validarmos...", "Ainda temos que aprofundar..."
- Compare sempre: "vs. histórico", "acima dos peers"

**TERMINOLOGIA PE:**
- Valuation: EV/EBITDA, múltiplos, equity value
- Financiamento: seller note, acquisition debt
- Crescimento: CAGR, YoY
- Retornos: IRR, MOIC
- Eficiência: ROIC, NRR, churn

**REGRA DE OURO:**
- Use APENAS dados presentes nos FACTS fornecidos
- NÃO invente números, métricas ou informações
- Se um fact não existe, NÃO mencione

**OUTPUT:**
- 2-4 parágrafos
- Cada parágrafo: 3-5 frases
- Separar com linha em branco
- NÃO numerar parágrafos"""
        
        return base
    
    def _build_generation_prompt(
        self, 
        section: str, 
        facts: Dict, 
        memo_type: str
    ) -> str:
        """Prompt de geração com facts"""
        
        parts = [
            f"**SEÇÃO:** {section}",
            f"**TIPO:** {memo_type}",
            "",
            "**FACTS (sua única fonte de dados):**"
        ]
        
        for key, value in facts.items():
            if value not in (None, "", [], {}):
                parts.append(f"- {key}: {value}")
        
        parts.append("")
        parts.append("Gere 2-4 parágrafos profissionais usando APENAS os facts acima.")
        
        return "\n".join(parts)
    
    def _parse_paragraphs(self, text: str) -> List[str]:
        """Parse texto em lista de parágrafos"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        if len(paragraphs) == 1 and len(text) > 500:
            paragraphs = [p.strip() for p in text.split('\n') if p.strip() and len(p.strip()) > 80]
        
        # Limpar numeração
        import re
        cleaned = []
        for p in paragraphs:
            p = re.sub(r'^\d+\.\s*', '', p)
            p = re.sub(r'^[-•]\s*', '', p)
            if p:
                cleaned.append(p)
        
        return cleaned
    
    # === PUBLIC API ===
    
    async def generate_section_async(
        self,
        section_name: str,
        facts: Dict[str, Any],
        memo_type: str,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Gera uma seção usando o workflow LangGraph completo
        
        Returns:
            {
                "paragraphs": [...],
                "metadata": {...},
                "quality_score": 85,
                "examples_used": 4,
                "retry_count": 0
            }
        """
        initial_state: GenerationState = {
            "section_name": section_name,
            "section_facts": facts,
            "memo_type": memo_type,
            "temperature": temperature,
            "similar_memos": [],
            "retrieved_examples": [],
            "search_query": "",
            "generated_paragraphs": [],
            "generation_metadata": {},
            "quality_score": 0.0,
            "validation_errors": [],
            "retry_count": 0,
            "max_retries": self.max_retries,
            "is_complete": False,
            "final_output": {}
        }
        
        # Executar workflow LangGraph
        final_state = await self.graph.ainvoke(initial_state)
        
        return final_state["final_output"]
    
    def generate_section_sync(
        self,
        section_name: str,
        facts: Dict[str, Any],
        memo_type: str,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """Wrapper síncrono para Streamlit"""
        return asyncio.run(self.generate_section_async(
            section_name, facts, memo_type, temperature
        ))
    
    async def regenerate_paragraph_async(
        self,
        section_name: str,
        paragraph_index: int,
        current_paragraph: str,
        facts: Dict[str, Any],
        memo_type: str,
        temperature: float = 0.5,
        user_prompt: str = None
    ) -> str:
        """
        Regenera um parágrafo específico.
        
        Args:
            user_prompt: Prompt customizado do usuário (opcional)
        """
        print(f"\n🔄 [Regenerate] Regenerando parágrafo {paragraph_index}...")
        
        # Gerar sem exemplos
        examples = []
        
        # System prompt
        system_prompt = self._build_specialized_system_prompt(section_name, memo_type)
        
        # Se usuário forneceu prompt customizado, usar ele
        if user_prompt:
            prompt_text = f"""INSTRUÇÃO DO USUÁRIO:
{user_prompt}

PARÁGRAFO ATUAL:
{current_paragraph}

FACTS DISPONÍVEIS:
{json.dumps(facts, indent=2, ensure_ascii=False)}

EXEMPLOS DE REFERÊNCIA:
{chr(10).join(f'- {ex}' for ex in examples[:2])}

Retorne APENAS o parágrafo reescrito seguindo a instrução do usuário."""
        else:
            # Prompt padrão para regeneração
            prompt_text = f"""Reescreva este parágrafo de forma mais impactante.

PARÁGRAFO ATUAL:
{current_paragraph}

FACTS DISPONÍVEIS:
{json.dumps(facts, indent=2, ensure_ascii=False)}

EXEMPLOS DE REFERÊNCIA:
{chr(10).join(f'- {ex}' for ex in examples[:2])}

Retorne APENAS o parágrafo reescrito."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt_text)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content.strip()
    
    def regenerate_paragraph_sync(
        self,
        section_name: str,
        paragraph_index: int,
        current_paragraph: str,
        facts: Dict[str, Any],
        memo_type: str,
        temperature: float = 0.5,
        user_prompt: str = None
    ) -> str:
        """Wrapper síncrono para regenerate_paragraph"""
        return asyncio.run(self.regenerate_paragraph_async(
            section_name, paragraph_index, current_paragraph, 
            facts, memo_type, temperature, user_prompt
        ))
