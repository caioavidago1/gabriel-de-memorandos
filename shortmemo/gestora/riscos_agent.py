"""
Agente especializado em RISCOS E CONSIDERAÇÕES para Short Memo Gestora

RESPONSABILIDADE:
- Gerar seção "Riscos e Considerações" identificando pontos de atenção
- Contexto: Riscos de concentração, track record, mercado, equipe

ESTRUTURA:
- 2-3 parágrafos OU lista organizada por categoria
- Categorias: Estratégia, Portfólio, Governança, Mercado

VERSÃO: 1.0
"""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from .facts_builder import build_facts_section
from .validator import fix_number_formatting


class RiscosAgent:
    """Agente especializado em gerar Riscos e Considerações para Short Memo Gestora"""
    
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.25):
        """
        Inicializa agente de Riscos e Considerações.
        
        Args:
            model: Modelo OpenAI a usar
            temperature: Criatividade (0.0 = determinístico, 1.0 = criativo)
        """
        self.model = model
        self.temperature = temperature
        self.section_name = "Riscos e Considerações"
        self.llm = None  # Será injetado pelo LangGraph orchestrator
    
    def set_llm(self, llm):
        """Injeta LLM compartilhado (usado pelo LangGraph orchestrator)"""
        self.llm = llm
    
    def generate(self, facts: Dict[str, Any], rag_context: Optional[str] = None) -> str:
        """
        Gera seção de Riscos e Considerações.
        
        Args:
            facts: Facts extraídos do CIM
            rag_context: Contexto opcional do documento original
        
        Returns:
            Texto da seção (parágrafos ou lista organizada)
        """
        # 1. Query de facts relevantes
        portfolio_risks_section = build_facts_section(facts, "qualitativo", [
            "portfolio_concentration", "sector_concentration",
            "geographic_concentration", "active_monitoring"
        ])
        
        strategy_risks_section = build_facts_section(facts, "qualitativo", [
            "strategy_risks", "market_timing", "competition",
            "execution_risks", "key_person_risk"
        ])
        
        track_record_risks_section = build_facts_section(facts, "retornos", [
            "track_record_maturity", "unrealized_valuations",
            "vintage_performance_variance", "exit_environment"
        ])
        
        governance_section = build_facts_section(facts, "qualitativo", [
            "team_stability", "succession_planning",
            "conflicts_of_interest", "transparency"
        ])
        
        # System prompt especializado
        system_prompt = f"""Você é um analista de Private Equity escrevendo a seção de RISCOS E CONSIDERAÇÕES de um Short Memo sobre uma gestora.

CONTEXTO: Short Memo Gestora - identificação de pontos de atenção e riscos materiais.

ESTRUTURA SUGERIDA (escolher formato mais adequado):
OPÇÃO 1 - Parágrafos (2-3):
- Parágrafo 1: Riscos de estratégia e mercado
- Parágrafo 2: Riscos de portfólio e concentração
- Parágrafo 3: Riscos de governança e equipe

OPÇÃO 2 - Lista organizada por categoria:
- **Estratégia**: [riscos estratégicos]
- **Portfólio**: [concentração, exposição]
- **Governança**: [equipe, key person]
- **Mercado**: [ciclo, competição]

REGRAS:
- Tom objetivo e construtivo (não alarmista)
- Foco em riscos MATERIAIS e quantificáveis
- Mencione concentrações específicas: "XX% do portfólio em setor Y"
- Avalie maturação do track record: "ZZ% do MOIC não realizado"
- Identifique key person risks se relevante
- Considere riscos de timing de mercado (valuations altos, saídas difíceis)
- Seja balanceado: riscos sem exagero, mas sem omitir pontos críticos
- Use dados e números quando disponível

OUTPUT: Retorne APENAS os parágrafos ou lista organizada, sem títulos de seção."""
        
        # 4. Human prompt com facts
        human_prompt = f"""Gere a seção de RISCOS E CONSIDERAÇÕES para esta gestora:

{portfolio_risks_section}

{strategy_risks_section}

{track_record_risks_section}

{governance_section}

Lembre-se: Identifique riscos materiais de estratégia, portfólio, governança e mercado. Seja objetivo e construtivo."""
        
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
