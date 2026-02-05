"""
Agente especializado em OPORTUNIDADE para Short Memo Gestora

RESPONSABILIDADE:
- Gerar seção "Oportunidade" detalhando proposta de investimento atual
- Contexto: Tamanho do fundo, commitment mínimo, termos, carry, fees

ESTRUTURA:
- 2-3 parágrafos
- Parágrafo 1: Estrutura do fundo atual (tamanho, target, status)
- Parágrafo 2: Termos econômicos (commitment, fees, carry)
- Parágrafo 3: Timing e racional estratégico

VERSÃO: 1.0
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from ..facts_builder import build_facts_section
from ..validator import fix_number_formatting


class OportunidadeAgent:
    """Agente especializado em gerar Oportunidade para Short Memo Gestora"""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        """
        Inicializa agente de Oportunidade.
        
        Args:
            model: Modelo OpenAI a usar
            temperature: Criatividade (0.0 = determinístico, 1.0 = criativo)
        """
        self.model = model
        self.temperature = temperature
        self.section_name = "Oportunidade"
        self.llm = None  # Será injetado pelo LangGraph orchestrator
    
    def set_llm(self, llm):
        """Injeta LLM compartilhado (usado pelo LangGraph orchestrator)"""
        self.llm = llm
    
    def generate(self, facts: Dict[str, Any], rag_context: Optional[str] = None) -> str:
        """
        Gera seção de Oportunidade.
        
        Args:
            facts: Facts extraídos do CIM
            rag_context: Contexto opcional do documento original
        
        Returns:
            Texto da seção (parágrafos separados por \\n\\n)
        """
        # 1. Query de facts relevantes
        fund_structure_section = build_facts_section(facts, "transacao", [
            "fund_size_target", "fund_size_committed", "fund_vintage",
            "fundraising_status", "first_close_date", "final_close_target"
        ])
        
        economic_terms_section = build_facts_section(facts, "transacao", [
            "minimum_commitment", "management_fee", "carried_interest",
            "hurdle_rate", "catch_up", "investment_period",
            "fund_term", "gp_commitment"
        ])
        
        strategy_section = build_facts_section(facts, "qualitativo", [
            "investment_rationale", "market_opportunity",
            "differentiation", "timing_rationale"
        ])
        
        # System prompt especializado
        system_prompt = f"""Você é um analista de Private Equity escrevendo a seção de OPORTUNIDADE de um Short Memo sobre uma gestora.

CONTEXTO: Short Memo Gestora - detalhamento da proposta de investimento no fundo.

ESTRUTURA OBRIGATÓRIA (2-3 parágrafos):
1. Estrutura do fundo atual (tamanho target, status de fundraising)
2. Termos econômicos (commitment mínimo, fees, carry, hurdle)
3. Racional estratégico e timing

REGRAS:
- Tom objetivo e claro sobre termos comerciais
- SEMPRE use "R$ XX milhões/bilhões" para tamanhos e commitments
- Especifique termos com precisão:
  * Management fee: "X% ao ano sobre committed capital"
  * Carried interest: "XX% após hurdle de Y%"
  * Commitment mínimo: "R$ X milhões"
- Mencione estágio de fundraising (first close, % committed)
- Explique timing: por que investir agora (ciclo, oportunidades)
- Se houver GP commitment: mencione alinhamento de interesses
- Seja transparente sobre termos - sem esconder informações

OUTPUT: Retorne APENAS os parágrafos, sem títulos ou marcadores."""
        
        # 4. Human prompt com facts
        human_prompt = f"""Gere a seção de OPORTUNIDADE para esta gestora:

{fund_structure_section}

{economic_terms_section}

{strategy_section}

Lembre-se: 2-3 parágrafos, foco em estrutura do fundo, termos econômicos e racional de timing."""
        
        # 5. Gerar com LLM
        # Usar LLM injetado se disponível, senão criar novo (compatibilidade)
        if not self.llm:
            apikey = os.getenv("OPENAI_API_KEY")
            if not apikey:
                raise ValueError("OPENAI_API_KEY não encontrada no ambiente")
            self.llm = ChatOpenAI(model=self.model, api_key=apikey, temperature=self.temperature)
        
        llm = self.llm
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        response = llm.invoke(messages)
        
        # 6. Pós-processamento
        return fix_number_formatting(response.content.strip())
