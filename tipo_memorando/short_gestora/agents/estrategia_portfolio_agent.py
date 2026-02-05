"""
Agente especializado em ESTRATÉGIA E PORTFÓLIO para Short Memo Gestora

RESPONSABILIDADE:
- Gerar seção "Estratégia e Portfólio" detalhando abordagem de investimento
- Contexto: Tese de investimento, setores-alvo, portfólio atual, diversificação

ESTRUTURA:
- 3-4 parágrafos
- Parágrafo 1: Tese de investimento e critérios de seleção
- Parágrafo 2: Setores-alvo e posicionamento competitivo
- Parágrafo 3: Composição atual do portfólio (se aplicável)
- Parágrafo 4: Processo de value creation e governança

VERSÃO: 1.0
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from ..facts_builder import build_facts_section
from ..validator import fix_number_formatting


class EstrategiaPortfolioAgent:
    """Agente especializado em gerar Estratégia e Portfólio para Short Memo Gestora"""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        """
        Inicializa agente de Estratégia e Portfólio.
        
        Args:
            model: Modelo OpenAI a usar
            temperature: Criatividade (0.0 = determinístico, 1.0 = criativo)
        """
        self.model = model
        self.temperature = temperature
        self.section_name = "Estratégia e Portfólio"
        self.llm = None  # Será injetado pelo LangGraph orchestrator
    
    def set_llm(self, llm):
        """Injeta LLM compartilhado (usado pelo LangGraph orchestrator)"""
        self.llm = llm
    
    def generate(self, facts: Dict[str, Any], rag_context: Optional[str] = None) -> str:
        """
        Gera seção de Estratégia e Portfólio.
        
        Args:
            facts: Facts extraídos do CIM
            rag_context: Contexto opcional do documento original
        
        Returns:
            Texto da seção (parágrafos separados por \\n\\n)
        """
        # 1. Query de facts relevantes
        strategy_section = build_facts_section(facts, "qualitativo", [
            "strategy_type", "investment_thesis", "target_sectors", 
            "geographic_focus", "ticket_size_min", "ticket_size_max",
            "target_companies_profile", "value_creation_approach"
        ])
        
        portfolio_section = build_facts_section(facts, "qualitativo", [
            "current_portfolio_size", "portfolio_companies", 
            "diversification", "sector_allocation"
        ])
        
        process_section = build_facts_section(facts, "qualitativo", [
            "investment_process", "governance_approach", 
            "board_participation", "value_creation_levers"
        ])
        
        # System prompt especializado
        system_prompt = f"""Você é um analista de Private Equity escrevendo a seção de ESTRATÉGIA E PORTFÓLIO de um Short Memo sobre uma gestora.

CONTEXTO: Short Memo Gestora - análise da abordagem de investimento e portfólio.

ESTRUTURA OBRIGATÓRIA (3-4 parágrafos):
1. Tese de investimento e critérios de seleção
2. Setores-alvo e posicionamento competitivo
3. Composição atual do portfólio
4. Processo de value creation e governança

REGRAS:
- Tom analítico e objetivo
- SEMPRE use "R$ XX milhões/bilhões" para tickets
- Detalhe critérios específicos de seleção (EBITDA mínimo, receita, perfil)
- Mencione setores-alvo com clareza
- Se houver portfólio: mencione número de empresas, setores, ticket médio
- Descreva abordagem de value creation (operacional, M&A, expansão)
- Evite generalidades - seja específico
- Baseie-se em fatos e dados

OUTPUT: Retorne APENAS os parágrafos, sem títulos ou marcadores."""
        
        # 4. Human prompt com facts
        human_prompt = f"""Gere a seção de ESTRATÉGIA E PORTFÓLIO para esta gestora:

{strategy_section}

{portfolio_section}

{process_section}

Lembre-se: 3-4 parágrafos, foco em tese, setores-alvo, portfólio atual e value creation."""
        
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
